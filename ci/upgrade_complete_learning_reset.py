from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")

s = main.read_text(encoding="utf-8")
start = s.find('        section("Lernfortschritt"')
if start < 0:
    raise SystemExit("FEHLER: Bestehender Lernfortschritt-Abschnitt nicht gefunden.")
end = s.find('\n        section("Über Saitenwerk"', start)
if end < 0:
    raise SystemExit("FEHLER: Ende des Lernfortschritt-Abschnitts nicht gefunden.")

block = '''        section("Lernfortschritt","Setze sämtliche gespeicherten Lernzeiten, Punkte, XP, Serien, Quizwerte und Lernpfad-Fortschritte auf diesem Gerät zurück. Trainings-Einstellungen wie Akkordauswahl, Tempo und Taktart bleiben erhalten.","Alles zurücksetzen") {
            androidx.appcompat.app.AlertDialog.Builder(a)
                .setTitle("Gesamten Lernfortschritt zurücksetzen?")
                .setMessage("Dabei werden alle Lernstudio- und Lernpfad-Werte gelöscht: Übungsminuten, Tages- und Wochenzeiten, XP, Level, Serien, Quizpunkte, Bestwerte, geführte Sessions, Schlagmuster-, Rhythmus-, Griffbrett- und Akkordwechsel-Statistiken sowie abgeschlossene Lernstufen. Deine App-Einstellungen, Akkordauswahl, Tempi, Taktarten und Song-Arrangements bleiben erhalten.")
                .setNegativeButton("Abbrechen", null)
                .setPositiveButton("Alles zurücksetzen") { _, _ ->
                    a.getSharedPreferences("saitenwerk", 0).edit()
                        // Lernstudio: Zeit, Serien, XP, Quiz und Routine
                        .remove("learn_daily_day")
                        .remove("learn_daily_seconds")
                        .remove("learn_daily_minutes")
                        .remove("learn_last_session_day")
                        .remove("learn_week_key")
                        .remove("learn_week_seconds")
                        .remove("learn_sessions")
                        .remove("learn_streak")
                        .remove("learn_xp")
                        .remove("learn_quiz_correct")
                        .remove("learn_quiz_total")
                        .remove("learn_best_quiz_streak")
                        .remove("learn_routine_day")
                        .remove("learn_routine_done")
                        .remove("learn_guided_day")
                        .remove("learn_guided_done")
                        // Lernpfad / Kompetenzwerte
                        .remove("learning_path_done")
                        .remove("learn_skill_changes")
                        .remove("learn_skill_rhythm")
                        .remove("learn_skill_strum")
                        // Rhythmus- und Schlagmuster-Bestwerte
                        .remove("learn_strum_best_score")
                        .remove("learn_strum_best_rounds")
                        .remove("learn_strum_best_combo")
                        // Akkordwechsel-Training
                        .remove("chord_training_best_streak")
                        .remove("chord_training_sessions")
                        .remove("chord_training_mastered")
                        // Griffbrett-Notentrainer
                        .remove("learn_fretboard_best_streak")
                        .remove("learn_fretboard_best_score")
                        .apply()
                    Toast.makeText(a, "Gesamter Lernfortschritt wurde zurückgesetzt", Toast.LENGTH_SHORT).show()
                }
                .show()
        }
'''
s = s[:start] + block + s[end:]
main.write_text(s, encoding="utf-8")
print("VOLLSTÄNDIGER-LERNRESET: PASS")
print("Lernstudio, Lernpfad, Zeit, XP, Punkte, Serien, Bestwerte und Trainingsstatistiken werden gemeinsam zurückgesetzt.")
