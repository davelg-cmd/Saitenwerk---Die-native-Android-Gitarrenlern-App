#!/usr/bin/env python3
"""Center the Songpraxis stop button label vertically."""
from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

# The current play/stop toggle styles its own TextView. Do not inject a
# gravity assignment into the click-listener scope around its stop label.
if "var progressionPlaying = false" in s:
    print("SONGPRAXIS: Start/Stopp-Button ist bereits im Toggle-Patch zentriert; kein separater Eingriff nötig.")
    raise SystemExit(0)

needle = "Wiedergabe stoppen"
positions = [m.start() for m in re.finditer(re.escape(needle), s)]
if not positions:
    # The dedicated stop button was intentionally removed from the current
    # Song-Praxis layout; the play button itself now toggles to stop.
    print("SONGPRAXIS: Kein separater Stoppbutton vorhanden; Zentrierung des Start/Stopp-Buttons erfolgt im Toggle-Patch.")
    raise SystemExit(0)

# Locate the button declaration associated with the visible stop label.
target = None
for pos in positions:
    window_start = max(0, pos - 1400)
    window = s[window_start:pos]
    declarations = list(re.finditer(
        r"(?m)^\s*(?:val|var)\s+([A-Za-z_]\w*)\s*=\s*(?:[A-Za-z_]\w*\.)?(?:button|Button)\s*\(",
        window
    ))
    if declarations:
        decl = declarations[-1]
        target = (window_start + decl.start(), decl.group(1), pos)
        break

if target is None:
    raise SystemExit("FEHLER: Button-Deklaration zur Stopp-Beschriftung konnte nicht eindeutig zugeordnet werden.")

decl_start, button_name, label_pos = target
line_start = s.rfind("\n", 0, label_pos) + 1
line_end = s.find("\n", label_pos)
if line_end < 0:
    line_end = len(s)
label_line = s[line_start:line_end]

# If the label is inside an apply { ... } block, set gravity in that block.
prefix = s[decl_start:label_pos]
open_blocks = prefix.count("{") - prefix.count("}")
if open_blocks > 0:
    indent = re.match(r"\s*", label_line).group(0) + "    "
    insertion = f"\n{indent}gravity = Gravity.CENTER"
    s = s[:line_end] + insertion + s[line_end:]
else:
    # For a direct button constructor, set the property immediately after its declaration.
    decl_line_start = s.rfind("\n", 0, decl_start) + 1
    decl_line_end = s.find("\n", decl_start)
    if decl_line_end < 0:
        decl_line_end = len(s)
    decl_line = s[decl_line_start:decl_line_end]
    if button_name + ".gravity = Gravity.CENTER" not in s:
        indent = re.match(r"\s*", decl_line).group(0)
        insertion = f"\n{indent}{button_name}.gravity = Gravity.CENTER"
        s = s[:decl_line_end] + insertion + s[decl_line_end:]

# Confirm the adjustment is present close to the stop-button declaration.
check_start = max(0, decl_start - 100)
check_end = min(len(s), label_pos + 500)
if "gravity = Gravity.CENTER" not in s[check_start:check_end]:
    raise SystemExit("FEHLER: Vertikale Zentrierung des Stopp-Buttons konnte nicht validiert werden.")

path.write_text(s, encoding="utf-8")
print("SONGPRAXIS: PASS – Beschriftung des Wiedergabe-Stopp-Buttons vertikal zentriert.")
