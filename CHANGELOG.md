## Akkord-Blitztrainer Premium – 25.11.2026
- **Vier Trainingsmodi:** Griffbild erkennen, Griff zuordnen (Name → Griffbild), 60-Sekunden-Blitzrunde und gezieltes Fehlertraining.
- **Adaptive Wiederholung:** Individuelle Trefferquoten je Akkord, gewichtete Fragenauswahl zugunsten unsicherer Griffe, dauerhaft gespeicherte Fehlerliste und automatische Entlastung nach drei sicheren Antworten in Folge.
- **Leistungsfeedback:** Reaktionszeit, Trefferquote, laufende Serie, persönliche Bestserie und Rundenfortschritt.
- **Zentrale Akkorddatenbank erweitert:** Die vorhandene `ChordLibrary` wächst von 67 auf 94 eindeutige Griffbilder. Ergänzt wurden chromatische Dur- und Moll-Barrégriffe, weitere Septakkorde, Add9-, Sus-, Power-, übermäßige und verminderte Akkorde. Jede Ergänzung wird auf sechs Saitenwerte, Bundpositionen und Fingerzuordnung geprüft.
- **Fehlertraining und Lernfortschritt:** Unsichere Akkorde werden dauerhaft vorgemerkt und bevorzugt wiederholt. Der vollständige Lernfortschritt-Reset löscht auch die neuen Einzelakkord-Statistiken und Fehlerlisten; Modus- und Kategorieeinstellungen bleiben erhalten.
- **Technik:** Die Akkordbibliothek bleibt die einzige Datenquelle; keine zweite Datenbank und keine Änderungen am gemeinsamen Akkordwechsel-/Schlagmustertrainer.

## Update-Installation – 25.11.2026
- **Automatisches Öffnen des Installationsdialogs repariert:** Der DownloadManager-Abschluss-Broadcast wird auf Android 13+ jetzt über `Context.RECEIVER_EXPORTED` empfangen. Der Empfänger prüft weiterhin die gespeicherte Download-ID und den tatsächlichen DownloadManager-Status, bevor die APK-Validierung und der Android-Installer gestartet werden. Ziel: Installation direkt nach Downloadabschluss, ohne Antippen der Download-Benachrichtigung.

## Changelog-Korrektur – 25.11.2026
- **In-App-Changelog korrigiert:** Historische Einträge verwenden wieder ihre ursprünglichen Build-Nummern statt die Nummer des jeweils aktuellen Builds. Der gemeinsame Gitarrentrainer ist Build 427, die nachfolgende Überarbeitung vom 20.11. ist Build 436; ältere Einträge behalten 426, 399, 394, 392, 390 und 387.

## Vollständiger Songbook-Rückbau – 25.11.2026
- Rückbau des verworfenen Songbook-Experiments in der Build-Pipeline umgesetzt: Der Workflow verwendet für diesen einmaligen Rückbau den geprüften Ausgangsstand Build 436 statt des Songbook-haltigen Build 479.
- Die CI entfernt Songbook-Navigation, Song-Datenmodell, Repository, Listen- und Detailansichten, PDF-Importer/-Viewer, PDFBox-Abhängigkeit sowie die zugehörigen Ressourcen.
- Die Entfernung wird vor dem Android-Build automatisiert auf verbliebene Klassen, Verweise, Abhängigkeiten und Ressourcen geprüft.
- Song-Praxis, gemeinsamer Gitarrentrainer, Akkordbibliothek, Lernstudio, Lernfortschritt, Stimmgerät und die übrigen bestehenden Trainingsfunktionen bleiben erhalten.
- Reparatur: Das CI-Entfernungsskript bewahrt die Felder der MainActivity (Update-Verwaltung, Navigation und Mikrofonberechtigung) zuverlässig und entfernt nur die Songbook-Einstiegsmethode sowie die zugehörigen Songbook-Klassen.
- Build #483: Android-Kotlin-Kompilierung und vollständiger GitHub-Actions-Workflow erfolgreich; bereinigter Quellstand und APK-Artefakt wurden bereitgestellt, das Beta-Release `beta-latest` aktualisiert.
- Ein Test auf einem realen Android-Gerät wurde nicht durchgeführt.

# Saitenwerk – Changelog

Alle wesentlichen Änderungen, Erweiterungen, Reparaturen und Problembehebungen werden ab sofort hier dokumentiert. Neue Änderungen werden dem Changelog immer zusammen mit der jeweiligen Entwicklung eingetragen.

## Repository-Aufräumung – 23.11.2026
- **Repository bereinigt:** Nicht vom aktuellen GitHub-Actions-Build benötigte historische Alpha-7-Backups und das ursprüngliche Alpha-7-ZIP wurden aus dem aktiven Repository-Pfad nach `archiv/` verschoben.
- **Unverändert:** Der aktuell vom Build-Workflow verwendete Bereich `build-backups/beta` bleibt vollständig erhalten.
- **Neu:** `.gitignore` ergänzt für Gradle-/Android-Buildausgaben, APK/AAB-Dateien, Backup-Archive und lokale Konfigurations-/Schlüsseldateien.
- **Sicherheitsprüfung:** Im Repository wurden keine versionierten Keystore-, JKS-, P12-, PEM-, Secret- oder lokalen Konfigurationsdateien gefunden.
- **Funktionalität:** Keine App-Quellcodes, CI-Skripte oder Workflow-Logik wurden verändert.

## Build 399 – Lernfortschritt vollständig zurücksetzen
- **Neu:** In **Einstellungen → Lernfortschritt** gibt es jetzt **„Alles zurücksetzen“**.
- **Neu:** Sicherheitsabfrage vor dem Zurücksetzen des gesamten Lernfortschritts.
- **Zurückgesetzt werden:** tägliche und wöchentliche Übungszeit, Trainingstage/Streak, XP und Level, Quiz-Statistiken, Quiz-Bestserie, Tagesroutine, geführte 10-Minuten-Einheit, Lernpfad-Fortschritt und die zugehörigen Lernwerte.
- **Ebenfalls zurückgesetzt:** Bestwerte und Sitzungs-/Rundenwerte der Strumming- und Akkordwechsel-Übungen sowie der Bestwert des Griffbrett-Notentrainers.
- **Wichtig:** Persönliche bzw. App-Konfigurationen wie gespeicherte Akkordauswahl, Tempo, Takt, Instrument, Stimmung, Song-Arrangements und sonstige Einstellungen bleiben erhalten.
- **Reparatur:** Die bisherige, unvollständige Lernfortschritt-Zurücksetzung wurde durch eine vollständige Zurücksetzung der Lernmetriken ersetzt.
- **Reparatur:** Veraltete CI-Prüfungen, die noch die frühere Bezeichnung des Zurücksetzen-Buttons erwarteten, wurden an die neue Funktion angepasst.
- **Build-Qualität:** Der vollständige GitHub-Actions-Build einschließlich APK-Erstellung und Artefaktbereitstellung wurde erfolgreich geprüft.

## Build 394 – Griffbrett-Notentrainer
- **Neu:** Interaktiver Griffbrett-Notentrainer mit 6 Saiten und 12 Bünden.
- **Neu:** Standardstimmung und zufällige natürliche Zielnoten.
- **Neu:** Antippen eines Bundes spielt den zugehörigen Gitarrenton.
- **Neu:** Rückmeldung bei richtigen und falschen Antworten.
- **Neu:** 10-Runden-Training mit Bestserie und persönlicher Bestleistung.
- **Neu:** Schnellstart **„🎸 Griffbrett entdecken“**.
- **Integration:** Nutzung der Gitarren-Audio-Engine für die Tonwiedergabe.

## Build 390 – Persönlicher Übungsbereich
- **Neu:** Persönlicher Bereich **„Heute üben“** im Lernstudio.
- **Neu/Erweitert:** Übungsübersicht und darauf aufbauende Lernstudio-Funktionen.
- **Erweiterung:** Geführte 10-Minuten-Einheit, Tagesroutine, Wochenziel und weitere Lernfortschrittsfunktionen.

## Build 387 – Referenzstand
- Erfolgreicher Build und damaliger Ausgangspunkt für die weitere Entwicklung.
- Dieser Stand wurde anschließend durch die erfolgreichen Builds 390, 394 und 399 weiterentwickelt.

---

## Dokumentationsregel
Bei jeder weiteren Entwicklung an Saitenwerk werden **neue Funktionen, Änderungen, Verbesserungen, Reparaturen und behobene Fehler** im Changelog dokumentiert. Das gilt auch für kleinere UI-, Audio-, Funktions- und Build-/CI-Korrekturen.
