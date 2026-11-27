#!/usr/bin/env python3
"""Add per-user YouTube OAuth authorization to the intelligent Songbook."""
from pathlib import Path
import os, re

ROOT = Path(os.environ["PROJECT_DIR"])
SONGBOOK = ROOT / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
GRADLE = ROOT / "app/build.gradle.kts"
MARKER = ROOT / "YOUTUBE_OAUTH_SONGBOOK_V1.txt"

if not SONGBOOK.is_file():
    raise SystemExit("FEHLER: IntelligentSongbook.kt fehlt.")

g = GRADLE.read_text(encoding="utf-8")
if 'com.google.android.gms:play-services-auth:' not in g:
    marker = 'dependencies {'
    if marker not in g:
        raise SystemExit("FEHLER: dependencies-Block fehlt.")
    g = g.replace(marker, marker + '\n    implementation("com.google.android.gms:play-services-auth:22.0.0")', 1)
    GRADLE.write_text(g, encoding="utf-8")

s = SONGBOOK.read_text(encoding="utf-8")

imports = [
    'import android.app.Activity',
    'import androidx.activity.result.IntentSenderRequest',
    'import com.google.android.gms.auth.api.identity.AuthorizationRequest',
    'import com.google.android.gms.auth.api.identity.Identity',
    'import com.google.android.gms.common.api.ApiException',
    'import com.google.android.gms.common.api.Scope',
]
anchor = 'import androidx.activity.result.contract.ActivityResultContracts'
for imp in imports:
    if imp not in s:
        s = s.replace(anchor, anchor + '\n' + imp, 1)

field_anchor = '    private val executor = Executors.newSingleThreadExecutor()'
fields = '''    private val youtubePrefs by lazy {
        requireContext().getSharedPreferences("saitenwerk_youtube", Context.MODE_PRIVATE)
    }
    private var youtubeAccessToken: String? = null
    private var youtubeConnected = false
    private var youtubeChannelName: String? = null
    private val youtubeAuthLauncher =
        registerForActivityResult(ActivityResultContracts.StartIntentSenderForResult()) { result ->
            if (result.resultCode != Activity.RESULT_OK) {
                Toast.makeText(requireContext(), "YouTube-Verbindung abgebrochen.", Toast.LENGTH_SHORT).show()
                return@registerForActivityResult
            }
            try {
                val authorizationResult =
                    Identity.getAuthorizationClient(requireContext())
                        .getAuthorizationResultFromIntent(result.data)
                youtubeAccessToken = authorizationResult.accessToken
                youtubeConnected = !youtubeAccessToken.isNullOrBlank()
                if (!youtubeConnected) {
                    Toast.makeText(requireContext(), "Keine YouTube-Berechtigung erhalten.", Toast.LENGTH_LONG).show()
                    return@registerForActivityResult
                }
                youtubePrefs.edit().putBoolean("connected", true).apply()
                fetchYoutubeChannel()
            } catch (e: ApiException) {
                Toast.makeText(requireContext(), "YouTube-Autorisierung fehlgeschlagen: ${e.statusCode}", Toast.LENGTH_LONG).show()
            } catch (t: Throwable) {
                Toast.makeText(requireContext(), "YouTube-Autorisierung fehlgeschlagen.", Toast.LENGTH_LONG).show()
            }
        }
'''
if 'private val youtubeAuthLauncher' not in s:
    s = s.replace(field_anchor, field_anchor + '\n' + fields, 1)

oncreate_anchor = '        db = SongbookDb(requireContext())'
if 'youtubeConnected = youtubePrefs.getBoolean("connected", false)' not in s:
    s = s.replace(oncreate_anchor, oncreate_anchor + '\n        youtubeConnected = youtubePrefs.getBoolean("connected", false)\n        youtubeChannelName = youtubePrefs.getString("channel_name", null)', 1)

home_anchor = '        root.addView(import)'
home_block = '''        val youtube = button(if (youtubeConnected) {
            "✓ YouTube verbunden" + (youtubeChannelName?.let { " · $it" } ?: "")
        } else {
            "▶ YouTube verbinden"
        })
        youtube.setOnClickListener {
            if (youtubeConnected) {
                AlertDialog.Builder(requireContext())
                    .setTitle("YouTube verbunden")
                    .setMessage(
                        "Saitenwerk ist für dein YouTube-Konto autorisiert. " +
                        "Die App nutzt die Berechtigung nur für YouTube-Funktionen im Songbook."
                    )
                    .setNegativeButton("Verbindung lokal trennen") {
                        _, _ ->
                        youtubeAccessToken = null
                        youtubeConnected = false
                        youtubeChannelName = null
                        youtubePrefs.edit().clear().apply()
                        buildHome()
                    }
                    .setPositiveButton("OK", null)
                    .show()
            } else {
                authorizeYoutube()
            }
        }
        root.addView(youtube)
'''
if '▶ YouTube verbinden' not in s:
    s = s.replace(home_anchor, home_anchor + '\n' + home_block, 1)

methods_anchor = '    private fun openYoutube(song: SongbookSong) {'
methods = '''    private fun authorizeYoutube() {
        val requestedScopes = listOf(
            Scope("https://www.googleapis.com/auth/youtube.readonly")
        )
        val request = AuthorizationRequest.builder()
            .setRequestedScopes(requestedScopes)
            .build()

        Identity.getAuthorizationClient(requireContext())
            .authorize(request)
            .addOnSuccessListener { authorizationResult ->
                if (authorizationResult.hasResolution()) {
                    val pendingIntent = authorizationResult.pendingIntent
                    if (pendingIntent == null) {
                        Toast.makeText(requireContext(), "Google konnte den Autorisierungsdialog nicht öffnen.", Toast.LENGTH_LONG).show()
                    } else {
                        youtubeAuthLauncher.launch(
                            IntentSenderRequest.Builder(pendingIntent.intentSender).build()
                        )
                    }
                } else {
                    youtubeAccessToken = authorizationResult.accessToken
                    youtubeConnected = !youtubeAccessToken.isNullOrBlank()
                    if (youtubeConnected) {
                        youtubePrefs.edit().putBoolean("connected", true).apply()
                        fetchYoutubeChannel()
                    } else {
                        Toast.makeText(requireContext(), "YouTube-Berechtigung wurde nicht erteilt.", Toast.LENGTH_LONG).show()
                    }
                }
            }
            .addOnFailureListener {
                Toast.makeText(requireContext(), "YouTube-Autorisierung konnte nicht gestartet werden.", Toast.LENGTH_LONG).show()
            }
    }

    private fun fetchYoutubeChannel() {
        val token = youtubeAccessToken ?: return
        executor.execute {
            try {
                val url = java.net.URL("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true")
                val connection = (url.openConnection() as java.net.HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 10000
                    readTimeout = 10000
                    setRequestProperty("Authorization", "Bearer $token")
                    setRequestProperty("Accept", "application/json")
                }
                val code = connection.responseCode
                val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                val body = stream?.bufferedReader()?.use { it.readText() } ?: ""
                connection.disconnect()
                if (code !in 200..299) {
                    requireActivity().runOnUiThread {
                        youtubePrefs.edit().putBoolean("connected", true).apply()
                        Toast.makeText(
                            requireContext(),
                            "YouTube ist verbunden. Kanalinformationen konnten nicht gelesen werden.",
                            Toast.LENGTH_LONG
                        ).show()
                        buildHome()
                    }
                    return@execute
                }
                val items = org.json.JSONObject(body).optJSONArray("items")
                val name = items?.optJSONObject(0)?.optJSONObject("snippet")?.optString("title").orEmpty()
                youtubeChannelName = name.ifBlank { null }
                youtubePrefs.edit().putBoolean("connected", true).apply {
                    if (name.isBlank()) remove("channel_name") else putString("channel_name", name)
                }.apply()
                requireActivity().runOnUiThread {
                    Toast.makeText(
                        requireContext(),
                        if (name.isBlank()) "YouTube erfolgreich verbunden." else "YouTube verbunden mit: $name",
                        Toast.LENGTH_LONG
                    ).show()
                    buildHome()
                }
            } catch (t: Throwable) {
                requireActivity().runOnUiThread {
                    Toast.makeText(requireContext(), "YouTube verbunden, Kanal konnte nicht geladen werden.", Toast.LENGTH_LONG).show()
                    buildHome()
                }
            }
        }
    }

'''
if 'private fun authorizeYoutube()' not in s:
    s = s.replace(methods_anchor, methods + methods_anchor, 1)

s = s.replace(
    '        val query=Uri.encode(song.artist + " " + song.title + " guitar")',
    '        val query=Uri.encode(song.artist + " " + song.title + " guitar")'
)

SONGBOOK.write_text(s, encoding="utf-8")
MARKER.write_text(
    "Saitenwerk YouTube OAuth V1\n"
    "Per-user Google/YouTube authorization via Google Identity AuthorizationClient.\n"
    "Requested scope: youtube.readonly. Short-lived access token is kept in memory; connection state/channel label is local.\n"
    "No YouTube password is requested or stored.\n",
    encoding="utf-8"
)
print("YOUTUBE-OAUTH-SONGBOOK: PASS")
