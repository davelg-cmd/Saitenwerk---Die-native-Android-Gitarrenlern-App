from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

# Keep the chord picker actions visible by bounding the scrollable list height.
picker_start = s.find("    private fun openChordPicker() {")
picker_end = s.find("\n    private fun openMeterPicker()", picker_start)
if picker_start < 0 or picker_end < 0:
    raise SystemExit("FEHLER: Akkordauswahl-Dialog nicht eindeutig gefunden.")
picker = s[picker_start:picker_end]
if "val pickerHeightDp =" not in picker:
    old = """        val scroll = android.widget.ScrollView(host).apply {
            isFillViewport = true
            setPadding(host.dp(20), host.dp(4), host.dp(20), host.dp(4))
        }"""
    new = """        // Begrenzte Listenhöhe hält die Dialogaktionen dauerhaft sichtbar.
        val pickerHeightDp = (host.resources.displayMetrics.heightPixels /
            host.resources.displayMetrics.density * 0.48f).toInt().coerceIn(220, 380)
        val scroll = android.widget.ScrollView(host).apply {
            isFillViewport = true
            layoutParams = android.view.ViewGroup.LayoutParams(-1, host.dp(pickerHeightDp))
            setPadding(host.dp(20), host.dp(4), host.dp(20), host.dp(4))
        }"""
    if old not in picker:
        raise SystemExit("FEHLER: ScrollView der Akkordauswahl weicht unerwartet ab.")
    picker = picker.replace(old, new, 1)
    s = s[:picker_start] + picker + s[picker_end:]

# Remove the redundant textual pattern row; the larger beat arrows below the
# preview button remain the single, prominent representation of the pattern.
trainer_start = s.find("        fun showStrumming() {")
trainer_end = s.find("\n        fun showSongPractice() {", trainer_start)
if trainer_start < 0 or trainer_end < 0:
    raise SystemExit("FEHLER: Schlagmuster-Trainer nicht eindeutig gefunden.")
trainer = s[trainer_start:trainer_end]
trainer = trainer.replace("""            val patternHint = TextView(a).apply {
                text = "Pattern: " + selected.joinToString("  ")
                textSize = 16f
                gravity = Gravity.CENTER
                setTextColor(a.getColor(R.color.sw_text))
                setPadding(0, a.dp(9), 0, a.dp(9))
            }
""", "", 1)
trainer = trainer.replace("""            box.addView(patternHint)
""", "", 1)
trainer = trainer.replace("""            box.addView(beatRow, LinearLayout.LayoutParams(-1, a.dp(58)))""",
                          """            box.addView(beatRow, LinearLayout.LayoutParams(-1, a.dp(76)))""", 1)
trainer = trainer.replace("""                    }, LinearLayout.LayoutParams(0, a.dp(52), 1f))""",
                          """                    }, LinearLayout.LayoutParams(0, a.dp(68), 1f))""", 1)
trainer = trainer.replace("""                    v.textSize = if (isActive) 28f else 22f""",
                          """                    v.textSize = if (isActive) 38f else 30f""", 1)
trainer = trainer.replace("""                        patternHint.text = "Pattern: " + selected.joinToString("  ")
""", "", 1)
if "patternHint" in trainer:
    raise SystemExit("FEHLER: Redundanter patternHint ist noch im Trainer vorhanden.")
if 'box.addView(beatRow, LinearLayout.LayoutParams(-1, a.dp(76)))' not in trainer:
    raise SystemExit("FEHLER: Vergrößerte Schlagpfeile wurden nicht korrekt integriert.")
if 'v.textSize = if (isActive) 38f else 30f' not in trainer:
    raise SystemExit("FEHLER: Pfeilgrößen wurden nicht korrekt angepasst.")
s = s[:trainer_start] + trainer + s[trainer_end:]

# Validate the explicit apply action and its visibility safeguards.
required_picker = [
    '.setPositiveButton("Übernehmen", null)',
    'getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)',
    'pickerHeightDp',
    'sequence = selected',
    'putStringSet("chord_training_selected_chords", selected.toSet())',
]
missing = [x for x in required_picker if x not in s]
if missing:
    raise SystemExit("FEHLER: Akkordauswahl-Übernahme unvollständig: " + ", ".join(missing))

main.write_text(s, encoding="utf-8")
print("TRAININGS-AUSWAHL: Übernehmen-Button im begrenzten Dialogbereich abgesichert.")
print("SCHLAGMUSTER-TRAINER: Doppelte Pattern-Textzeile entfernt; Pfeile unter Vorhör-Button vergrößert.")
