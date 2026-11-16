from pathlib import Path
import os

p = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("/** Checks the Alpha channel's GitHub release and offers an Android-approved APK install. */", "/** Checks the current Beta release and offers an Android-approved APK install. */")
s = s.replace("fetchAlphaRelease()", "fetchBetaRelease()")
s = s.replace("Kein veröffentlichter Alpha-7-Release gefunden", "Kein veröffentlichter Beta-Release gefunden")
s = s.replace("Neue Alpha-Version wird heruntergeladen", "Neue Beta-Version wird heruntergeladen")
a = s.index("    private fun fetchBetaRelease(): JSONObject? {")
b = s.index("    private fun showMessage", a)
method = '''    private fun fetchBetaRelease(): JSONObject? {
        val connection = (URL(RELEASES_API).openConnection() as HttpURLConnection).apply {
            connectTimeout = 15000
            readTimeout = 15000
            instanceFollowRedirects = true
            requestMethod = "GET"
            setRequestProperty("Accept", "application/vnd.github+json")
            setRequestProperty("X-GitHub-Api-Version", "2022-11-28")
            setRequestProperty("User-Agent", "Saitenwerk-Android-App")
            setRequestProperty("Cache-Control", "no-cache")
        }
        return try {
            val code = connection.responseCode
            if (code !in 200..299) {
                val detail = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                throw IllegalStateException("GitHub antwortet mit HTTP " + code + if (detail.isNotBlank()) ": " + detail else "")
            }
            val release = JSONObject(connection.inputStream.bufferedReader().use { it.readText() })
            if (release.optString("tag_name") != RELEASE_TAG || release.optBoolean("draft", false)) null else release
        } finally {
            connection.disconnect()
        }
    }

'''
s = s[:a] + method + s[b:]
s = s.replace('''        private const val RELEASES_API = "https://api.github.com/repos/davelg-cmd/Saitenwerk---Die-native-Android-Gitarrenlern-App/releases?per_page=20"
        private const val RELEASE_TAG = "alpha-latest"
        private const val APK_NAME = "saitenwerk-alpha7.apk"
''','''        private const val RELEASES_API = "https://api.github.com/repos/davelg-cmd/Saitenwerk---Die-native-Android-Gitarrenlern-App/releases/tags/beta-latest"
        private const val RELEASE_TAG = "beta-latest"
        private const val APK_NAME = "saitenwerk-beta.apk"
''')
if "alpha-latest" in s or "saitenwerk-alpha7.apk" in s:
    raise SystemExit("Update-Fix unvollständig: Alpha-Release-Konfiguration gefunden")
p.write_text(s, encoding="utf-8")
print("UPDATE-FIX PASS: App prüft beta-latest und lädt saitenwerk-beta.apk")
