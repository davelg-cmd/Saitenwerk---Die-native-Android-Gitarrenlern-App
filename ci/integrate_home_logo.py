#!/usr/bin/env python3
"""Install the same transparent Saitenwerk logo used by the launcher on the home screen."""
from pathlib import Path
import os
import struct

workspace = Path(os.environ["GITHUB_WORKSPACE"])
root = Path(os.environ["PROJECT_DIR"])
source = workspace / "assets/saitenwerk_launcher.png"
res = root / "app/src/main/res/drawable-nodpi"
res.mkdir(parents=True, exist_ok=True)

if not source.is_file():
    raise SystemExit(f"FEHLER: Gemeinsames Saitenwerk-Logo fehlt: {source}")
data = source.read_bytes()
if len(data) < 33 or data[:8] != bytes.fromhex("89504e470d0a1a0a"):
    raise SystemExit("FEHLER: Das gemeinsame Saitenwerk-Logo ist keine gueltige PNG-Datei.")
width, height = struct.unpack(">II", data[16:24])
color_type = data[25]
has_alpha = color_type in (4, 6) or b"tRNS" in data
if not (1 <= width <= 4096 and 1 <= height <= 4096):
    raise SystemExit(f"FEHLER: Unplausible Logo-Abmessungen: {width}x{height}")
if not has_alpha:
    raise SystemExit("FEHLER: Das gemeinsame Logo besitzt keinen Transparenzkanal.")

target = res / "saitenwerk_original.png"
target.write_bytes(data)

main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
source_code = main.read_text(encoding="utf-8")
old_background = "            setBackgroundColor(a.getColor(R.color.sw_navy))"
if old_background in source_code:
    source_code = source_code.replace(
        old_background,
        "            setBackgroundColor(android.graphics.Color.TRANSPARENT)",
        1,
    )
    main.write_text(source_code, encoding="utf-8")

old = res / "saitenwerk_original.jpg"
if old.exists():
    old.unlink()

print(f"STARTSEITEN-LOGO: Gemeinsames Launcher-Logo integriert ({width}x{height}, Transparenz, {len(data)} Bytes).")
print("STARTSEITEN-LOGO: Das SAITENWERK-Schriftbild bleibt direkt unter dem Emblem erhalten.")
