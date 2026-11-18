#!/usr/bin/env python3
"""Remove the redundant stop control from Lernstudio > Song-Praxis."""
from pathlib import Path
import os

main = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

blocks = [
'''            val stopProgression = a.button("■ Wiedergabe stoppen")
            stopProgression.gravity = Gravity.CENTER
''',
'''            box.addView(stopProgression, LinearLayout.LayoutParams(-1, a.dp(42)).apply { topMargin = a.dp(5) })
''',
'''            stopProgression.setOnClickListener {
                GuitarAudioEngine.stopAll()
                playProgression.text = "▶ Akkordfolge anhören"
            }
''',
]
for block in blocks:
    if block not in s:
        raise SystemExit("FEHLER: Erwarteter Stoppbutton-Abschnitt nicht gefunden; Änderung abgebrochen.")

for block in blocks:
    s = s.replace(block, "", 1)

if 'a.button("■ Wiedergabe stoppen")' in s or "stopProgression.setOnClickListener" in s:
    raise SystemExit("FEHLER: Stoppbutton wurde nicht vollständig entfernt.")

main.write_text(s, encoding="utf-8")
print("Redundanter Wiedergabe-stoppen-Button aus Song-Praxis entfernt; Anhören-Funktion bleibt erhalten.")
