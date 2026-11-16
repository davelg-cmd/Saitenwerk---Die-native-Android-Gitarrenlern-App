from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
java_root = root / "app/src/main"
files = [p for base in (java_root / "java", java_root / "res") if base.exists()
         for p in base.rglob("*") if p.is_file() and p.suffix in {".kt", ".java", ".xml"}]

# "Credits" wird in der sichtbaren Oberfläche konsequent zu "Über".
changed = []
for p in files:
    try:
        s = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    updated = re.sub(r'(?i)(?<=["\'])Credits(?=["\'])', "Über", s)
    if updated != s:
        p.write_text(updated, encoding="utf-8")
        changed.append(str(p.relative_to(root)))

main = java_root / "java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt für die Startseiten-Anpassung fehlt.")
s = main.read_text(encoding="utf-8")

if "moveSettingsControlToBottom" not in s:
    # Find the MainActivity class and its matching closing brace.
    m = re.search(r'\bclass\s+MainActivity\b[^{]*\{', s)
    if not m:
        raise SystemExit("FEHLER: MainActivity-Klasse nicht eindeutig gefunden.")
    depth = 1
    i = m.end()
    while i < len(s) and depth:
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
        i += 1
    if depth:
        raise SystemExit("FEHLER: MainActivity-Klammerstruktur unvollständig.")
    class_end = i - 1

    helper = r'''
    /**
     * Platziert den Einstellungen-Einstieg am Ende des vertikalen Startseitenlayouts.
     * Die vorhandenen Layout-Parameter und das bestehende Button-Design bleiben erhalten.
     */
    private fun moveSettingsControlToBottom() {
        val root = window.decorView
        fun findSettings(view: android.view.View): android.view.View? {
            if (view is android.widget.TextView &&
                view.text.toString().trim().equals("Einstellungen", ignoreCase = true)) return view
            if (view.contentDescription?.toString()?.trim()?.equals("Einstellungen", ignoreCase = true) == true) return view
            if (view is android.view.ViewGroup) {
                for (index in 0 until view.childCount) {
                    findSettings(view.getChildAt(index))?.let { return it }
                }
            }
            return null
        }
        val aboutText = "Saitenwerk ist mehr als nur eine Gitarren-App – es ist ein Experiment.\\n\\n" +
            "Die Idee hinter diesem Projekt war von Anfang an eine ganz bestimmte: Ich wollte zeigen, dass man keine Programmierkenntnisse oder jahrelange Erfahrung in der Softwareentwicklung benötigt, um eine eigene App auf die Beine zu stellen.\\n\\n" +
            "Mit Neugier, Ausdauer und der Unterstützung künstlicher Intelligenz ist Saitenwerk entstanden – von der ersten Idee bis hin zu einer eigenständigen Android-App.\\n\\n" +
            "Mir ging es dabei vor allem darum, zu zeigen, was heute möglich ist, wenn man bereit ist, neue Wege auszuprobieren und KI als Werkzeug zu nutzen. Nicht darum, zu beweisen, dass ich ein professioneller Entwickler bin, sondern dass die Einstiegshürden in die App-Entwicklung längst nicht mehr so hoch sind, wie viele vielleicht denken.\\n\\n" +
            "Saitenwerk ist deshalb auch ein Beispiel dafür, wie aus einer Idee mithilfe von KI Schritt für Schritt etwas Greifbares werden kann.\\n\\n" +
            "Man muss nicht alles können, um etwas Eigenes zu erschaffen. Man muss nur anfangen."
        fun findAbout(view: android.view.View): android.widget.TextView? {
            if (view is android.widget.TextView && view.text.toString().trim().equals("Über", ignoreCase = true)) return view
            if (view is android.view.ViewGroup) {
                for (index in 0 until view.childCount) {
                    findAbout(view.getChildAt(index))?.let { return it }
                }
            }
            return null
        }
        findAbout(root)?.setOnClickListener {
            androidx.appcompat.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Über Saitenwerk")
                .setMessage(aboutText)
                .setPositiveButton("Schließen", null)
                .show()
        }

        val target = findSettings(root) ?: return
        val originalParent = target.parent as? android.view.ViewGroup ?: return
        var container: android.widget.LinearLayout? = null
        var node: android.view.ViewGroup? = originalParent
        while (node != null) {
            if (node is android.widget.LinearLayout && node.orientation == android.widget.LinearLayout.VERTICAL) {
                container = node
                break
            }
            node = node.parent as? android.view.ViewGroup
        }
        val destination = container ?: return
        if (target.parent === destination && destination.indexOfChild(target) == destination.childCount - 1) return
        val params = target.layoutParams
        (target.parent as? android.view.ViewGroup)?.removeView(target)
        destination.addView(target, params)
    }
'''
    s = s[:class_end] + helper + "\n" + s[class_end:]

    # Schedule after the content view has been inflated; post lets the full view tree exist.
    if "setContentView(" not in s:
        raise SystemExit("FEHLER: setContentView-Aufruf in MainActivity nicht gefunden.")
    # Find the first setContentView call and its balanced closing parenthesis.
    pos = s.find("setContentView(") + len("setContentView(")
    paren = 1
    j = pos
    while j < len(s) and paren:
        if s[j] == "(":
            paren += 1
        elif s[j] == ")":
            paren -= 1
        j += 1
    if paren:
        raise SystemExit("FEHLER: setContentView-Aufruf konnte nicht ausgewertet werden.")
    s = s[:j] + "\n        window.decorView.post { moveSettingsControlToBottom() }" + s[j:]

    main.write_text(s, encoding="utf-8")

# Verify both visible label migration and runtime relocation hook.
verify = main.read_text(encoding="utf-8")
if "moveSettingsControlToBottom" not in verify:
    raise SystemExit("FEHLER: Einstellungen-Positionierung wurde nicht integriert.")
print("UI-UPDATE: Credits heißt jetzt Über.")
print("UI-UPDATE: Einstellungen-Button wird nach Aufbau des Startseitenlayouts nach unten verschoben.")
print("Geänderte Credit-Dateien:", changed if changed else "keine separaten Credits-Texte gefunden")
