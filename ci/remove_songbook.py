#!/usr/bin/env python3
"""Remove the abandoned songbook implementation from an extracted Saitenwerk project."""
from pathlib import Path
import os
import re
import sys

ROOT = Path(os.environ["PROJECT_DIR"])
MAIN = ROOT / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
GRADLE = ROOT / "app/build.gradle.kts"
VERIFY_ONLY = "--verify" in sys.argv

if not MAIN.is_file():
    raise SystemExit(f"FEHLER: MainActivity.kt nicht gefunden: {MAIN}")

def kotlin_matching_brace(source: str, opening: int) -> int:
    depth = 0
    i = opening
    state = "code"
    block_depth = 0
    while i < len(source):
        if state == "code":
            if source.startswith("//", i):
                state = "line_comment"
                i += 2
                continue
            if source.startswith("/*", i):
                state = "block_comment"
                block_depth = 1
                i += 2
                continue
            if source.startswith('"""', i):
                state = "raw_string"
                i += 3
                continue
            ch = source[i]
            if ch == '"':
                state = "string"
            elif ch == "'":
                state = "char"
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        elif state == "line_comment":
            if source[i] == "\n":
                state = "code"
        elif state == "block_comment":
            if source.startswith("/*", i):
                block_depth += 1
                i += 2
                continue
            if source.startswith("*/", i):
                block_depth -= 1
                i += 2
                if block_depth == 0:
                    state = "code"
                continue
        elif state == "raw_string":
            if source.startswith('"""', i):
                state = "code"
                i += 3
                continue
        elif state in ("string", "char"):
            if source[i] == "\\":
                i += 2
                continue
            if (state == "string" and source[i] == '"') or (state == "char" and source[i] == "'"):
                state = "code"
        i += 1
    raise SystemExit("FEHLER: Nicht geschlossene Kotlin-Klammer beim Entfernen einer Songbook-Deklaration.")

TOP_LEVEL = re.compile(
    r"(?m)^(?:(?:private|internal|public|protected|data|sealed|abstract|open|inner|enum|annotation|value)\s+)*(?:class|object|interface)\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)
TARGETS = {"Song", "SongRepository", "SongsFragment", "SongAdapter", "SongDetailFragment"}

def remove_top_level_declarations(source: str) -> str:
    matches = [m for m in TOP_LEVEL.finditer(source) if m.group(1) in TARGETS]
    found = {}
    for m in matches:
        found[m.group(1)] = found.get(m.group(1), 0) + 1
    duplicate = sorted(name for name, count in found.items() if count != 1)
    if duplicate:
        raise SystemExit(
            "FEHLER: Songbook-Deklarationen mehrfach gefunden. "
            f"Mehrfach: {duplicate}; gefunden: {found}"
        )
    # Alle Grenzen anhand derselben Originalfassung berechnen. Andernfalls würde
    # das Entfernen rückwärts liegender Klassen die nächste Deklaration verschieben
    # und eine körperlose data class könnte versehentlich fremde Klassen mitlöschen.
    spans = []
    for m in matches:
        opening = source.find("{", m.end())
        next_decl = TOP_LEVEL.search(source, m.end())
        if opening < 0 or (next_decl and next_decl.start() < opening):
            end = next_decl.start() if next_decl else source.find("\n", m.start())
            if end < 0:
                end = len(source)
        else:
            end = kotlin_matching_brace(source, opening) + 1
            if end < len(source) and source[end] == "\r":
                end += 1
            if end < len(source) and source[end] == "\n":
                end += 1
        spans.append((m.start(), end))
    for start, end in reversed(spans):
        source = source[:start] + source[end:]
    return source

def remove_function(source: str, name: str, signature: str) -> str:
    matches = list(re.finditer(signature, source, re.MULTILINE))
    if len(matches) != 1:
        raise SystemExit(f"FEHLER: {name} nicht eindeutig gefunden (Treffer: {len(matches)}).")
    m = matches[0]
    # Die Signatur-RegEx enthält bereits die öffnende Klammer.
    # Nicht erst nach m.end() suchen: Das würde bei einer Funktion mit
    # Properties direkt danach versehentlich den nächsten Lambda-Block erwischen.
    opening = source.find("{", m.start(), m.end())
    if opening < 0:
        raise SystemExit(f"FEHLER: Funktionsblock {name} ohne öffnende Klammer.")
    end = kotlin_matching_brace(source, opening) + 1
    if end < len(source) and source[end] == "\r":
        end += 1
    if end < len(source) and source[end] == "\n":
        end += 1
    return source[:m.start()] + source[end:]

def remove_optional_line(source: str, pattern: str, label: str) -> str:
    source, count = re.subn(pattern, "", source, flags=re.MULTILINE)
    if count > 1:
        raise SystemExit(f"FEHLER: {label} mehrfach gefunden (Treffer: {count}).")
    if count == 1:
        print(f"ENTFERNT: {label}")
    else:
        print(f"NICHT VORHANDEN: {label} (bereits entfernt oder im Ausgangsstand nicht enthalten)")
    return source

def apply_removal():
    s = MAIN.read_text(encoding="utf-8")
    s = remove_optional_line(
        s,
        r'^[ \t]*menu\.add\(0,\s*4,\s*3,\s*"Lieder"\)\.setIcon\(R\.drawable\.ic_nav_songs\)[ \t]*\r?\n',
        "Lieder-Navigation"
    )
    s = remove_optional_line(s, r'^[ \t]*is SongsFragment -> 4[ \t]*\r?\n', "Navigation-Synchronisierung")
    s = remove_optional_line(s, r'^[ \t]*4 -> current is SongsFragment[ \t]*\r?\n', "Navigation-Routing")
    s = remove_optional_line(s, r'^[ \t]*4 -> show\(SongsFragment\(\)\)[ \t]*\r?\n', "Navigation-Ziel")
    s = remove_optional_line(s, r'^[ \t]*"[^"\n]*Liederbuch" to 4,[ \t]*\r?\n', "Liederbuch-Startseiteneinstieg")
    open_song = re.compile(r"^[ \t]*fun\s+openSong\s*\(\s*song\s*:\s*Song\s*\)\s*\{", re.MULTILINE)
    if open_song.search(s):
        s = remove_function(s, "openSong()", open_song.pattern)
    else:
        print("NICHT VORHANDEN: openSong()-Routing")
    s = remove_top_level_declarations(s)
    MAIN.write_text(s, encoding="utf-8")

    if GRADLE.is_file():
        g = GRADLE.read_text(encoding="utf-8")
        g, count = re.subn(
            r'^[ \t]*implementation\(["\']com\.tom-roush:pdfbox-android:[^"\']+["\']\)[ \t]*\r?\n',
            "",
            g,
            flags=re.MULTILINE
        )
        if count > 1:
            raise SystemExit(f"FEHLER: PDFBox-Abhängigkeit mehrfach gefunden ({count}).")
        GRADLE.write_text(g, encoding="utf-8")

    for rel in [
        "app/src/main/java/de/saitenwerk/app/SongbookPdfImporter.kt",
        "app/src/main/java/de/saitenwerk/app/SongbookPdfViewer.kt",
        "app/src/main/assets/saitenwerk_legacy.html",
        "app/src/main/assets/songs.json",
        "app/src/main/assets/public_domain_sheets.json",
        "app/src/main/res/drawable/ic_nav_songs.xml",
        "UPLOAD_INSTRUCTIONS.md",
        "SONGBOOK_PUBLIC_DOMAIN.md",
        "CHANGELOG_ALPHA7_LIEDERBUCH.md",
        "UPDATE_ALPHA7_SONGREADER_V3.md",
        "fix_v3.py",
        "UPDATEFIX_README.md",
    ]:
        path = ROOT / rel
        if path.is_file():
            path.unlink()
            print(f"ENTFERNT: {rel}")

def validate():
    if not MAIN.is_file():
        raise SystemExit("FEHLER: MainActivity.kt fehlt nach dem Rückbau.")
    main = MAIN.read_text(encoding="utf-8")
    declarations = [m.group(1) for m in TOP_LEVEL.finditer(main) if m.group(1) in TARGETS]
    if declarations:
        raise SystemExit("FEHLER: Songbook-Klassen/-Modelle verblieben: " + ", ".join(declarations))
    forbidden = [
        "SongsFragment", "SongDetailFragment", "SongRepository", "SongAdapter",
        "SongbookPdfImporter", "SongbookPdfViewer", "songbook_catalog",
        "sourcePageStart", "sourcePageEnd", "importedContent",
        "pdfbox-android", "ic_nav_songs",
    ]
    files = list((ROOT / "app/src/main").rglob("*"))
    for path in files:
        if not path.is_file() or path.suffix.lower() not in {".kt", ".kts", ".xml", ".json", ".toml"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found = [term for term in forbidden if term in content]
        if found:
            raise SystemExit(f"FEHLER: Songbook-Rest in {path.relative_to(ROOT)}: {', '.join(found)}")
    if GRADLE.is_file() and "pdfbox-android" in GRADLE.read_text(encoding="utf-8"):
        raise SystemExit("FEHLER: PDFBox-Abhängigkeit ist weiterhin vorhanden.")
    for rel in [
        "app/src/main/java/de/saitenwerk/app/SongbookPdfImporter.kt",
        "app/src/main/java/de/saitenwerk/app/SongbookPdfViewer.kt",
        "app/src/main/assets/songs.json",
        "app/src/main/assets/public_domain_sheets.json",
        "app/src/main/res/drawable/ic_nav_songs.xml",
    ]:
        if (ROOT / rel).exists():
            raise SystemExit(f"FEHLER: Songbook-Ressource verblieben: {rel}")
    if "showSongPractice()" not in main:
        raise SystemExit("FEHLER: Song-Praxis wurde beim Songbook-Rückbau unbeabsichtigt entfernt.")
    print("SONGBOOK-RÜCKBAU: PASS")
    print("Songbook-Navigation, Datenmodell, Repository, Listen-/Detailansichten, PDF-Importer/-Viewer, PDFBox und zugehörige Ressourcen sind entfernt.")
    print("Song-Praxis und übrige Trainingsfunktionen sind im Quelltext weiterhin vorhanden.")

if not VERIFY_ONLY:
    apply_removal()
validate()
