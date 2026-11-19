#!/usr/bin/env python3
"""Upgrade the Saitenwerk strumming trainer into a guided, adaptive practice mode."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
source = main.read_text(encoding="utf-8")
start = source.find("        fun showStrumming() {")
end = source.find("\n        fun showSongPractice() {", start)
if start < 0 or end < 0:
    raise SystemExit("FEHLER: showStrumming()-Bereich nicht gefunden.")

new_function = r'''        fun showStrumming() {
            prefs.edit().putInt("learn_skill_strum", prefs.getInt("learn_skill_strum", 0) + 1).apply()
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); stopStrumming(); content.removeAllViews()
            val (card, box) = panel("Schlagmuster-Trainer", "Saitenwerk zeigt dir erst das Muster, dann spielst du selbst. Timing, Richtung und Serien werden direkt ausgewertet.")

            val patterns = linkedMapOf(
                "Anfänger · ↓ ↓ ↓ ↓" to listOf("↓","↓","↓","↓"),
                "Grundlagen · ↓ ↑ ↓ ↑" to listOf("↓","↑","↓","↑"),
                "Pop · ↓ ↓ ↑ ↑ ↓ ↑" to listOf("↓","↓","↑","↑","↓","↑"),
                "Achtel · ↓ ↑ ↓ ↑ ↓ ↑ ↓ ↑" to listOf("↓","↑","↓","↑","↓","↑","↓","↑"),
                "Akustik · ↓ ↓ ↑ ↓ ↑" to listOf("↓","↓","↑","↓","↑"),
                "Flow · ↓ ↑ ↑ ↓ ↑ ↓" to listOf("↓","↑","↑","↓","↑","↓"),
                "Offbeat · ↓ ↑ · ↑ ↓ ↑ · ↑" to listOf("↓","↑","·","↑","↓","↑","·","↑"),
                "Profi · ↓ · ↑ ↑ · ↑ ↓ ↑" to listOf("↓","·","↑","↑","·","↑","↓","↑")
            )
            val levels = linkedMapOf(
                "Anfänger" to Triple(60, 420L, 3),
                "Grundlagen" to Triple(75, 330L, 4),
                "Fortgeschritten" to Triple(95, 240L, 5),
                "Profi" to Triple(115, 150L, 6)
            )

            var selectedName = prefs.getString("learn_strum_pattern", patterns.keys.first()) ?: patterns.keys.first()
            var selected = patterns[selectedName] ?: patterns.values.first()
            var selectedChordName = prefs.getString("learn_strum_chord", "G") ?: "G"
            var selectedChord = ChordLibrary.all.firstOrNull { it.name == selectedChordName } ?: ChordLibrary.all.first()
            var difficulty = prefs.getString("learn_strum_difficulty", "Grundlagen") ?: "Grundlagen"
            if (!levels.containsKey(difficulty)) difficulty = "Grundlagen"
            var bpm = prefs.getInt("learn_strum_bpm", levels[difficulty]!!.first).coerceIn(50, 160)

            var phase = "ready"
            var step = 0
            var round = 0
            var hits = 0
            var misses = 0
            var score = 0
            var combo = 0
            var bestCombo = 0
            var expectedAt = 0L
            var answered = true
            var sessionBest = prefs.getInt("learn_strum_best_score", 0)
            var roundBest = prefs.getInt("learn_strum_best_rounds", 0)

            val patternButton = a.button(selectedName)
            val chordButton = a.button("Gitarrenklang · " + selectedChordName)
            val levelButton = a.button("Stufe · " + difficulty)
            val previewButton = a.button("▶ Muster vorhören")
            val status = TextView(a).apply {
                text = "Bereit · zuerst Muster vorhören"
                textSize = 13f
                gravity = Gravity.CENTER
                setTextColor(a.getColor(R.color.sw_muted))
                setPadding(0, a.dp(7), 0, a.dp(8))
            }
            val patternHint = TextView(a).apply {
                text = "Pattern: " + selected.joinToString("  ")
                textSize = 16f
                gravity = Gravity.CENTER
                setTextColor(a.getColor(R.color.sw_text))
                setPadding(0, a.dp(9), 0, a.dp(9))
            }
            val beatRow = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
            val tempoLabel = TextView(a).apply {
                text = "Tempo: " + bpm + " BPM"
                textSize = 14f
                setTextColor(a.getColor(R.color.sw_text))
            }
            val slider = SeekBar(a).apply { max = 110; progress = bpm - 50 }
            val stats = TextView(a).apply {
                text = "Punkte: 0 · Genauigkeit: 0% · Serie: 0"
                textSize = 12f
                setTextColor(a.getColor(R.color.sw_muted))
                gravity = Gravity.CENTER
            }
            val roundLabel = TextView(a).apply {
                text = "Runde 0 · Bestwert " + sessionBest
                textSize = 12f
                setTextColor(a.getColor(R.color.sw_muted))
                gravity = Gravity.CENTER
            }
            val timing = TextView(a).apply {
                text = "Timing-Fenster · ±" + levels[difficulty]!!.second + " ms"
                textSize = 12f
                setTextColor(a.getColor(R.color.sw_muted))
                gravity = Gravity.CENTER
            }
            val start = a.button("Jetzt du · Training starten")
            val down = a.button("↓ Abschlag")
            val up = a.button("↑ Aufschlag")
            val actionRow = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }

            box.addView(levelButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(chordButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(patternButton, LinearLayout.LayoutParams(-1, a.dp(46)))
            box.addView(patternHint)
            box.addView(previewButton, LinearLayout.LayoutParams(-1, a.dp(46)).apply { topMargin = a.dp(2) })
            box.addView(beatRow, LinearLayout.LayoutParams(-1, a.dp(58)))
            box.addView(status)
            box.addView(roundLabel)
            box.addView(tempoLabel)
            box.addView(slider, LinearLayout.LayoutParams(-1, a.dp(42)))
            box.addView(timing)
            box.addView(stats)
            box.addView(start, LinearLayout.LayoutParams(-1, a.dp(48)).apply { topMargin = a.dp(4) })
            actionRow.addView(down, LinearLayout.LayoutParams(0, a.dp(52), 1f).apply { rightMargin = a.dp(4) })
            actionRow.addView(up, LinearLayout.LayoutParams(0, a.dp(52), 1f).apply { leftMargin = a.dp(4) })
            box.addView(actionRow, LinearLayout.LayoutParams(-1, a.dp(56)).apply { topMargin = a.dp(6) })

            fun rebuildBeats() {
                beatRow.removeAllViews()
                selected.forEachIndexed { index, dir ->
                    beatRow.addView(TextView(a).apply {
                        text = dir
                        textSize = 22f
                        gravity = Gravity.CENTER
                        setTypeface(typeface, android.graphics.Typeface.BOLD)
                        setTextColor(a.getColor(R.color.sw_muted))
                        contentDescription = "Schlag " + (index + 1) + ": " + dir
                    }, LinearLayout.LayoutParams(0, a.dp(52), 1f))
                }
            }
            fun markBeat(active: Int = step) {
                for (i in 0 until beatRow.childCount) {
                    val v = beatRow.getChildAt(i) as TextView
                    val isActive = i == active
                    v.setTextColor(a.getColor(if (isActive) R.color.sw_copper else R.color.sw_muted))
                    v.textSize = if (isActive) 28f else 22f
                }
            }
            fun refreshStats() {
                val attempts = hits + misses
                val accuracy = if (attempts > 0) hits * 100 / attempts else 0
                stats.text = "Punkte: " + score + " · Genauigkeit: " + accuracy + "% · Serie: " + combo + " · Bestserie: " + bestCombo
                roundLabel.text = "Runde " + round + " · Bestwert " + sessionBest
            }
            fun updateTimingLabel() {
                timing.text = "Timing-Fenster · ±" + levels[difficulty]!!.second + " ms · Zieltempo " + levels[difficulty]!!.first + " BPM"
            }

            chordButton.setOnClickListener {
                if (phase == "play" || phase == "preview") return@setOnClickListener
                val names = ChordLibrary.all.map { it.name }.toTypedArray()
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Akkord für das Schlagmuster")
                    .setSingleChoiceItems(names, names.indexOf(selectedChordName).coerceAtLeast(0)) { dialog, which ->
                        selectedChordName = names[which]
                        selectedChord = ChordLibrary.all.first { it.name == selectedChordName }
                        prefs.edit().putString("learn_strum_chord", selectedChordName).apply()
                        chordButton.text = "Gitarrenklang · " + selectedChordName
                        dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
            levelButton.setOnClickListener {
                if (phase == "play" || phase == "preview") return@setOnClickListener
                val names = levels.keys.toTypedArray()
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Trainingsstufe")
                    .setSingleChoiceItems(names, names.indexOf(difficulty).coerceAtLeast(0)) { dialog, which ->
                        difficulty = names[which]
                        bpm = levels[difficulty]!!.first
                        slider.progress = bpm - 50
                        levelButton.text = "Stufe · " + difficulty
                        prefs.edit().putString("learn_strum_difficulty", difficulty).putInt("learn_strum_bpm", bpm).apply()
                        updateTimingLabel()
                        status.text = "Stufe gesetzt · " + difficulty
                        dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
            patternButton.setOnClickListener {
                if (phase == "play" || phase == "preview") return@setOnClickListener
                val names = patterns.keys.toTypedArray()
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Schlagmuster auswählen")
                    .setSingleChoiceItems(names, names.indexOf(selectedName).coerceAtLeast(0)) { dialog, which ->
                        selectedName = names[which]
                        selected = patterns[selectedName] ?: selected
                        step = 0
                        patternButton.text = selectedName
                        patternHint.text = "Pattern: " + selected.joinToString("  ")
                        status.text = "Muster gewählt · jetzt vorhören"
                        rebuildBeats(); markBeat()
                        dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
            slider.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(v: SeekBar?, p: Int, from: Boolean) {
                    bpm = 50 + p
                    tempoLabel.text = "Tempo: " + bpm + " BPM"
                    prefs.edit().putInt("learn_strum_bpm", bpm).apply()
                }
                override fun onStartTrackingTouch(v: SeekBar?) {}
                override fun onStopTrackingTouch(v: SeekBar?) {}
            })

            fun playPreview() {
                if (phase == "play" || phase == "preview") return
                phase = "preview"
                status.text = "Saitenwerk spielt vor …"
                previewButton.text = "▶ Läuft …"
                step = 0
                markBeat()
                val previewHandler = Handler(Looper.getMainLooper())
                val interval = (60000L / bpm / 2).coerceAtLeast(100L)
                fun tick(index: Int) {
                    if (phase != "preview") return
                    if (index >= selected.size) {
                        phase = "ready"
                        previewButton.text = "▶ Muster vorhören"
                        status.text = "Jetzt du · spiele das Muster"
                        markBeat(0)
                        return
                    }
                    step = index
                    markBeat(index)
                    val dir = selected[index]
                    if (dir != "·") GuitarAudioEngine.playChord(a, selectedChord, downstroke = dir == "↓", volume = if (index == 0) 0.78f else 0.56f)
                    previewHandler.postDelayed({ tick(index + 1) }, interval)
                }
                tick(0)
            }
            previewButton.setOnClickListener { playPreview() }

            fun userHit(direction: String) {
                if (phase != "play" || selected.isEmpty() || answered) return
                val expected = selected[step]
                if (expected == "·") {
                    misses++; combo = 0; status.text = "✕ Pause · hier nicht anschlagen"; refreshStats(); answered = true; return
                }
                val delta = kotlin.math.abs(android.os.SystemClock.elapsedRealtime() - expectedAt)
                val window = levels[difficulty]!!.second
                answered = true
                if (direction == expected && delta <= window) {
                    hits++; combo++; bestCombo = maxOf(bestCombo, combo)
                    when {
                        delta <= window / 4 -> { score += 100 + combo.coerceAtMost(20) * 3; status.text = "✓ Perfekt · " + delta + " ms" }
                        delta <= window / 2 -> { score += 80 + combo.coerceAtMost(20) * 2; status.text = "✓ Sehr gut · " + delta + " ms" }
                        else -> { score += 60; status.text = "✓ Im Timing · " + delta + " ms" }
                    }
                } else {
                    misses++; combo = 0
                    status.text = if (direction != expected) "✕ " + direction + " · erwartet " + expected else "◷ Zu spät/früh · " + delta + " ms"
                }
                refreshStats()
            }
            down.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, selectedChord, downstroke = true, volume = 0.84f)
                userHit("↓")
            }
            up.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, selectedChord, downstroke = false, volume = 0.84f)
                userHit("↑")
            }

            start.setOnClickListener {
                if (phase == "play") {
                    prefs.edit()
                        .putInt("learn_strum_best_score", maxOf(sessionBest, score))
                        .putInt("learn_strum_best_rounds", maxOf(roundBest, round))
                        .putInt("learn_strum_best_combo", maxOf(prefs.getInt("learn_strum_best_combo", 0), bestCombo))
                        .apply()
                    sessionBest = maxOf(sessionBest, score)
                    roundBest = maxOf(roundBest, round)
                    stopStrumming()
                    phase = "ready"
                    start.text = "Jetzt du · Training starten"
                    status.text = "Pausiert · " + score + " Punkte"
                    return@setOnClickListener
                }
                if (phase == "preview") return@setOnClickListener

                phase = "play"
                start.text = "Training stoppen"
                previewButton.text = "▶ Muster vorhören"
                step = 0; hits = 0; misses = 0; score = 0; combo = 0; bestCombo = 0; round = 0; answered = false
                strumRunning = true
                strumStartedAt = android.os.SystemClock.elapsedRealtime()
                strumHandler = Handler(Looper.getMainLooper())
                val interval = (60000L / bpm / 2).coerceAtLeast(100L)
                val task = object : Runnable {
                    override fun run() {
                        if (!strumRunning || phase != "play") return
                        step = (step + 1) % selected.size
                        if (step == 0) round++
                        answered = false
                        expectedAt = android.os.SystemClock.elapsedRealtime()
                        markBeat(step)
                        val dir = selected[step]
                        if (dir != "·") {
                            GuitarAudioEngine.playChord(a, selectedChord, downstroke = dir == "↓", volume = if (step == 0) 0.78f else 0.56f)
                        } else {
                            status.text = "• Pause · nächster Schlag vorbereitet"
                        }
                        refreshStats()
                        strumHandler?.postDelayed(this, interval)
                    }
                }
                status.text = "Jetzt du · spiele passend zur Markierung"
                strumHandler?.post(task)
            }

            updateTimingLabel()
            rebuildBeats()
            markBeat(0)
            refreshStats()
            content.addView(card)
        }'''
source = source[:start] + new_function + source[end:]
main.write_text(source, encoding="utf-8")

check = main.read_text(encoding="utf-8")
required = ["Schlagmuster-Trainer","Muster vorhören","Jetzt du · Training starten","Anfänger","Grundlagen","Fortgeschritten","Profi","Offbeat","learn_strum_best_combo","learn_strum_best_rounds","Timing-Fenster","GuitarAudioEngine.playChord","private fun stopStrumming()"]
missing = [x for x in required if x not in check]
if missing:
    raise SystemExit("FEHLER: intelligenter Schlagmuster-Trainer unvollständig: " + ", ".join(missing))
if check.count("fun showStrumming()") != 1:
    raise SystemExit("FEHLER: showStrumming() wurde mehrfach eingebaut.")
print("INTELLIGENTER-SCHLAGMUSTER-TRAINER: PASS")
print("Vorschau, Eigenphase, 4 Stufen, 8 Muster, Timingbewertung, Serien und Bestwerte integriert.")
