#!/usr/bin/env python3
"""Harden beta APK completion handling and report the real downloaded file metadata."""
from pathlib import Path
import os

p = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
s = p.read_text(encoding="utf-8")
start = s.index("    private fun completeDownloadIfReady(id: Long) {")
end = s.index("\n    fun dispose()", start)
method = r'''    private fun completeDownloadIfReady(id: Long) {
        if (id != prefs.getLong(KEY_DOWNLOAD_ID, -2L)) return

        val dm = activity.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        var status = -1
        var reason = 0
        dm.query(DownloadManager.Query().setFilterById(id)).use { cursor ->
            if (!cursor.moveToFirst()) return
            status = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS))
            reason = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON))
        }

        val name = prefs.getString(KEY_DOWNLOAD_FILE, APK_NAME) ?: APK_NAME
        val file = File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), name)
        if (status == DownloadManager.STATUS_FAILED) {
            prefs.edit().remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).remove(KEY_PENDING_APK).commit()
            if (file.exists()) file.delete()
            showMessage("APK-Download fehlgeschlagen", "Android DownloadManager meldet Fehlercode $reason. Bitte erneut nach Updates suchen.")
            return
        }
        if (status != DownloadManager.STATUS_SUCCESSFUL) return
        if (!file.exists() || file.length() <= 0L) {
            prefs.edit().remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).remove(KEY_PENDING_APK).commit()
            showMessage("APK-Download unvollständig", "Android meldet einen erfolgreichen Download, aber die APK-Datei fehlt oder ist leer.")
            return
        }

        // Read metadata before cleanup; the previous implementation deleted the file first
        // and consequently always displayed Download -1 / Paket unbekannt.
        val archive = readApkInfo(file)
        if (archive == null) {
            val size = file.length()
            val header = try {
                file.inputStream().use { input ->
                    val bytes = ByteArray(4)
                    val count = input.read(bytes)
                    if (count > 0) bytes.take(count).joinToString("") { "%02X".format(it) } else "leer"
                }
            } catch (_: Exception) { "nicht lesbar" }
            prefs.edit().remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).remove(KEY_PENDING_APK).commit()
            file.delete()
            showMessage("Ungültige Update-Datei", "Android kann die Datei nicht als APK lesen. Größe: $size Bytes · Dateikopf: $header. Bitte erneut nach Updates suchen.")
            return
        }

        val archiveCode = if (Build.VERSION.SDK_INT >= 28) archive.longVersionCode else archive.versionCode.toLong()
        val archivePackage = archive.packageName
        val currentCode = installedVersionCode()
        if (archivePackage != activity.packageName || archiveCode <= currentCode) {
            prefs.edit().remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).remove(KEY_PENDING_APK).commit()
            file.delete()
            showMessage("Update-Datei stimmt nicht", "Installiert: $currentCode · Download: $archiveCode · Paket: $archivePackage. Die APK gehört nicht zu Saitenwerk oder ist nicht neuer.")
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
s = s[:start] + method + s[end:]

# Remove an old destination before enqueueing so a failed request cannot leave stale bytes.
needle = '    private fun download(url: String, fileName: String = APK_NAME) {\n        try {\n'
replacement = '''    private fun download(url: String, fileName: String = APK_NAME) {
        try {
            val destination = File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), fileName)
            if (destination.exists() && !destination.delete()) {
                throw IllegalStateException("Eine alte Update-Datei konnte nicht entfernt werden.")
            }
            prefs.edit().remove(KEY_PENDING_APK).remove(KEY_DOWNLOAD_ID).remove(KEY_DOWNLOAD_FILE).commit()
'''
if "Eine alte Update-Datei konnte nicht entfernt werden." not in s:
    if needle not in s:
        raise SystemExit("FEHLER: Download-Funktion nicht gefunden.")
    s = s.replace(needle, replacement, 1)

# Android DownloadManager sends ACTION_DOWNLOAD_COMPLETE from its own provider process.
# RECEIVER_NOT_EXPORTED can suppress that cross-package system broadcast on Android 13+,
# leaving a successful download without the app ever opening the installer.
old_receiver = "activity.registerReceiver(downloadReceiver, filter, Context.RECEIVER_NOT_EXPORTED)"
new_receiver = "activity.registerReceiver(downloadReceiver, filter, Context.RECEIVER_EXPORTED)"
if old_receiver in s:
    s = s.replace(old_receiver, new_receiver, 1)
elif new_receiver not in s:
    raise SystemExit("FEHLER: DownloadManager-Empfängerregistrierung nicht gefunden.")
if s.count(new_receiver) != 1:
    raise SystemExit("FEHLER: DownloadManager-Empfänger muss exakt einmal exportiert registriert sein.")

p.write_text(s, encoding="utf-8")
for token in ["Context.RECEIVER_EXPORTED", "DownloadManager.STATUS_FAILED", "Dateikopf: $header", "val archive = readApkInfo(file)", "Eine alte Update-Datei konnte nicht entfernt werden."]:
    if token not in s:
        raise SystemExit("FEHLER: Update-Diagnose fehlt: " + token)
print("UPDATE-DOWNLOAD-VALIDIERUNG: PASS")
