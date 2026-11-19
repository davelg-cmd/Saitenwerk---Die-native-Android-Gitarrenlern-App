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
new = '''            val orderedChordJson = prefs.getString("learn_strum_chords_ordered", null)
            val savedChordNames = if (!orderedChordJson.isNullOrBlank()) {
                runCatching {
                    val array = org.json.JSONArray(orderedChordJson)
                    (0 until array.length()).map { array.getString(it) }
                }.getOrElse { prefs.getStringSet("learn_strum_chords", null)?.toList().orEmpty() }
            } else {
                prefs.getStringSet("learn_strum_chords", null)?.toList()
                    ?: listOf(prefs.getString("learn_strum_chord", "G") ?: "G")
            }
            val selectedChordNames = savedChordNames.distinct()
                .filter { name -> ChordLibrary.all.any { it.name == name } }
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
                val selectionOrder = selectedChordNames.toMutableList()
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Akkordfolge für den Gitarrenklang")
                    .setMultiChoiceItems(names, checked) { _, which, isChecked ->
                        checked[which] = isChecked
                        if (isChecked) {
                            if (names[which] !in selectionOrder) selectionOrder.add(names[which])
                        } else {
                            selectionOrder.remove(names[which])
                        }
                    }
                    .setPositiveButton("Übernehmen") { dialog, _ ->
                        val chosen = selectionOrder.filter { name ->
                            val index = names.indexOf(name)
                            index >= 0 && checked[index]
                        }
                        if (chosen.isNotEmpty()) {
                            selectedChordNames.clear()
                            selectedChordNames.addAll(chosen)
                            selectedChords = selectedChordNames.mapNotNull { name -> ChordLibrary.all.firstOrNull { it.name == name } }
                            prefs.edit()
                                .putString("learn_strum_chords_ordered", org.json.JSONArray(selectedChordNames).toString())
                                .putStringSet("learn_strum_chords", selectedChordNames.toSet())
                                .putString("learn_strum_chord", selectedChordNames.first())
                                .apply()
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
                val barIndex = round.coerceAtLeast(0)
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
                        val chord = selectedChords[round % selectedChords.size]
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


# Nicht mehr benötigte Bedienelemente aus dem finalen Trainer entfernen.
def remove_once(old, label):
    global t
    if old not in t:
        raise SystemExit("FEHLER: Entfernen nicht möglich, Element nicht gefunden: " + label)
    t = t.replace(old, "", 1)

# Der separate Takte-Wähler und die nur dafür benötigte Hilfsfunktion entfallen.
remove_once('''            var selectedBars = prefs.getInt("learn_strum_bars", 4).coerceIn(1, 8)
''', "Taktanzahl-Status")
remove_once('''            fun currentPracticeChord(): ChordShape {
                val beatsPerBar = when (selectedMeter) { "3/4" -> 3; "6/8" -> 6; else -> 4 }
                val stepsPerBar = if (selected.size >= 6) beatsPerBar * 2 else beatsPerBar
                val barIndex = round.coerceAtLeast(0)
                return selectedChords[barIndex % selectedChords.size]
            }
''', "Hilfsfunktion für entfernte Abschlag-/Aufschlag-Buttons")

remove_once('''            val previewButton = a.button("▶ Muster vorhören")
''', "Muster-vorhören-Button")
remove_once('''            val barsButton = a.button("Takte · " + selectedBars)
''', "Takte-Button")
remove_once('''            val down = a.button("↓ Abschlag")
            val up = a.button("↑ Aufschlag")
            val actionRow = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL }
''', "Abschlag-/Aufschlag-Buttons")
remove_once('''            box.addView(barsButton, LinearLayout.LayoutParams(-1, a.dp(42)).apply { bottomMargin = a.dp(5) })
''', "Takte-Button-Layout")
remove_once('''            box.addView(previewButton, LinearLayout.LayoutParams(-1, a.dp(46)).apply { topMargin = a.dp(2) })
''', "Muster-vorhören-Layout")
remove_once('''            actionRow.addView(down, LinearLayout.LayoutParams(0, a.dp(52), 1f).apply { rightMargin = a.dp(4) })
            actionRow.addView(up, LinearLayout.LayoutParams(0, a.dp(52), 1f).apply { leftMargin = a.dp(4) })
            box.addView(actionRow, LinearLayout.LayoutParams(-1, a.dp(56)).apply { topMargin = a.dp(6) })
''', "Abschlag-/Aufschlag-Layout")
remove_once('''            barsButton.setOnClickListener {
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
''', "Takte-Auswahldialog")
remove_once('''            down.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, currentPracticeChord(), downstroke = true, volume = 0.84f)
                userHit("↓")
            }
            up.setOnClickListener {
                if (phase == "play") GuitarAudioEngine.playChord(a, currentPracticeChord(), downstroke = false, volume = 0.84f)
                userHit("↑")
            }
''', "Abschlag-/Aufschlag-Listener")
# The preview routine is no longer reachable and is removed with its button.
preview_start = t.find("            fun playPreview() {")
preview_end = t.find("            fun userHit(direction: String) {", preview_start)
if preview_start < 0 or preview_end < 0:
    raise SystemExit("FEHLER: Vorhörfunktion nicht eindeutig gefunden.")
t = t[:preview_start] + t[preview_end:]
t = t.replace('''                previewButton.text = "▶ Muster vorhören"
''', "")
t = t.replace('''                previewButton.text = "▶ Läuft …"
''', "")
t = t.replace('''            previewButton.setOnClickListener { playPreview() }
''', "")
t = t.replace('''            start.text = "Jetzt du · Training starten"
''', '''            start.text = "Training starten"
''')
t = t.replace('''            val start = a.button("Jetzt du · Training starten")
''', '''            val start = a.button("Training starten")
''')
t = t.replace('''                status.text = "Jetzt du · spiele passend zur Markierung"
''', '''                status.text = "Spiele passend zur Markierung"
''')
# Finale Oberfläche und Laufzeitlogik nach dem Entfernen der Vorschau vollständig bereinigen.
t = t.replace('''            prefs.edit().putInt("learn_skill_strum", prefs.getInt("learn_skill_strum", 0) + 1).apply()
''', '''            prefs.edit().remove("learn_strum_bars")
                .putInt("learn_skill_strum", prefs.getInt("learn_skill_strum", 0) + 1).apply()
''')
t = t.replace('''            val (card, box) = panel("Schlagmuster-Trainer", "Saitenwerk zeigt dir erst das Muster, dann spielst du selbst. Timing, Richtung und Serien werden direkt ausgewertet.")
''', '''            val (card, box) = panel("Schlagmuster-Trainer", "Wähle ein Muster und übe den Rhythmus. Timing, Richtung und Serien werden direkt ausgewertet.")
''')
t = t.replace('''            val beatRow = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER }
''', '''            val beatRow = LinearLayout(a).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
                isClickable = true
                isFocusable = true
            }
            val gestureHint = TextView(a).apply {
                text = "Im Training auf den Schlagpfeilen wischen: ↓ Abschlag · ↑ Aufschlag"
                textSize = 12f
                gravity = Gravity.CENTER
                setTextColor(a.getColor(R.color.sw_muted))
                setPadding(a.dp(4), a.dp(2), a.dp(4), a.dp(6))
            }
''')
t = t.replace('''            box.addView(beatRow, LinearLayout.LayoutParams(-1, a.dp(76)))
            box.addView(status)
''', '''            box.addView(beatRow, LinearLayout.LayoutParams(-1, a.dp(76)))
            box.addView(gestureHint)
            box.addView(status)
''')
t = t.replace('''            start.setOnClickListener {
                if (phase == "play") {
''', '''            var gestureStartX = 0f
            var gestureStartY = 0f
            beatRow.setOnTouchListener { _, event ->
                when (event.actionMasked) {
                    android.view.MotionEvent.ACTION_DOWN -> {
                        gestureStartX = event.x
                        gestureStartY = event.y
                        true
                    }
                    android.view.MotionEvent.ACTION_UP -> {
                        val deltaX = event.x - gestureStartX
                        val deltaY = event.y - gestureStartY
                        if (phase == "play" &&
                            kotlin.math.abs(deltaY) >= a.dp(28).toFloat() &&
                            kotlin.math.abs(deltaY) > kotlin.math.abs(deltaX)) {
                            val direction = if (deltaY > 0f) "↓" else "↑"
                            val chord = selectedChords[round.coerceAtLeast(0) % selectedChords.size]
                            GuitarAudioEngine.playChord(
                                a, chord, downstroke = direction == "↓", volume = 0.84f
                            )
                            userHit(direction)
                        }
                        true
                    }
                    android.view.MotionEvent.ACTION_CANCEL -> true
                    else -> true
                }
            }

            start.setOnClickListener {
                if (phase == "play") {
''')
t = t.replace('''                        step = (step + 1) % stepsPerBar
                        if (step == 0) round++
''', '''                        step += 1
                        if (step >= stepsPerBar) {
                            step = 0
                            round++
                        }
''')
t = t.replace('''                step = 0; hits = 0; misses = 0; score = 0; combo = 0; bestCombo = 0; round = 0; answered = false
''', '''                step = -1; hits = 0; misses = 0; score = 0; combo = 0; bestCombo = 0; round = 0; answered = false
''')
t = t.replace('if (phase == "play" || phase == "preview") return@setOnClickListener',
              'if (phase == "play") return@setOnClickListener')
t = t.replace('''                if (phase == "preview") return@setOnClickListener
''', "")
# Ohne Vorhörmodus darf der Status keine nicht mehr vorhandene Vorhör-Aktion ankündigen.
t = t.replace('''                text = "Bereit · zuerst Muster vorhören"
''', '''                text = "Bereit · Training starten"
''')
t = t.replace('''                        status.text = "Muster gewählt · jetzt vorhören"
''', '''                        status.text = "Muster gewählt · bereit zum Training"
''')
if "preview" in t or "selectedBars" in t:
    raise SystemExit("FEHLER: Verwaiste Vorschau- oder Taktanzahl-Referenz im finalen Trainer.")
if t.count('remove("learn_strum_bars")') != 1 or 'getInt("learn_strum_bars"' in t or 'putInt("learn_strum_bars"' in t:
    raise SystemExit("FEHLER: Veraltete Taktanzahl-Einstellung wurde nicht vollständig bereinigt.")
if "previewButton" in t or "barsButton" in t or "actionRow" in t or "val down =" in t or "val up =" in t:
    raise SystemExit("FEHLER: Entfernte Bedienelemente sind noch im Trainer enthalten.")
if 'val start = a.button("Training starten")' not in t:
    raise SystemExit("FEHLER: Startbutton-Beschriftung wurde nicht bereinigt.")
if 'beatRow.setOnTouchListener' not in t or 'userHit(direction)' not in t:
    raise SystemExit("FEHLER: Wischsteuerung ist nicht mit der Timing-Auswertung verbunden.")
if 'learn_strum_chords_ordered' not in t or 'org.json.JSONArray(selectedChordNames)' not in t:
    raise SystemExit("FEHLER: Akkordreihenfolge wird nicht dauerhaft und geordnet gespeichert.")
if 'step = -1;' not in t:
    raise SystemExit("FEHLER: Der erste Schlag wird beim Trainingsstart nicht korrekt initialisiert.")

s = s[:start] + t + s[end:]
if "    private var strumStep = 0\n" in s:
    s = s.replace("    private var strumStep = 0\n", "", 1)
main.write_text(s, encoding="utf-8")

required = [
    'setMultiChoiceItems(names, checked)',
    'putStringSet("learn_strum_chords"',
    'learn_strum_chords_ordered',
    'org.json.JSONArray(selectedChordNames)',
    'beatRow.setOnTouchListener',
    'userHit(direction)',
    'gestureHint',
    'Taktart auswählen',
    'learn_strum_meter',
    'GuitarAudioEngine.playChord(a, chord',
]
missing = [item for item in required if item not in t]
if missing:
    raise SystemExit("FEHLER: Akkordfolge/Takt-Auswahl unvollständig: " + ", ".join(missing))
if "selectedChord," in t or "selectedChord)" in t:
    raise SystemExit("FEHLER: Einzelakkord-Wiedergabe ist noch vorhanden.")
print("SCHLAGMUSTER-TRAINER: PASS – Vorschau- und Taktzustände entfernt, Wischsteuerung an Timing-Auswertung gekoppelt, Akkordreihenfolge dauerhaft gesichert.")
