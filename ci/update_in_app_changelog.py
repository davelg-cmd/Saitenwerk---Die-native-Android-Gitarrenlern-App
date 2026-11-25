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
            "25.11.2026 · Build 490" to "Update-Installation repariert: DownloadManager-Abschlussmeldungen werden auf Android 13+ über einen exportierten, auf die erwartete Download-ID und den tatsächlichen Download-Status geprüften Broadcast-Empfänger verarbeitet. Nach erfolgreichem APK-Download kann der Android-Installationsdialog automatisch geöffnet werden, ohne die Download-Benachrichtigung antippen zu müssen.",
            "25.11.2026 · Build 483" to "Verworfenes Songbook vollständig zurückgebaut: Navigation, Datenmodell, Repository, Listen-/Detailansichten, PDF-Importer, PDF-Viewer, PDFBox-Abhängigkeit und zugehörige Ressourcen aus dem App-Projekt entfernt. Song-Praxis, gemeinsamer Gitarrentrainer, Akkordbibliothek, Lernstudio, Lernfortschritt und Stimmgerät bleiben erhalten. Die CI prüft die Abwesenheit aller Songbook-Komponenten vor dem Build.",
            "20.11.2026 · Build 436" to "Gemeinsamer Gitarrentrainer: Akkordwechsel- und Schlagmuster-Training zu einem Trainer zusammengeführt. Beide Modi teilen Akkordauswahl, geordnete Akkordfolge, Taktart und Tempo; vorhandene Einstellungen werden übernommen. Akkordwechsel zeigt den aktuellen und nächsten Griff samt Griffbild, Schlagmuster nutzt die bestehende Wischsteuerung mit Tonwiedergabe und Timing-Auswertung. Separate ChordTrainingPanel-Implementierung und doppelte Traineroberfläche entfernt; Einstiege aus Song-Praxis und Akkordbibliothek auf den gemeinsamen Trainer umgestellt.",
            "19.11.2026 · Build 427" to "Gemeinsamer Gitarrentrainer: Akkordwechsel- und Schlagmuster-Modus in einer einzigen Trainingsoberfläche zusammengeführt. Akkordauswahl, geordnete Akkordfolge, Taktart und Tempo werden gemeinsam verwaltet; Modusumschaltung, ein Start-/Stopp-Steuerelement und ein gemeinsamer Trainingsablauf. Im Akkordwechsel-Modus werden Akkorddiagramm, Akkordfolge und Gitarrenwiedergabe pro Takt angezeigt; im Schlagmuster-Modus bleiben Wischgesten, Tonwiedergabe und Timing-Auswertung aktiv. Bestehende Akkordfolgen, Taktarten, Tempi und Trainingsfortschritte aus beiden bisherigen Trainern werden migriert und die Statistikwerte getrennt fortgeführt. Die separate Trainerklasse und doppelte Traineroberfläche in der Akkordbibliothek entfernt; Song-Praxis besitzt nur noch einen gemeinsamen Trainer-Einstieg.",
            "19.11.2026 · Build 426" to "Akkordwechsel-Training: Akkordauswahl-Dialog überarbeitet, damit Übernehmen auch bei langen Listen sichtbar bleibt. Schlagmuster-Trainer: Mehrfachauswahl von Gitarrenakkorden und Taktarten 3/4, 4/4 und 6/8; Akkordwechsel pro Takt. Bedienoberfläche vereinfacht: Muster-vorhören-Button, Takte-Button sowie Abschlag- und Aufschlag-Buttons entfernt. Schlag-Eingabe durch vertikale Wischgesten direkt auf den Schlagpfeilen ersetzt und mit Tonwiedergabe sowie Timing-Auswertung verbunden. Verwaiste Vorschau- und Taktanzahl-Zustände entfernt, erster Taktschlag korrigiert und Akkordreihenfolge dauerhaft geordnet gespeichert. Startbutton heißt jetzt Training starten. Redundante Pattern-Textzeile entfernt und Schlagpfeile vergrößert.",
            "18.11.2026 · Build 399" to "Vollständiger Lernfortschritt-Reset unter Einstellungen → Lernfortschritt. Übungszeiten, Tages- und Wochenwerte, XP, Level, Serien, Quizstatistiken, Lernpfad-Fortschritt und Trainings-Bestwerte werden gemeinsam zurückgesetzt. Persönliche App-Einstellungen und Trainingskonfigurationen bleiben erhalten.",
            "18.11.2026 · Build 394" to "Interaktiver Griffbrett-Notentrainer mit sechs Saiten und zwölf Bünden, zufälligen Notenaufgaben, Gitarrenton-Wiedergabe, direkter Richtig/Falsch-Rückmeldung und 10-Runden-Training. Bestserie und persönliche Bestleistung werden gespeichert.",
            "18.11.2026 · Build 392" to "Intelligenter Schlagmuster-Trainer mit acht Rhythmen in vier Schwierigkeitsstufen. Muster können vorgehört und anschließend selbst gespielt werden. Timing-Fenster, Rückmeldung und persönliche Bestwerte unterstützen das Training.",
            "18.11.2026 · Build 390" to "Persönliches Heute-üben-Dashboard im Lernstudio mit Schnellstart, Wochenübersicht und direktem Einstieg in die Trainingseinheiten.",
            "18.11.2026 · Build 387" to "Ausgangsbasis für die anschließenden Lernstudio-, Trainings- und Fortschrittsverbesserungen."
        )"""
s = s[:start] + changes + s[end:]
# Keep this merge build in the visible history on every later release without duplicating it in Build 427 itself.
current_build = int(os.environ.get("VERSION_CODE", "0")) - 1000
if current_build != 427:
    build_427 = '            "19.11.2026 · Build 427" to "Gemeinsamer Gitarrentrainer: Akkordwechsel- und Schlagmuster-Modus in einer einzigen Trainingsoberfläche zusammengeführt. Akkordauswahl, geordnete Akkordfolge, Taktart und Tempo werden gemeinsam verwaltet; Modusumschaltung, ein Start-/Stopp-Steuerelement und ein gemeinsamer Trainingsablauf. Im Akkordwechsel-Modus werden Akkorddiagramm, Akkordfolge und Gitarrenwiedergabe pro Takt angezeigt; im Schlagmuster-Modus bleiben Wischgesten, Tonwiedergabe und Timing-Auswertung aktiv. Bestehende Akkordfolgen, Taktarten, Tempi und Trainingsfortschritte aus beiden bisherigen Trainern werden migriert und die Statistikwerte getrennt fortgeführt. Die separate Trainerklasse und doppelte Traineroberfläche in der Akkordbibliothek entfernt; Song-Praxis besitzt nur noch einen gemeinsamen Trainer-Einstieg.",\n'
    anchor = '            "19.11.2026 · Build 426" to'
    if anchor not in changes:
        raise SystemExit("FEHLER: Build-426-Historieneintrag zum Ergänzen des Build-427-Verlaufs nicht gefunden.")
    changes = changes.replace(anchor, build_427 + anchor, 1)
main.write_text(s, encoding="utf-8")

required = [
    "Verworfenes Songbook vollständig zurückgebaut",
    "PDF-Importer",
    "PDF-Viewer",
    "Song-Praxis",
    "Gemeinsamer Gitarrentrainer",
    "Vollständiger Lernfortschritt-Reset",
    "Interaktiver Griffbrett-Notentrainer",
    "Intelligenter Schlagmuster-Trainer",
    "Timing-Fenster",
    "Heute-üben-Dashboard",
    "Akkordauswahl-Dialog überarbeitet",
    "Pattern-Textzeile entfernt",
    "Muster-vorhören-Button",
    "Takte-Button",
    "Abschlag- und Aufschlag-Buttons entfernt",
    "Training starten",
    "Wischgesten",
    "Akkordreihenfolge",
    "Vorschau- und Taktanzahl-Zustände entfernt",
    "Mehrfachauswahl von Gitarrenakkorden",
    "Taktarten 3/4, 4/4 und 6/8",
    "Akkordfolge",
    "Build 483",
    "Build 490",
]
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit("FEHLER: In-App-Changelog unvollständig: " + ", ".join(missing))
print("IN-APP-CHANGELOG: PASS – aktuelle Reparaturen und die letzten wichtigen Funktionen dokumentiert.")
