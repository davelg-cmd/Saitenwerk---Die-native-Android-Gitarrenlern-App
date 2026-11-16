#!/usr/bin/env python3
"""Install the supplied transparent Saitenwerk home logo into the Android app."""
from pathlib import Path
import os
import struct
import urllib.request

root = Path(os.environ["PROJECT_DIR"])
res = root / "app/src/main/res/drawable-nodpi"
res.mkdir(parents=True, exist_ok=True)
url = "https://i.postimg.cc/mkQWqSXK/file-00000000f98081f4837b61109cc94cbf.png"
request = urllib.request.Request(url, headers={"User-Agent": "Saitenwerk-Android-Build/1.0"})
try:
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read(12 * 1024 * 1024 + 1)
except Exception as exc:
    raise SystemExit(f"FEHLER: Startseiten-Logo konnte nicht geladen werden: {exc}")
if len(data) > 12 * 1024 * 1024:
    raise SystemExit("FEHLER: Startseiten-Logo ist groesser als 12 MiB.")
if len(data) < 33 or data[:8] != bytes.fromhex("89504e470d0a1a0a"):
    raise SystemExit("FEHLER: Der Bildlink liefert keine gueltige PNG-Datei.")
width, height = struct.unpack(">II", data[16:24])
color_type = data[25]
if not (1 <= width <= 4096 and 1 <= height <= 4096):
    raise SystemExit(f"FEHLER: Unplausible Logo-Abmessungen: {width}x{height}")
# PNG color types 4/6 carry alpha; indexed PNGs may define transparency via tRNS.
has_alpha = color_type in (4, 6) or b"tRNS" in data
if not has_alpha:
    raise SystemExit("FEHLER: Das PNG besitzt keinen Transparenzkanal. Das alte Bild bleibt unveraendert.")
target = res / "saitenwerk_original.png"
target.write_bytes(data)
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
source = main.read_text(encoding="utf-8")
old_background = "            setBackgroundColor(a.getColor(R.color.sw_navy))"
if old_background not in source:
    raise SystemExit("FEHLER: Erwartete Logo-Hintergrundzeile in HomeFragment nicht gefunden.")
source = source.replace(old_background, "            setBackgroundColor(android.graphics.Color.TRANSPARENT)", 1)
main.write_text(source, encoding="utf-8")
old = res / "saitenwerk_original.jpg"
if old.exists():
    old.unlink()
print(f"STARTSEITEN-LOGO: PNG integriert ({width}x{height}, Transparenz vorhanden, {len(data)} Bytes).")
print("STARTSEITEN-LOGO: Altes rechteckiges JPG entfernt; Android verwendet die transparente PNG-Ressource.")
