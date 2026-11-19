from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")

s = main.read_text(encoding="utf-8")
start = s.find("        val changes = listOf(")
end = s.find("\n        changes.forEach", start)
if start < 0 or end < 0:
    raise SystemExit("FEHLER: In-App-Changelog-Liste nicht gefunden.")

changes = """        val changes = listOf(
            "19.11.2026 · Build $buildNumber" to "Akkordwechsel-Training: Akkordauswahl-Dialog überarbeitet, damit Übernehmen auch bei langen Listen sichtbar bleibt. Schlagmuster-Trainer: Mehrfachauswahl von Gitarrenakkorden, Taktarten 3/4, 4/4 und 6/8 sowie Auswahl von 1 bis 8 Takten. Die Vorschau spielt das gewählte Schlagmuster mit der Akkordfolge und wechselt den Akkord taktweise. Redundante Pattern-Textzeile entfernt und Schlagpfeile vergrößert.",
            "18.11.2026 · Build 399" to "Vollständiger Lernfortschritt-Reset unter Einstellungen → Lernfortschritt. Übungszeiten, Tages- und Wochenwerte, XP, Level, Serien, Quizstatistiken, Lernpfad-Fortschritt und Trainings-Bestwerte werden gemeinsam zurückgesetzt. Persönliche App-Einstellungen und Trainingskonfigurationen bleiben erhalten.",
            "18.11.2026 · Build 394" to "Interaktiver Griffbrett-Notentrainer mit sechs Saiten und zwölf Bünden, zufälligen Notenaufgaben, Gitarrenton-Wiedergabe, direkter Richtig/Falsch-Rückmeldung und 10-Runden-Training. Bestserie und persönliche Bestleistung werden gespeichert.",
            "18.11.2026 · Build 392" to "Intelligenter Schlagmuster-Trainer mit acht Rhythmen in vier Schwierigkeitsstufen. Muster können vorgehört und anschließend selbst gespielt werden. Timing-Fenster, Rückmeldung und persönliche Bestwerte unterstützen das Training.",
            "18.11.2026 · Build 390" to "Persönliches Heute-üben-Dashboard im Lernstudio mit Schnellstart, Wochenübersicht und direktem Einstieg in die Trainingseinheiten.",
            "18.11.2026 · Build 387" to "Ausgangsbasis für die anschließenden Lernstudio-, Trainings- und Fortschrittsverbesserungen."
        )"""
s = s[:start] + changes + s[end:]
main.write_text(s, encoding="utf-8")

required = [
    "Vollständiger Lernfortschritt-Reset",
    "Interaktiver Griffbrett-Notentrainer",
    "Intelligenter Schlagmuster-Trainer",
    "Timing-Fenster",
    "Heute-üben-Dashboard",
    "Akkordauswahl-Dialog überarbeitet",
    "Pattern-Textzeile entfernt",
    "Mehrfachauswahl von Gitarrenakkorden",
    "Taktarten 3/4, 4/4 und 6/8",
    "Akkordfolge",
    "Build $buildNumber",
]
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit("FEHLER: In-App-Changelog unvollständig: " + ", ".join(missing))
print("IN-APP-CHANGELOG: PASS – aktuelle Reparaturen und die letzten wichtigen Funktionen dokumentiert.")
