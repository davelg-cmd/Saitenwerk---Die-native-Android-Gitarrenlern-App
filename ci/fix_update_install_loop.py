#!/usr/bin/env python3
"""Prevent the updater from reopening an already-consumed Android APK installer."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
source = root / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
if not source.is_file():
    raise SystemExit(f"FEHLER: AppUpdateManager.kt nicht gefunden: {source}")

text = source.read_text(encoding="utf-8")

old = """    private fun completeDownloadIfReady(id: Long) {
        if (id != prefs.getLong(KEY_DOWNLOAD_ID, -2L)) return
        val fileName = prefs.getString(KEY_DOWNLOAD_FILE, APK_NAME) ?: APK_NAME
        val file = File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), fileName)
        if (file.exists() && file.length() > 0L) {
            prefs.edit().putString(KEY_PENDING_APK, file.absolutePath).apply()
            installIfAllowed()
        }
    }
"""

new = """    private fun completeDownloadIfReady(id: Long) {
        if (id != prefs.getLong(KEY_DOWNLOAD_ID, -2L)) return
        val fileName = prefs.getString(KEY_DOWNLOAD_FILE, APK_NAME) ?: APK_NAME
        val file = File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), fileName)
        if (file.exists() && file.length() > 0L) {
            // Consume the completed DownloadManager ID BEFORE opening Android's installer.
            // Otherwise onResume() sees the same successful download after the app update
            // and launches the exact same installer again, creating an update loop.
            val consumed = prefs.edit()
                .putString(KEY_PENDING_APK, file.absolutePath)
                .remove(KEY_DOWNLOAD_ID)
                .remove(KEY_DOWNLOAD_FILE)
                .commit()
            if (consumed) installIfAllowed()
        } else {
            // Do not keep a stale completed download that can be replayed on every resume.
            prefs.edit()
                .remove(KEY_DOWNLOAD_ID)
                .remove(KEY_DOWNLOAD_FILE)
                .commit()
        }
    }
"""

if old not in text:
    if "Consume the completed DownloadManager ID BEFORE opening Android's installer." in text:
        print("UPDATE INSTALL LOOP FIX: bereits vorhanden")
    else:
        raise SystemExit("FEHLER: Erwartete completeDownloadIfReady()-Implementierung nicht gefunden; Datei unverändert.")
else:
    text = text.replace(old, new, 1)
    print("OK: abgeschlossene DownloadManager-ID wird vor der Installation verbraucht")

old_clear = '            prefs.edit().remove(KEY_PENDING_APK).apply()'
new_clear = '            prefs.edit().remove(KEY_PENDING_APK).commit()'
if old_clear in text:
    text = text.replace(old_clear, new_clear, 1)
    print("OK: Pending-Installationsstatus wird synchron gelöscht")
elif new_clear in text:
    print("OK: Pending-Installationsstatus wird bereits synchron gelöscht")
else:
    raise SystemExit("FEHLER: Erfolgreicher Installer-Start konnte nicht abgesichert werden.")

source.write_text(text, encoding="utf-8")

check = source.read_text(encoding="utf-8")
required = [
    "remove(KEY_DOWNLOAD_ID)",
    "remove(KEY_DOWNLOAD_FILE)",
    ".commit()",
    "Consume the completed DownloadManager ID",
]
missing = [item for item in required if item not in check]
if missing:
    raise SystemExit("FEHLER: Update-Loop-Fix unvollständig: " + ", ".join(missing))

print("UPDATE INSTALL LOOP FIX: PASS")
print("Ein abgeschlossener Download kann nach dem App-Neustart nicht erneut installiert werden.")
