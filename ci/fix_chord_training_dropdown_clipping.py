#!/usr/bin/env python3
"""Prevent the chord-training selector outlines from being clipped by their row."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

old_controls = """        val controls = LinearLayout(host).apply { orientation = HORIZONTAL }
        chooseChords.setOnClickListener { openChordPicker() }
        randomize.setOnClickListener { shuffleSequence() }
        controls.addView(chooseChords, LayoutParams(0, host.dp(44), 1f))
        controls.addView(randomize, LayoutParams(0, host.dp(44), 1f).apply {
            leftMargin = host.dp(6)
        })
        addView(controls, LayoutParams(-1, host.dp(44)).apply {
            bottomMargin = host.dp(8)
        })"""
new_controls = """        // Die Auswahlflächen brauchen mehr Höhe als die frühere 44-dp-Zeile:
        // Das Premium-Button-Design zeichnet einen 52-dp-Rahmen samt Rundungen.
        val controls = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            clipChildren = false
            clipToPadding = false
            setPadding(0, host.dp(3), 0, host.dp(3))
        }
        chooseChords.setOnClickListener { openChordPicker() }
        randomize.setOnClickListener { shuffleSequence() }
        controls.addView(chooseChords, LayoutParams(0, host.dp(56), 1f))
        controls.addView(randomize, LayoutParams(0, host.dp(56), 1f).apply {
            leftMargin = host.dp(8)
        })
        addView(controls, LayoutParams(-1, host.dp(62)).apply {
            bottomMargin = host.dp(10)
        })"""

if old_controls in s:
    s = s.replace(old_controls, new_controls, 1)
elif "clipToPadding = false" in s and "controls.addView(chooseChords, LayoutParams(0, host.dp(56), 1f))" in s:
    print("AKKORDWECHSEL-DROPDOWNS: Containerhöhe bereits korrigiert.")
else:
    raise SystemExit("FEHLER: Akkordauswahl-/Reihenfolge-Zeile nicht eindeutig gefunden; keine Änderung vorgenommen.")

# Zusätzliche Absicherung: auch die beiden Auswahlflächen selbst dürfen nicht
# durch einen übergeordneten Layout-Container an der Unterkante beschnitten werden.
anchor = """        controls.addView(chooseChords, LayoutParams(0, host.dp(56), 1f))"""
if anchor in s:
    s = s.replace(anchor, """        chooseChords.clipToOutline = false
        randomize.clipToOutline = false
        controls.addView(chooseChords, LayoutParams(0, host.dp(56), 1f))""", 1)

main.write_text(s, encoding="utf-8")
print("AKKORDWECHSEL-DROPDOWNS: Rahmen vollständig sichtbar, 56-dp-Steuerelemente in 62-dp-Container.")
