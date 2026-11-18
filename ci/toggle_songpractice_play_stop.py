#!/usr/bin/env python3
"""Make the Song-Praxis progression button a reliable play/stop toggle and prevent label clipping."""
from pathlib import Path
import os

main = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

old = """            val playProgression = a.button("▶ Akkordfolge anhören")
            box.addView(playProgression, LinearLayout.LayoutParams(-1, a.dp(46)).apply { topMargin = a.dp(6) })
            playProgression.setOnClickListener {
                val names = selected.text.toString().substringAfter(":").split("–").map { it.trim() }
                if (names.any { name -> ChordLibrary.all.none { it.name == name } }) {
                    Toast.makeText(a, "Für diese Folge fehlt ein Akkordgriff.", Toast.LENGTH_SHORT).show()
                } else {
                    playProgression.text = "♫ Akkordfolge läuft · 80 BPM"
                    GuitarAudioEngine.playProgression(a, names, 80) {
                        playProgression.text = "▶ Akkordfolge anhören"
                    }
                }
            }
"""
new = """            val playProgression = a.button("▶ Akkordfolge anhören").apply {
                gravity = Gravity.CENTER
                textAlignment = View.TEXT_ALIGNMENT_CENTER
                includeFontPadding = true
                minLines = 1
                maxLines = 1
                setPadding(a.dp(16), a.dp(14), a.dp(16), a.dp(14))
                minHeight = a.dp(60)
                minimumHeight = a.dp(60)
            }
            box.addView(playProgression, LinearLayout.LayoutParams(-1, a.dp(60)).apply { topMargin = a.dp(8) })
            var progressionPlaying = false
            playProgression.setOnClickListener {
                if (progressionPlaying) {
                    GuitarAudioEngine.stopAll()
                    progressionPlaying = false
                    playProgression.text = "▶ Akkordfolge anhören"
                } else {
                    val names = selected.text.toString().substringAfter(":").split("–").map { it.trim() }
                    if (names.any { name -> ChordLibrary.all.none { it.name == name } }) {
                        Toast.makeText(a, "Für diese Folge fehlt ein Akkordgriff.", Toast.LENGTH_SHORT).show()
                    } else {
                        progressionPlaying = true
                        playProgression.text = "■ Wiedergabe stoppen"
                        GuitarAudioEngine.playProgression(a, names, 80) {
                            progressionPlaying = false
                            playProgression.text = "▶ Akkordfolge anhören"
                        }
                    }
                }
            }
"""
if s.count(old) != 1:
    raise SystemExit(f"FEHLER: Erwarteter Song-Praxis-Button-Abschnitt nicht eindeutig gefunden (Treffer: {s.count(old)}).")
s = s.replace(old, new, 1)

old_reset = """                        GuitarAudioEngine.stopAll()
                        playProgression.text = "▶ Akkordfolge anhören"
                        prefs.edit().putString("learn_song_progression", progression).apply()
"""
new_reset = """                        GuitarAudioEngine.stopAll()
                        progressionPlaying = false
                        playProgression.text = "▶ Akkordfolge anhören"
                        prefs.edit().putString("learn_song_progression", progression).apply()
"""
if s.count(old_reset) != 1:
    raise SystemExit("FEHLER: Zurücksetzen beim Wechsel der Akkordfolge nicht eindeutig gefunden.")
s = s.replace(old_reset, new_reset, 1)

checks = [
    'var progressionPlaying = false',
    'if (progressionPlaying) {',
    'playProgression.text = "■ Wiedergabe stoppen"',
    'setPadding(a.dp(16), a.dp(14), a.dp(16), a.dp(14))',
    'LinearLayout.LayoutParams(-1, a.dp(60))',
    'progressionPlaying = false',
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("FEHLER: Umschaltfunktion/Clipping-Schutz unvollständig: " + ", ".join(missing))
main.write_text(s, encoding="utf-8")
print("SONG-PRAXIS: Anhören-Button schaltet zwischen Start und Stopp um; 60dp Höhe und großzügiger Text-Innenabstand.")
