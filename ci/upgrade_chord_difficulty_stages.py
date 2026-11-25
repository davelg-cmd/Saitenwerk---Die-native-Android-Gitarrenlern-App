#!/usr/bin/env python3
from pathlib import Path
import os, re

main = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")
if 'fun difficultyFor(shape: ChordShape): String' in s:
    required = ['Schwierigkeitsstufe', 'ChordLibrary.difficultyFor(it) == category',
                'Fehlertraining bleibt innerhalb der gewählten Stufe']
    missing = [x for x in required if x not in s]
    if missing:
        raise SystemExit("FEHLER: Vorhandene Stufen unvollständig: " + ", ".join(missing))
    print("SCHWIERIGKEITSSTUFEN: bereits vollständig integriert.")
    raise SystemExit(0)

lib_end = s.find('\n    )\n}', s.find("object ChordLibrary {"))
if lib_end < 0:
    raise SystemExit("FEHLER: ChordLibrary-Ende nicht gefunden.")
classifier = '''
    val difficultyStages = listOf("Anfänger", "Fortgeschrittene Anfänger", "Fortgeschritten", "Experte")
    private val beginnerOpenChords = setOf("C", "G", "D", "A", "E", "Am", "Em", "Dm")
    private val expertExtensions = setOf(
        "C6", "Am6", "Eaug", "Edim7", "Hmaj7", "Bbmaj7", "Amaj7", "Emaj7", "Dmaj7", "Cmaj7",
        "Hadd9", "Fadd9", "A9"
    )
    fun difficultyFor(shape: ChordShape): String {
        if (shape.name in beginnerOpenChords) return "Anfänger"
        if (shape.name in expertExtensions || shape.quality == "Vermindert" || shape.name.endsWith("aug")) return "Experte"
        val fretted = shape.frets.filter { it > 0 }
        val indexBarre = shape.fingers.count { it == 1 } >= 3
        val movablePosition = shape.baseFret > 1 || (fretted.isNotEmpty() && fretted.minOrNull()!! > 0 && indexBarre)
        if (shape.quality == "Power-Akkord" || movablePosition) return "Fortgeschritten"
        return "Fortgeschrittene Anfänger"
    }
'''
s = s[:lib_end + len("\n    )")] + classifier + s[lib_end + len("\n    )"):]

old = '            var category = prefs.getString("learn_chord_quiz_category", "Alle") ?: "Alle"'
new = '''            val validStages = listOf("Alle") + ChordLibrary.difficultyStages
            var category = (prefs.getString("learn_chord_quiz_category", "Alle") ?: "Alle")
                .takeIf { it in validStages } ?: "Alle"
            if (prefs.getString("learn_chord_quiz_category", "Alle") !in validStages) {
                prefs.edit().putString("learn_chord_quiz_category", "Alle").apply()
            }'''
if old not in s: raise SystemExit("Kategorie-Einstellung nicht gefunden")
s = s.replace(old, new, 1)

old = '''            val modeButton = a.button("Modus · " + (modeNames[mode] ?: modeNames["recognize"]))
            val categoryButton = a.button("Kategorie · $category")
            header.addView(modeButton, LinearLayout.LayoutParams(0, a.dp(44), 1f))
            header.addView(categoryButton, LinearLayout.LayoutParams(0, a.dp(44), 1f).apply { leftMargin = a.dp(6) })
            box.addView(header)'''
new = '''            val modeButton = a.button("Modus · " + (modeNames[mode] ?: modeNames["recognize"]))
            val categoryButton = a.button("Stufe · $category")
            header.addView(modeButton, LinearLayout.LayoutParams(0, a.dp(44), 1f))
            header.addView(categoryButton, LinearLayout.LayoutParams(0, a.dp(44), 1f).apply { leftMargin = a.dp(6) })
            box.addView(header)
            val stageHint = TextView(a).apply {
                textSize = 12f
                setTextColor(a.getColor(R.color.sw_muted))
                setPadding(a.dp(2), a.dp(5), a.dp(2), a.dp(4))
            }
            box.addView(stageHint, LinearLayout.LayoutParams(-1, -2))
            val stageDescriptions = mapOf(
                "Alle" to "Alle Griffbilder · gemischtes Training",
                "Anfänger" to "Offene Grundakkorde · sichere erste Wechsel",
                "Fortgeschrittene Anfänger" to "Offene Sus-, Sept- und Add9-Griffe",
                "Fortgeschritten" to "Barré-Griffe und Powerchords",
                "Experte" to "Erweiterte Voicings, Jazz- und Sonderakkorde"
            )
            fun updateStageHeader() {
                val count = ChordLibrary.all.filterNot { it.name == "Bb" }.distinctBy { it.name }
                    .count { category == "Alle" || ChordLibrary.difficultyFor(it) == category }
                categoryButton.text = if (category == "Alle") "Stufe · Alle" else "Stufe · $category"
                stageHint.text = (stageDescriptions[category] ?: "") + " · $count Akkorde"
            }
            updateStageHeader()'''
if old not in s: raise SystemExit("Quiz-Kopfzeile nicht gefunden")
s = s.replace(old, new, 1)

old = '                val byCategory = if (category == "Alle") all else all.filter { it.quality == category }'
new = '                val byCategory = if (category == "Alle") all else all.filter { ChordLibrary.difficultyFor(it) == category }'
if old not in s: raise SystemExit("Bisheriger Qualitätsfilter nicht gefunden")
s = s.replace(old, new, 1)

old = '''                val usable = when {
                    mode == "mistakes" && byMistakes.size >= 4 -> byMistakes
                    mode == "mistakes" -> all
                    byCategory.size >= 4 -> byCategory
                    else -> all
                }'''
new = '''                // Fehlertraining bleibt innerhalb der gewählten Stufe.
                val usable = if (mode == "mistakes" && byMistakes.size >= 4) byMistakes else byCategory'''
if old not in s: raise SystemExit("Fehlertraining-Pool nicht gefunden")
s = s.replace(old, new, 1)

old = '''            val categories = listOf("Alle") + ChordLibrary.all.groupBy { it.quality }
                .filterValues { shapes -> shapes.map { it.name }.distinct().size >= 4 }.keys.sorted()
            categoryButton.setOnClickListener {
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog).setTitle("Akkordfamilie")
                    .setSingleChoiceItems(categories.toTypedArray(), categories.indexOf(category).coerceAtLeast(0)) { dialog, which ->
                        category = categories[which]; prefs.edit().putString("learn_chord_quiz_category", category).apply()
                        categoryButton.text = "Kategorie · $category"
                        roundFinished = false; answered = 0; localCorrect = 0; localStreak = 0
                        newQuestion(); dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }'''
new = '''            val stageOptions = listOf("Alle") + ChordLibrary.difficultyStages
            val stageCounts = stageOptions.associateWith { stage ->
                ChordLibrary.all.filterNot { it.name == "Bb" }.distinctBy { it.name }
                    .count { stage == "Alle" || ChordLibrary.difficultyFor(it) == stage }
            }
            val categoryLabels = stageOptions.map { stage ->
                val count = stageCounts[stage] ?: 0
                if (stage == "Alle") "Alle Akkorde · $count" else "$stage · $count Akkorde"
            }
            categoryButton.setOnClickListener {
                androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog).setTitle("Schwierigkeitsstufe")
                    .setSingleChoiceItems(categoryLabels.toTypedArray(), stageOptions.indexOf(category).coerceAtLeast(0)) { dialog, which ->
                        category = stageOptions[which]
                        prefs.edit().putString("learn_chord_quiz_category", category).apply()
                        updateStageHeader()
                        roundFinished = false; answered = 0; localCorrect = 0; localStreak = 0
                        newQuestion(); dialog.dismiss()
                    }.setNegativeButton("Abbrechen", null).show()
            }'''
if old not in s: raise SystemExit("Alter Kategorien-Dialog nicht gefunden")
s = s.replace(old, new, 1)
s = s.replace('            categoryButton.text = "Kategorie · $category"', '            updateStageHeader()', 1)

required = ['val difficultyStages = listOf("Anfänger", "Fortgeschrittene Anfänger", "Fortgeschritten", "Experte")',
            'fun difficultyFor(shape: ChordShape): String', 'setTitle("Schwierigkeitsstufe")',
            'ChordLibrary.difficultyFor(it) == category', 'Fehlertraining bleibt innerhalb der gewählten Stufe']
missing = [x for x in required if x not in s]
if missing: raise SystemExit("FEHLER: Stufenintegration unvollständig: " + ", ".join(missing))

shapes = re.findall(r'ChordShape\("([^"]+)",\s*"([^"]+)",\s*intArrayOf\(([^)]*)\)(?:,\s*(\d+))?[^\n]*?fingers=intArrayOf\(([^)]*)\)', s[s.find("object ChordLibrary {"):s.find("\n}\n", s.find("object ChordLibrary {"))])
unique = {}
for name, quality, fret_text, base, finger_text in shapes:
    if name == "Bb": continue
    frets = [int(x.strip()) for x in fret_text.split(",")]
    fingers = [int(x.strip()) for x in finger_text.split(",")]
    if name in {"C","G","D","A","E","Am","Em","Dm"}: stage = "Anfänger"
    elif name in {"C6","Am6","Eaug","Edim7","Hmaj7","Bbmaj7","Amaj7","Emaj7","Dmaj7","Cmaj7","Hadd9","Fadd9","A9"} or quality == "Vermindert" or name.endswith("aug"): stage = "Experte"
    elif quality == "Power-Akkord" or int(base or 1) > 1 or (any(f > 0 for f in frets) and min(f for f in frets if f > 0) > 0 and fingers.count(1) >= 3): stage = "Fortgeschritten"
    else: stage = "Fortgeschrittene Anfänger"
    unique[name] = stage
counts = {stage: sum(v == stage for v in unique.values()) for stage in ["Anfänger","Fortgeschrittene Anfänger","Fortgeschritten","Experte"]}
if len(unique) < 90 or any(v < 4 for v in counts.values()):
    raise SystemExit(f"FEHLER: Unplausible Verteilung: {len(unique)} Akkorde, {counts}")
main.write_text(s, encoding="utf-8")
print(f"SCHWIERIGKEITSSTUFEN PASS: {len(unique)} Akkorde, {counts}")
