# 🎸 Saitenwerk – Die native Android-Gitarrenlern-App

Saitenwerk ist eine moderne, vollständig native Android-App zum **Lernen, Üben und Spielen von Gitarre**. Die App verbindet die wichtigsten Werkzeuge für den Gitarrenalltag in einer gemeinsamen Lernumgebung – vom ersten Akkord bis zur gezielten Weiterentwicklung fortgeschrittener Spieltechniken.

## ✨ Was ist Saitenwerk?

Saitenwerk verfolgt das Ziel, das Gitarrenlernen nicht in viele einzelne Apps und Werkzeuge aufzuteilen, sondern alles Wesentliche an einem Ort zusammenzuführen.

Im Mittelpunkt stehen:

- 🎸 **Gitarrenstimmgerät** mit alternativen Stimmungen
- 🎵 **Akkordbibliothek** mit Griffbildern und praktischen Lernmöglichkeiten
- 🎼 **Songpraxis und Akkordfolgen** zum praktischen Üben
- 🧠 **Lernstudio** für strukturiertes und individuelles Training
- 🖐️ **Interaktive Griffbrett- und Notenübungen**
- 🥁 **Intelligentes Rhythmus- und Schlagmustertraining**
- 🔄 **Akkord- und Schlagwechseltraining** in einer gemeinsamen Trainingsumgebung
- 📈 **Persönlicher Lernfortschritt** und Lernpfad
- 🔊 **Realistische Gitarrenklänge** für ein möglichst musikalisches Übungserlebnis
- 🌙 **Offline-Nutzung**, soweit die jeweilige Funktion keine Online-Daten benötigt

Die einzelnen Bereiche sind dabei nicht als voneinander isolierte Werkzeuge gedacht. Einstellungen, Lernfortschritt und Trainingsfunktionen sollen sinnvoll ineinandergreifen und ein zusammenhängendes Lernerlebnis schaffen.

## 🎯 Ziel

Saitenwerk soll sich nicht wie eine Sammlung einzelner Gitarren-Tools anfühlen, sondern wie ein **persönlicher digitaler Gitarrenlehrer und Übungsbegleiter**.

Dabei stehen drei Dinge im Vordergrund:

1. **Verstehen** – Akkorde, Noten, Griffbrett und rhythmische Grundlagen lernen.
2. **Üben** – gezielt trainieren, wiederholen und Fehler erkennen.
3. **Spielen** – das Gelernte direkt auf Songs und musikalische Situationen übertragen.

## 🏗️ Technischer Anspruch

Saitenwerk wird als **native Android-Anwendung** entwickelt. Besonderer Wert liegt auf:

- sauberer und wartbarer Architektur
- konsistentem UI/UX
- hochwertiger visueller Gestaltung
- flüssiger Bedienung
- zuverlässiger Offline-Funktionalität
- wiederverwendbaren Komponenten
- klar getrennten Zuständigkeiten
- robuster Daten- und Zustandsverwaltung
- automatisierter Build- und Validierungsinfrastruktur

Funktionen sollen nicht nur oberflächlich angepasst werden. Änderungen werden möglichst vollständig über die damit verbundenen UI-, Daten-, Navigations-, Trainings- und Abhängigkeitsstrukturen hinweg berücksichtigt.

## 🧪 Qualitätssicherung

Für die Entwicklung wird eine automatisierte **GitHub-Actions-Build-Pipeline** verwendet.

Dabei werden unter anderem:

- Android-Builds erstellt
- automatisierte Prüfungen ausgeführt
- Build-Artefakte erzeugt
- Entwicklungsstände als Backups dokumentiert
- Änderungen nachvollziehbar im Changelog festgehalten

Wichtig: Ein erfolgreicher CI-Build ist nicht automatisch gleichbedeutend mit einem erfolgreichen Test auf einem realen Android-Gerät. Diese beiden Prüfungen werden getrennt betrachtet.

## 📦 Repository-Struktur

Wichtige Bereiche des Repositorys:

- `app/` – Android-App und Quellcode
- `.github/workflows/` – GitHub-Actions-Workflows
- `ci/` – Entwicklungs- und Validierungsskripte
- `build-backups/beta/` – vom aktuellen Build-Prozess verwendete Build-Backups
- `archiv/` – historische, nicht mehr für den aktuellen Build benötigte Entwicklungsstände
- `CHANGELOG.md` – vollständige Änderungsdokumentation
- `.gitignore` – Ausschluss lokaler und generierter Dateien

Historische Entwicklungsstände werden bewusst von den aktuell verwendeten Build-Backups getrennt gehalten.

## 🔐 Sicherheit

Lokale Konfigurationen und sensible Dateien gehören nicht in das Repository.

Die `.gitignore` berücksichtigt unter anderem:

- `local.properties`
- `.env*`
- `*.jks`
- `*.keystore`
- `*.p12`
- `*.pem`
- lokale IDE- und Build-Dateien
- erzeugte APK/AAB-Dateien
- lokale Backup-Archive

Produktive Zugangsdaten, Signaturschlüssel und Passwörter werden nicht als normale Repository-Dateien abgelegt.

## 🚀 Entwicklung

Für die lokale Entwicklung wird ein aktuelles Android-Entwicklungssetup mit Android Studio und einem passenden Android SDK benötigt.

Nach dem Klonen des Repositorys kann das Projekt in Android Studio geöffnet und über das Gradle-System gebaut werden.

Lokale Entwicklungsdateien und erzeugte Build-Artefakte sollten nicht in das Repository eingecheckt werden.

## 📝 Änderungen dokumentieren

Bei Änderungen an Saitenwerk wird Wert auf eine nachvollziehbare Entwicklungshistorie gelegt.

Wesentliche:

- neue Funktionen
- Reparaturen
- Designänderungen
- strukturelle Änderungen
- Problemlösungen
- Validierungen
- Änderungen an Build- und Entwicklungsprozessen

werden im **CHANGELOG.md** dokumentiert.

## 📜 Lizenz

Eine verbindliche Open-Source-Lizenz ist derzeit nicht angegeben. Bis zur ausdrücklichen Festlegung gelten die Rechte am Quellcode und an den enthaltenen Inhalten beim jeweiligen Rechteinhaber.

## 👤 Entwicklung

**Saitenwerk** wird von **David Elger** entwickelt.

Die App befindet sich in aktiver Weiterentwicklung. Ziel ist ein hochwertiges, zuverlässiges und musikalisch sinnvolles Gitarrenlern-Erlebnis für Android.

---

🎸 **Saitenwerk – lernen. üben. spielen.**
