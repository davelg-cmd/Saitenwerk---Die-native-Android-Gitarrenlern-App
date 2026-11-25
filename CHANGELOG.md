## CI-Reparatur Premium-Songbook – 25.11.2026
- Beschädigte, mehrfach angehängte Fragmente aus `ci/premium_songbook_patch.py` entfernt; Python-RegEx-Import ergänzt.
- Original-PDF-Viewer: Seitenanzeige-Interpolation korrigiert.
- Diese Änderungen beheben den zuletzt diagnostizierten Python-Syntaxfehler; ein erfolgreicher Android-Build und ein PDF-Import auf einem Gerät sind damit noch nicht bestätigt.

## Persönliches Premium-Songbook – 23.11.2026
- Alte gemeinfreie/Legacy-Liederbuch-Datenquelle und veraltete HTML-Songbook-Implementierung aus dem App-Projekt entfernt.
- Vollständigen privaten PDF-Import für 452 Songs mit Prüfung der fortlaufenden Inhaltsverzeichnis-Einträge und Erfassung der jeweiligen vollständigen Songseitenbereiche vorbereitet.
- Original-PDF und extrahierter Katalog werden ausschließlich im nicht automatisch gesicherten privaten App-Speicher abgelegt; keine PDF- oder Songtextdatei wird in öffentliche App-Assets eingebettet.
- Songsterr-orientierte Songansicht mit Text-/Akkordaufbereitung, Suche über Titel/Künstler/Text/Akkorde, Favoriten, Setlisten, Transponierung, Kapodaster und Songplayer-Anbindung ergänzt.
- Layoutgetreue Original-PDF-Ansicht pro Song sowie Zugriff auf das vollständige 477-seitige Originaldokument ergänzt.
- GitHub-Buildworkflow auf private Songbook-Architektur umgestellt; alte Wiederherstellung aus dem Alpha-7-Liederbucharchiv wird nicht mehr ausgeführt.

## Liederbuch wiederhergestellt – 23.11.2026
- **Liederbuch wieder aktiviert:** Der vorhandene SongRepository-, SongsFragment- und SongDetailFragment-Code wird wieder über die aktive Bottom-Navigation und einen Startseiten-Einstieg erreichbar gemacht.
- **Songdaten wiederhergestellt:** Die zuvor entfernten Songbook-Assets werden aus dem archivierten Alpha-7-Quellstand in den aktuellen Build-Prozess übernommen.
- **Songreader wiederhergestellt:** Songblätter, Akkorddarstellung, Transponierung, Kapodaster, Favoriten, Setlist und der vorhandene Song-Player bleiben an den bestehenden Songbook-Code angebunden.
- **CI angepasst:** Die bisherige Prüfung auf die Entfernung des Liederbuchs wurde durch eine vollständige Wiederherstellungs- und Validierungsprüfung ersetzt.
- **Wichtig:** Der App-Quellstand im aktuellen Build-Backup wird nicht durch einen alten Gesamtstand ersetzt; die Wiederherstellung erfolgt gezielt und nur für die fehlenden Liederbuch-Einstiege und -Assets.

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
