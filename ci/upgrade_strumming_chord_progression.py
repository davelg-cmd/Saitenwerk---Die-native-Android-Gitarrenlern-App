from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")
start = s.find("        fun showStrumming() {")
end = s.find("\n        fun showSongPractice() {", start)
if start < 0 or end < 0:
    raise SystemExit("FEHLER: showStrumming() nicht eindeutig gefunden.")
t = s[start:end]

old = '''            var selectedChordName = prefs.getString("learn_strum_chord", "G") ?: "G"
            var selectedChord = ChordLibrary.all.firstOrNull { it.name == selectedChordName } ?: ChordLibrary.all.first()
'''
new = '''            val savedChordNames = prefs.getStringSet("learn_strum_chords", null)?.toList()
                ?: listOf(prefs.getString("learn_strum_chord", "G") ?: "G")
            val selectedChordNames = savedChordNames.filter { name -> ChordLibrary.all.any { it.name == name } }
                .ifEmpty { listOf(ChordLibrary.all.first().name) }.toMutableList()
            var selectedChords = selectedChordNames.mapNotNull { name -> ChordLibrary.all.firstOrNull { it.name == name } }
            var selectedMeter = prefs.getString("learn_strum_meter", "4/4") ?: "4/4"
            if (selectedMeter !in listOf("3/4", "4/4", "6/8")) selectedMeter = "4/4"
            var selectedBars = prefs.getInt("learn_strum_bars", 4).coerceIn(1, 8)
'''
if old not in t: raise SystemExit("FEHLER: Einzelakkord-Status nicht gefunden.")
t = t.replace(old, new, 1)

old = '''            val chordButton = a.button("Gitarrenklang · " + selectedChordName)
            val levelButton = a.button("Stufe · " + difficulty)
'''
new = '''            val chordButton = a.button("Gitarrenklang · " + selectedChordNames.joinToString(" – "))
            val meterButton = a.button("Taktart · " + selectedMeter)
            val barsButton = a.button("Takte · " + selectedBars)
            val levelButton = a.button("Stufe · " + difficulty)
'''
if old not in t: raise SystemExit("FEHLER: Akkordbutton nicht gefunden.")
t = t.replace(old, new, 1)

old = '''            box.addView(levelButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(chordButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(patternButton, LinearLayout.LayoutParams(-1, a.dp(46)))
'''
new = '''            box.addView(levelButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(chordButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(meterButton, LinearLayout.LayoutParams(-1, a.dp(42)).apply { bottomMargin = a.dp(4) })
            box.addView(barsButton, LinearLayout.LayoutParams(-1, a.dp(42)).apply { bottomMargin = a.dp(5) })
            box.addView(patternButton, LinearLayout.LayoutParams(-1, a.dp(46)))
'''
if old not in t: raise SystemExit("FEHLER: Trainings-Layout-Anker nicht gefunden.")
t = t.replace(old, new, 1)

old = '''            chordButton.setOnClickListener {
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
'''
new = '''            chordButton.setOnClickListener {
                if (phase == "play" || phase == "preview") return@setOnClickListener
                val names = ChordLibrary.all.map { it.name }.toTypedArray()
                val checked = BooleanArray(names.size) { names[it] in selectedChordNames }
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Akkordfolge für den Gitarrenklang")
                    .setMultiChoiceItems(names, checked) { _, which, isChecked -> checked[which] = isChecked }
                    .setPositiveButton("Übernehmen") { dialog, _ ->
                        val chosen = names.indices.filter { checked[it] }.map { names[it] }
                        if (chosen.isNotEmpty()) {
                            selectedChordNames.clear()
                            selectedChordNames.addAll(chosen)
                            selectedChords = selectedChordNames.mapNotNull { name -> ChordLibrary.all.firstOrNull { it.name == name } }
                            prefs.edit().putStringSet("learn_strum_chords", selectedChordNames.toSet())
                                .putString("learn_strum_chord", selectedChordNames.first()).apply()
                            chordButton.text = "Gitarrenklang · " + selectedChordNames.joinToString(" – ")
                            status.text = selectedChordNames.size.toString() + " Akkorde ausgewählt · ein Akkord pro Takt"
                        } else {
                            android.widget.Toast.makeText(a, "Bitte mindestens einen Akkord auswählen.", android.widget.Toast.LENGTH_SHORT).show()
                        }
                        dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
            meterButton.setOnClickListener {
                if (phase == "play" || phase == "preview") return@setOnClickListener
                val meters = arrayOf("3/4", "4/4", "6/8")
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Taktart auswählen")
                    .setSingleChoiceItems(meters, meters.indexOf(selectedMeter).coerceAtLeast(0)) { dialog, which ->
                        selectedMeter = meters[which]
                        meterButton.text = "Taktart · " + selectedMeter
                        prefs.edit().putString("learn_strum_meter", selectedMeter).apply()
                        dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
            barsButton.setOnClickListener {
                if (phase == "play" || phase == "preview") return@setOnClickListener
                val bars = (1..8).map { it.toString() + (if (it == 1) " Takt" else " Takte") }.toTypedArray()
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Anzahl der Takte")
                    .setSingleChoiceItems(bars, selectedBars - 1) { dialog, which ->
                        selectedBars = which + 1
                        barsButton.text = "Takte · " + selectedBars
                        prefs.edit().putInt("learn_strum_bars", selectedBars).apply()
                        dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }
'''
if old not in t: raise SystemExit("FEHLER: Akkord-Auswahldialog nicht gefunden.")
t = t.replace(old, new, 1)

old = '''                fun tick(index: Int) {
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
'''
new = '''                val beatsPerBar = when (selectedMeter) { "3/4" -> 3; "6/8" -> 6; else -> 4 }
                val stepsPerBar = if (selected.size >= 6) beatsPerBar * 2 else beatsPerBar
                val totalSteps = selectedBars * stepsPerBar
                fun tick(index: Int) {
                    if (phase != "preview") return
                    if (index >= totalSteps) {
                        phase = "ready"
                        previewButton.text = "▶ Muster vorhören"
                        status.text = "Vorschau beendet · " + selectedChordNames.size + " Akkorde · " + selectedBars + " Takte"
                        markBeat(0)
                        return
                    }
                    val barIndex = index / stepsPerBar
                    val patternIndex = index % selected.size
                    step = patternIndex
                    markBeat(patternIndex)
                    val dir = selected[patternIndex]
                    val chord = selectedChords[barIndex % selectedChords.size]
                    if (dir != "·") GuitarAudioEngine.playChord(a, chord, downstroke = dir == "↓", volume = if (patternIndex == 0) 0.78f else 0.56f)
                    status.text = "Takt " + (barIndex + 1) + "/" + selectedBars + " · " + selectedChordNames[barIndex % selectedChordNames.size]
                    previewHandler.postDelayed({ tick(index + 1) }, interval)
                }
'''
if old not in t: raise SystemExit("FEHLER: Vorschau-Takt nicht gefunden.")
t = t.replace(old, new, 1)

old = '''            down.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, selectedChord, downstroke = true, volume = 0.84f)
                userHit("↓")
            }
            up.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, selectedChord, downstroke = false, volume = 0.84f)
                userHit("↑")
            }
'''
new = '''            fun currentPracticeChord(): ChordShape {
                val beatsPerBar = when (selectedMeter) { "3/4" -> 3; "6/8" -> 6; else -> 4 }
                val stepsPerBar = if (selected.size >= 6) beatsPerBar * 2 else beatsPerBar
                val barIndex = (round % selectedBars).coerceAtLeast(0)
                return selectedChords[barIndex % selectedChords.size]
            }
            down.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, currentPracticeChord(), downstroke = true, volume = 0.84f)
                userHit("↓")
            }
            up.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, currentPracticeChord(), downstroke = false, volume = 0.84f)
                userHit("↑")
            }
'''
if old not in t: raise SystemExit("FEHLER: Nutzer-Schlagbuttons nicht gefunden.")
t = t.replace(old, new, 1)

old = '''                        step = (step + 1) % selected.size
                        if (step == 0) round++
                        answered = false
                        expectedAt = android.os.SystemClock.elapsedRealtime()
                        markBeat(step)
                        val dir = selected[step]
                        if (dir != "·") {
                            GuitarAudioEngine.playChord(a, selectedChord, downstroke = dir == "↓", volume = if (step == 0) 0.78f else 0.56f)
                        } else {
'''
new = '''                        val beatsPerBar = when (selectedMeter) { "3/4" -> 3; "6/8" -> 6; else -> 4 }
                        val stepsPerBar = if (selected.size >= 6) beatsPerBar * 2 else beatsPerBar
                        step = (step + 1) % stepsPerBar
                        if (step == 0) round++
                        answered = false
                        expectedAt = android.os.SystemClock.elapsedRealtime()
                        markBeat(step % selected.size)
                        val patternIndex = step % selected.size
                        val dir = selected[patternIndex]
                        val chord = selectedChords[((round - 1).coerceAtLeast(0)) % selectedChordNames.size]
                        if (dir != "·") {
                            GuitarAudioEngine.playChord(a, chord, downstroke = dir == "↓", volume = if (patternIndex == 0) 0.78f else 0.56f)
                        } else {
'''
if old not in t: raise SystemExit("FEHLER: Trainings-Takt nicht gefunden.")
t = t.replace(old, new, 1)

# Ensure the selected pattern is displayed/marked using a valid pattern index.
t = t.replace('''                val expected = selected[step]
''','''                val expected = selected[step % selected.size]
''',1)
if "selectedChord" in t and "selectedChordNames" not in t:
    raise SystemExit("FEHLER: Alte Einzelakkord-Referenz ist noch vorhanden.")

s = s[:start] + t + s[end:]
main.write_text(s, encoding="utf-8")

required = [
    'setMultiChoiceItems(names, checked)',
    'putStringSet("learn_strum_chords"',
    'Taktart auswählen',
    'learn_strum_meter',
    'Anzahl der Takte',
    'learn_strum_bars',
    'selectedBars * stepsPerBar',
    'selectedChords[barIndex % selectedChords.size]',
    'GuitarAudioEngine.playChord(a, chord',
]
missing = [item for item in required if item not in t]
if missing:
    raise SystemExit("FEHLER: Akkordfolge/Takt-Auswahl unvollständig: " + ", ".join(missing))
if "selectedChord," in t or "selectedChord)" in t:
    raise SystemExit("FEHLER: Einzelakkord-Wiedergabe ist noch vorhanden.")
print("SCHLAGMUSTER-AKKORDFOLGE: PASS – Mehrfachauswahl, Taktart, Taktanzahl und Akkordwechsel pro Takt integriert.")
