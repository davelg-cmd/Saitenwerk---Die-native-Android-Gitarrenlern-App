from pathlib import Path
import os, re, zipfile, shutil

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
assets = root / "app/src/main/assets"
drawables = root / "app/src/main/res/drawable"
assets.mkdir(parents=True, exist_ok=True)
drawables.mkdir(parents=True, exist_ok=True)

# Restore the previously shipped songbook data from the archived Alpha-7
# starting project. The current source already contains SongRepository,
# SongsFragment and SongDetailFragment; only their active entry points/assets
# were removed.
archive = Path(os.environ.get("GITHUB_WORKSPACE", root.parent)) / "archiv/Saitenwerk_ALPHA_7_Songplayer_V3_Start_Originaltempo_Realistic.zip"
if not archive.is_file():
    raise SystemExit(f"FEHLER: Archiviertes Songbook-Quellarchiv fehlt: {archive}")

wanted = {
    "songs.json": "app/src/main/assets/songs.json",
    "public_domain_sheets.json": "app/src/main/assets/public_domain_sheets.json",
    "ic_nav_songs.xml": "app/src/main/res/drawable/ic_nav_songs.xml",
}
with zipfile.ZipFile(archive) as z:
    names = z.namelist()
    for filename, target in wanted.items():
        candidates = [n for n in names if n.replace("\\", "/").endswith("/" + target) or n.replace("\\", "/").endswith("/" + filename)]
        if not candidates:
            raise SystemExit(f"FEHLER: {filename} nicht im archivierten Songbook-Quellarchiv gefunden.")
        source = candidates[0]
        with z.open(source) as src, open(root / target, "wb") as dst:
            shutil.copyfileobj(src, dst)

s = main.read_text(encoding="utf-8")

def once(pattern, replacement, label):
    global s
    s2, n = re.subn(pattern, replacement, s, count=1)
    if n != 1:
        raise SystemExit(f"FEHLER: Songbook-Wiederherstellung nicht eindeutig: {label} (Treffer {n})")
    s = s2

if 'menu.add(0, 4, 3, "Lieder")' not in s:
    once(
        r'(menu\.add\(0, 3, 2, "Akkorde"\)\.setIcon\(R\.drawable\.ic_nav_chords\)\n)',
        r'\1            menu.add(0, 4, 3, "Lieder").setIcon(R.drawable.ic_nav_songs)\n',
        "Bottom-Navigation"
    )

if "is SongsFragment -> 4" not in s:
    once(r'(is ChordsFragment -> 3\n)', r'\1            is SongsFragment -> 4\n', "Navigation-Synchronisierung")
if "4 -> current is SongsFragment" not in s:
    once(r'(3 -> current is ChordsFragment\n)', r'\1            4 -> current is SongsFragment\n', "Navigation-Zustand")
if "4 -> show(SongsFragment())" not in s:
    once(r'(3 -> show(ChordsFragment\(\))\n)', r'\1            4 -> show(SongsFragment())\n', "Navigation-Ziel")

if '"♫  Liederbuch"' not in s:
    marker = '        page.addView(top)\n'
    replacement = marker + '        page.addView(a.button("♫  Liederbuch").apply { setOnClickListener { a.openSection(4) } }, LinearLayout.LayoutParams(-1, a.dp(50)).apply { topMargin = a.dp(10) })\n'
    if marker not in s:
        raise SystemExit("FEHLER: Startseiten-Einstiegspunkt für das Liederbuch nicht gefunden.")
    s = s.replace(marker, replacement, 1)

# Keep the in-app changelog synchronized with the repository changelog.
if 'Liederbuch wiederhergestellt' not in s:
    marker = 'val changelog = listOf(\n'
    entry = '            "23.11.2026 · Build $buildNumber" to "Liederbuch vollständig wiederhergestellt: Bottom-Navigation und Startseiten-Einstieg reaktiviert; vorhandene SongRepository-, SongsFragment- und SongDetailFragment-Funktionen wieder erreichbar; Songdaten und Songreader-Assets aus dem archivierten Alpha-7-Quellstand wieder eingebunden.",\\n'
    if marker in s:
        s = s.replace(marker, marker + entry, 1)
    else:
        print("WARNUNG: In-App-Changelog-Liste nicht gefunden; Repository-CHANGELOG wurde aktualisiert.")

main.write_text(s, encoding="utf-8")
print("LIEDERBUCH-WIEDERHERSTELLUNG: PASS")
print("Bottom-Navigation, Startseiten-Einstieg, SongRepository-Daten und Songreader-Assets wiederhergestellt.")
