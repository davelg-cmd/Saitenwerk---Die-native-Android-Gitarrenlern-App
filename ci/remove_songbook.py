from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not main.is_file():
    raise SystemExit(f"FEHLER: MainActivity.kt nicht gefunden: {main}")
s = main.read_text(encoding="utf-8")

s, n = re.subn(r'\n\s*menu\.add\(0, 4, 3, "Lieder"\)\.setIcon\(R\.drawable\.ic_nav_songs\)', '', s)
if n != 1:
    raise SystemExit(f"FEHLER: Lieder-Navigation nicht eindeutig gefunden (Treffer: {n})")

s, n1 = re.subn(r'\n\s*is SongsFragment -> 4', '', s)
s, n2 = re.subn(r'\n\s*4 -> current is SongsFragment', '', s)
s, n3 = re.subn(r'\n\s*4 -> show\(SongsFragment\(\)\)', '', s)
if (n1, n2, n3) != (1, 1, 1):
    raise SystemExit(f"FEHLER: Lieder-Routing nicht vollständig gefunden: {(n1, n2, n3)}")

s, n = re.subn(r'\s*"♫  Liederbuch" to 4,', '', s)
if n != 1:
    raise SystemExit(f"FEHLER: Liederbuch-Startseitenbutton nicht gefunden (Treffer: {n})")

s, n = re.subn(r'\n\s*fun openSong\(song: Song\) \{\n\s*show\(SongDetailFragment\.newInstance\(song\)\)\n\s*\}\n', '\n', s)
if n != 1:
    raise SystemExit(f"FEHLER: openSong()-Routing nicht gefunden (Treffer: {n})")

main.write_text(s, encoding="utf-8")

for rel in [
    "app/src/main/assets/songs.json",
    "app/src/main/assets/public_domain_sheets.json",
    "app/src/main/res/drawable/ic_nav_songs.xml",
]:
    p = root / rel
    if p.exists():
        p.unlink()
        print(f"OK: entfernt: {rel}")

print("LIEDERBUCH ENTFERNT: PASS")
print("Lieder sind nicht mehr in Bottom-Navigation oder Startseite erreichbar.")
print("Song-Code bleibt isoliert im Quellstand für eine spätere Neuentwicklung erhalten.")
