#!/usr/bin/env python3
"""Treat an APK already installed during the Android installer round-trip as completed."""
from pathlib import Path
import os

p = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
s = p.read_text(encoding="utf-8")

old = '''        val archiveCode = if (Build.VERSION.SDK_INT >= 28) archive.longVersionCode else archive.versionCode.toLong()
        val archivePackage = archive.packageName
        val currentCode = installedVersionCode()
        if (archivePackage != activity.packageName || archiveCode <= currentCode) {
            prefs.edit().remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).remove(KEY_PENDING_APK).commit()
            file.delete()
            showMessage("Update-Datei stimmt nicht", "Installiert: $currentCode · Download: $archiveCode · Paket: $archivePackage. Die APK gehört nicht zu Saitenwerk oder ist nicht neuer.")
            return
        }
'''
new = '''        val archiveCode = if (Build.VERSION.SDK_INT >= 28) archive.longVersionCode else archive.versionCode.toLong()
        val archivePackage = archive.packageName
        val currentCode = installedVersionCode()

        // The Android installer can finish the package replacement before this process
        // handles a delayed DownloadManager callback / resume event. In that case both
        // codes are equal: the update is already installed, not an invalid APK.
        if (archivePackage != activity.packageName) {
            prefs.edit().remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).remove(KEY_PENDING_APK).commit()
            file.delete()
            showMessage("Update-Datei stimmt nicht", "Installiert: $currentCode · Download: $archiveCode · Paket: $archivePackage. Die APK gehört nicht zu Saitenwerk.")
            return
        }
        if (archiveCode <= currentCode) {
            prefs.edit().remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).remove(KEY_PENDING_APK).commit()
            file.delete()
            return
        }
'''
if old not in s:
    raise SystemExit("FEHLER: Versionsvergleich in completeDownloadIfReady nicht gefunden.")
s = s.replace(old, new, 1)

old_pending = '''        if (pending != null) {
            val file = File(pending)
            if (!file.exists() || !isNewerApk(file)) {
                prefs.edit().remove(KEY_PENDING_APK).commit()
            } else {
                installIfAllowed()
                return
            }
        }
'''
new_pending = '''        if (pending != null) {
            val file = File(pending)
            if (!file.exists()) {
                prefs.edit().remove(KEY_PENDING_APK).commit()
            } else {
                val archive = readApkInfo(file)
                val archiveCode = archive?.let {
                    if (Build.VERSION.SDK_INT >= 28) it.longVersionCode else it.versionCode.toLong()
                } ?: -1L
                val currentCode = installedVersionCode()
                if (archive?.packageName == activity.packageName && archiveCode <= currentCode) {
                    // Installer already completed (or a newer build is installed); consume stale state.
                    prefs.edit().remove(KEY_PENDING_APK).commit()
                    file.delete()
                } else if (archive?.packageName == activity.packageName && archiveCode > currentCode) {
                    installIfAllowed()
                    return
                } else {
                    prefs.edit().remove(KEY_PENDING_APK).commit()
                    file.delete()
                }
            }
        }
'''
if old_pending not in s:
    raise SystemExit("FEHLER: resumePendingInstall-Block nicht gefunden.")
s = s.replace(old_pending, new_pending, 1)

p.write_text(s, encoding="utf-8")
for token in [
    "The Android installer can finish the package replacement",
    "if (archiveCode <= currentCode)",
    "Installer already completed (or a newer build is installed)",
]:
    if token not in s:
        raise SystemExit("FEHLER: Installationsabschluss-Korrektur fehlt: " + token)
print("UPDATE-ABSCHLUSS: PASS")
