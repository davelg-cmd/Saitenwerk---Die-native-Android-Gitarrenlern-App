#!/usr/bin/env python3
"""Add working manual and OAuth-backed automatic YouTube video linking to Songbook."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s = path.read_text(encoding="utf-8")

# Persist the selected video ID on the exact song row.
db_anchor = "    fun all(): List<SongbookSong> {"
db_method = r'''    fun updateYoutube(songId: Long, videoId: String) {
        db.execSQL(
            "UPDATE songs SET youtube_id=?, youtube_confidence=100 WHERE id=?",
            arrayOf(videoId, songId)
        )
    }
'''
if "fun updateYoutube(songId: Long, videoId: String)" not in s:
    if db_anchor not in s:
        raise SystemExit("FEHLER: SongbookDb.all() Einfügepunkt nicht gefunden.")
    s = s.replace(db_anchor, db_method + db_anchor, 1)

# Always expose manual linking, independent of Google OAuth or API access.
ui_anchor = "        root.addView(playerCard)\n        val playback="
ui_block = r'''        root.addView(playerCard)
        val youtubeActions = LinearLayout(requireContext()).apply { orientation = LinearLayout.HORIZONTAL }
        val automaticLink = button("Automatisch finden")
        automaticLink.setOnClickListener { searchYoutubeForSong(song) }
        val manualLink = button("Link manuell eintragen")
        manualLink.setOnClickListener { showManualYoutubeLink(song) }
        youtubeActions.addView(automaticLink, LinearLayout.LayoutParams(0, dp(48), 1f))
        youtubeActions.addView(manualLink, LinearLayout.LayoutParams(0, dp(48), 1f))
        root.addView(youtubeActions)
        val playback='''
if "Link manuell eintragen" not in s:
    if ui_anchor not in s:
        raise SystemExit("FEHLER: Songdetail-Einfügepunkt für YouTube-Aktionen nicht gefunden.")
    s = s.replace(ui_anchor, ui_block, 1)

methods_anchor = "    private fun openYoutube(song: SongbookSong) {"
methods = r'''
    private fun showManualYoutubeLink(song: SongbookSong) {
        val input = EditText(requireContext()).apply {
            hint = "YouTube-Link oder 11-stellige Video-ID"
            setSingleLine(true)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
            setText(song.youtubeId?.let { "https://youtu.be/" + it } ?: "")
            setSelection(text.length)
        }
        AlertDialog.Builder(requireContext())
            .setTitle("YouTube-Video manuell verknüpfen")
            .setMessage("Füge einen YouTube-Link ein (youtu.be, watch, shorts oder embed). SaitenWerk speichert die Video-ID direkt bei diesem Song.")
            .setView(input)
            .setNegativeButton("Abbrechen", null)
            .setPositiveButton("Verknüpfen") { _, _ ->
                val videoId = parseYoutubeVideoId(input.text?.toString().orEmpty())
                if (videoId == null) {
                    Toast.makeText(requireContext(), "Ungültiger YouTube-Link. Bitte einen vollständigen Video-Link oder eine gültige Video-ID eintragen.", Toast.LENGTH_LONG).show()
                } else {
                    persistYoutubeLink(song, videoId)
                }
            }
            .show()
    }

    private fun parseYoutubeVideoId(value: String): String? {
        val clean = value.trim()
        if (clean.matches(Regex("""[A-Za-z0-9_-]{11}"""))) return clean
        val match = Regex(
            """(?:youtu\.be/|youtube\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/))([A-Za-z0-9_-]{11})"""
        ).find(clean) ?: return null
        return match.groupValues.getOrNull(1)
    }

    private fun persistYoutubeLink(song: SongbookSong, videoId: String) {
        db.updateYoutube(song.id, videoId)
        val updated = song.copy(youtubeId = videoId, youtubeConfidence = 100)
        Toast.makeText(requireContext(), "YouTube-Video wurde diesem Song zugeordnet.", Toast.LENGTH_SHORT).show()
        showSong(updated)
    }

    private fun searchYoutubeForSong(song: SongbookSong) {
        val token = youtubeAccessToken
        if (token.isNullOrBlank()) {
            AlertDialog.Builder(requireContext())
                .setTitle("YouTube-Zugriff benötigt")
                .setMessage("Für die automatische Suche muss dein YouTube-Konto zuerst verbunden werden. Die manuelle Verknüpfung funktioniert unabhängig davon.")
                .setNegativeButton("Abbrechen", null)
                .setPositiveButton("YouTube verbinden") { _, _ -> authorizeYoutube() }
                .show()
            return
        }
        Toast.makeText(requireContext(), "Suche passende YouTube-Videos …", Toast.LENGTH_SHORT).show()
        executor.execute {
            val matches = mutableListOf<Pair<String, String>>()
            var failure: String? = null
            var connection: java.net.HttpURLConnection? = null
            try {
                val query = java.net.URLEncoder.encode(song.artist + " " + song.title, "UTF-8")
                val url = java.net.URL(
                    "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=8&q=" + query
                )
                connection = (url.openConnection() as java.net.HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 12000
                    readTimeout = 15000
                    setRequestProperty("Authorization", "Bearer " + token)
                    setRequestProperty("Accept", "application/json")
                }
                val code = connection.responseCode
                val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
                if (code !in 200..299) {
                    failure = when (code) {
                        401 -> "Die YouTube-Berechtigung ist abgelaufen. Bitte verbinde YouTube erneut."
                        403 -> "YouTube hat die Suche abgelehnt (Berechtigung oder API-Kontingent)."
                        else -> "YouTube-Suche fehlgeschlagen (HTTP " + code + ")."
                    }
                } else {
                    val items = org.json.JSONObject(body).optJSONArray("items")
                    if (items != null) {
                        for (i in 0 until items.length()) {
                            val item = items.optJSONObject(i) ?: continue
                            val id = item.optJSONObject("id")?.optString("videoId").orEmpty()
                            val snippet = item.optJSONObject("snippet")
                            val title = snippet?.optString("title").orEmpty()
                            val channel = snippet?.optString("channelTitle").orEmpty()
                            if (id.matches(Regex("""[A-Za-z0-9_-]{11}"""))) {
                                matches += id to (title + if (channel.isBlank()) "" else " · " + channel)
                            }
                        }
                    }
                }
            } catch (t: Throwable) {
                failure = "YouTube-Suche nicht erreichbar: " + (t.message ?: "Netzwerkfehler")
            } finally {
                connection?.disconnect()
            }
            activity?.runOnUiThread {
                if (!isAdded) return@runOnUiThread
                if (matches.isEmpty()) {
                    AlertDialog.Builder(requireContext())
                        .setTitle("Keine passenden Videos gefunden")
                        .setMessage(failure ?: "Die YouTube-Suche hat keine Videos geliefert. Du kannst den Link stattdessen manuell eintragen.")
                        .setPositiveButton("Link manuell eintragen") { _, _ -> showManualYoutubeLink(song) }
                        .setNegativeButton("Schließen", null)
                        .show()
                } else {
                    val labels = matches.map { it.second }.toTypedArray()
                    AlertDialog.Builder(requireContext())
                        .setTitle("Passendes YouTube-Video auswählen")
                        .setItems(labels) { _, which -> persistYoutubeLink(song, matches[which].first) }
                        .setNegativeButton("Abbrechen", null)
                        .show()
                }
            }
        }
    }

'''
if "private fun showManualYoutubeLink(song: SongbookSong)" not in s:
    if methods_anchor not in s:
        raise SystemExit("FEHLER: openYoutube()-Einfügepunkt für YouTube-Linkmethoden nicht gefunden.")
    s = s.replace(methods_anchor, methods + methods_anchor, 1)

# A persisted 'connected' flag is not an access token. Do not claim an active
# API session after process restart; OAuth is requested again when needed.
s = s.replace(
    '        youtubeConnected = youtubePrefs.getBoolean("connected", false)\n        youtubeChannelName = youtubePrefs.getString("channel_name", null)',
    '        youtubeConnected = false\n        youtubeChannelName = youtubePrefs.getString("channel_name", null)',
    1
)

required = [
    "fun updateYoutube(songId: Long, videoId: String)",
    "Link manuell eintragen",
    "private fun parseYoutubeVideoId(value: String): String?",
    "private fun searchYoutubeForSong(song: SongbookSong)",
    "youtube/v3/search?part=snippet&type=video",
    "persistYoutubeLink(song, matches[which].first)",
]
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit("FEHLER: YouTube-Verknüpfung unvollständig: " + ", ".join(missing))

path.write_text(s, encoding="utf-8")
(root / "YOUTUBE_SONG_LINKING_V2.txt").write_text(
    "SaitenWerk YouTube Song Linking V2\n"
    "Manual URL/video-ID parsing and persistence per song; OAuth-backed YouTube Data API search with candidate selection.\n",
    encoding="utf-8"
)
print("YOUTUBE-SONG-LINKING-V2: PASS")
