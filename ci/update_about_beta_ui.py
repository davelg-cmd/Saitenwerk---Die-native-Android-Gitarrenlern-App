from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")
s = main.read_text(encoding="utf-8")

# Die Einstellungsaufteilung wurde bereits in Build 354 integriert.
# Hier wird ausschließlich die tatsächliche Reihenfolge der Lernstudio-Ansicht korrigiert.
if "App-Informationen" not in s or "Changelog" not in s:
    raise SystemExit("FEHLER: Die bereits integrierten App-Informationen fehlen im Ausgangsprojekt.")

learn_start = s.find("class LearnFragment : Fragment() {")
learn_end = s.find("\nclass PathFragment : Fragment() {", learn_start)
if learn_start < 0 or learn_end < 0:
    raise SystemExit("FEHLER: Lernstudio-Klasse nicht gefunden.")
learn = s[learn_start:learn_end]

overview_start = learn.find("        overviewAction = {")
intro_anchor = '            content.addView(a.body("Dein persönlicher Trainingsbereich für Akkorde, Rhythmus, Timing, Schlagmuster und Songs."))'
intro_pos = learn.find(intro_anchor, overview_start)
quick_start = learn.find("            val quick = roundedCard()", overview_start)
quick_end = learn.find("            val path = roundedCard()", quick_start)
if min(overview_start, intro_pos, quick_start, quick_end) < 0:
    raise SystemExit("FEHLER: Schnellstart oder Lernstudio-Einstieg nicht gefunden.")

quick_block = learn[quick_start:quick_end]
quick_pos = quick_start
xp_pos = learn.find("            val xp = prefs.getInt", overview_start)

# Die Schnellstart-Karte verwendet das Wochenziel. Dessen Werte müssen vor
# dem Kartenaufbau initialisiert sein, auch wenn die Karte vor dem Wochenziel-Panel steht.
import re
week_decl = re.search(
    r'            val cal = java\\.util\\.Calendar\\.getInstance\\(\\)\\n'
    r'            val weekKey = .*?\\n'
    r'            val weekSeconds = .*?\\n'
    r'            val weekGoal = .*?\\n',
    learn,
    re.DOTALL,
)
if week_decl:
    week_values = week_decl.group(0)
    learn = learn[:week_decl.start()] + learn[week_decl.end():]
    quick_start = learn.find("            val quick = roundedCard()", overview_start)
    if quick_start < 0:
        raise SystemExit("FEHLER: Schnellstart-Karte für Wochenziel-Initialisierung nicht gefunden.")
    learn = learn[:quick_start] + week_values + learn[quick_start:]
else:
    # Bereits korrekt vorgezogene Initialisierung nicht erneut einfügen.
    if "val weekSeconds" not in learn[:learn.find("val quick = roundedCard()")]:
        raise SystemExit("FEHLER: Wochenziel-Initialisierung nicht gefunden.")

# Nur verschieben, wenn Schnellstart nicht bereits direkt nach der Einleitung steht.
if quick_pos > intro_pos and (xp_pos < 0 or quick_pos > xp_pos):
    learn = learn[:quick_start] + learn[quick_end:]
    intro_pos = learn.find(intro_anchor, overview_start)
    insert_at = intro_pos + len(intro_anchor)
    learn = learn[:insert_at] + "\n\n" + quick_block.rstrip() + learn[insert_at:]
    print("LERNSTUDIO: Schnellstart-Block an den Anfang verschoben.")
else:
    print("LERNSTUDIO: Schnellstart steht bereits am Anfang; keine erneute Verschiebung.")

s = s[:learn_start] + learn + s[learn_end:]

# Prüfen, dass die Karte tatsächlich vor Level, Fortschritt und Empfehlung aufgebaut wird.
learn_start = s.find("class LearnFragment : Fragment() {")
learn_end = s.find("\nclass PathFragment : Fragment() {", learn_start)
learn = s[learn_start:learn_end]
overview_start = learn.find("        overviewAction = {")
intro_pos = learn.find("Dein persönlicher Trainingsbereich für Akkorde, Rhythmus, Timing, Schlagmuster und Songs.", overview_start)
quick_pos = learn.find("val quick = roundedCard()", overview_start)
quick_add_pos = learn.find("content.addView(quick)", quick_pos)
xp_pos = learn.find("val xp = prefs.getInt", overview_start)
if min(overview_start, intro_pos, quick_pos, quick_add_pos, xp_pos) < 0:
    raise SystemExit("FEHLER: Schnellstart-Karte oder Lernstudio-Start fehlt.")
if not (intro_pos < quick_pos < quick_add_pos < xp_pos):
    raise SystemExit("FEHLER: Schnellstart wird nicht vor Level und den übrigen Lernstudio-Karten hinzugefügt.")

main.write_text(s, encoding="utf-8")
print("LERNSTUDIO: PASS – Schnellstart wird direkt nach Titel und Einleitung als erste Karte angezeigt.")
print("EINSTELLUNGEN: PASS – App-Informationen und Changelog sind im Ausgangsprojekt vorhanden.")
