import re
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
            "27.11.2026 · Build 540" to "PDF-Parser stabilisiert: Zeilenumbrüche und Textnormalisierung werden in der Kotlin-Integration korrekt verarbeitet, damit PDF-Inhalte nicht durch fehlerhafte Escape-Sequenzen beschädigt werden.",
            "27.11.2026 · Build 543" to "PDF-Songbook erweitert: ein vorhandenes PDF-Inhaltsverzeichnis kann als Songindex ausgewertet werden. Zusätzlich wurden Kontraste und Bedienelemente im Dark-Theme vereinheitlicht.",
            "27.11.2026 · Build 545" to "Songbook auf persönliche Bibliotheken umgestellt: jeder Nutzer startet mit einem eigenen leeren Songbestand und kann eigene PDFs importieren, statt ungefragt einen gemeinsamen Beispielbestand zu erhalten.",
            "27.11.2026 · Build 551" to "Songbook-Datenmodell stabilisiert: Songs werden mit expliziten benannten Feldern gespeichert, damit Künstler, Liedtext, Akkorde und YouTube-Metadaten korrekt zugeordnet bleiben.",
            "27.11.2026 · Build 559" to "Song-Praxis erweitert: synchronisierter Player mit Start/Stopp, Zeitmarken für Liedtext und Akkorde sowie zugehöriger Songbook-Wiedergabe.",
            "27.11.2026 · Build 563" to "Songbook-Listenlayout korrigiert: Scrollbereich und Listencontainer verwenden passende Layoutparameter, damit die Songliste zuverlässig angezeigt wird.",
            "27.11.2026 · Build 565" to "PDF-Inhaltsverzeichnis robuster erkannt: unterschiedliche Punktlinien, Seitenversätze und Formatierungen werden toleranter ausgewertet.",
            "27.11.2026 · Build 572" to "PDF/OCR-Erkennung verbessert: fehlerhafte oder unvollständige Textauszüge werden zuverlässiger erkannt und bei Bedarf durch Texterkennung der gerenderten PDF-Seite ersetzt.",
            "25.11.2026 · Build 515" to "Premium-Akkordbibliothek: neuer Akkord-Atlas mit Suche, Favoriten, Qualitätsfiltern und zweispaltiger Übersicht. Detailansicht mit großem Griffbild, Saiten-/Fingerlegende und authentischer Gitarren-Hörprobe. Die zentrale ChordLibrary und alle vorhandenen Trainer bleiben erhalten.",
            "25.11.2026 · Build 520" to "Songbook erweitert: YouTube-Verbindung pro Nutzer über den offiziellen Google-Authorization-Flow. Minimale Leseberechtigung, sichere Token-Verarbeitung, Kanalprüfung und Möglichkeit zum Trennen der lokalen Verbindung.",
            "25.11.2026 · Build 525" to "Songbook-Absturz beim Öffnen behoben: Karten werden nur noch einmal zur Ansicht hinzugefügt. Statistik-, Songkarten- und Detailansichten verwenden dieselbe sichere Karten-Erzeugung.",
            "27.11.2026 · Build 581" to "PDF-Songbookimport neu aufgebaut: PDF-Seiten werden layoutbasiert ausgewertet, gescannte Seiten per OCR erkannt und Akkordzeilen anhand ihrer Position den passenden Liedtextzeilen zugeordnet. Importierte Songs werden lokal gespeichert.",
            "27.11.2026 · Build 582" to "PDF-Import-Diagnose erweitert: bei einem Importfehler werden Fehlertyp, Ursache und relevante Aufrufstellen ausgegeben, damit Abstürze gezielt behoben werden können.",
            "27.11.2026 · Build 583" to "PDF-Import repariert: PDFBox-Android initialisiert jetzt vor der ersten Textanalyse seine Android-Ressourcen. Dadurch wird der Absturz beim Laden des PDF-Text-Engines verhindert.",
            "27.11.2026 · Build 584" to "PDF-Erkennung verbessert: Titelkandidaten werden anhand von Schriftgröße, Schriftstil, Abständen und nachfolgendem Liedtext bewertet. Inhaltsverzeichnisse, Seitenköpfe und doppelte Titel werden stärker herausgefiltert.",
            "27.11.2026 · Build 585" to "PDF-Import-Build repariert: Die CI-Bereinigung entfernt den generierten Songbook-Importer vor dessen erneuter Integration, statt ihn versehentlich vor dem Kompilieren zu löschen.",
            "27.11.2026 · Build 586" to "PDF-Titelerkennung weiter präzisiert: normale Liedtextzeilen werden strenger von echten Liedüberschriften unterschieden, um zu viele erkannte Songs zu vermeiden.",
            "27.11.2026 · Build 587" to "PDF-Songgrenzen weiter verbessert: Großschreibung allein zählt nicht mehr als Titelmerkmal. Erforderlich sind stärkere Layout-Abstände und typografische Abhebung, damit Verszeilen nicht als neue Songs gezählt werden.",
            "25.11.2026 · Build 503" to "Akkord-Blitztrainer Hör-Quiz: Akkorde ausschließlich anhand authentischer Gitarrenklänge erkennen. Wiederholbare Wiedergabe, vier Antwortmöglichkeiten und dieselben vier Schwierigkeitsstufen. Eigene Hör-Trefferquoten, Fehlerliste, Serien und Reaktionszeiten bleiben von der visuellen Akkorderkennung getrennt; stufengebundenes Hör-Fehlertraining. Der vollständige Lernfortschritt-Reset löscht auch sämtliche Hör- und Einzelakkord-Statistiken.",
            "25.11.2026 · Build 498" to "Akkord-Blitztrainer: vier technikbasierte Schwierigkeitsstufen (Anfänger, Fortgeschrittene Anfänger, Fortgeschritten, Experte). 93 eindeutige Griffbilder werden nach Grifftechnik einsortiert; Beschreibung und Akkordanzahl werden angezeigt. Adaptive Wiederholung, Fehlerliste und Einzelakkord-Statistiken bleiben erhalten; Fehlertraining bleibt innerhalb der gewählten Stufe.",\n            "25.11.2026 · Build 495" to "Akkordgriff-Korrektur: C#7 und D#7 um die fehlende Quinte ergänzt. Das C6-Griffbild wurde als gültiger Shell-Akkord mit Grundton, Terz und Sexte geprüft; die Quinte darf hier bewusst entfallen. Die CI prüft Tonklassen sowie Sechs-Saiten- und Fingerpositionen. Der Premium-Blitztrainer und seine adaptive Datenbank bleiben erhalten.",
            "25.11.2026 · Build 491" to "Akkord-Blitztrainer Premium: vier Modi (Griffbild erkennen, Griff zuordnen, 60-Sekunden-Blitzrunde und Fehlertraining), adaptive Wiederholung nach individueller Trefferquote, dauerhaft gespeicherte Fehlerliste, Reaktionszeit und Serien. Die zentrale ChordLibrary wurde von 67 auf 94 eindeutige Griffbilder erweitert; neue Dur-, Moll-, Sept-, Add-, Sus-, Power-, übermäßige und verminderte Akkorde mit geprüften Sechs-Saiten- und Fingerpositionen. Der vollständige Lernfortschritt-Reset löscht auch die neuen Einzelakkord-Statistiken, bewahrt aber Modus- und Kategorieeinstellungen.",
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
current_build_for_entry = int(os.environ.get("VERSION_CODE", "0")) - 1000
if current_build_for_entry > 503:
    from datetime import datetime
    build_date = datetime.now().strftime("%d.%m.%Y")
    description = (
        "PDF-Songbookimport mit sichtbarem Fortschrittsfenster: Seitenanalyse mit laufender Anzeige „Seite X von Y“, anschließende Auswertung der Liedanfänge und automatisches Schließen des Statusfensters bei Erfolg oder Fehler. Das Changelog wurde um die seit Build 503 hinzugekommenen Funktionen und Reparaturen ergänzt und ist jetzt in einem eigenen Scrollbereich vollständig lesbar."
        if current_build_for_entry >= 590 else
        "PDF-Songbookimport: Seiten werden layoutbasiert analysiert; gescannte Seiten werden per OCR erkannt, Akkordpositionen den passenden Textzeilen zugeordnet und die Titelerkennung gegen falsche Songgrenzen abgesichert."
        if current_build_for_entry >= 581 else
        "Premium-Akkordbibliothek: Akkord-Atlas mit Suche, Favoriten, Qualitätsfiltern, zweispaltiger Übersicht, großem Griffbild und authentischer Gitarren-Hörprobe. Die zentrale ChordLibrary und alle vorhandenen Trainer bleiben erhalten."
        if current_build_for_entry >= 515 else
        "Akkord-Blitztrainer Hör-Quiz: Akkorde ausschließlich anhand authentischer Gitarrenklänge erkennen. Wiederholbare Wiedergabe, vier Antwortmöglichkeiten, vier Schwierigkeitsstufen, getrennte Hörstatistiken und stufengebundenes Hör-Fehlertraining."
    )
    entry = f'            "{build_date} · Build {current_build_for_entry}" to "{description}",\n'
    changes = changes.replace("val changes = listOf(\n", "val changes = listOf(\n" + entry, 1)
s = s[:start] + changes + s[end:]
# Keep this merge build in the visible history on every later release without duplicating it in Build 427 itself.
current_build = int(os.environ.get("VERSION_CODE", "0")) - 1000
if current_build != 427:
    build_427 = '            "19.11.2026 · Build 427" to "Gemeinsamer Gitarrentrainer: Akkordwechsel- und Schlagmuster-Modus in einer einzigen Trainingsoberfläche zusammengeführt. Akkordauswahl, geordnete Akkordfolge, Taktart und Tempo werden gemeinsam verwaltet; Modusumschaltung, ein Start-/Stopp-Steuerelement und ein gemeinsamer Trainingsablauf. Im Akkordwechsel-Modus werden Akkorddiagramm, Akkordfolge und Gitarrenwiedergabe pro Takt angezeigt; im Schlagmuster-Modus bleiben Wischgesten, Tonwiedergabe und Timing-Auswertung aktiv. Bestehende Akkordfolgen, Taktarten, Tempi und Trainingsfortschritte aus beiden bisherigen Trainern werden migriert und die Statistikwerte getrennt fortgeführt. Die separate Trainerklasse und doppelte Traineroberfläche in der Akkordbibliothek entfernt; Song-Praxis besitzt nur noch einen gemeinsamen Trainer-Einstieg.",\n'
    anchor = '            "19.11.2026 · Build 426" to'
    if anchor not in changes:
        raise SystemExit("FEHLER: Build-426-Historieneintrag zum Ergänzen des Build-427-Verlaufs nicht gefunden.")
    changes = changes.replace(anchor, build_427 + anchor, 1)

# The changelog is part of the scrollable About page, not an AlertDialog.
# appInfoBox already belongs to the page's vertical content container.
if "val changelogScroll = ScrollView(" not in s:
    anchor = '        page.addView(appInfoCard'
    pos = s.find(anchor)
    if pos < 0:
        raise SystemExit("FEHLER: App-Info-Karte der Über-Seite nicht gefunden.")
    # Wrap the complete About page content in a ScrollView at its existing root.
    # The page is the LinearLayout populated by the About section.
    page_decl = re.search(r"val\s+page\s*=\s*LinearLayout\(a\)", s)
    if not page_decl:
        raise SystemExit("FEHLER: Wurzel-Layout der Über-Seite nicht gefunden.")
    page_name = "page"
    # Replace the root content's insertion into its parent with a ScrollView wrapper.
    # Locate the exact final attachment of this page after all About cards are added.
    attach = list(re.finditer(r"\broot\.addView\(page(?:,|\))", s))
    if not attach:
        raise SystemExit("FEHLER: Einbindung der Über-Seite in das Hauptlayout nicht gefunden.")
    m = attach[-1]
    wrapper = (
        "        val aboutScroll = ScrollView(a).apply {\n"
        "            isFillViewport = true\n"
        "            isVerticalScrollBarEnabled = true\n"
        "            overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS\n"
        "        }\n"
        "        aboutScroll.addView(page, ScrollView.LayoutParams(-1, -2))\n"
    )
    s = s[:m.start()] + wrapper + s[m.start():]
    s = s[m.start():] + s[m.start():] if False else s
    # Change only the located attachment to use the wrapper.
    tail = s[m.start()+len(wrapper):]
    tail = re.sub(r"\broot\.addView\(page", "root.addView(aboutScroll", tail, count=1)
    if "root.addView(aboutScroll" not in tail:
        raise SystemExit("FEHLER: ScrollView konnte nicht an die Über-Seite angeschlossen werden.")
    s = s[:m.start()+len(wrapper)] + tail

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
    "Build 491",
    "Build 503",
    "Build 498",
    "Hör-Quiz",
    "Hör-Fehlertraining",
    "authentischer Gitarrenklänge",
    "Build 495",
    "Akkordgriff-Korrektur",
    "C#7",
    "D#7",
    "C6",
    "Akkord-Blitztrainer Premium",
    "60-Sekunden-Blitzrunde",
    "94 eindeutige Griffbilder",
    "adaptive Wiederholung",
]
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit("FEHLER: In-App-Changelog unvollständig: " + ", ".join(missing))
print("IN-APP-CHANGELOG: PASS – aktuelle Reparaturen und die letzten wichtigen Funktionen dokumentiert.")
