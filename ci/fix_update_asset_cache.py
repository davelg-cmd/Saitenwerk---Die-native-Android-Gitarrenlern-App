#!/usr/bin/env python3
"""Avoid stale GitHub release APKs being served after beta-latest asset replacement."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
s = p.read_text(encoding="utf-8")

old = '                val url = apkUrl ?: throw IllegalStateException("Keine APK im Release gefunden")'
new = '''                val baseUrl = apkUrl ?: throw IllegalStateException("Keine APK im Release gefunden")
                // beta-latest reuses one asset URL. Add versionCode as a cache-buster:
                // otherwise a CDN/proxy may return the previous APK after --clobber.
                val separator = if (baseUrl.contains("?")) "&" else "?"
                val url = baseUrl + separator + "saitenwerk_version=" + remoteCode'''
if "saitenwerk_version=" not in s:
    if old not in s:
        raise SystemExit("FEHLER: APK-Download-URL-Sequenz nicht gefunden.")
    s = s.replace(old, new, 1)

old_msg = 'showMessage("Update bereits installiert", "Die heruntergeladene APK ist nicht neuer als die installierte Version.")'
new_msg = '''val archive = readApkInfo(file)
                val archiveCode = archive?.let {
                    if (Build.VERSION.SDK_INT >= 28) it.longVersionCode else it.versionCode.toLong()
                } ?: -1L
                val archivePackage = archive?.packageName ?: "unbekannt"
                showMessage(
                    "Update-Datei stimmt nicht",
                    "Installiert: " + installedVersionCode() + " · Download: " + archiveCode +
                        " · Paket: " + archivePackage +
                        ". Die Datei ist veraltet oder gehört nicht zu Saitenwerk. Bitte erneut nach Updates suchen."
                )'''
if old_msg in s:
    s = s.replace(old_msg, new_msg, 1)

marker = '    private fun isNewerApk(file: File): Boolean {'
helper = '''    private fun readApkInfo(file: File): android.content.pm.PackageInfo? {
        return try {
            if (Build.VERSION.SDK_INT >= 33) {
                activity.packageManager.getPackageArchiveInfo(
                    file.absolutePath,
                    android.content.pm.PackageManager.PackageInfoFlags.of(0)
                )
            } else {
                @Suppress("DEPRECATION")
                activity.packageManager.getPackageArchiveInfo(file.absolutePath, 0)
            }
        } catch (_: Exception) {
            null
        }
    }

'''
if "private fun readApkInfo(file: File)" not in s:
    if marker not in s:
        raise SystemExit("FEHLER: APK-Versionsprüfung nicht gefunden.")
    s = s.replace(marker, helper + marker, 1)

start = s.index(marker)
end = s.index('\n    private fun completeDownloadIfReady', start)
s = s[:start] + '''    private fun isNewerApk(file: File): Boolean {
        val archive = readApkInfo(file) ?: return false
        val remoteCode = if (Build.VERSION.SDK_INT >= 28) archive.longVersionCode else archive.versionCode.toLong()
        return remoteCode > installedVersionCode() && archive.packageName == activity.packageName
    }
''' + s[end:]

p.write_text(s, encoding="utf-8")
for token in ["saitenwerk_version=", "private fun readApkInfo(file: File)", "archiveCode"]:
    if token not in s:
        raise SystemExit("FEHLER: Cache-/Diagnosekorrektur fehlt: " + token)
print("UPDATE-ASSET-CACHE-BUSTING: PASS")
