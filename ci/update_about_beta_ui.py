from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
java_root = root / "app/src/main"
files = [p for base in (java_root / "java", java_root / "res") if base.exists()
         for p in base.rglob("*") if p.is_file() and p.suffix in {".kt", ".java", ".xml"}]

# Sichtbare Bezeichnung vereinheitlichen.
for p in files:
    try:
        source = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    updated = re.sub(r'(?i)(?<=[\"\'])Credits(?=[\"\'])', "Über", source)
    if updated != source:
        p.write_text(updated, encoding="utf-8")

main = java_root / "java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")
s = main.read_text(encoding="utf-8")

# Den vorherigen heuristischen View-Tree-Hack vollständig entfernen.
s = s.replace("        window.decorView.post { moveSettingsControlToBottom() }\n", "")
helper_start = s.find("    private fun moveSettingsControlToBottom() {")
if helper_start >= 0:
    brace = s.find("{", helper_start)
    depth = 0
    end = brace
    while end < len(s):
        if s[end] == "{": depth += 1
        elif s[end] == "}":
            depth -= 1
            if depth == 0:
                end += 1
                break
        end += 1
    s = s[:helper_start] + s[end:]

# Einstellungen-Button direkt im HomeFragment ans Ende des echten Layouts setzen.
button_start = s.find('        val settingsButton = a.button("⚙  Einstellungen")')
entries_start = s.find("        val entries = listOf(", button_start)
if button_start < 0 or entries_start < 0:
    raise SystemExit("FEHLER: Einstellungen-Button oder Startseiten-Einträge nicht gefunden.")
settings_block = s[button_start:entries_start]
s = s[:button_start] + s[entries_start:]
entries_start = s.find("        entries.forEach {", button_start)
if entries_start < 0:
    raise SystemExit("FEHLER: Startseiten-Einträge-Schleife nicht gefunden.")
brace = s.find("{", entries_start)
depth = 0
end = brace
while end < len(s):
    if s[end] == "{": depth += 1
    elif s[end] == "}":
        depth -= 1
        if depth == 0:
            end += 1
            break
    end += 1
if depth != 0:
    raise SystemExit("FEHLER: Startseiten-Einträge-Schleife ist nicht ausgeglichen.")
s = s[:end] + "\n\n" + settings_block.rstrip() + "\n" + s[end:]

# Den bisherigen nicht klickbaren Credits-Platzhalter durch eine echte Über-Karte ersetzen.
credits_start = s.find("        val credits = a.card()")
return_start = s.find("        return ScrollView(a).apply { addView(content) }", credits_start)
if credits_start < 0 or return_start < 0:
    raise SystemExit("FEHLER: Über-Karte oder Rückgabe des Einstellungsbildschirms nicht gefunden.")
about_block = r'''        val appInfo = a.packageManager.getPackageInfo(a.packageName, 0)
        val appVersionName = appInfo.versionName ?: "unbekannt"
        val appVersionCode = appInfo.versionCode
        val credits = a.card().apply {
            isClickable = true
            isFocusable = true
            setOnClickListener {
                val about = "Saitenwerk ist mehr als nur eine Gitarren-App – es ist ein Experiment.\n\n" +
                    "Die Idee hinter diesem Projekt war von Anfang an eine ganz bestimmte: Ich wollte zeigen, dass man keine Programmierkenntnisse oder jahrelange Erfahrung in der Softwareentwicklung benötigt, um eine eigene App auf die Beine zu stellen.\n\n" +
                    "Mit Neugier, Ausdauer und der Unterstützung künstlicher Intelligenz ist Saitenwerk entstanden – von der ersten Idee bis hin zu einer eigenständigen Android-App.\n\n" +
                    "Mir ging es dabei vor allem darum, zu zeigen, was heute möglich ist, wenn man bereit ist, neue Wege auszuprobieren und KI als Werkzeug zu nutzen. Nicht darum, zu beweisen, dass ich ein professioneller Entwickler bin, sondern dass die Einstiegshürden in die App-Entwicklung längst nicht mehr so hoch sind, wie viele vielleicht denken.\n\n" +
                    "Saitenwerk ist deshalb auch ein Beispiel dafür, wie aus einer Idee mithilfe von KI Schritt für Schritt etwas Greifbares werden kann.\n\n" +
                    "Man muss nicht alles können, um etwas Eigenes zu erschaffen. Man muss nur anfangen."
                val details = "Saitenwerk\nDie native Android-Gitarrenlern-App\n\n" +
                    "Version: $appVersionName\n" +
                    "Build: $appVersionCode\n" +
                    "Release-Kanal: Beta\n" +
                    "Paket-ID: \${a.packageName}\n" +
                    "Mindestversion: Android 8.0 (API 26)\n" +
                    "Plattform: Android\n\n" +
                    "Über das Projekt\n$about"
                androidx.appcompat.app.AlertDialog.Builder(a)
                    .setTitle("Über Saitenwerk")
                    .setMessage(details)
                    .setPositiveButton("Schließen", null)
                    .show()
            }
        }
        val creditsContent = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(18), a.dp(16), a.dp(18), a.dp(16))
        }
        creditsContent.addView(TextView(a).apply {
            text = "Über"
            textSize = 18f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_text))
        })
        creditsContent.addView(TextView(a).apply {
            text = "Saitenwerk · Version $appVersionName · Build $appVersionCode · Beta\nApp-Informationen und Projektgeschichte anzeigen"
            textSize = 14f
            setTextColor(a.getColor(R.color.sw_muted))
            setPadding(0, a.dp(6), 0, 0)
        })
        credits.addView(creditsContent)
        content.addView(credits, LinearLayout.LayoutParams(-1, -2).apply {
            setMargins(0, a.dp(14), 0, 0)
        })

'''
s = s[:credits_start] + about_block + s[return_start:]

# Strukturelle Sicherungen gegen Rückfall auf die vorherige fehlerhafte Umsetzung.
home = s[s.find("class HomeFragment") : s.find("class SettingsFragment")]
if home.find('root.addView(settingsButton') < home.find('entries.forEach'):
    raise SystemExit("FEHLER: Einstellungen-Button steht nicht hinter den Startseiten-Einträgen.")
about_start = s.find('val credits = a.card()')
about_end = s.find('return ScrollView(a).apply { addView(content) }', about_start)
if 'setOnClickListener {' not in s[about_start:about_end]:
    raise SystemExit("FEHLER: Über-Karte besitzt keinen Klick-Handler.")
if "moveSettingsControlToBottom" in s:
    raise SystemExit("FEHLER: Alter heuristischer Positions-Hack ist noch vorhanden.")
main.write_text(s, encoding="utf-8")
print("UI-UPDATE PASS: Einstellungen-Button steht nach allen Startseiten-Aktionen am unteren Ende.")
print("UI-UPDATE PASS: Über-Karte öffnet eine scrollbare Informationsansicht mit App- und Builddaten.")
