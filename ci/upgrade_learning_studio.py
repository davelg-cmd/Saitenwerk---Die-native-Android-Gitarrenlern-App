# Premium Lernstudio: adaptive XP, guided sessions and level progression
#!/usr/bin/env python3
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("ChordPreviewPlayer.play(ch)", "ChordPreviewPlayer.play(ch, a)")
# Keep the already-upgraded learning studio intact. Replacing it with the legacy
# template would reintroduce ToneGenerator references and overwrite chord audio.
if (
    "object GuitarAudioEngine {" in s
    and "learn_strum_chord" in s
    and "GuitarAudioEngine.playTick(a, strong)" in s
    and "GuitarAudioEngine.playProgression" in s
):
    print("LERNSTUDIO: PREMIUM-VERSION MIT SHARED GUITAR AUDIO BEREITS AKTIV")
    raise SystemExit(0)
# Remove the redundant orientation hint from the chord detail; keep the symbol legend.
s = s.replace(
    r"Hochkant: tiefe E-Saite links · hohe e-Saite rechts\n× = nicht anschlagen · ○ = leere Saite",
    "× = nicht anschlagen · ○ = leere Saite",
)

start = s.find("class LearnFragment : Fragment() {")
end = s.find("\nclass PathFragment : Fragment() {", start)
if start < 0 or end < 0:
    raise SystemExit("FEHLER: LearnFragment nicht gefunden.")

replacement = r'''class LearnFragment : Fragment() {
    private var chordTraining: ChordTrainingPanel? = null
    private var rhythmTone: ToneGenerator? = null
    private var rhythmHandler: Handler? = null
    private var rhythmRunning = false
    private var rhythmBeat = 0
    private var rhythmBpm = 80
    private var rhythmMeter = "4/4"
    private var rhythmStartedAt = 0L
    private var quizStartedAt = 0L
    private var onSessionElapsed: ((Int) -> Unit)? = null
    private var strumTone: ToneGenerator? = null
    private var strumHandler: Handler? = null
    private var strumRunning = false
    private var strumStep = 0
    private var strumStartedAt = 0L

    override fun onDestroyView() {
        chordTraining?.stop()
        chordTraining = null
        finishQuizSession()
        stopRhythm()
        stopStrumming()
        onSessionElapsed = null
        super.onDestroyView()
    }

    override fun onCreateView(i: android.view.LayoutInflater, c: ViewGroup?, s: Bundle?): View {
        val a = requireActivity() as MainActivity
        val prefs = a.getSharedPreferences("saitenwerk", 0)
        val root = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(16), a.dp(8), a.dp(16), a.dp(24))
        }
        val scroll = ScrollView(a).apply { clipToPadding = false; isFillViewport = true }
        val content = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(0, 0, 0, a.dp(20)) }
        scroll.addView(content)

        fun roundedCard(): MaterialCardView = a.card().apply {
            radius = a.dp(20).toFloat()
            strokeColor = a.getColor(R.color.sw_outline)
            strokeWidth = a.dp(1)
            cardElevation = a.dp(2).toFloat()
        }
        fun addGap(dp: Int = 10) { content.addView(Space(a), LinearLayout.LayoutParams(1, a.dp(dp))) }

        fun updatePracticeStats() {
            val correct = prefs.getInt("learn_quiz_correct", 0)
            val total = prefs.getInt("learn_quiz_total", 0)
            val best = prefs.getInt("learn_best_quiz_streak", 0)
            val day = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date())
            val dailySeconds = if (prefs.getString("learn_daily_day", "") == day) prefs.getInt("learn_daily_seconds", prefs.getInt("learn_daily_minutes", 0) * 60) else 0
            val minutes = String.format(java.util.Locale.GERMANY, "%.1f min", dailySeconds / 60.0)
            val routineDone = if (prefs.getString("learn_routine_day", "") == day) Integer.bitCount(prefs.getInt("learn_routine_done", 0)) else 0
            val routineTotal = 5
            val rate = if (total > 0) correct * 100 / total else 0
            val stats = content.findViewWithTag<LinearLayout>("learnStats")
            stats?.let {
                it.removeAllViews()
                fun stat(value: String, label: String) {
                    val box = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; gravity = Gravity.CENTER }
                    box.addView(TextView(a).apply { text = value; textSize = 21f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_copper)); gravity = Gravity.CENTER })
                    box.addView(TextView(a).apply { text = label; textSize = 10f; setTextColor(a.getColor(R.color.sw_muted)); gravity = Gravity.CENTER; setPadding(0, a.dp(2), 0, 0) })
                    it.addView(box, LinearLayout.LayoutParams(0, a.dp(58), 1f))
                }
                stat("$routineDone/$routineTotal", "Heute")
                stat(minutes, "Übungszeit")
                stat("$rate%", "Quiz-Treffer")
                stat("$best", "Beste Serie")
            }
            content.findViewWithTag<TextView>("learnToday")?.text =
                if (routineDone == routineTotal) "Heute geschafft · starke Arbeit!" else "Heute: $routineDone von $routineTotal Einheiten"
            content.findViewWithTag<ProgressBar>("learnTodayProgress")?.apply { max = routineTotal; progress = routineDone }
        }

        fun recordPracticeDay() {
            val day = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date())
            val last = prefs.getString("learn_last_session_day", "")
            val streak = prefs.getInt("learn_streak", 0)
            val yesterday = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date(System.currentTimeMillis() - 86400000L))
            if (last != day) {
                prefs.edit().putString("learn_last_session_day", day).putInt("learn_streak", if (last == yesterday) streak + 1 else 1).apply()
            }
        }

        fun recordSession(seconds: Int) {
            val day = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date())
            recordPracticeDay()
            val oldSeconds = if (prefs.getString("learn_daily_day", "") == day) prefs.getInt("learn_daily_seconds", prefs.getInt("learn_daily_minutes", 0) * 60) else 0
            val totalSeconds = oldSeconds + seconds.coerceAtLeast(1)
            val cal = java.util.Calendar.getInstance()
            val weekKey = cal.get(java.util.Calendar.YEAR).toString() + "-" + cal.get(java.util.Calendar.WEEK_OF_YEAR).toString()
            val oldWeekSeconds = if (prefs.getString("learn_week_key", "") == weekKey) prefs.getInt("learn_week_seconds", 0) else 0
            prefs.edit().putString("learn_daily_day", day).putInt("learn_daily_seconds", totalSeconds)
                .putInt("learn_daily_minutes", totalSeconds / 60)
                .putString("learn_week_key", weekKey)
                .putInt("learn_week_seconds", oldWeekSeconds + seconds.coerceAtLeast(1))
                .putInt("learn_sessions", prefs.getInt("learn_sessions", 0) + 1).apply()
            updatePracticeStats()
        }
        onSessionElapsed = { seconds -> recordSession(seconds) }

        fun finishQuizSession() { this@LearnFragment.finishQuizSession() }

        var overviewAction: (() -> Unit)? = null

        fun panel(heading: String, description: String): Pair<MaterialCardView, LinearLayout> {
            val card = roundedCard()
            val box = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(16), a.dp(15), a.dp(16), a.dp(16)) }
            box.addView(TextView(a).apply { text = heading; textSize = 19f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_copper)) })
            box.addView(a.body(description, 13f))
            card.addView(box)
            return card to box
        }

        fun showQuiz() {
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); stopStrumming(); content.removeAllViews()
            quizStartedAt = android.os.SystemClock.elapsedRealtime()
            val (card, box) = panel("Akkord-Blitztrainer", "Erkenne Griffbilder. Die Serie steigt nur bei richtigen Antworten – so siehst du sofort, wie sicher du bist.")
            val header = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
            val score = TextView(a).apply { textSize = 13f; setTextColor(a.getColor(R.color.sw_muted)) }
            val streak = TextView(a).apply { textSize = 13f; setTextColor(a.getColor(R.color.sw_copper)); gravity = Gravity.END }
            header.addView(score, LinearLayout.LayoutParams(0, -2, 1f)); header.addView(streak, LinearLayout.LayoutParams(0, -2, 1f))
            box.addView(header)
            val diagram = FrameLayout(a); box.addView(diagram, LinearLayout.LayoutParams(-1, a.dp(210)))
            val choices = GridLayout(a).apply { columnCount = 2 }; box.addView(choices)
            val feedback = TextView(a).apply { text = "Wähle den passenden Akkord."; gravity = Gravity.CENTER; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(10), 0, a.dp(6)) }
            box.addView(feedback)
            val actions = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
            val next = a.button("Nächster Akkord"); val finish = a.button("Fertig")
            actions.addView(next, LinearLayout.LayoutParams(0, a.dp(46), 1f))
            actions.addView(finish, LinearLayout.LayoutParams(0, a.dp(46), 1f).apply { leftMargin = a.dp(6) })
            box.addView(actions)
            var answer = ""; var locked = false; var localStreak = 0

            fun updateHeader() {
                val total = prefs.getInt("learn_quiz_total", 0); val correct = prefs.getInt("learn_quiz_correct", 0)
                val rate = if (total > 0) correct * 100 / total else 0
                score.text = "Gesamt: $correct/$total · $rate%"; streak.text = "Serie: $localStreak"
            }
            fun newQuestion() {
                val pool = ChordLibrary.all.filter { it.name in listOf("C", "G", "D", "A", "E", "F", "Am", "Em", "Dm") }
                if (pool.size < 4) return
                val shape = pool.random(); answer = shape.name; locked = false
                feedback.text = "Welcher Akkord ist auf dem Griffbild zu sehen?"; feedback.setTextColor(a.getColor(R.color.sw_muted))
                diagram.removeAllViews(); diagram.addView(ChordDiagramView(a, shape), FrameLayout.LayoutParams(-1, -1)); choices.removeAllViews()
                val options = (listOf(answer) + pool.filter { it.name != answer }.shuffled().take(3).map { it.name }).shuffled()
                options.forEach { option ->
                    val b = a.button(option)
                    b.setOnClickListener {
                        if (locked) return@setOnClickListener
                        locked = true
                        val correctAnswer = option == answer
                        if (correctAnswer) localStreak++ else localStreak = 0
                        val total = prefs.getInt("learn_quiz_total", 0) + 1
                        val correct = prefs.getInt("learn_quiz_correct", 0) + if (correctAnswer) 1 else 0
                        val best = maxOf(prefs.getInt("learn_best_quiz_streak", 0), localStreak)
                        prefs.edit().putInt("learn_quiz_total", total).putInt("learn_quiz_correct", correct).putInt("learn_best_quiz_streak", best)
                            .putInt("learn_xp", prefs.getInt("learn_xp", 0) + if (correctAnswer) 10 else 3).apply()
                        feedback.text = if (correctAnswer) "Richtig! Serie $localStreak." else "Noch nicht ganz – gesucht war $answer."
                        feedback.setTextColor(a.getColor(if (correctAnswer) R.color.sw_copper else R.color.sw_muted))
                        for (j in 0 until choices.childCount) choices.getChildAt(j).isEnabled = false
                        updateHeader(); updatePracticeStats()
                    }
                    choices.addView(b, GridLayout.LayoutParams().apply { width = 0; height = a.dp(46); columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f); setMargins(a.dp(3), a.dp(3), a.dp(3), a.dp(3)) })
                }
                updateHeader()
            }
            next.setOnClickListener { newQuestion() }
            finish.setOnClickListener { finishQuizSession(); overviewAction?.invoke() }
            newQuestion(); content.addView(card)
        }

        fun showChanges() {
            prefs.edit().putInt("learn_skill_changes", prefs.getInt("learn_skill_changes", 0) + 1).apply()
            finishQuizSession(); stopRhythm(); content.removeAllViews()
            content.addView(a.body("Dein Haupttraining für saubere Akkordwechsel. Wähle Akkorde, Takt und Tempo direkt im Trainer und steigere dich erst, wenn die Wechsel sicher sitzen."))
            chordTraining = ChordTrainingPanel(a); content.addView(chordTraining, LinearLayout.LayoutParams(-1, -2))
        }

        fun showRhythm() {
            prefs.edit().putInt("learn_skill_rhythm", prefs.getInt("learn_skill_rhythm", 0) + 1).apply()
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); content.removeAllViews()
            val (card, box) = panel("Rhythmus & Timing", "Trainiere Puls, Taktgefühl und Geschwindigkeit. Im 6/8-Takt hörst du zwei große Pulse pro Takt.")
            rhythmBpm = prefs.getInt("learn_rhythm_bpm", 80).coerceIn(50, 160)
            rhythmMeter = prefs.getString("learn_rhythm_meter", "4/4") ?: "4/4"
            val tempoLabel = TextView(a).apply { text = "BPM $rhythmBpm"; textSize = 18f; setTextColor(a.getColor(R.color.sw_text)); gravity = Gravity.CENTER }
            box.addView(tempoLabel, LinearLayout.LayoutParams(-1, a.dp(36)))
            val slider = SeekBar(a).apply { max = 110; progress = rhythmBpm - 50 }
            slider.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(v: SeekBar?, p: Int, from: Boolean) { rhythmBpm = 50 + p; tempoLabel.text = "BPM $rhythmBpm"; prefs.edit().putInt("learn_rhythm_bpm", rhythmBpm).apply() }
                override fun onStartTrackingTouch(v: SeekBar?) {}
                override fun onStopTrackingTouch(v: SeekBar?) {}
            })
            box.addView(slider, LinearLayout.LayoutParams(-1, a.dp(42)))
            val meterRow = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
            meterRow.addView(TextView(a).apply { text = "Takt"; textSize = 13f; setTextColor(a.getColor(R.color.sw_muted)) }, LinearLayout.LayoutParams(0, a.dp(46), 1f))
            val meterButton = a.button(rhythmMeter); meterRow.addView(meterButton, LinearLayout.LayoutParams(a.dp(100), a.dp(46))); box.addView(meterRow)
            val meterHint = TextView(a).apply { text = if (rhythmMeter == "6/8") "Zwei große Pulse pro Takt (1–2), jeweils über drei Achtel." else "Ein Puls pro Zählzeit."; textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, 0, 0, a.dp(4)) }
            box.addView(meterHint)
            meterButton.setOnClickListener {
                val meters = arrayOf("2/4", "3/4", "4/4", "6/8")
                androidx.appcompat.app.AlertDialog.Builder(a).setTitle("Taktart").setSingleChoiceItems(meters, meters.indexOf(rhythmMeter).coerceAtLeast(0)) { d, which ->
                    rhythmMeter = meters[which]; meterButton.text = rhythmMeter
                    meterHint.text = if (rhythmMeter == "6/8") "Zwei große Pulse pro Takt (1–2), jeweils über drei Achtel." else "Ein Puls pro Zählzeit."
                    prefs.edit().putString("learn_rhythm_meter", rhythmMeter).apply(); d.dismiss()
                }.setNegativeButton("Abbrechen", null).show()
            }
            val beat = TextView(a).apply { text = "Bereit"; textSize = 30f; gravity = Gravity.CENTER; setTextColor(a.getColor(R.color.sw_copper)); setPadding(0, a.dp(12), 0, a.dp(8)) }
            box.addView(beat, LinearLayout.LayoutParams(-1, a.dp(72)))
            val start = a.button("Metronom starten"); box.addView(start, LinearLayout.LayoutParams(-1, a.dp(48)))
            start.setOnClickListener {
                if (rhythmRunning) { stopRhythm(); start.text = "Metronom starten"; beat.text = "Pausiert" }
                else {
                    rhythmRunning = true; rhythmStartedAt = android.os.SystemClock.elapsedRealtime(); rhythmBeat = 0; rhythmTone = ToneGenerator(AudioManager.STREAM_MUSIC, 65); rhythmHandler = Handler(Looper.getMainLooper()); start.text = "Metronom stoppen"
                    val compoundSixEight = rhythmMeter == "6/8"
                    val beatsPerBar = if (compoundSixEight) 2 else rhythmMeter.substringBefore("/").toIntOrNull() ?: 4
                    val pulseInterval = if (compoundSixEight) 90000L / rhythmBpm else 60000L / rhythmBpm
                    val task = object : Runnable {
                        override fun run() {
                            if (!rhythmRunning) return
                            val beatInBar = rhythmBeat % beatsPerBar
                            val strong = beatInBar == 0
                            rhythmTone?.startTone(if (strong) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP, if (strong) 80 else 55)
                            beat.text = if (strong) "1 · TAKT" else "${beatInBar + 1}"
                            rhythmBeat++; rhythmHandler?.postDelayed(this, pulseInterval.coerceAtLeast(100L))
                        }
                    }
                    rhythmHandler?.post(task)
                }
            }
            content.addView(card)
        }

        fun showStrumming() {
            prefs.edit().putInt("learn_skill_strum", prefs.getInt("learn_skill_strum", 0) + 1).apply()
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); stopStrumming(); content.removeAllViews()
            val (card, box) = panel("Schlagmuster-Trainer", "Übe typische Gitarren-Schlagmuster im Takt. Der aktuelle Schlag wird hervorgehoben – danach spielst du ihn selbst.")
            val patterns = linkedMapOf(
                "Basis · ↓ ↑ ↓ ↑" to listOf("↓","↑","↓","↑"),
                "Pop · ↓ ↓ ↑ ↑ ↓ ↑" to listOf("↓","↓","↑","↑","↓","↑"),
                "Achtel · ↓ ↑ ↓ ↑ ↓ ↑ ↓ ↑" to listOf("↓","↑","↓","↑","↓","↑","↓","↑"),
                "Akustik · ↓ ↓ ↑ ↓ ↑" to listOf("↓","↓","↑","↓","↑"),
                "Flow · ↓ ↑ ↑ ↓ ↑ ↓" to listOf("↓","↑","↑","↓","↑","↓")
            )
            var selectedName = prefs.getString("learn_strum_pattern", patterns.keys.first()) ?: patterns.keys.first()
            var selected = patterns[selectedName] ?: patterns.values.first()
            var bpm = prefs.getInt("learn_strum_bpm", 80).coerceIn(50, 160)
            var step = 0
            var hits = 0
            var mistakes = 0
            var score = 0
            var combo = 0
            var bestCombo = 0
            var answered = false
            var expectedAt = 0L
            var difficulty = prefs.getString("learn_strum_difficulty", "Normal") ?: "Normal"
            val patternButton = a.button(selectedName)
            val patternHint = TextView(a).apply { text = "Pattern: " + selected.joinToString("  "); textSize = 16f; gravity = Gravity.CENTER; setTextColor(a.getColor(R.color.sw_text)); setPadding(0, a.dp(10), 0, a.dp(10)) }
            val beatRow = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
            val status = TextView(a).apply { text = "Bereit · spiele die hervorgehobenen Schläge"; textSize = 13f; gravity = Gravity.CENTER; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(6), 0, a.dp(8)) }
            val tempoLabel = TextView(a).apply { text = "Tempo: $bpm BPM"; textSize = 15f; setTextColor(a.getColor(R.color.sw_text)) }
            val slider = SeekBar(a).apply { max = 110; progress = bpm - 50 }
            val difficultyButton = a.button("Schwierigkeit · $difficulty")
            val stats = TextView(a).apply { text = "Punkte: 0 · Genauigkeit: 0% · Serie: 0"; textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); gravity = Gravity.CENTER }
            val timing = TextView(a).apply { text = "Timing-Fenster · ±300 ms"; textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); gravity = Gravity.CENTER }
            val start = a.button("Training starten")
            val down = a.button("↓ Abschlag")
            val up = a.button("↑ Aufschlag")
            val actionRow = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
            actionRow.addView(down, LinearLayout.LayoutParams(0, a.dp(50), 1f).apply { rightMargin = a.dp(4) })
            actionRow.addView(up, LinearLayout.LayoutParams(0, a.dp(50), 1f).apply { leftMargin = a.dp(4) })
            box.addView(patternButton, LinearLayout.LayoutParams(-1, a.dp(46)))
            box.addView(patternHint)
            box.addView(difficultyButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { topMargin = a.dp(5) })
            box.addView(beatRow, LinearLayout.LayoutParams(-1, a.dp(58)))
            box.addView(status)
            box.addView(tempoLabel)
            box.addView(slider, LinearLayout.LayoutParams(-1, a.dp(42)))
            box.addView(timing)
            box.addView(stats)
            box.addView(start, LinearLayout.LayoutParams(-1, a.dp(48)))
            box.addView(actionRow, LinearLayout.LayoutParams(-1, a.dp(54)).apply { topMargin = a.dp(6) })

            fun rebuildBeats() {
                beatRow.removeAllViews()
                selected.forEach { dir ->
                    beatRow.addView(TextView(a).apply {
                        text = dir; textSize = 22f; gravity = Gravity.CENTER; setTypeface(typeface, 1)
                        setTextColor(a.getColor(R.color.sw_muted))
                    }, LinearLayout.LayoutParams(0, a.dp(52), 1f))
                }
            }
            fun markBeat() {
                for (i in 0 until beatRow.childCount) {
                    val v = beatRow.getChildAt(i) as TextView
                    v.setTextColor(a.getColor(if (i == step) R.color.sw_copper else R.color.sw_muted))
                    v.textSize = if (i == step) 28f else 22f
                }
            }
            slider.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(v: SeekBar?, p: Int, from: Boolean) { bpm = 50 + p; tempoLabel.text = "Tempo: $bpm BPM"; prefs.edit().putInt("learn_strum_bpm", bpm).apply() }
                override fun onStartTrackingTouch(v: SeekBar?) {}
                override fun onStopTrackingTouch(v: SeekBar?) {}
            })
            patternButton.setOnClickListener {
                val names = patterns.keys.toTypedArray()
                androidx.appcompat.app.AlertDialog.Builder(a).setTitle("Schlagmuster auswählen")
                    .setSingleChoiceItems(names, names.indexOf(selectedName).coerceAtLeast(0)) { d, which ->
                        selectedName = names[which]; selected = patterns[selectedName] ?: selected
                        prefs.edit().putString("learn_strum_pattern", selectedName).apply()
                        step = 0; hits = 0; mistakes = 0; patternButton.text = selectedName
                        patternHint.text = "Pattern: " + selected.joinToString("  "); status.text = "Neues Muster gewählt · bereit"
                        rebuildBeats(); markBeat(); d.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
            fun userHit(direction: String) {
                if (!strumRunning || selected.isEmpty() || answered) return
                val expected = selected[step]
                val delta = kotlin.math.abs(android.os.SystemClock.elapsedRealtime() - expectedAt)
                val window = when (difficulty) {
                    "Leicht" -> 420L
                    "Schwer" -> 220L
                    "Profi" -> 140L
                    else -> 300L
                }
                answered = true
                if (direction == expected && delta <= window) {
                    hits++
                    combo++
                    bestCombo = maxOf(bestCombo, combo)
                    score += when {
                        delta <= 80L -> 100
                        delta <= 160L -> 80
                        else -> 60
                    } + combo.coerceAtMost(20) * 2
                    status.text = "✓ Perfekt · " + delta + " ms"
                } else {
                    mistakes++
                    combo = 0
                    status.text = if (direction != expected) "✕ " + direction + " · erwartet " + expected else "◷ Timing · " + delta + " ms"
                }
                val attempts = hits + mistakes
                val accuracy = if (attempts > 0) hits * 100 / attempts else 0
                stats.text = "Punkte: " + score + " · Genauigkeit: " + accuracy + "% · Serie: " + combo + " · Bestwert: " + bestCombo
            }
            down.setOnClickListener { userHit("↓") }
            up.setOnClickListener { userHit("↑") }
            difficultyButton.setOnClickListener {
                if (strumRunning) return@setOnClickListener
                val levels = arrayOf("Leicht", "Normal", "Schwer", "Profi")
                androidx.appcompat.app.AlertDialog.Builder(a)
                    .setTitle("Schwierigkeit")
                    .setSingleChoiceItems(levels, levels.indexOf(difficulty).coerceAtLeast(0)) { d, which ->
                        difficulty = levels[which]
                        difficultyButton.text = "Schwierigkeit · " + difficulty
                        prefs.edit().putString("learn_strum_difficulty", difficulty).apply()
                        timing.text = "Timing-Fenster · ±" + when (difficulty) {
                            "Leicht" -> 420
                            "Schwer" -> 220
                            "Profi" -> 140
                            else -> 300
                        } + " ms"
                        d.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
            start.setOnClickListener {
                if (strumRunning) {
                    prefs.edit().putInt("learn_strum_best_score", maxOf(prefs.getInt("learn_strum_best_score", 0), score)).apply()
                    stopStrumming(); start.text = "Training starten"; status.text = "Pausiert · " + score + " Punkte"
                } else {
                    strumRunning = true; strumStartedAt = android.os.SystemClock.elapsedRealtime(); strumStep = 0
                    start.text = "Training stoppen"; step = 0; hits = 0; mistakes = 0; score = 0; combo = 0; bestCombo = 0; answered = false
                    strumTone = ToneGenerator(AudioManager.STREAM_MUSIC, 60); strumHandler = Handler(Looper.getMainLooper())
                    val interval = (60000L / bpm / 2).coerceAtLeast(100L)
                    val task = object : Runnable {
                        override fun run() {
                            if (!strumRunning) return
                            step = strumStep % selected.size
                            answered = false
                            expectedAt = android.os.SystemClock.elapsedRealtime()
                            val strong = step == 0
                            strumTone?.startTone(if (strong) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP, if (strong) 75 else 45)
                            markBeat(); strumStep++
                            strumHandler?.postDelayed(this, interval)
                        }
                    }
                    strumHandler?.post(task); markBeat()
                }
            }
            timing.text = "Timing-Fenster · ±" + when (difficulty) {
                "Leicht" -> 420
                "Schwer" -> 220
                "Profi" -> 140
                else -> 300
            } + " ms"
            rebuildBeats(); markBeat()
            content.addView(card)
        }

        fun showSongPractice() {
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); stopStrumming()
            content.removeAllViews()
            val (card, box) = panel("Song-Praxis", "Übe typische Song-Akkordfolgen im eigenen Tempo. Wähle eine Folge und trainiere anschließend Wechsel, Rhythmus und Anschlag.")
            val selected = TextView(a).apply {
                text = "Aktuelle Folge: " + (prefs.getString("learn_song_progression", "G – D – Em – C") ?: "G – D – Em – C")
                textSize = 16f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_copper))
                setPadding(0, a.dp(10), 0, a.dp(8))
            }
            box.addView(selected)
            val progressions = listOf("G – D – Em – C", "C – Am – F – G", "Am – F – C – G", "Em – C – G – D")
            progressions.forEach { progression ->
                box.addView(a.button(progression).apply {
                    isAllCaps = false
                    setOnClickListener {
                        prefs.edit().putString("learn_song_progression", progression).apply()
                        selected.text = "Aktuelle Folge: $progression"
                    }
                }, LinearLayout.LayoutParams(-1, a.dp(44)).apply { topMargin = a.dp(5) })
            }
            box.addView(a.body("Tipp: Spiele jeden Akkord zunächst vier gleichmäßige Schläge. Wenn der Wechsel sicher sitzt, erhöhe das Tempo schrittweise.", 12f).apply {
                setPadding(0, a.dp(10), 0, a.dp(8))
            })
            content.addView(card)
            val actions = roundedCard()
            val actionBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(14), a.dp(12), a.dp(14), a.dp(12)) }
            actionBox.addView(a.button("↔ Akkordwechsel trainieren").apply { setOnClickListener { showChanges() } },
                LinearLayout.LayoutParams(-1, a.dp(46)).apply { bottomMargin = a.dp(8) })
            actionBox.addView(a.button("↘ Schlagmuster trainieren").apply { setOnClickListener { showStrumming() } },
                LinearLayout.LayoutParams(-1, a.dp(46)).apply { bottomMargin = a.dp(8) })
            actionBox.addView(a.button("♩ Rhythmus und Tempo üben").apply { setOnClickListener { showRhythm() } },
                LinearLayout.LayoutParams(-1, a.dp(46)))
            actionBox.addView(a.button("Zur Lernstudio-Übersicht").apply { setOnClickListener { overviewAction?.invoke() } },
                LinearLayout.LayoutParams(-1, a.dp(44)).apply { topMargin = a.dp(12) })
            actions.addView(actionBox)
            content.addView(actions)
        }

        fun showGuidedSession() {
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); stopStrumming(); content.removeAllViews()
            val (card, box) = panel("🎯 Geführte 10-Minuten-Session", "Eine kompakte, adaptive Trainingseinheit. Die Reihenfolge passt sich deinem bisherigen Lernstand an.")
            val day = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date())
            val doneKey = "learn_guided_day"; val doneCountKey = "learn_guided_done"
            val already = if (prefs.getString(doneKey, "") == day) prefs.getInt(doneCountKey, 0) else 0
            val tasks = listOf(
                Triple("Akkorde", "2 Min · C – G – Am – F sauber greifen", 2),
                Triple("Wechsel", "3 Min · langsame, gleichmäßige Wechsel", 3),
                Triple("Rhythmus", "2 Min · Metronom und gleichmäßiger Puls", 2),
                Triple("Schlagmuster", "2 Min · Anschlag mit Timing-Fenster", 2),
                Triple("Freies Spielen", "1 Min · das Gelernte in einem Song anwenden", 1)
            )
            val progressLabel = TextView(a).apply { textSize = 13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, 0, 0, a.dp(8)) }
            val progress = ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply { max = 10; this.progress = already.coerceIn(0, 10) }
            box.addView(progressLabel); box.addView(progress, LinearLayout.LayoutParams(-1, a.dp(10)).apply { bottomMargin = a.dp(10) })
            fun updateGuided() {
                val n = if (prefs.getString(doneKey, "") == day) prefs.getInt(doneCountKey, 0) else 0
                progress.progress = n.coerceIn(0, 10)
                progressLabel.text = if (n >= 10) "Heute abgeschlossen · +10 XP" else n.toString() + "/10 Minuten abgeschlossen"
            }
            tasks.forEach { task ->
                val row = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(0, a.dp(5), 0, a.dp(5)) }
                val textBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL }
                textBox.addView(TextView(a).apply { text = task.first; textSize = 15f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text)) })
                textBox.addView(TextView(a).apply { text = task.second; textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(2), 0, 0) })
                row.addView(textBox, LinearLayout.LayoutParams(0, -2, 1f))
                row.addView(a.button("Start").apply {
                    minWidth = a.dp(74)
                    setOnClickListener {
                        val current = if (prefs.getString(doneKey, "") == day) prefs.getInt(doneCountKey, 0) else 0
                        val next = (current + task.third).coerceAtMost(10)
                        prefs.edit().putString(doneKey, day).putInt(doneCountKey, next).putInt("learn_xp", prefs.getInt("learn_xp", 0) + task.third * 10).apply()
                        updateGuided()
                        (it as Button).text = "✓"; it.isEnabled = false
                        recordSession(task.third * 60)
                    }
                })
                box.addView(row)
            }
            box.addView(a.button("Schlagmuster direkt trainieren").apply { setOnClickListener { showStrumming() } }, LinearLayout.LayoutParams(-1, a.dp(46)).apply { topMargin = a.dp(8) })
            updateGuided()
            content.addView(card)
        }

        fun showRoutine() {
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); content.removeAllViews()
            val (card, box) = panel("Deine tägliche 10-Minuten-Routine", "Fünf kurze Einheiten statt einer langen Session. Hake ab, was du heute erledigt hast.")
            val day = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date())
            if (prefs.getString("learn_routine_day", "") != day) prefs.edit().putString("learn_routine_day", day).putInt("learn_routine_done", 0).apply()
            val tasks = listOf("2 Min. Akkordgriffe sauber aufsetzen", "3 Min. C – G – Am – F wechseln", "2 Min. Rhythmus mit Metronom", "2 Min. einen Song begleiten", "1 Min. freies Spielen")
            val progressLabel = TextView(a).apply { setTextColor(a.getColor(R.color.sw_text)); textSize = 14f }
            val progress = ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply { max = tasks.size }
            box.addView(progressLabel); box.addView(progress, LinearLayout.LayoutParams(-1, a.dp(10)).apply { bottomMargin = a.dp(8) })
            fun update(mask: Int) {
                val n = Integer.bitCount(mask); progress.progress = n
                progressLabel.text = if (n == tasks.size) "Heute komplett · 10 Minuten geschafft" else "Heute erledigt: $n von ${tasks.size}"
                prefs.edit().putInt("learn_routine_done", mask).apply(); updatePracticeStats()
            }
            tasks.forEachIndexed { index, task ->
                val cb = CheckBox(a).apply { text = task; textSize = 14f; setTextColor(a.getColor(R.color.sw_text)); isChecked = (prefs.getInt("learn_routine_done", 0) and (1 shl index)) != 0 }
                cb.setOnCheckedChangeListener { _, checked ->
                    val previous = prefs.getInt("learn_routine_done", 0)
                    var mask = previous; mask = if (checked) mask or (1 shl index) else mask and (1 shl index).inv()
                    if (checked && previous == 0) recordPracticeDay()
                    update(mask)
                }
                box.addView(cb)
            }
            update(prefs.getInt("learn_routine_done", 0))
            box.addView(a.button("Lernpfad öffnen").apply { setOnClickListener { a.openSection(6) } }, LinearLayout.LayoutParams(-1, a.dp(46)).apply { topMargin = a.dp(8) })
            content.addView(card)
        }

        overviewAction = {
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); content.removeAllViews()
            content.addView(a.title("Lernstudio"))
            content.addView(a.body("Dein persönlicher Trainingsbereich für Akkorde, Rhythmus, Timing, Schlagmuster und Songs."))

            val xp = prefs.getInt("learn_xp", 0)
            val level = (xp / 100) + 1
            val levelXp = xp % 100
            val levelCard = roundedCard()
            val levelBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(16), a.dp(15), a.dp(16), a.dp(15)) }
            levelBox.addView(TextView(a).apply { text = "⭐ Level " + level; textSize = 22f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_copper)) })
            levelBox.addView(TextView(a).apply { text = xp.toString() + " XP · " + (100 - levelXp) + " XP bis Level " + (level + 1); textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(3), 0, a.dp(8)) })
            levelBox.addView(ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply { max = 100; progress = levelXp }, LinearLayout.LayoutParams(-1, a.dp(10)))
            levelCard.addView(levelBox); content.addView(levelCard); addGap(8)

            val sessionCard = roundedCard()
            val sessionBox = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(a.dp(14), a.dp(12), a.dp(14), a.dp(12)) }
            val sessionText = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL }
            sessionText.addView(TextView(a).apply { text = "🎯 Heute trainieren"; textSize = 17f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text)) })
            sessionText.addView(TextView(a).apply { text = "Adaptive 10-Minuten-Session · passend zu deinem Lernstand"; textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(2), 0, 0) })
            sessionBox.addView(sessionText, LinearLayout.LayoutParams(0, -2, 1f))
            sessionBox.addView(a.button("Start").apply { setOnClickListener { showGuidedSession() } }, LinearLayout.LayoutParams(a.dp(86), a.dp(44)))
            sessionCard.addView(sessionBox); content.addView(sessionCard); addGap(10)
            val streak = prefs.getInt("learn_streak", 0)
            val hero = roundedCard()
            val heroBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(16), a.dp(15), a.dp(16), a.dp(15)) }
            heroBox.addView(TextView(a).apply { text = if (streak > 0) "🔥 $streak Tage Lernserie" else "Heute ist ein guter Tag zum Üben"; textSize = 19f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_copper)) })
            heroBox.addView(TextView(a).apply { tag = "learnToday"; textSize = 13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(4), 0, a.dp(8)) })
            heroBox.addView(ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply { tag = "learnTodayProgress"; max = 5 }, LinearLayout.LayoutParams(-1, a.dp(10)))
            hero.addView(heroBox); content.addView(hero); addGap(8)

            val stats = LinearLayout(a).apply { tag = "learnStats"; orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(a.dp(4), a.dp(2), a.dp(4), a.dp(2)) }
            val statsCard = roundedCard(); statsCard.addView(stats); content.addView(statsCard); addGap(10)

            val weekCard = roundedCard()
            val weekBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(14), a.dp(13), a.dp(14), a.dp(13)) }
            val cal = java.util.Calendar.getInstance()
            val weekKey = cal.get(java.util.Calendar.YEAR).toString() + "-" + cal.get(java.util.Calendar.WEEK_OF_YEAR).toString()
            val weekSeconds = if (prefs.getString("learn_week_key", "") == weekKey) prefs.getInt("learn_week_seconds", 0) else 0
            val weekGoal = 60 * 60
            val weekLabel = TextView(a).apply {
                text = (weekSeconds / 60).coerceAtMost(60).toString() + "/60 Minuten · " + if (weekSeconds >= weekGoal) "Ziel erreicht 🎉" else ((weekGoal - weekSeconds).coerceAtLeast(0) / 60).toString() + " Min. übrig"
                textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(3), 0, a.dp(7))
            }
            weekBox.addView(TextView(a).apply { text = "📅 Wochenziel"; textSize = 17f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text)) })
            weekBox.addView(weekLabel)
            weekBox.addView(ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply { max = 100; progress = ((weekSeconds.toFloat() / weekGoal).coerceIn(0f, 1f) * 100).toInt() }, LinearLayout.LayoutParams(-1, a.dp(10)))
            weekBox.addView(a.body("60 Minuten pro Woche · kleine Einheiten zählen genauso.", 11f))
            weekCard.addView(weekBox); content.addView(weekCard); addGap(10)

            val skillCard = roundedCard()
            val skillBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(14), a.dp(13), a.dp(14), a.dp(13)) }
            skillBox.addView(TextView(a).apply { text = "🏆 Deine Skills"; textSize = 17f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text)) })
            skillBox.addView(a.body("Jede Trainingseinheit stärkt deinen persönlichen Lernpfad.", 12f))
            fun skillRow(name: String, value: Int, detail: String) {
                val row = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(0, a.dp(5), 0, a.dp(3)) }
                val head = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
                head.addView(TextView(a).apply { text = name; textSize = 13f; setTextColor(a.getColor(R.color.sw_text)) }, LinearLayout.LayoutParams(0, -2, 1f))
                head.addView(TextView(a).apply { text = "Level " + value; textSize = 12f; setTextColor(a.getColor(R.color.sw_copper)) })
                row.addView(head)
                row.addView(TextView(a).apply { text = detail; textSize = 10f; setTextColor(a.getColor(R.color.sw_muted)) })
                skillBox.addView(row)
            }
            val chordLevel = (1 + prefs.getInt("learn_quiz_correct", 0) / 5).coerceAtMost(5)
            val changeLevel = (1 + prefs.getInt("learn_skill_changes", 0) / 3).coerceAtMost(5)
            val rhythmLevel = (1 + prefs.getInt("learn_skill_rhythm", 0) / 3).coerceAtMost(5)
            val strumLevel = (1 + prefs.getInt("learn_strum_best_score", 0) / 300).coerceAtMost(5)
            skillRow("Akkorde", chordLevel, "Treffer: " + prefs.getInt("learn_quiz_correct", 0))
            skillRow("Akkordwechsel", changeLevel, "Trainerstarts: " + prefs.getInt("learn_skill_changes", 0))
            skillRow("Rhythmus", rhythmLevel, "Metronom-Sessions: " + prefs.getInt("learn_skill_rhythm", 0))
            skillRow("Schlagmuster", strumLevel, "Bestscore: " + prefs.getInt("learn_strum_best_score", 0))
            skillCard.addView(skillBox); content.addView(skillCard); addGap(10)

            // Kleine, nachvollziehbare Meilensteine motivieren ohne künstliche Trainerstarts zu belohnen.
            val quizAttempts = prefs.getInt("learn_quiz_total", 0)
            val quizHits = prefs.getInt("learn_quiz_correct", 0)
            val quizAccuracy = if (quizAttempts > 0) quizHits * 100 / quizAttempts else 0
            val sessions = prefs.getInt("learn_sessions", 0)
            val strumBest = prefs.getInt("learn_strum_best_score", 0)
            val achievements = listOf(
                Triple("Erster Schritt", sessions >= 1, "Erste Übungszeit gesammelt"),
                Triple("Dranbleiber", sessions >= 10, "$sessions von 10 Übungseinheiten"),
                Triple("Wochenprofi", weekSeconds >= weekGoal, (weekSeconds / 60).coerceAtMost(60).toString() + " von 60 Wochenminuten"),
                Triple("Lernserie", prefs.getInt("learn_streak", 0) >= 5, prefs.getInt("learn_streak", 0).toString() + " von 5 Tagen in Folge"),
                Triple("Akkord-Sicherheit", quizAttempts >= 10 && quizAccuracy >= 80, quizAccuracy.toString() + "% Treffer · mindestens 80% bei 10 Fragen"),
                Triple("Timing-Meister", strumBest >= 500, strumBest.toString() + " von 500 Schlagmuster-Punkten")
            )
            val earned = achievements.count { it.second }
            val achievementCard = roundedCard()
            val achievementBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(14), a.dp(13), a.dp(14), a.dp(13)) }
            achievementBox.addView(TextView(a).apply {
                text = "🏅 Erfolge · $earned/${achievements.size}"
                textSize = 17f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text))
            })
            achievementBox.addView(a.body("Echte Lernfortschritte schalten diese Meilensteine frei.", 11f))
            val achievementGrid = GridLayout(a).apply { columnCount = 2; useDefaultMargins = false }
            achievements.forEach { achievement ->
                val cell = LinearLayout(a).apply {
                    orientation = LinearLayout.VERTICAL
                    setPadding(a.dp(8), a.dp(8), a.dp(6), a.dp(8))
                    background = android.graphics.drawable.GradientDrawable().apply {
                        setColor(a.getColor(if (achievement.second) R.color.sw_surface else R.color.sw_surface))
                        cornerRadius = a.dp(10).toFloat()
                    }
                }
                cell.addView(TextView(a).apply {
                    text = (if (achievement.second) "✓  " else "○  ") + achievement.first
                    textSize = 12f; setTypeface(typeface, 1)
                    setTextColor(a.getColor(if (achievement.second) R.color.sw_copper else R.color.sw_text))
                })
                cell.addView(TextView(a).apply {
                    text = achievement.third; textSize = 10f
                    setTextColor(a.getColor(R.color.sw_muted))
                })
                achievementGrid.addView(cell, GridLayout.LayoutParams().apply {
                    width = 0; height = -2
                    columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)
                    setMargins(a.dp(3), a.dp(3), a.dp(3), a.dp(3))
                })
            }
            achievementBox.addView(achievementGrid)
            achievementCard.addView(achievementBox); content.addView(achievementCard); addGap(10)

            // Adaptive Tagesfokus: Die Startseite schlägt anhand des bisherigen Lernstands
            // automatisch den sinnvollsten nächsten Schwerpunkt vor.
            val focusCard = roundedCard()
            val focusBox = LinearLayout(a).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(a.dp(14), a.dp(13), a.dp(14), a.dp(13))
            }
            val focusTitle = TextView(a).apply {
                text = "🎯 Dein Fokus heute"
                textSize = 17f
                setTypeface(typeface, 1)
                setTextColor(a.getColor(R.color.sw_text))
            }
            val focusText = TextView(a).apply {
                textSize = 13f
                setTextColor(a.getColor(R.color.sw_muted))
                setPadding(0, a.dp(3), 0, a.dp(8))
            }
            val focusButton = a.button("Jetzt trainieren").apply { minHeight = a.dp(44) }
            val quizTotal = prefs.getInt("learn_quiz_total", 0)
            val quizCorrect = prefs.getInt("learn_quiz_correct", 0)
            val quizRate = if (quizTotal > 0) quizCorrect * 100 / quizTotal else 0
            val today = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date())
            val minutesToday = if (prefs.getString("learn_daily_day", "") == today) prefs.getInt("learn_daily_minutes", 0) else 0
            val focusAction: () -> Unit = when {
                quizTotal < 5 -> {
                    focusText.text = "Starte mit dem Akkord-Blitztrainer und sammle deine ersten sicheren Treffer."
                    { showQuiz() }
                }
                quizRate < 70 -> {
                    focusText.text = "Deine Akkorderkennung ist noch ausbaufähig. Kurze, häufige Wiederholungen bringen dich weiter."
                    { showQuiz() }
                }
                prefs.getString("learn_daily_day", "") != today || minutesToday < 5 -> {
                    focusText.text = "Du hast heute noch wenig Übungszeit gesammelt. Ein kurzer Wechselblock reicht."
                    { showChanges() }
                }
                prefs.getInt("learn_strum_best_score", 0) < 250 -> {
                    focusText.text = "Dein Schlagmuster-Score ist noch ausbaufähig. Trainiere Timing und Anschlag mit kurzen, präzisen Serien."
                    { showStrumming() }
                }
                weekSeconds < 20 * 60 -> {
                    focusText.text = "Dein Wochenziel ist noch nicht halb voll. Ein kurzer Wechsel- oder Rhythmusblock bringt dich direkt weiter."
                    { showChanges() }
                }
                else -> {
                    focusText.text = "Deine Basis sitzt. Trainiere jetzt Timing und Anschlag mit einem Schlagmuster."
                    { showStrumming() }
                }
            }
            focusButton.setOnClickListener { focusAction() }
            focusBox.addView(focusTitle)
            focusBox.addView(focusText)
            focusBox.addView(focusButton, LinearLayout.LayoutParams(-1, a.dp(44)))
            focusCard.addView(focusBox)
            content.addView(focusCard)
            addGap(10)

            val quick = roundedCard()
            val quickBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(14), a.dp(14), a.dp(14), a.dp(14)) }
            quickBox.addView(TextView(a).apply { text = "Schnellstart"; textSize = 18f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text)) })
            quickBox.addView(TextView(a).apply { text = "Wähle nach deinem aktuellen Ziel."; textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(3), 0, a.dp(8)) })
            val row1 = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }; val row2 = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
            fun quickButton(text: String, action: () -> Unit): Button = a.button(text).apply { textSize = 12f; minHeight = a.dp(48); setOnClickListener { action() } }
            row1.addView(quickButton("⚡ Akkorde erkennen") { showQuiz() }, LinearLayout.LayoutParams(0, a.dp(48), 1f).apply { rightMargin = a.dp(5) })
            row1.addView(quickButton("↔ Wechsel üben") { showChanges() }, LinearLayout.LayoutParams(0, a.dp(48), 1f).apply { leftMargin = a.dp(5) })
            row2.addView(quickButton("♩ Rhythmus") { showRhythm() }, LinearLayout.LayoutParams(0, a.dp(48), 1f).apply { rightMargin = a.dp(5); topMargin = a.dp(8) })
            row2.addView(quickButton("✓ Tagesroutine") { showRoutine() }, LinearLayout.LayoutParams(0, a.dp(48), 1f).apply { leftMargin = a.dp(5); topMargin = a.dp(8) })
            val row3 = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
            row3.addView(quickButton("↘ Schlagmuster") { showStrumming() }, LinearLayout.LayoutParams(0, a.dp(48), 1f).apply { rightMargin = a.dp(5); topMargin = a.dp(8) })
            row3.addView(quickButton("♬ Song-Praxis") { showSongPractice() }, LinearLayout.LayoutParams(0, a.dp(48), 1f).apply { leftMargin = a.dp(5); topMargin = a.dp(8) })
            val row4 = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
            row4.addView(quickButton("🎯 10-Min-Session") { showGuidedSession() }, LinearLayout.LayoutParams(-1, a.dp(48)).apply { topMargin = a.dp(8) })
            quickBox.addView(row1); quickBox.addView(row2); quickBox.addView(row3); quick.addView(quickBox); content.addView(quick); addGap(10)

            val path = roundedCard()
            val pathBox = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(a.dp(14), a.dp(12), a.dp(12), a.dp(12)) }
            val pathText = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL }
            pathText.addView(TextView(a).apply { text = "Dein Lernpfad"; textSize = 17f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text)) })
            pathText.addView(TextView(a).apply { text = "Lernstufen, persönliches Ziel und langfristiger Fortschritt"; textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(3), 0, 0) })
            pathBox.addView(pathText, LinearLayout.LayoutParams(0, -2, 1f))
            pathBox.addView(a.button("Öffnen").apply { setOnClickListener { a.openSection(6) } }, LinearLayout.LayoutParams(a.dp(92), a.dp(44)))
            path.addView(pathBox); content.addView(path); updatePracticeStats()
        }

        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        overviewAction?.invoke()
        return root
    }

    private fun finishQuizSession() {
        val started = quizStartedAt
        quizStartedAt = 0L
        if (started > 0L) onSessionElapsed?.invoke(((android.os.SystemClock.elapsedRealtime() - started) / 1000L).toInt().coerceAtLeast(1))
    }

    private fun stopStrumming() {
        val started = strumStartedAt
        strumStartedAt = 0L
        strumRunning = false
        strumHandler?.removeCallbacksAndMessages(null)
        strumHandler = null
        if (started > 0L) onSessionElapsed?.invoke(((android.os.SystemClock.elapsedRealtime() - started) / 1000L).toInt().coerceAtLeast(1))
        try { strumTone?.stopTone(); strumTone?.release() } catch (_: Exception) {}
        strumTone = null
    }

    private fun stopRhythm() {
        val started = rhythmStartedAt
        rhythmStartedAt = 0L
        rhythmRunning = false; rhythmHandler?.removeCallbacksAndMessages(null); rhythmHandler = null
        if (started > 0L) onSessionElapsed?.invoke(((android.os.SystemClock.elapsedRealtime() - started) / 1000L).toInt().coerceAtLeast(1))
        try { rhythmTone?.stopTone(); rhythmTone?.release() } catch (_: Exception) {}
        rhythmTone = null
    }
}'''

s = s[:start] + replacement + s[end:]


# Griffbrett im Akkordwechseltrainer ergänzen: horizontale Gitarrenansicht mit
# sechs Saiten, Bundlinien und den gegriffenen Positionen des aktiven Akkords.
replacements = [
    ("    private val next = TextView(host)\n", "    private val next = TextView(host)\n    private val fretboard = GuitarFretboardView(host)\n"),
    ("        else \"\"\n    }\n\n    private fun openChordPicker()", "        else \"\"\n        fretboard.setChord(ChordLibrary.all.firstOrNull { it.name == current.text.toString() })\n    }\n\n    private fun openChordPicker()"),
    ("                current.text = sequence[index]\n                next.text =", "                current.text = sequence[index]\n                fretboard.setChord(ChordLibrary.all.firstOrNull { it.name == sequence[index] })\n                next.text ="),
    ("        stage.addView(next, LayoutParams(-1, host.dp(28)))\n        addView(stage, LayoutParams(-1, host.dp(104)).apply {", "        stage.addView(next, LayoutParams(-1, host.dp(28)))\n        stage.addView(fretboard, LayoutParams(-1, host.dp(154)))\n        addView(stage, LayoutParams(-1, -2).apply {")
]
for old, new in replacements:
    if old == "    private val next = TextView(host)\n" and "private val fretboard = ChordDiagramView(host)" in s:
        continue
    if new in s:
        continue
    if old in s:
        s = s.replace(old, new, 1)
    else:
        # Der zuletzt gesicherte Build enthält das Griffbrett bereits mit 210dp;
        # die ältere 154dp-Einfügestelle existiert dort erwartungsgemäß nicht mehr.
        if old.startswith("        stage.addView(next, LayoutParams(-1, host.dp(28)))") and "stage.addView(fretboard, LayoutParams(-1, host.dp(210)))" in s:
            continue
        raise SystemExit("FEHLER: Griffbrett-Patchanker nicht gefunden: " + old[:80])
s = s.replace("private val fretboard = GuitarFretboardView(host)", "private val fretboard = ChordDiagramView(host)")
s = s.replace("stage.addView(fretboard, LayoutParams(-1, host.dp(154)))", "stage.addView(fretboard, LayoutParams(-1, host.dp(210)))")



# Gemeinsame Akkorddarstellung mit Fingersätzen für Bibliothek, Quiz und Trainer.
finger_data = [
('data class ChordShape(val name: String, val quality: String, val frets: IntArray, val baseFret: Int = 1, val note: String = "")','data class ChordShape(val name: String, val quality: String, val frets: IntArray, val baseFret: Int = 1, val note: String = "", val fingers: IntArray = IntArray(6))'),
('ChordShape("C", "Dur", intArrayOf(-1,3,2,0,1,0), note="Offener C-Dur-Griff")','ChordShape("C", "Dur", intArrayOf(-1,3,2,0,1,0), note="Offener C-Dur-Griff", fingers=intArrayOf(0,3,2,0,1,0))'),
('ChordShape("G", "Dur", intArrayOf(3,2,0,0,0,3), note="Offener G-Dur-Griff")','ChordShape("G", "Dur", intArrayOf(3,2,0,0,0,3), note="Offener G-Dur-Griff", fingers=intArrayOf(2,1,0,0,0,3))'),
('ChordShape("D", "Dur", intArrayOf(-1,-1,0,2,3,2), note="Offener D-Dur-Griff")','ChordShape("D", "Dur", intArrayOf(-1,-1,0,2,3,2), note="Offener D-Dur-Griff", fingers=intArrayOf(0,0,0,1,3,2))'),
('ChordShape("A", "Dur", intArrayOf(-1,0,2,2,2,0), note="Offener A-Dur-Griff")','ChordShape("A", "Dur", intArrayOf(-1,0,2,2,2,0), note="Offener A-Dur-Griff", fingers=intArrayOf(0,0,1,2,3,0))'),
('ChordShape("E", "Dur", intArrayOf(0,2,2,1,0,0), note="Offener E-Dur-Griff")','ChordShape("E", "Dur", intArrayOf(0,2,2,1,0,0), note="Offener E-Dur-Griff", fingers=intArrayOf(0,2,3,1,0,0))'),
('ChordShape("F", "Dur", intArrayOf(1,3,3,2,1,1), note="Barré-Griff im 1. Bund")','ChordShape("F", "Dur", intArrayOf(1,3,3,2,1,1), note="Barré-Griff im 1. Bund", fingers=intArrayOf(1,3,4,2,1,1))'),
('ChordShape("Am", "Moll", intArrayOf(-1,0,2,2,1,0))','ChordShape("Am", "Moll", intArrayOf(-1,0,2,2,1,0), fingers=intArrayOf(0,0,2,3,1,0))'),
('ChordShape("Em", "Moll", intArrayOf(0,2,2,0,0,0))','ChordShape("Em", "Moll", intArrayOf(0,2,2,0,0,0), fingers=intArrayOf(0,2,3,0,0,0))'),
('ChordShape("Dm", "Moll", intArrayOf(-1,-1,0,2,3,1))','ChordShape("Dm", "Moll", intArrayOf(-1,-1,0,2,3,1), fingers=intArrayOf(0,0,0,2,3,1))'),
('ChordShape("Bm", "Moll", intArrayOf(-1,2,4,4,3,2), 2)','ChordShape("Bm", "Moll", intArrayOf(-1,2,4,4,3,2), 2, fingers=intArrayOf(0,1,3,4,2,1))'),
('ChordShape("C7", "Septakkord", intArrayOf(-1,3,2,3,1,0))','ChordShape("C7", "Septakkord", intArrayOf(-1,3,2,3,1,0), fingers=intArrayOf(0,3,2,4,1,0))'),
('ChordShape("D7", "Septakkord", intArrayOf(-1,-1,0,2,1,2))','ChordShape("D7", "Septakkord", intArrayOf(-1,-1,0,2,1,2), fingers=intArrayOf(0,0,0,2,1,3))'),
('ChordShape("E7", "Septakkord", intArrayOf(0,2,0,1,0,0))','ChordShape("E7", "Septakkord", intArrayOf(0,2,0,1,0,0), fingers=intArrayOf(0,2,0,1,0,0))'),
('ChordShape("G7", "Septakkord", intArrayOf(3,2,0,0,0,1))','ChordShape("G7", "Septakkord", intArrayOf(3,2,0,0,0,1), fingers=intArrayOf(3,2,0,0,0,1))'),
('ChordShape("Am7", "Septakkord", intArrayOf(-1,0,2,0,1,0))','ChordShape("Am7", "Septakkord", intArrayOf(-1,0,2,0,1,0), fingers=intArrayOf(0,0,2,0,1,0))'),
('ChordShape("Em7", "Septakkord", intArrayOf(0,2,0,0,0,0))','ChordShape("Em7", "Septakkord", intArrayOf(0,2,0,0,0,0), fingers=intArrayOf(0,2,0,0,0,0))'),
('ChordShape("Dsus2", "Sus-Akkord", intArrayOf(-1,-1,0,2,3,0))','ChordShape("Dsus2", "Sus-Akkord", intArrayOf(-1,-1,0,2,3,0), fingers=intArrayOf(0,0,0,1,3,0))'),
('ChordShape("Dsus4", "Sus-Akkord", intArrayOf(-1,-1,0,2,3,3))','ChordShape("Dsus4", "Sus-Akkord", intArrayOf(-1,-1,0,2,3,3), fingers=intArrayOf(0,0,0,1,3,4))'),
('ChordShape("Asus2", "Sus-Akkord", intArrayOf(-1,0,2,2,0,0))','ChordShape("Asus2", "Sus-Akkord", intArrayOf(-1,0,2,2,0,0), fingers=intArrayOf(0,0,2,3,0,0))'),
('ChordShape("Asus4", "Sus-Akkord", intArrayOf(-1,0,2,2,3,0))','ChordShape("Asus4", "Sus-Akkord", intArrayOf(-1,0,2,2,3,0), fingers=intArrayOf(0,0,1,2,3,0))')
]
for old, new in finger_data:
    if new in s:
        continue
    if old in s:
        s = s.replace(old, new, 1)
    elif old.startswith('ChordShape("Bm", "Moll", intArrayOf(-1,2,4,4,3,2), 2)'):
        # The source backup may already use German H notation.
        german_old = 'ChordShape("Hm", "Moll", intArrayOf(-1,2,4,4,3,2), 2, note="Deutscher H-Moll-Barrégriff")'
        german_new = 'ChordShape("Hm", "Moll", intArrayOf(-1,2,4,4,3,2), 2, note="Deutscher H-Moll-Barrégriff", fingers=intArrayOf(0,1,3,4,2,1))'
        if german_new not in s and german_old in s:
            s = s.replace(german_old, german_new, 1)
        elif german_new not in s:
            raise SystemExit("FEHLER: Weder Bm- noch Hm-Fingersatz-Anker gefunden.")
    else:
        raise SystemExit("FEHLER: Fingersatz-Anker fehlt: " + old[:70])

shared_diagram_class = r'''
open class ChordDiagramView(context: android.content.Context, initialShape: ChordShape? = null) : View(context) {
    private var shape: ChordShape? = initialShape
    private val gridPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(142, 151, 163)
        strokeWidth = dp(1.35f)
        style = android.graphics.Paint.Style.STROKE
    }
    private val nutPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(224, 226, 229)
        strokeWidth = dp(4f)
        strokeCap = android.graphics.Paint.Cap.ROUND
    }
    private val dotPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(217, 154, 112)
        style = android.graphics.Paint.Style.FILL
    }
    private val fingerPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.WHITE
        textAlign = android.graphics.Paint.Align.CENTER
        textSize = dp(10f)
        typeface = android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.BOLD)
    }
    private val labelPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.LTGRAY
        textAlign = android.graphics.Paint.Align.CENTER
        textSize = dp(11f)
        typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
    }
    private val titlePaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(217, 154, 112)
        textAlign = android.graphics.Paint.Align.LEFT
        textSize = dp(11f)
        typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
    }

    fun setChord(value: ChordShape?) {
        shape = value
        contentDescription = value?.let { "Akkord ${it.name}, sechs Saiten, Griffbild mit Fingerzahlen und Barré" } ?: "Gitarrengriffbild"
        invalidate()
    }

    override fun onDraw(canvas: android.graphics.Canvas) {
        super.onDraw(canvas)
        val chord = shape ?: return
        val left = dp(51f)
        val right = width - dp(13f)
        val top = dp(39f)
        val bottom = height - dp(31f)
        if (right <= left || bottom <= top) return
        val fretWidth = (right - left) / 4f
        val stringGap = (bottom - top) / 5f
        val radius = dp(8.5f)
        val strings = arrayOf("E", "A", "D", "G", "H", "e")

        canvas.drawText(if (chord.baseFret <= 1) "Sattel" else "Bund ${chord.baseFret}", left, dp(15f), titlePaint)
        // Sechs waagerechte Saiten, von der tiefen E- bis zur hohen e-Saite.
        for (i in 0..5) {
            val y = top + i * stringGap
            gridPaint.strokeWidth = dp(if (i == 0 || i == 5) 1.8f else 1.25f)
            canvas.drawLine(left, y, right, y, gridPaint)
            canvas.drawText(strings[i], dp(10f), y + dp(4f), labelPaint)
        }
        // Senkrechte Bundlinien; am ersten Bund ersetzt der kräftige Sattel die Linie.
        for (i in 0..4) {
            val x = left + i * fretWidth
            gridPaint.strokeWidth = dp(1.25f)
            canvas.drawLine(x, top, x, bottom, gridPaint)
        }
        if (chord.baseFret <= 1) canvas.drawLine(left, top, left, bottom, nutPaint)
        else {
            for (i in 0..3) {
                val x = left + (i + .5f) * fretWidth
                labelPaint.textSize = dp(9f)
                canvas.drawText((chord.baseFret + i).toString(), x, dp(28f), labelPaint)
            }
            labelPaint.textSize = dp(11f)
        }

        // Gleicher Finger auf gleichem Bund über mehrere Saiten = Barré.
        val fingerGroups = (0..5).mapNotNull { string ->
            val fret = chord.frets.getOrElse(string) { -1 }
            val finger = chord.fingers.getOrElse(string) { 0 }
            if (fret > 0 && finger in 1..4) Triple(string, fret, finger) else null
        }.groupBy { Pair(it.second, it.third) }
        fingerGroups.values.filter { it.size > 1 }.forEach { group ->
            val fret = group.first().second
            val relative = fret - chord.baseFret
            if (relative in 0..3) {
                val x = left + (relative + .5f) * fretWidth
                val firstY = top + group.minOf { it.first } * stringGap
                val lastY = top + group.maxOf { it.first } * stringGap
                val barrePaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                    color = dotPaint.color
                    strokeWidth = dp(16f)
                    strokeCap = android.graphics.Paint.Cap.ROUND
                }
                canvas.drawLine(x, firstY, x, lastY, barrePaint)
            }
        }

        for (i in 0..5) {
            val y = top + i * stringGap
            val fret = chord.frets.getOrElse(i) { -1 }
            val finger = chord.fingers.getOrElse(i) { 0 }
            when {
                fret < 0 -> canvas.drawText("×", dp(32f), y + dp(4f), labelPaint)
                fret == 0 -> canvas.drawText("○", dp(32f), y + dp(4f), labelPaint)
                else -> {
                    val relative = fret - chord.baseFret
                    if (relative in 0..3) {
                        val x = left + (relative + .5f) * fretWidth
                        canvas.drawCircle(x, y, radius, dotPaint)
                        if (finger in 1..4) {
                            val baseline = y - (fingerPaint.ascent() + fingerPaint.descent()) / 2f
                            canvas.drawText(finger.toString(), x, baseline, fingerPaint)
                        }
                    }
                }
            }
        }
        labelPaint.textSize = dp(9f)
        canvas.drawText("1 Zeige  ·  2 Mitte  ·  3 Ring  ·  4 Klein", width / 2f, height - dp(7f), labelPaint)
        labelPaint.textSize = dp(11f)
    }

    private fun dp(value: Float) = value * resources.displayMetrics.density
}
'''
shared_diagram_class = shared_diagram_class.replace(r"\$", "$")
# Saitenfolge im Griffbild um 180 Grad drehen: tiefe E-Saite unten,
# hohe e-Saite oben. Die Akkorddaten bleiben in E-A-D-G-H-e-Reihenfolge.
shared_diagram_class = shared_diagram_class.replace(
    "val y = top + i * stringGap",
    "val y = bottom - i * stringGap",
)
shared_diagram_class = shared_diagram_class.replace(
    "val firstY = top + group.minOf { it.first } * stringGap",
    "val firstY = bottom - group.maxOf { it.first } * stringGap",
)
shared_diagram_class = shared_diagram_class.replace(
    "val lastY = top + group.maxOf { it.first } * stringGap",
    "val lastY = bottom - group.minOf { it.first } * stringGap",
)
diagram_start = s.find("open class ChordDiagramView(context: android.content.Context, initialShape: ChordShape? = null) : View(context) {")
diagram_end = s.find("\n/** Spielt den ausgewählten Griff", diagram_start)
if diagram_start >= 0 and diagram_end > diagram_start:
    s = s[:diagram_start] + shared_diagram_class.rstrip() + s[diagram_end:]
elif "open class ChordDiagramView(context: android.content.Context, initialShape: ChordShape? = null)" not in s:
    raise SystemExit("FEHLER: Gemeinsame Akkorddiagramm-Ansicht konnte nicht ersetzt werden.")

# Neue Sekunden-Erfassung muss beim Zurücksetzen des Lernstands ebenfalls gelöscht werden.
reset_anchor = '.remove("learn_quiz_correct")'
if reset_anchor in s and '.remove("learn_daily_seconds")' not in s:
    s = s.replace(reset_anchor, reset_anchor + '.remove("learn_daily_seconds")', 1)

# Erweiterte Akkordauswahl mit praxisnahen Dur-, Moll-, Sept-, Add- und Power-Voicings.
library_anchor = '        ChordShape("Asus4", "Sus-Akkord", intArrayOf(-1,0,2,2,3,0), fingers=intArrayOf(0,0,1,2,3,0))'
library_additions = [
        '        ChordShape("H", "Dur", intArrayOf(-1,2,4,4,4,2), 2, note="Deutscher H-Dur-Barrégriff", fingers=intArrayOf(0,1,3,3,3,1)),'
        '        ChordShape("Hm", "Moll", intArrayOf(-1,2,4,4,3,2), 2, note="Deutscher H-Moll-Barrégriff", fingers=intArrayOf(0,1,3,4,2,1)),'
        '        ChordShape("H7", "Septakkord", intArrayOf(-1,2,1,2,0,2), note="Dominantischer H-Septakkord", fingers=intArrayOf(0,2,1,3,0,4)),'
        '        ChordShape("Hm7", "Septakkord", intArrayOf(-1,2,0,2,0,2), note="H-Moll-Septakkord", fingers=intArrayOf(0,2,0,1,0,3)),'
        '        ChordShape("Hsus4", "Sus-Akkord", intArrayOf(-1,2,4,4,5,2), 2, note="H-Sus4-Barrégriff", fingers=intArrayOf(0,1,3,3,4,1)),'
'        ChordShape("B", "Dur", intArrayOf(-1,2,4,4,4,2), 2, note="Barré-Durgriff", fingers=intArrayOf(0,1,3,3,3,1)),',
'        ChordShape("Bb", "Dur", intArrayOf(-1,1,3,3,3,1), note="Barré-Durgriff", fingers=intArrayOf(0,1,3,3,3,1)),',
'        ChordShape("F#m", "Moll", intArrayOf(2,4,4,2,2,2), 2, note="Barré-Mollgriff", fingers=intArrayOf(1,3,4,1,1,1)),',
'        ChordShape("C#m", "Moll", intArrayOf(-1,4,6,6,5,4), 4, note="Barré-Mollgriff", fingers=intArrayOf(0,1,3,4,2,1)),',
'        ChordShape("B7", "Septakkord", intArrayOf(-1,2,1,2,0,2), note="Dominantischer Septakkord", fingers=intArrayOf(0,2,1,3,0,4)),',
'        ChordShape("A7", "Septakkord", intArrayOf(-1,0,2,0,2,0), note="Offener Septakkord", fingers=intArrayOf(0,0,1,0,2,0)),',
'        ChordShape("Dmaj7", "Septakkord", intArrayOf(-1,-1,0,2,2,2), note="Dur-Septakkord", fingers=intArrayOf(0,0,0,1,2,3)),',
'        ChordShape("Cmaj7", "Septakkord", intArrayOf(-1,3,2,0,0,0), note="Offener Dur-Septakkord", fingers=intArrayOf(0,3,2,0,0,0)),',
'        ChordShape("Dm7", "Septakkord", intArrayOf(-1,-1,0,2,1,1), note="Moll-Septakkord", fingers=intArrayOf(0,0,0,2,1,1)),',
'        ChordShape("Cadd9", "Add-Akkord", intArrayOf(-1,3,2,0,3,0), note="Offener Add9-Klang", fingers=intArrayOf(0,2,1,0,3,0)),',
'        ChordShape("Gsus4", "Sus-Akkord", intArrayOf(3,3,0,0,1,3), note="Sus4-Klang", fingers=intArrayOf(2,3,0,0,1,4)),',
'        ChordShape("E5", "Power-Akkord", intArrayOf(0,2,2,-1,-1,-1), note="Powerchord", fingers=intArrayOf(0,1,3,0,0,0)),',
'        ChordShape("A5", "Power-Akkord", intArrayOf(-1,0,2,2,-1,-1), note="Powerchord", fingers=intArrayOf(0,0,1,3,0,0))'
]
if library_anchor in s and 'ChordShape("Cadd9"' not in s:
    s = s.replace(library_anchor, library_anchor + ",\n" + "\n".join(library_additions), 1)
elif 'ChordShape("Cadd9"' not in s:
    raise SystemExit("FEHLER: Akkorddatenbank-Erweiterungsanker fehlt.")

# Vollständige Akkordfamilien für alle deutschen Grundton-Buchstaben.
# H wird unabhängig von Cadd9/anderen älteren Datenbank-Erweiterungen ergänzt.
if 'ChordShape("Hm", "Moll"' not in s:
    old_h_minor = '        ChordShape("Bm", "Moll", intArrayOf(-1,2,4,4,3,2), 2, fingers=intArrayOf(0,1,3,4,2,1)),'
    new_h_minor = '        ChordShape("Hm", "Moll", intArrayOf(-1,2,4,4,3,2), 2, note="Deutscher H-Moll-Barrégriff", fingers=intArrayOf(0,1,3,4,2,1)),'
    if old_h_minor in s:
        s = s.replace(old_h_minor, new_h_minor, 1)

# In deutscher Notation ist B = B♭ und H = B natural.
s = s.replace(
    'ChordShape("B", "Dur", intArrayOf(-1,2,4,4,4,2), 2, note="Barré-Durgriff", fingers=intArrayOf(0,1,3,3,3,1))',
    'ChordShape("B", "Dur", intArrayOf(-1,1,3,3,3,1), note="Deutscher B-Dur-Griff (international Bb)", fingers=intArrayOf(0,1,3,3,3,1))',
    1
)
s = s.replace(
    'ChordShape("B7", "Septakkord", intArrayOf(-1,2,1,2,0,2), note="Dominantischer Septakkord", fingers=intArrayOf(0,2,1,3,0,4))',
    'ChordShape("B7", "Septakkord", intArrayOf(-1,1,3,1,3,1), note="Deutscher B7 (international Bb7)", fingers=intArrayOf(0,1,3,1,4,1))',
    1
)

complete_chords = [
    '        ChordShape("H", "Dur", intArrayOf(-1,2,4,4,4,2), 2, note="H-Dur-Barrégriff", fingers=intArrayOf(0,1,3,3,3,1)),',
    '        ChordShape("H7", "Septakkord", intArrayOf(-1,2,1,2,0,2), note="H-Dominantseptakkord", fingers=intArrayOf(0,2,1,3,0,4)),',
    '        ChordShape("Hmaj7", "Septakkord", intArrayOf(-1,2,4,3,4,2), 2, note="H-Dur mit großer Septime", fingers=intArrayOf(0,1,3,2,4,1)),',
    '        ChordShape("Hm7", "Septakkord", intArrayOf(-1,2,0,2,0,2), note="H-Mollseptakkord", fingers=intArrayOf(0,2,0,3,0,4)),',
    '        ChordShape("Hsus2", "Sus-Akkord", intArrayOf(-1,2,4,4,2,2), 2, note="H-Sus2-Barrégriff", fingers=intArrayOf(0,1,3,4,1,1)),',
    '        ChordShape("Hsus4", "Sus-Akkord", intArrayOf(-1,2,4,4,5,2), 2, note="H-Sus4-Barrégriff", fingers=intArrayOf(0,1,3,3,4,1)),',
    '        ChordShape("Hadd9", "Add-Akkord", intArrayOf(-1,2,1,4,2,2), note="Hadd9-Barrégriff", fingers=intArrayOf(0,2,1,4,3,3)),',
    '        ChordShape("H5", "Power-Akkord", intArrayOf(-1,2,4,4,-1,-1), 2, note="H-Powerchord", fingers=intArrayOf(0,1,3,4,0,0)),',
    '        ChordShape("Bbm", "Moll", intArrayOf(-1,1,3,3,2,1), note="B-Moll-Barrégriff", fingers=intArrayOf(0,1,3,4,2,1)),',
    '        ChordShape("Bbmaj7", "Septakkord", intArrayOf(-1,1,3,2,3,1), note="B-Dur mit großer Septime", fingers=intArrayOf(0,1,4,2,3,1)),',
    '        ChordShape("Bbm7", "Septakkord", intArrayOf(-1,1,3,1,2,1), note="B-Mollseptakkord", fingers=intArrayOf(0,1,3,1,2,1)),',
    '        ChordShape("Bbsus4", "Sus-Akkord", intArrayOf(-1,1,3,3,4,1), note="B-Sus4-Barrégriff", fingers=intArrayOf(0,1,3,3,4,1)),',
    '        ChordShape("Bb5", "Power-Akkord", intArrayOf(-1,1,3,-1,-1,-1), note="B-Powerchord", fingers=intArrayOf(0,1,3,0,0,0)),',
    '        ChordShape("Amaj7", "Septakkord", intArrayOf(-1,0,2,1,2,0), note="A-Dur mit großer Septime", fingers=intArrayOf(0,0,2,1,3,0)),',
    '        ChordShape("Aadd9", "Add-Akkord", intArrayOf(-1,0,2,4,2,0), note="Offener Aadd9-Klang", fingers=intArrayOf(0,0,1,3,2,0)),',
    '        ChordShape("Cm", "Moll", intArrayOf(-1,3,5,5,4,3), 3, note="C-Moll-Barrégriff", fingers=intArrayOf(0,1,3,4,2,1)),',
    '        ChordShape("Cm7", "Septakkord", intArrayOf(-1,3,5,3,4,3), 3, note="C-Mollseptakkord", fingers=intArrayOf(0,1,3,1,2,1)),',
    '        ChordShape("Csus4", "Sus-Akkord", intArrayOf(-1,3,3,0,1,1), note="C-Sus4", fingers=intArrayOf(0,3,4,0,1,1)),',
    '        ChordShape("C5", "Power-Akkord", intArrayOf(-1,3,5,5,-1,-1), 3, note="C-Powerchord", fingers=intArrayOf(0,1,3,4,0,0)),',
    '        ChordShape("Dadd9", "Add-Akkord", intArrayOf(-1,-1,0,2,3,0), note="Offener Dadd9-Klang", fingers=intArrayOf(0,0,0,1,3,0)),',
    '        ChordShape("D5", "Power-Akkord", intArrayOf(-1,-1,0,2,3,-1), note="D-Powerchord", fingers=intArrayOf(0,0,0,1,3,0)),',
    '        ChordShape("Emaj7", "Septakkord", intArrayOf(0,2,1,1,0,0), note="E-Dur mit großer Septime", fingers=intArrayOf(0,2,1,3,0,0)),',
    '        ChordShape("Esus2", "Sus-Akkord", intArrayOf(0,2,4,4,0,0), note="E-Sus2", fingers=intArrayOf(0,1,3,4,0,0)),',
    '        ChordShape("Esus4", "Sus-Akkord", intArrayOf(0,2,2,2,0,0), note="E-Sus4", fingers=intArrayOf(0,1,2,3,0,0)),',
    '        ChordShape("Fm", "Moll", intArrayOf(1,3,3,1,1,1), note="F-Moll-Barrégriff", fingers=intArrayOf(1,3,4,1,1,1)),',
    '        ChordShape("F7", "Septakkord", intArrayOf(1,3,1,2,1,1), note="F-Dominantseptakkord", fingers=intArrayOf(1,3,1,2,1,1)),',
    '        ChordShape("Fmaj7", "Septakkord", intArrayOf(-1,-1,3,2,1,0), note="F-Dur mit großer Septime", fingers=intArrayOf(0,0,3,2,1,0)),',
    '        ChordShape("Fm7", "Septakkord", intArrayOf(1,3,1,1,1,1), note="F-Mollseptakkord", fingers=intArrayOf(1,3,1,1,1,1)),',
    '        ChordShape("Fsus4", "Sus-Akkord", intArrayOf(1,3,3,3,1,1), note="F-Sus4-Barrégriff", fingers=intArrayOf(1,3,3,3,1,1)),',
    '        ChordShape("F5", "Power-Akkord", intArrayOf(1,3,3,-1,-1,-1), note="F-Powerchord", fingers=intArrayOf(1,3,4,0,0,0)),',
    '        ChordShape("Gm", "Moll", intArrayOf(3,5,5,3,3,3), 3, note="G-Moll-Barrégriff", fingers=intArrayOf(1,3,4,1,1,1)),',
    '        ChordShape("Gmaj7", "Septakkord", intArrayOf(3,2,0,0,0,2), note="Offener G-Durseptakkord", fingers=intArrayOf(2,1,0,0,0,3)),',
    '        ChordShape("Gm7", "Septakkord", intArrayOf(3,5,3,3,3,3), 3, note="G-Mollseptakkord", fingers=intArrayOf(1,3,1,1,1,1)),',
    '        ChordShape("Gsus2", "Sus-Akkord", intArrayOf(3,0,0,0,3,3), note="Offener G-Sus2-Klang", fingers=intArrayOf(2,0,0,0,3,4)),',
    '        ChordShape("G5", "Power-Akkord", intArrayOf(3,5,5,-1,-1,-1), 3, note="G-Powerchord", fingers=intArrayOf(1,3,4,0,0,0)),'
]
chord_anchor = '        ChordShape("B", "Dur", intArrayOf(-1,1,3,3,3,1)'
for chord_line in complete_chords:
    chord_name = chord_line.split('ChordShape("', 1)[1].split('"', 1)[0]
    if f'ChordShape("{chord_name}"' not in s:
        if chord_anchor not in s:
            raise SystemExit("FEHLER: Akkorddatenbank-Einfügeanker fehlt: " + chord_name)
        s = s.replace(chord_anchor, chord_line + "\n" + chord_anchor, 1)

# Datenbank-Integrität: kein Grundton-Dropdown darf leer bleiben.
for required_chord in ['ChordShape("A",', 'ChordShape("B",', 'ChordShape("C",', 'ChordShape("D",', 'ChordShape("E",', 'ChordShape("F",', 'ChordShape("G",', 'ChordShape("H",', 'ChordShape("Hm",']:
    if required_chord not in s:
        raise SystemExit("FEHLER: Akkorddatenbank unvollständig, Eintrag fehlt: " + required_chord)

# Suchfilter, Favoriten und kompakteres Kartenraster verbessern.
s = s.replace(
'val categories = listOf("Alle", "Dur", "Moll", "Septakkord", "Sus-Akkord"); var category = "Alle"',
'val categories = listOf("Alle", "Dur", "Moll", "Septakkord", "Sus-Akkord", "Add-Akkord", "Power-Akkord", "Favoriten"); var category = "Alle"',
1)
old_filter = 'val matches = ChordLibrary.all.filter { (category == "Alle" || it.quality == category) && it.name.lowercase().contains(q) }'
new_filter = '''val favorites = a.getSharedPreferences("saitenwerk", 0).getStringSet("fav_chords", emptySet()) ?: emptySet()
            val matches = ChordLibrary.all.filter {
                (category == "Alle" || (category == "Favoriten" && it.name in favorites) || it.quality == category) &&
                (it.name.lowercase().contains(q) || it.quality.lowercase().contains(q) || it.note.lowercase().contains(q))
            }.sortedWith(compareByDescending<ChordShape> { it.name in favorites }.thenBy { it.name })'''
if old_filter in s:
    s = s.replace(old_filter, new_filter, 1)
s = s.replace('val grid = GridLayout(a).apply { columnCount = 3;', 'val grid = GridLayout(a).apply { columnCount = 2;', 1)
s = s.replace('height = a.dp(52); columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)', 'height = a.dp(60); columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)', 1)
if 'val resultCount = TextView(a)' not in s:
    s = s.replace('val grid = GridLayout(a).apply { columnCount = 2;', 'val resultCount = TextView(a).apply { textSize = 12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(a.dp(16), 0, 0, a.dp(4)) }\n        val grid = GridLayout(a).apply { columnCount = 2;', 1)
    s = s.replace('matches.forEach { chord ->', 'resultCount.text = matches.size.toString() + " Akkorde gefunden"\n            matches.forEach { chord ->', 1)
    s = s.replace('content.addView(detailCard); content.addView(grid)', 'content.addView(detailCard); content.addView(resultCount); content.addView(grid)', 1)


# Buchstaben-Dropdowns: jeder Grundton öffnet seine komplette Akkordauswahl.
letter_dropdown_code = """        val letterScroll = HorizontalScrollView(a).apply { isHorizontalScrollBarEnabled = false }
        val letterRow = LinearLayout(a).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(a.dp(10), a.dp(4), a.dp(10), a.dp(8))
        }
        letterScroll.addView(letterRow)
        listOf("A", "B", "C", "D", "E", "F", "G", "H").forEach { letter ->
            val letterChords = ChordLibrary.all.filter { it.name.startsWith(letter, ignoreCase = true) }.sortedBy { it.name }
            val menuButton = a.button(letter + "  ▾").apply { textSize = 13f }
            menuButton.isEnabled = letterChords.isNotEmpty()
            menuButton.alpha = if (letterChords.isNotEmpty()) 1f else .45f
            menuButton.setOnClickListener { anchor ->
                val popup = android.widget.PopupMenu(a, anchor)
                letterChords.forEachIndexed { index, chord -> popup.menu.add(android.view.Menu.NONE, index, index, chord.name) }
                popup.setOnMenuItemClickListener { item ->
                    letterChords.getOrNull(item.itemId)?.let { chord ->
                        category = "Alle"
                        showChord(chord)
                        resultCount.text = "Ausgewählt: " + chord.name
                    }
                    true
                }
                popup.show()
            }
            letterRow.addView(menuButton, LinearLayout.LayoutParams(a.dp(62), a.dp(42)).apply { rightMargin = a.dp(5) })
        }
        root.addView(letterScroll, LinearLayout.LayoutParams(-1, a.dp(52)))
"""
letter_render_anchor = '        fun render() {\n            grid.removeAllViews(); val q = search.text.toString().trim().lowercase()'
if letter_render_anchor in s and 'val letterScroll = HorizontalScrollView(a)' not in s:
    s = s.replace(letter_render_anchor, letter_dropdown_code + "\n" + letter_render_anchor, 1)
# Der frühere Akkorddatenbank-Renderer wurde inzwischen durch ChordsFragment ersetzt.
# Falls der alte Renderanker fehlt, ist das erwartbar; die Dropdowns werden unten neu aufgebaut.


# Kompakte 4x2-Grundtonauswahl statt Such-/Filterleisten und Akkordraster.
chords_start = s.find("class ChordsFragment : Fragment() {")
chords_end = s.find("\n\nclass GuitarFretboardView", chords_start)
if chords_start < 0 or chords_end < 0:
    raise SystemExit("FEHLER: ChordsFragment nicht gefunden.")
chords_replacement = r'''class ChordsFragment : Fragment() {
    private var training: ChordTrainingPanel? = null

    override fun onDestroyView() {
        training?.stop()
        training = null
        super.onDestroyView()
    }

    override fun onCreateView(i: android.view.LayoutInflater, c: ViewGroup?, s: Bundle?): View {
        val a = requireActivity() as MainActivity
        val root = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL }
        root.addView(a.title("Akkorde"))
        root.addView(a.body("Griffbilder · Akkordwissen · Wechseltraining"))
        val scroll = ScrollView(a).apply { clipToPadding = false }
        val content = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(12), a.dp(8), a.dp(12), a.dp(24))
        }
        val chooserCard = a.card()
        val chooser = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(14), a.dp(14), a.dp(14), a.dp(14))
        }
        chooser.addView(TextView(a).apply {
            text = "Akkord auswählen"
            textSize = 18f
            setTypeface(typeface, 1)
            setTextColor(a.getColor(R.color.sw_text))
        })
        chooser.addView(a.body("Wähle einen Buchstaben und anschließend den gewünschten Akkord."))
        var showChordSelection: ((ChordShape) -> Unit)? = null
        val letterGrid = GridLayout(a).apply {
            columnCount = 4
            useDefaultMargins = false
            setPadding(0, a.dp(10), 0, 0)
        }
        listOf("A", "B", "C", "D", "E", "F", "G", "H").forEach { letter ->
            val chords = ChordLibrary.all
                .filter { it.name.startsWith(letter, ignoreCase = true) }
                .sortedBy { it.name }
            val button = a.button("$letter  ▾").apply {
                textSize = 14f
                isEnabled = chords.isNotEmpty()
                alpha = if (chords.isNotEmpty()) 1f else .4f
            }
            button.setOnClickListener { anchor ->
                val popup = android.widget.PopupMenu(a, anchor)
                chords.forEachIndexed { index, chord ->
                    popup.menu.add(android.view.Menu.NONE, index, index, chord.name)
                }
                popup.setOnMenuItemClickListener { item ->
                    chords.getOrNull(item.itemId)?.let { showChordSelection?.invoke(it) }
                    true
                }
                popup.show()
            }
            letterGrid.addView(button, GridLayout.LayoutParams().apply {
                width = 0
                height = a.dp(46)
                columnSpec = GridLayout.spec(GridLayout.UNDEFINED, 1f)
                setMargins(a.dp(3), a.dp(3), a.dp(3), a.dp(3))
            })
        }
        chooser.addView(letterGrid)
        chooserCard.addView(chooser)
        content.addView(chooserCard)

        val detailCard = a.card().apply { visibility = View.GONE }
        val detail = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(16), a.dp(14), a.dp(16), a.dp(16))
        }
        detailCard.addView(detail)

        showChordSelection = { ch ->
            detail.removeAllViews()
            detail.addView(TextView(a).apply {
                text = ch.name
                textSize = 29f
                setTextColor(a.getColor(R.color.sw_copper))
                setTypeface(typeface, 1)
            })
            detail.addView(TextView(a).apply {
                text = ch.quality + " · " + ch.note
                setTextColor(a.getColor(R.color.sw_muted))
            })
            detail.addView(ChordDiagramView(a, ch), LinearLayout.LayoutParams(-1, a.dp(270)))
            detail.addView(TextView(a).apply {
                text = "× = nicht anschlagen · ○ = leere Saite"
                setTextColor(a.getColor(R.color.sw_muted))
                textSize = 13f
            })
            val preview = a.button("▶ Akkord anhören")
            preview.setOnClickListener { ChordPreviewPlayer.play(ch) }
            detail.addView(preview, LinearLayout.LayoutParams(-1, a.dp(48)).apply {
                topMargin = a.dp(8)
            })
            val prefs = a.getSharedPreferences("saitenwerk", 0)
            val key = "fav_chords"
            val saved = prefs.getStringSet(key, emptySet())?.toMutableSet() ?: mutableSetOf()
            val favorite = a.button(if (ch.name in saved) "★ Favorit entfernen" else "☆ Als Favorit speichern")
            favorite.setOnClickListener {
                val now = prefs.getStringSet(key, emptySet())?.toMutableSet() ?: mutableSetOf()
                if (!now.add(ch.name)) now.remove(ch.name)
                prefs.edit().putStringSet(key, now).apply()
                favorite.text = if (ch.name in now) "★ Favorit entfernen" else "☆ Als Favorit speichern"
            }
            detail.addView(favorite, LinearLayout.LayoutParams(-1, a.dp(46)).apply {
                topMargin = a.dp(8)
            })
            detailCard.visibility = View.VISIBLE
        }

        content.addView(detailCard, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = a.dp(12)
        })
        training = ChordTrainingPanel(a)
        content.addView(training, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = a.dp(14)
        })
        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        return root
    }
}'''
s = s[:chords_start] + chords_replacement + s[chords_end:]

p.write_text(s, encoding="utf-8")
if "Timing-Meister" not in s or "Akkord-Sicherheit" not in s or "Erfolge · $earned" not in s:
    raise SystemExit("LERNSTUDIO: achievement milestones missing")
print("LERNSTUDIO-OPTIMIERUNG: PASS")
