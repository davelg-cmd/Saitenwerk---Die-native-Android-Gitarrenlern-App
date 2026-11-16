#!/usr/bin/env python3
"""Prevent an APK installer from being relaunched after the app has been updated."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
source = root / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
if not source.is_file():
    raise SystemExit(f"FEHLER: AppUpdateManager.kt nicht gefunden: {source}")

text = source.read_text(encoding="utf-8")

# Consume the pending APK synchronously BEFORE handing control to Android's
# package installer. Doing it afterwards leaves a lifecycle/process-death race:
# onResume() can see the stale path and open the same installer a second time.
old_launch = """            activity.startActivity(install)
            prefs.edit().remove(KEY_PENDING_APK).commit()
"""
new_launch = """            // Atomar verbrauchen, bevor Android den Installationsdialog übernimmt.
            // So kann onResume() denselben APK-Pfad nach dem App-Neustart nicht erneut öffnen.
            val consumed = prefs.edit().remove(KEY_PENDING_APK).commit()
            if (!consumed) throw IllegalStateException("Installationsstatus konnte nicht zurückgesetzt werden.")
            try {
                activity.startActivity(install)
            } catch (e: Exception) {
                // Nur bei einem fehlgeschlagenen Start den Installationsversuch wieder freigeben.
                prefs.edit().putString(KEY_PENDING_APK, file.absolutePath).commit()
                throw e
            }
"""
if old_launch in text:
    text = text.replace(old_launch, new_launch, 1)
elif "Atomar verbrauchen, bevor Android den Installationsdialog übernimmt." in text:
    print("UPDATE INSTALL LOOP FIX: Installer-Status wird bereits vor dem Start verbraucht")
else:
    raise SystemExit("FEHLER: Erwartete Installer-Startsequenz nicht gefunden; Datei unverändert.")

# Keep DownloadManager state one-shot as well.
old_download = """            prefs.edit().putString(KEY_PENDING_APK, file.absolutePath).apply()
            installIfAllowed()
"""
new_download = """            val consumed = prefs.edit()
                .putString(KEY_PENDING_APK, file.absolutePath)
                .remove(KEY_DOWNLOAD_ID)
                .remove(KEY_DOWNLOAD_FILE)
                .commit()
            if (consumed) installIfAllowed()
"""
if old_download in text:
    text = text.replace(old_download, new_download, 1)
elif "Consume the completed DownloadManager ID BEFORE opening Android's installer." in text:
    print("UPDATE INSTALL LOOP FIX: DownloadManager-ID wird bereits vor dem Installer verbraucht")
else:
    raise SystemExit("FEHLER: DownloadManager-Abschlusssequenz nicht gefunden.")

old_clear = '            prefs.edit().remove(KEY_PENDING_APK).apply()'
new_clear = '            prefs.edit().remove(KEY_PENDING_APK).commit()'
if old_clear in text:
    text = text.replace(old_clear, new_clear, 1)

source.write_text(text, encoding="utf-8")
check = source.read_text(encoding="utf-8")
launch_pos = check.find("Atomar verbrauchen, bevor Android den Installationsdialog übernimmt.")
start_pos = check.find("activity.startActivity(install)", launch_pos)
clear_pos = check.find("prefs.edit().remove(KEY_PENDING_APK).commit()", launch_pos)
if launch_pos < 0 or start_pos < 0 or (clear_pos >= 0 and clear_pos < start_pos):
    raise SystemExit("FEHLER: Pending-APK wird nicht vor dem Installer-Start verbraucht.")
if "remove(KEY_DOWNLOAD_ID)" not in check or "remove(KEY_DOWNLOAD_FILE)" not in check:
    raise SystemExit("FEHLER: DownloadManager-Status wird nicht vollständig bereinigt.")

print("UPDATE INSTALL LOOP FIX: PASS")
print("Pending-APK wird vor dem Installer-Start synchron verbraucht; DownloadManager-ID bleibt einmalig.")
