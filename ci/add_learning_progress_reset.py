from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")

s = main.read_text(encoding="utf-8")
marker = '        section("Über Saitenwerk",'
if marker not in s:
    raise SystemExit("FEHLER: Über-Saitenwerk-Abschnitt nicht gefunden.")

if 'section("Lernfortschritt"' in s:
    print("LERNFORTSCHRITT-RESET: bereits vorhanden; keine Änderung.")
    raise SystemExit(0)

block = '''        section("Lernfortschritt","Setze deine gespeicherten Lernstände auf diesem Gerät zurück. Deine App-Einstellungen, gespeicherten Akkorde und Song-Arrangements bleiben erhalten.","Lernfortschritt zurücksetzen") {
            androidx.appcompat.app.AlertDialog.Builder(a)
                .setTitle("Lernfortschritt zurücksetzen?")
                .setMessage("Quiz-Ergebnisse, Übungsstatistiken, Tagesroutine und abgeschlossene Lernstufen werden gelöscht. Deine persönlichen Einstellungen, gespeicherten Akkorde und Song-Arrangements bleiben erhalten.")
                .setNegativeButton("Abbrechen", null)
                .setPositiveButton("Zurücksetzen") { _, _ ->
                    a.getSharedPreferences("saitenwerk", 0).edit()
                        .remove("learn_quiz_correct")
                        .remove("learn_quiz_total")
                        .remove("learn_routine_day")
                        .remove("learn_routine_done")
                        .remove("chord_training_mastered")
                        .remove("chord_training_sessions")
                        .remove("learning_path_done")
                        .apply()
                    Toast.makeText(a, "Lernfortschritt wurde zurückgesetzt", Toast.LENGTH_SHORT).show()
                }
                .show()
        }
'''
s = s.replace(marker, block + marker, 1)
main.write_text(s, encoding="utf-8")
print("LERNFORTSCHRITT-RESET PASS: Einstellungen enthalten einen bestätigungspflichtigen Reset.")
print("LERNFORTSCHRITT-RESET PASS: Nur Lernstände werden entfernt; Einstellungen, Favoriten und Song-Arrangements bleiben erhalten.")
