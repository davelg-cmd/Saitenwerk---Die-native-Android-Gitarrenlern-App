#!/usr/bin/env python3
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

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

    override fun onDestroyView() {
        chordTraining?.stop()
        chordTraining = null
        finishQuizSession()
        stopRhythm()
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
            prefs.edit().putString("learn_daily_day", day).putInt("learn_daily_seconds", totalSeconds)
                .putInt("learn_daily_minutes", totalSeconds / 60)
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
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); content.removeAllViews()
            quizStartedAt = SystemClock.elapsedRealtime()
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
            var answer = ""; var locked = false; var localStreak = 0; var sessionRecorded = false

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
                        sessionRecorded = true
                        val correctAnswer = option == answer
                        if (correctAnswer) localStreak++ else localStreak = 0
                        val total = prefs.getInt("learn_quiz_total", 0) + 1
                        val correct = prefs.getInt("learn_quiz_correct", 0) + if (correctAnswer) 1 else 0
                        val best = maxOf(prefs.getInt("learn_best_quiz_streak", 0), localStreak)
                        prefs.edit().putInt("learn_quiz_total", total).putInt("learn_quiz_correct", correct).putInt("learn_best_quiz_streak", best).apply()
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
            finishQuizSession(); stopRhythm(); content.removeAllViews()
            content.addView(a.body("Dein Haupttraining für saubere Akkordwechsel. Wähle Akkorde, Takt und Tempo direkt im Trainer und steigere dich erst, wenn die Wechsel sicher sitzen."))
            chordTraining = ChordTrainingPanel(a); content.addView(chordTraining, LinearLayout.LayoutParams(-1, -2))
        }

        fun showRhythm() {
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); content.removeAllViews()
            val (card, box) = panel("Rhythmus & Timing", "Trainiere Puls, Taktgefühl und Geschwindigkeit. Der erste Schlag jedes Taktes wird deutlich markiert.")
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
            meterButton.setOnClickListener {
                val meters = arrayOf("2/4", "3/4", "4/4", "6/8")
                androidx.appcompat.app.AlertDialog.Builder(a).setTitle("Taktart").setSingleChoiceItems(meters, meters.indexOf(rhythmMeter).coerceAtLeast(0)) { d, which ->
                    rhythmMeter = meters[which]; meterButton.text = rhythmMeter; prefs.edit().putString("learn_rhythm_meter", rhythmMeter).apply(); d.dismiss()
                }.setNegativeButton("Abbrechen", null).show()
            }
            val beat = TextView(a).apply { text = "Bereit"; textSize = 30f; gravity = Gravity.CENTER; setTextColor(a.getColor(R.color.sw_copper)); setPadding(0, a.dp(12), 0, a.dp(8)) }
            box.addView(beat, LinearLayout.LayoutParams(-1, a.dp(72)))
            val start = a.button("Metronom starten"); box.addView(start, LinearLayout.LayoutParams(-1, a.dp(48)))
            start.setOnClickListener {
                if (rhythmRunning) { stopRhythm(); start.text = "Metronom starten"; beat.text = "Pausiert" }
                else {
                    rhythmRunning = true; rhythmStartedAt = SystemClock.elapsedRealtime(); rhythmBeat = 0; rhythmTone = ToneGenerator(AudioManager.STREAM_MUSIC, 65); rhythmHandler = Handler(Looper.getMainLooper()); start.text = "Metronom stoppen"
                    val beatsPerBar = rhythmMeter.substringBefore("/").toIntOrNull() ?: 4
                    val task = object : Runnable {
                        override fun run() {
                            if (!rhythmRunning) return
                            val strong = rhythmBeat % beatsPerBar == 0
                            rhythmTone?.startTone(if (strong) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP, if (strong) 80 else 55)
                            beat.text = if (strong) "1 · TAKT" else "${rhythmBeat % beatsPerBar + 1}"
                            rhythmBeat++; rhythmHandler?.postDelayed(this, (60000L / rhythmBpm).coerceAtLeast(100L))
                        }
                    }
                    rhythmHandler?.post(task)
                }
            }
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
            content.addView(a.body("Dein Übungsbereich für Akkorde, Rhythmus, Timing und tägliche Routinen. Wähle eine Übung und leg direkt los."))
            val streak = prefs.getInt("learn_streak", 0)
            val hero = roundedCard()
            val heroBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(16), a.dp(15), a.dp(16), a.dp(15)) }
            heroBox.addView(TextView(a).apply { text = if (streak > 0) "🔥 $streak Tage Lernserie" else "Heute ist ein guter Tag zum Üben"; textSize = 19f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_copper)) })
            heroBox.addView(TextView(a).apply { tag = "learnToday"; textSize = 13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(4), 0, a.dp(8)) })
            heroBox.addView(ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply { tag = "learnTodayProgress"; max = 5 }, LinearLayout.LayoutParams(-1, a.dp(10)))
            hero.addView(heroBox); content.addView(hero); addGap(8)

            val stats = LinearLayout(a).apply { tag = "learnStats"; orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(a.dp(4), a.dp(2), a.dp(4), a.dp(2)) }
            val statsCard = roundedCard(); statsCard.addView(stats); content.addView(statsCard); addGap(10)

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
                else -> {
                    focusText.text = "Deine Basis sitzt. Fordere jetzt dein Timing mit dem Rhythmustrainer heraus."
                    { showRhythm() }
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
            quickBox.addView(row1); quickBox.addView(row2); quick.addView(quickBox); content.addView(quick); addGap(10)

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
        if (started > 0L) onSessionElapsed?.invoke(((SystemClock.elapsedRealtime() - started) / 1000L).toInt().coerceAtLeast(1))
    }

    private fun stopRhythm() {
        val started = rhythmStartedAt
        rhythmStartedAt = 0L
        rhythmRunning = false; rhythmHandler?.removeCallbacksAndMessages(null); rhythmHandler = null
        if (started > 0L) onSessionElapsed?.invoke(((SystemClock.elapsedRealtime() - started) / 1000L).toInt().coerceAtLeast(1))
        try { rhythmTone?.stopTone(); rhythmTone?.release() } catch (_: Exception) {}
        rhythmTone = null
    }
}'''

s = s[:start] + replacement + s[end:]
p.write_text(s, encoding="utf-8")
print("LERNSTUDIO-OPTIMIERUNG: PASS")
