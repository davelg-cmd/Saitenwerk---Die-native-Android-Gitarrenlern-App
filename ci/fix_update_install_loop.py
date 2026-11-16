#!/usr/bin/env python3
"""Prevent an APK installer from being relaunched after the app has been updated."""
from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
source = root / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
if not source.is_file():
    raise SystemExit(f"FEHLER: AppUpdateManager.kt nicht gefunden: {source}")

text = source.read_text(encoding="utf-8")

# A completed DownloadManager request must be one-shot.
if "Consume the completed DownloadManager ID BEFORE opening Android's installer." in text:
    if "remove(KEY_DOWNLOAD_ID)" not in text or "remove(KEY_DOWNLOAD_FILE)" not in text:
        raise SystemExit("FEHLER: DownloadManager-Status wird nicht vollständig bereinigt.")
    print("UPDATE: DownloadManager-ID wird bereits einmalig verbraucht.")
else:
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
    if old_download not in text:
        raise SystemExit("FEHLER: DownloadManager-Abschlusssequenz nicht gefunden.")
    text = text.replace(old_download, new_download, 1)
    print("UPDATE: DownloadManager-ID wird vor dem Installer verbraucht.")

# Crucial lifecycle fix: clear the pending path BEFORE launching the package
# installer, not after startActivity() returns.
marker = "Pending-APK vor dem Installer-Start atomar verbrauchen."
if marker not in text:
    match = re.search(r"(?m)^(\s*)activity\.startActivity\(install\)\s*$", text)
    if not match:
        raise SystemExit("FEHLER: activity.startActivity(install) wurde nicht gefunden.")
    indent = match.group(1)
    replacement = (
        f"{indent}// {marker}\n"
        f"{indent}val consumed = prefs.edit().remove(KEY_PENDING_APK).commit()\n"
        f'{indent}if (!consumed) throw IllegalStateException("Installationsstatus konnte nicht zurückgesetzt werden.")\n'
        f"{indent}try {{\n"
        f"{indent}    activity.startActivity(install)\n"
        f"{indent}}} catch (e: Exception) {{\n"
        f"{indent}    prefs.edit().putString(KEY_PENDING_APK, file.absolutePath).commit()\n"
        f"{indent}    throw e\n"
        f"{indent}}}"
    )
    text = text[:match.start()] + replacement + text[match.end():]
    # Remove the old post-launch cleanup if it immediately follows the launch block.
    tail_start = match.start() + len(replacement)
    tail = text[tail_start:]
    tail = re.sub(
        r"^(\s*)prefs\.edit\(\)\.remove\(KEY_PENDING_APK\)\.(?:apply|commit)\(\)\s*\n",
        "",
        tail,
        count=1,
    )
    text = text[:tail_start] + tail
    print("UPDATE: Pending-APK wird vor startActivity() synchron gelöscht.")
else:
    print("UPDATE: Pending-APK wird bereits vor startActivity() gelöscht.")

source.write_text(text, encoding="utf-8")
check = source.read_text(encoding="utf-8")
launch_pos = check.find(marker)
consume_pos = check.find("val consumed = prefs.edit().remove(KEY_PENDING_APK).commit()", launch_pos)
start_pos = check.find("activity.startActivity(install)", launch_pos)
if launch_pos < 0 or consume_pos < 0 or start_pos < 0 or consume_pos > start_pos:
    raise SystemExit("FEHLER: Pending-APK wird nicht vor dem Installer-Start verbraucht.")
if "remove(KEY_DOWNLOAD_ID)" not in check or "remove(KEY_DOWNLOAD_FILE)" not in check:
    raise SystemExit("FEHLER: DownloadManager-Status wird nicht vollständig bereinigt.")

print("UPDATE INSTALL LOOP FIX: PASS")
