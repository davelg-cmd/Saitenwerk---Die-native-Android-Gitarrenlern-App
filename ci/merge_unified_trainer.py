from pathlib import Path
import os

main = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

# Idempotent rebuild: a later beta starts from the already merged build backup.
if 'fun showStrumming(initialMode: String = "strumming") {' in s and 'Gemeinsamer Gitarrentrainer' in s and 'class ChordTrainingPanel' not in s:
    required = ['fun showChanges() { showStrumming("changes") }', 'learn_training_chords_ordered', 'learn_training_meter', 'learn_training_bpm', 'beatRow.setOnTouchListener', 'userHit(direction)']
    if any(x not in s for x in required):
        raise SystemExit("FEHLER: Vorhandener gemeinsamer Trainer ist unvollständig.")
    print("GEMEINSAMER TRAINER: bereits integriert – idempotenter Durchlauf PASS")
    raise SystemExit(0)

def replace_once(source, old, new, label):
    if old not in source:
        raise SystemExit("FEHLER: " + label + " nicht eindeutig gefunden.")
    return source.replace(old, new, 1)

# Remove the separate ChordTrainingPanel from the chord library and LearnFragment.
s = s.replace('    private var chordTraining: ChordTrainingPanel? = null\n', '')
s = s.replace('        chordTraining?.stop()\n        chordTraining = null\n', '')
s = s.replace('chordTraining?.stop(); chordTraining = null; ', '')
s = replace_once(s, '''class ChordsFragment : Fragment() {
    private var training: ChordTrainingPanel? = null

    override fun onDestroyView() {
        training?.stop()
        training = null
        super.onDestroyView()
    }
''', '''class ChordsFragment : Fragment() {
''', "ChordsFragment-Trainerreferenz")
s = replace_once(s, '''        training = ChordTrainingPanel(a)
        content.addView(training, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = a.dp(14)
        })
''', '''        val unifiedTrainerEntry = a.button("Zum Lernstudio")
        unifiedTrainerEntry.setOnClickListener { a.openSection(5) }
        content.addView(unifiedTrainerEntry, LinearLayout.LayoutParams(-1, a.dp(50)).apply {
            topMargin = a.dp(14)
        })
''', "Akkordbibliothek-Trainerlink")
class_start = s.find('\nclass ChordTrainingPanel(private val host: MainActivity) : LinearLayout(host) {')
class_end = s.find('\nobject SongRepository {', class_start)
if class_start < 0 or class_end < 0:
    raise SystemExit("FEHLER: Alte ChordTrainingPanel-Klasse nicht gefunden.")
s = s[:class_start] + s[class_end:]

# The former Akkordwechsel entry now opens the shared trainer in its chord mode.
old_changes = '''        fun showChanges() {
            prefs.edit().putInt("learn_skill_changes", prefs.getInt("learn_skill_changes", 0) + 1).apply()
            finishQuizSession(); stopRhythm(); content.removeAllViews()
            content.addView(a.body("Dein Haupttraining für saubere Akkordwechsel. Wähle Akkorde, Takt und Tempo direkt im Trainer und steigere dich erst, wenn die Wechsel sicher sitzen."))
            chordTraining = ChordTrainingPanel(a); content.addView(chordTraining, LinearLayout.LayoutParams(-1, -2))
        }
'''
s = replace_once(s, old_changes, "", "showChanges-Altimplementierung")
s = s.replace('        fun showStrumming() {', '        fun showStrumming(initialMode: String = "strumming") {', 1)
start = s.find('        fun showStrumming(initialMode: String = "strumming") {')
end = s.find('\n        fun showFretboard() {', start)
if start < 0 or end < 0:
    raise SystemExit("FEHLER: Schlagmuster-Trainerbereich nicht gefunden.")
t = s[start:end]

t = t.replace('''            prefs.edit().remove("learn_strum_bars")
                .putInt("learn_skill_strum", prefs.getInt("learn_skill_strum", 0) + 1).apply()
''', '''            prefs.edit().remove("learn_strum_bars").apply()
''', 1)
t = replace_once(t, 'panel("Schlagmuster-Trainer", "Wähle ein Muster und übe den Rhythmus. Timing, Richtung und Serien werden direkt ausgewertet.")', 'panel("Gemeinsamer Gitarrentrainer", "Trainiere Akkordwechsel oder Schlagmuster mit denselben Akkorden, derselben Taktart und demselben Tempo.")', "Trainerüberschrift")

# Migrate both former trainers' settings to one ordered chord list, one meter and one BPM value.
old_settings = '''            var selectedMeter = prefs.getString("learn_strum_meter", "4/4") ?: "4/4"
            if (selectedMeter !in listOf("3/4", "4/4", "6/8")) selectedMeter = "4/4"
            var difficulty = prefs.getString("learn_strum_difficulty", "Grundlagen") ?: "Grundlagen"
            if (!levels.containsKey(difficulty)) difficulty = "Grundlagen"
            var bpm = prefs.getInt("learn_strum_bpm", levels[difficulty]!!.first).coerceIn(50, 160)
'''
new_settings = '''            val legacyChordSequence = prefs.getStringSet("chord_training_selected_chords", null)?.sorted().orEmpty()
            val legacyChordJson = prefs.getString("learn_strum_chords_ordered", null)
            val canonicalChordJson = prefs.getString("learn_training_chords_ordered", null)
            fun decodeChordOrder(raw: String?): List<String>? = raw?.takeIf { it.isNotBlank() }?.let {
                runCatching { org.json.JSONArray(it).let { array -> (0 until array.length()).map { index -> array.getString(index) } } }.getOrNull()
            }
            val sharedChordNames = decodeChordOrder(canonicalChordJson)
                ?: if (initialMode == "changes") legacyChordSequence.takeIf { it.isNotEmpty() } ?: decodeChordOrder(legacyChordJson) ?: listOf("C", "G", "Am", "F")
                else decodeChordOrder(legacyChordJson) ?: legacyChordSequence.takeIf { it.isNotEmpty() } ?: savedChordNames
            selectedChordNames.clear()
            selectedChordNames.addAll(sharedChordNames.distinct().filter { name -> ChordLibrary.all.any { it.name == name } }
                .ifEmpty { listOf(ChordLibrary.all.first().name) })
            selectedChords = selectedChordNames.mapNotNull { name -> ChordLibrary.all.firstOrNull { it.name == name } }
            val legacyMeter = if (initialMode == "changes") prefs.getString("chord_training_meter", null) ?: prefs.getString("learn_strum_meter", "4/4")
                else prefs.getString("learn_strum_meter", null) ?: prefs.getString("chord_training_meter", "4/4")
            var selectedMeter = (prefs.getString("learn_training_meter", null) ?: legacyMeter ?: "4/4")
            if (selectedMeter !in listOf("2/4", "3/4", "4/4", "6/8")) selectedMeter = "4/4"
            var difficulty = prefs.getString("learn_strum_difficulty", "Grundlagen") ?: "Grundlagen"
            if (!levels.containsKey(difficulty)) difficulty = "Grundlagen"
            val legacyBpm = if (initialMode == "changes") prefs.getInt("chord_training_bpm", prefs.getInt("learn_strum_bpm", levels[difficulty]!!.first)) else prefs.getInt("learn_strum_bpm", prefs.getInt("chord_training_bpm", levels[difficulty]!!.first))
            var bpm = prefs.getInt("learn_training_bpm", legacyBpm).coerceIn(50, 160)
            var trainingMode = initialMode
            prefs.edit().putString("learn_training_mode", trainingMode)
                .putString("learn_training_meter", selectedMeter)
                .putInt("learn_training_bpm", bpm)
                .putString("learn_training_chords_ordered", org.json.JSONArray(selectedChordNames).toString())
                .putString("learn_strum_meter", selectedMeter).putString("chord_training_meter", selectedMeter)
                .putInt("learn_strum_bpm", bpm).putInt("chord_training_bpm", bpm)
                .putStringSet("chord_training_selected_chords", selectedChordNames.toSet()).apply()
'''
t = replace_once(t, old_settings, new_settings, "gemeinsame Einstellungen und Migration")

# Add one mode selector and chord diagram; common controls are rendered once.
t = replace_once(t, '''            val patternButton = a.button(selectedName)
            val chordButton = a.button("Gitarrenklang · " + selectedChordNames.joinToString(" – "))
''', '''            val modeButton = a.button(if (trainingMode == "changes") "Trainingsmodus · Akkordwechsel" else "Trainingsmodus · Schlagmuster")
            val chordButton = a.button("Akkorde · " + selectedChordNames.joinToString(" – "))
            val chordSequenceLabel = TextView(a).apply {
                text = selectedChordNames.joinToString("   →   ")
                textSize = 19f; gravity = Gravity.CENTER
                setTextColor(a.getColor(R.color.sw_copper)); setPadding(0, a.dp(8), 0, a.dp(8))
            }
            val chordDiagram = ChordDiagramView(a, selectedChords.firstOrNull())
            val patternButton = a.button(selectedName)
''', "gemeinsame Modus- und Akkordansicht")
t = replace_once(t, '''            box.addView(levelButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(chordButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
''', '''            box.addView(modeButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(chordButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(chordSequenceLabel, LinearLayout.LayoutParams(-1, -2))
            box.addView(chordDiagram, LinearLayout.LayoutParams(-1, a.dp(190)))
            box.addView(levelButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
''', "gemeinsames Trainerlayout")

t = t.replace('val meters = arrayOf("3/4", "4/4", "6/8")', 'val meters = arrayOf("2/4", "3/4", "4/4", "6/8")', 1)
t = t.replace('prefs.edit().putString("learn_strum_meter", selectedMeter).apply()', 'prefs.edit().putString("learn_training_meter", selectedMeter).putString("learn_strum_meter", selectedMeter).putString("chord_training_meter", selectedMeter).apply()', 1)
t = t.replace('prefs.edit().putInt("learn_strum_bpm", bpm).apply()', 'prefs.edit().putInt("learn_training_bpm", bpm).putInt("learn_strum_bpm", bpm).putInt("chord_training_bpm", bpm).apply()', 1)
t = t.replace('prefs.edit().putString("learn_strum_difficulty", difficulty).putInt("learn_strum_bpm", bpm).apply()', 'prefs.edit().putString("learn_strum_difficulty", difficulty).putInt("learn_training_bpm", bpm).putInt("learn_strum_bpm", bpm).putInt("chord_training_bpm", bpm).apply()', 1)

# Chord picker keeps ordering and synchronizes the legacy preferences for migration safety.
old_picker_save = '''                            prefs.edit()
                                .putString("learn_strum_chords_ordered", org.json.JSONArray(selectedChordNames).toString())
                                .putStringSet("learn_strum_chords", selectedChordNames.toSet())
                                .putString("learn_strum_chord", selectedChordNames.first())
                                .apply()
                            chordButton.text = "Gitarrenklang · " + selectedChordNames.joinToString(" – ")
'''
new_picker_save = '''                            val ordered = org.json.JSONArray(selectedChordNames).toString()
                            prefs.edit().putString("learn_training_chords_ordered", ordered)
                                .putString("learn_strum_chords_ordered", ordered)
                                .putStringSet("learn_strum_chords", selectedChordNames.toSet())
                                .putString("learn_strum_chord", selectedChordNames.first())
                                .putStringSet("chord_training_selected_chords", selectedChordNames.toSet()).apply()
                            chordButton.text = "Akkorde · " + selectedChordNames.joinToString(" – ")
                            chordSequenceLabel.text = selectedChordNames.joinToString("   →   ")
                            chordDiagram.setChord(selectedChords.firstOrNull())
'''
t = replace_once(t, old_picker_save, new_picker_save, "geordnete gemeinsame Akkordauswahl")
t = t.replace('if (chosen.isNotEmpty()) {', 'if (chosen.isNotEmpty() && (trainingMode != "changes" || chosen.size >= 2)) {', 1)
t = t.replace('"Bitte mindestens einen Akkord auswählen."', 'if (trainingMode == "changes") "Wähle mindestens zwei Akkorde für Akkordwechsel." else "Bitte mindestens einen Akkord auswählen."', 1)

mode_block = '''            fun updateTrainingModeUi() {
                val changesMode = trainingMode == "changes"
                modeButton.text = if (changesMode) "Trainingsmodus · Akkordwechsel" else "Trainingsmodus · Schlagmuster"
                levelButton.visibility = if (changesMode) View.GONE else View.VISIBLE
                patternButton.visibility = if (changesMode) View.GONE else View.VISIBLE
                beatRow.visibility = if (changesMode) View.GONE else View.VISIBLE
                gestureHint.visibility = if (changesMode) View.GONE else View.VISIBLE
                chordSequenceLabel.visibility = if (changesMode) View.VISIBLE else View.GONE
                chordDiagram.visibility = if (changesMode) View.VISIBLE else View.GONE
                timing.visibility = if (changesMode) View.GONE else View.VISIBLE
                status.text = if (changesMode) "Ein Akkord pro Takt · mindestens zwei Akkorde auswählen" else "Spiele passend zur Markierung"
            }
            modeButton.setOnClickListener {
                if (phase == "play") return@setOnClickListener
                trainingMode = if (trainingMode == "changes") "strumming" else "changes"
                prefs.edit().putString("learn_training_mode", trainingMode).apply()
                updateTrainingModeUi()
            }
'''
t = replace_once(t, '            chordButton.setOnClickListener {', mode_block + '            chordButton.setOnClickListener {', "Modusumschaltung")

# Gesture input stays attached to the strumming mode and still triggers audio plus timing evaluation.
t = t.replace('if (phase == "play" &&\n                            kotlin.math.abs(deltaY)', 'if (phase == "play" && trainingMode == "strumming" &&\n                            kotlin.math.abs(deltaY)', 1)

# One start/stop control; each mode stores its own progress statistics.
old_stop = '''                if (phase == "play") {
                    prefs.edit()
                        .putInt("learn_strum_best_score", maxOf(sessionBest, score))
                        .putInt("learn_strum_best_rounds", maxOf(roundBest, round))
                        .putInt("learn_strum_best_combo", maxOf(prefs.getInt("learn_strum_best_combo", 0), bestCombo))
                        .apply()
                    sessionBest = maxOf(sessionBest, score)
                    roundBest = maxOf(roundBest, round)
'''
new_stop = '''                if (phase == "play") {
                    if (trainingMode == "strumming") {
                        prefs.edit().putInt("learn_strum_best_score", maxOf(sessionBest, score))
                            .putInt("learn_strum_best_rounds", maxOf(roundBest, round))
                            .putInt("learn_strum_best_combo", maxOf(prefs.getInt("learn_strum_best_combo", 0), bestCombo)).apply()
                        sessionBest = maxOf(sessionBest, score); roundBest = maxOf(roundBest, round)
                    } else prefs.edit().putInt("chord_training_best_streak", maxOf(prefs.getInt("chord_training_best_streak", 0), round)).apply()
'''
t = replace_once(t, old_stop, new_stop, "modusgetrennte Trainingsstatistik")
t = t.replace('''                phase = "play"
                start.text = "Training stoppen"
''', '''                if (trainingMode == "changes" && selectedChords.size < 2) {
                    android.widget.Toast.makeText(a, "Wähle zuerst mindestens zwei Akkorde aus.", android.widget.Toast.LENGTH_LONG).show()
                    return@setOnClickListener
                }
                if (trainingMode == "changes") prefs.edit().putInt("learn_skill_changes", prefs.getInt("learn_skill_changes", 0) + 1)
                    .putInt("chord_training_sessions", prefs.getInt("chord_training_sessions", 0) + 1).apply()
                else prefs.edit().putInt("learn_skill_strum", prefs.getInt("learn_skill_strum", 0) + 1).apply()
                phase = "play"
                start.text = "Training stoppen"
''', 1)
t = t.replace('val interval = (60000L / bpm / 2).coerceAtLeast(100L)', 'val interval = (if (trainingMode == "changes" && selectedMeter == "6/8") 90000L / bpm else 60000L / bpm / (if (trainingMode == "changes") 1 else 2)).coerceAtLeast(100L)', 1)
old_tick = '''                        val beatsPerBar = when (selectedMeter) { "3/4" -> 3; "6/8" -> 6; else -> 4 }
                        val stepsPerBar = if (selected.size >= 6) beatsPerBar * 2 else beatsPerBar
                        step += 1
                        if (step >= stepsPerBar) {
                            step = 0
                            round++
                        }
                        answered = false
                        expectedAt = android.os.SystemClock.elapsedRealtime()
                        markBeat(step % selected.size)
                        val patternIndex = step % selected.size
                        val dir = selected[patternIndex]
                        val chord = selectedChords[round % selectedChords.size]
                        if (dir != "·") {
                            GuitarAudioEngine.playChord(a, chord, downstroke = dir == "↓", volume = if (patternIndex == 0) 0.78f else 0.56f)
                        } else {
                            status.text = "• Pause · nächster Schlag vorbereitet"
                        }
                        refreshStats()
'''
new_tick = '''                        val beatsPerBar = when (selectedMeter) { "2/4" -> 2; "3/4" -> 3; "6/8" -> if (trainingMode == "changes") 2 else 6; else -> 4 }
                        val stepsPerBar = if (trainingMode == "changes") beatsPerBar else if (selected.size >= 6) beatsPerBar * 2 else beatsPerBar
                        step += 1
                        if (step >= stepsPerBar) { step = 0; round++ }
                        answered = false
                        expectedAt = android.os.SystemClock.elapsedRealtime()
                        val chord = selectedChords[round % selectedChords.size]
                        if (trainingMode == "changes") {
                            chordSequenceLabel.text = "Jetzt: \${chord.name}    →    Danach: \${selectedChords[(round + 1) % selectedChords.size].name}"
                            chordDiagram.setChord(chord)
                            status.text = "Akkordwechsel · Takt \${round + 1} · \${step + 1}/\${beatsPerBar}"
                            GuitarAudioEngine.playChord(a, chord, downstroke = step % 2 == 0, volume = if (step == 0) 0.80f else 0.56f)
                            roundLabel.text = "Takt \${round + 1} · \${chord.name} · \${selectedChords.size} Akkorde in Folge"
                            stats.text = "Akkordwechsel · \${round} abgeschlossene Takte · Tempo \${bpm} BPM"
                        } else {
                            markBeat(step % selected.size)
                            val patternIndex = step % selected.size
                            val dir = selected[patternIndex]
                            if (dir != "·") GuitarAudioEngine.playChord(a, chord, downstroke = dir == "↓", volume = if (patternIndex == 0) 0.78f else 0.56f)
                            else status.text = "• Pause · nächster Schlag vorbereitet"
                            refreshStats()
                        }
'''
t = replace_once(t, old_tick, new_tick, "gemeinsame Takt- und Wiedergabelogik")
t = t.replace('''                status.text = "Spiele passend zur Markierung"
                strumHandler?.post(task)
''', '''                status.text = if (trainingMode == "changes") "Akkordwechsel läuft" else "Spiele passend zur Markierung"
                strumHandler?.post(task)
''', 1)
t = t.replace('''            updateTimingLabel()
            rebuildBeats()
''', '''            updateTimingLabel()
            updateTrainingModeUi()
            rebuildBeats()
''', 1)

s = s[:start] + t + s[end:]
# Define showChanges only after showStrumming, because Kotlin local functions cannot forward-reference later local declarations.
s = replace_once(s, '\n        fun showFretboard() {', '\n        fun showChanges() { showStrumming("changes") }\n\n        fun showFretboard() {', "showChanges-Position")

# Replace two Song Practice buttons with one combined entry.
s = s.replace('''            actionBox.addView(a.button("↔ Akkordwechsel trainieren").apply { setOnClickListener { showChanges() } },
                LinearLayout.LayoutParams(-1, a.dp(46)).apply { bottomMargin = a.dp(8) })
''', '', 1)
s = s.replace('''            actionBox.addView(a.button("↘ Schlagmuster trainieren").apply { setOnClickListener { showStrumming() } },
                LinearLayout.LayoutParams(-1, a.dp(46)).apply { bottomMargin = a.dp(8) })
''', '''            actionBox.addView(a.button("Akkordwechsel & Schlagmuster trainieren").apply { setOnClickListener { showChanges() } },
                LinearLayout.LayoutParams(-1, a.dp(46)))
''', 1)

# Deep consistency checks: no dead class/field references and both modes share the same persisted settings.
for forbidden in ['ChordTrainingPanel', 'chordTraining?.stop()', 'chordTraining = null', 'training = ChordTrainingPanel']:
    if forbidden in s:
        raise SystemExit("FEHLER: Veraltete Trainerreferenz verbleibt: " + forbidden)
required = ['fun showChanges() { showStrumming("changes") }', 'fun showStrumming(initialMode: String = "strumming") {', 'learn_training_chords_ordered', 'learn_training_meter', 'learn_training_bpm', 'Trainingsmodus · Akkordwechsel', 'Trainingsmodus · Schlagmuster', 'beatRow.setOnTouchListener', 'userHit(direction)', 'Gemeinsamer Gitarrentrainer']
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("FEHLER: Gemeinsamer Trainer unvollständig: " + ", ".join(missing))
main.write_text(s, encoding="utf-8")
print("GEMEINSAMER TRAINER: PASS – ein Trainer, zwei Modi, gemeinsame Akkord-/Takt-/Tempo-Einstellungen, migrierte Präferenzen, getrennte Fortschrittswerte und entfernte Doppelimplementierung.")
