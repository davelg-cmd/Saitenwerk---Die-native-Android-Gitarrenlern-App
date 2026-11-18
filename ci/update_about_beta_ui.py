from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")
s = main.read_text(encoding="utf-8")
if "App-Informationen" not in s or "Changelog" not in s:
    raise SystemExit("FEHLER: App-Informationen oder Changelog fehlen.")

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
    raise SystemExit("FEHLER: Schnellstart oder Einleitung nicht gefunden.")

# Schnellstart-Card direkt hinter die Einleitung setzen.
quick_block = learn[quick_start:quick_end].rstrip()
learn = learn[:quick_start] + learn[quick_end:]
intro_pos = learn.find(intro_anchor, overview_start)
insert_at = intro_pos + len(intro_anchor)
learn = learn[:insert_at] + "\n\n" + quick_block + "\n\n" + learn[insert_at:]

# Gemeinsame Wochenziel-Werte vor Schnellstart initialisieren.
week_pattern = (
    r'            val cal = java\.util\.Calendar\.getInstance\(\)\n'
    r'            val weekKey = [^\n]*\n'
    r'            val weekSeconds = [^\n]*\n'
    r'            val weekGoal = [^\n]*\n'
)
week_decl = re.search(week_pattern, learn[overview_start:], re.MULTILINE)
if not week_decl:
    raise SystemExit("FEHLER: Wochenziel-Initialisierung im Lernstudio nicht gefunden.")
start = overview_start + week_decl.start()
end = overview_start + week_decl.end()
week_values = learn[start:end]
learn = learn[:start] + learn[end:]
quick_pos = learn.find("            val quick = roundedCard()", overview_start)
if quick_pos < 0:
    raise SystemExit("FEHLER: Schnellstart-Karte nach Verschiebung nicht gefunden.")
learn = learn[:quick_pos] + week_values + learn[quick_pos:]

s = s[:learn_start] + learn + s[learn_end:]

# Reihenfolge und eindeutige Deklaration strikt prüfen.
learn_start = s.find("class LearnFragment : Fragment() {")
learn_end = s.find("\nclass PathFragment : Fragment() {", learn_start)
learn = s[learn_start:learn_end]
overview_start = learn.find("        overviewAction = {")
intro_pos = learn.find("Dein persönlicher Trainingsbereich für Akkorde, Rhythmus, Timing, Schlagmuster und Songs.", overview_start)
week_pos = learn.find("val weekSeconds", overview_start)
quick_pos = learn.find("val quick = roundedCard()", overview_start)
quick_add_pos = learn.find("content.addView(quick)", quick_pos)
xp_pos = learn.find("val xp = prefs.getInt", overview_start)
if min(overview_start, intro_pos, week_pos, quick_pos, quick_add_pos, xp_pos) < 0:
    raise SystemExit("FEHLER: Schnellstart, Level oder Wochenziel fehlt.")
if not (intro_pos < week_pos < quick_pos < quick_add_pos < xp_pos):
    raise SystemExit("FEHLER: Wochenziel oder Schnellstart steht nicht an der erwarteten Position.")
if learn[overview_start:].count("val weekSeconds") != 1:
    raise SystemExit("FEHLER: Wochenziel-Variable ist nicht eindeutig deklariert.")

main.write_text(s, encoding="utf-8")
print("LERNSTUDIO: PASS – Schnellstart ist die erste Karte nach Titel und Einleitung.")
print("WOCHENZIEL: PASS – gemeinsame Werte sind vor Schnellstart initialisiert.")
print("EINSTELLUNGEN: PASS – App-Informationen und Changelog sind vorhanden.")
