#!/usr/bin/env python3
"""Make Songbook storage user-owned: no bundled/imported PDF data survives the transition."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
songbook = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
if not songbook.is_file():
    raise SystemExit("FEHLER: IntelligentSongbook.kt fehlt.")

s = songbook.read_text(encoding="utf-8")

old = 'private val db = context.openOrCreateDatabase("saitenwerk_songbook.db", Context.MODE_PRIVATE, null)'
new = '''private val db = run {
        // One-time cleanup of the legacy Songbook store. From this version onward
        // every installation starts with an empty, user-owned Songbook.
        val prefs = context.getSharedPreferences("saitenwerk_songbook_migration", Context.MODE_PRIVATE)
        if (!prefs.getBoolean("legacy_store_removed_v1", false)) {
            context.deleteDatabase("saitenwerk_songbook.db")
            prefs.edit().putBoolean("legacy_store_removed_v1", true).apply()
        }
        context.openOrCreateDatabase("saitenwerk_songbook_user.db", Context.MODE_PRIVATE, null)
    }'''
if old not in s:
    raise SystemExit("FEHLER: Alter Songbook-Datenbankname nicht gefunden.")
s = s.replace(old, new, 1)

# Make the user-owned nature explicit in the UI.
s = s.replace(
    'addText("Deine Songs. Deine Akkorde. Dein Training.", 15f, Color.LTGRAY, 2)',
    'addText("Deine Songs. Deine Akkorde. Dein Training.", 15f, Color.LTGRAY, 2)\n        addText("Importiere dein eigenes PDF – SaitenWerk analysiert es und legt nur deine Songs hier ab.", 13f, Color.LTGRAY, 1)',
    1
)

songbook.write_text(s, encoding="utf-8")
print("SONGBOOK-USER-ONLY: PASS – Legacy-Datenbank wird einmalig entfernt; neue Datenbank ist leer und ausschließlich benutzerbefüllt.")
