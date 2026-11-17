#!/usr/bin/env python3
"""Hardens the beta updater against stale/pending APK re-install loops."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
manager = root / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"

if not manager.is_file() or not main.is_file():
    raise SystemExit("FEHLER: Update- oder MainActivity-Quelle fehlt.")

s = manager.read_text(encoding="utf-8")

old_resume = '''    fun resumePendingInstall() {
        if (prefs.getString(KEY_PENDING_APK, null) != null) {
            installIfAllowed()
            return
        }
        val id = prefs.getLong(KEY_DOWNLOAD_ID, -1L)
        if (id >= 0L) {
            val manager = activity.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            manager.query(DownloadManager.Query().setFilterById(id)).use { cursor ->
                if (cursor.moveToFirst() && cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)) == DownloadManager.STATUS_SUCCESSFUL) {
                    completeDownloadIfReady(id)
                }
            }
        }
    }
'''
new_resume = '''    fun resumePendingInstall() {
        val pending = prefs.getString(KEY_PENDING_APK, null)
        if (pending != null) {
            val file = File(pending)
            if (!file.exists() || !isNewerApk(file)) {
                prefs.edit().remove(KEY_PENDING_APK).commit()
            } else {
                installIfAllowed()
                return
            }
        }

        val id = prefs.getLong(KEY_DOWNLOAD_ID, -1L)
        if (id >= 0L) {
            val manager = activity.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            manager.query(DownloadManager.Query().setFilterById(id)).use { cursor ->
                if (cursor.moveToFirst() && cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)) == DownloadManager.STATUS_SUCCESSFUL) {
                    completeDownloadIfReady(id)
                }
            }
        }
    }

    private fun isNewerApk(file: File): Boolean {
        return try {
            val archive = if (Build.VERSION.SDK_INT >= 33) {
                activity.packageManager.getPackageArchiveInfo(
                    file.absolutePath,
                    android.content.pm.PackageManager.PackageInfoFlags.of(0)
                )
            } else {
                @Suppress("DEPRECATION")
                activity.packageManager.getPackageArchiveInfo(file.absolutePath, 0)
            } ?: return false
            val remoteCode = if (Build.VERSION.SDK_INT >= 28) archive.longVersionCode else archive.versionCode.toLong()
            val currentCode = installedVersionCode()
            remoteCode > currentCode && archive.packageName == activity.packageName
        } catch (_: Exception) {
            false
        }
    }
'''
if old_resume not in s:
    raise SystemExit("FEHLER: resumePendingInstall-Sequenz nicht gefunden.")
s = s.replace(old_resume, new_resume, 1)

old_complete = '''        if (file.exists() && file.length() > 0L) {
            val consumed = prefs.edit()
                .putString(KEY_PENDING_APK, file.absolutePath)
                .remove(KEY_DOWNLOAD_ID)
                .remove(KEY_DOWNLOAD_FILE)
                .commit()
            if (consumed) installIfAllowed()
        }
'''
new_complete = '''        if (file.exists() && file.length() > 0L) {
            if (!isNewerApk(file)) {
                prefs.edit()
                    .remove(KEY_DOWNLOAD_ID)
                    .remove(KEY_DOWNLOAD_FILE)
                    .remove(KEY_PENDING_APK)
                    .commit()
                file.delete()
                showMessage("Update bereits installiert", "Die heruntergeladene APK ist nicht neuer als die installierte Version.")
                return
            }
            val consumed = prefs.edit()
                .putString(KEY_PENDING_APK, file.absolutePath)
                .remove(KEY_DOWNLOAD_ID)
                .remove(KEY_DOWNLOAD_FILE)
                .commit()
            if (consumed) installIfAllowed()
        }
'''
if old_complete not in s:
    raise SystemExit("FEHLER: Download-Abschlusssequenz nicht gefunden.")
s = s.replace(old_complete, new_complete, 1)

old_launch = '''            try {
                activity.startActivity(install)
            } catch (e: Exception) {
                prefs.edit().putString(KEY_PENDING_APK, file.absolutePath).commit()
                throw e
            }        } catch (_: Exception) {'''
new_launch = '''            try {
                activity.startActivity(install)
            } catch (e: Exception) {
                prefs.edit().putString(KEY_PENDING_APK, file.absolutePath).commit()
                throw e
            }
            // Die APK-Datei muss bestehen bleiben, bis Android sie installiert hat.
        } catch (_: Exception) {'''
if old_launch not in s:
    raise SystemExit("FEHLER: Installer-Startsequenz nicht gefunden.")
s = s.replace(old_launch, new_launch, 1)

manager.write_text(s, encoding="utf-8")

m = main.read_text(encoding="utf-8")
if "Updates werden ausschließlich auf ausdrücklichen Wunsch in den Einstellungen geprüft." not in m:
    m = m.replace(
        "appUpdateManager = AppUpdateManager(this)",
        "appUpdateManager = AppUpdateManager(this)\n        // Updates werden ausschließlich auf ausdrücklichen Wunsch in den Einstellungen geprüft."
    )
main.write_text(m, encoding="utf-8")

check = manager.read_text(encoding="utf-8")
for token in ["fun isNewerApk(file: File)", "remoteCode > currentCode", "archive.packageName == activity.packageName"]:
    if token not in check:
        raise SystemExit("FEHLER: Update-Härtung fehlt: " + token)

launch = check.find("activity.startActivity(install)")
if launch < 0:
    raise SystemExit("FEHLER: Android-Installer wird nicht gestartet.")
install_block = check[launch:check.find("} catch (_: Exception)", launch)]
if "file.delete()" in install_block:
    raise SystemExit("FEHLER: APK-Datei wird direkt nach dem Installer-Start gelöscht.")
if "remove(KEY_PENDING_APK).commit()" not in check[:launch]:
    raise SystemExit("FEHLER: Pending-Status wird nicht vor dem Installer-Start verbraucht.")
print("UPDATE LOOP HARDENING: PASS")
