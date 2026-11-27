#!/usr/bin/env python3
"""Use a PDF table of contents as the authoritative song index when available."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
songbook = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s = songbook.read_text(encoding="utf-8")

start = s.index("object SongbookParser {")
end = s.index("\nclass SongbookFragment : Fragment() {", start)

kotlin = r'''object SongbookParser {
    private data class TocEntry(val number: Int, val label: String, val page: Int)

    private val tocLinePattern = Regex("""^\s*(\d{1,3})\s*[.)]\s*(.+?)\s*(?:[.·…]\s*){3,}\s*(\d{1,3})\s*$""")
    private val chordPattern = Pattern.compile("""(?<![A-Za-z0-9])([A-Ga-g](?:#|b)?(?:maj(?:7|9|11|13)?|m(?:aj7|7|9|11|13)?|m9|sus[24]?|add9|dim7?|aug|[0-9]{1,2})?(?:/[A-Ga-g](?:#|b)?)?)(?![A-Za-z0-9])""")

    fun parse(text: String, source: String): List<SongbookSong> {
        val normalized = text.replace("\r\n", "\n").replace('\r', '\n').filter { it.code != 0 }.trim()
        if (normalized.isBlank()) return emptyList()
        val pages = splitPages(normalized)
        val indexed = parseFromContents(pages, source)
        if (indexed.isNotEmpty()) return indexed
        return parseHeuristically(normalized, source)
    }

    private fun splitPages(text: String): Map<Int, String> {
        val marker = Regex("""\[\[SAITENWERK_SEITE_(\d+)]]""")
        val matches = marker.findAll(text).toList()
        if (matches.isEmpty()) return mapOf(1 to text)
        val pages = linkedMapOf<Int, String>()
        matches.forEachIndexed { index, match ->
            val start = match.range.last + 1
            val end = matches.getOrNull(index + 1)?.range?.first ?: text.length
            val pageNumber = match.groupValues[1].toIntOrNull() ?: (index + 1)
            pages[pageNumber] = text.substring(start, end).trim()
        }
        return pages
    }

    private fun parseFromContents(pages: Map<Int, String>, source: String): List<SongbookSong> {
        val entries = mutableListOf<TocEntry>()
        var lastContentsPage = 0
        for ((pageNumber, pageText) in pages.toSortedMap()) {
            if (pageNumber > 20) break
            var foundOnPage = false
            for (rawLine in pageText.lines()) {
                val line = rawLine.replace('\u00A0', ' ').trim()
                val match = tocLinePattern.matchEntire(line) ?: continue
                val number = match.groupValues[1].toIntOrNull() ?: continue
                val label = match.groupValues[2].replace(Regex("""\s+"""), " ").trim()
                val songPage = match.groupValues[3].toIntOrNull() ?: continue
                if (number > 0 && songPage > 1 && label.isNotBlank()) {
                    entries += TocEntry(number, label, songPage)
                    foundOnPage = true
                }
            }
            if (foundOnPage) lastContentsPage = pageNumber
        }

        val ordered = entries.sortedBy { it.number }
        if (ordered.size < 3) return emptyList()
        if (ordered.indices.any { ordered[it].number != it + 1 }) return emptyList()
        val lastPdfPage = pages.keys.maxOrNull() ?: return emptyList()
        if (ordered.first().page <= lastContentsPage || ordered.last().page > lastPdfPage) return emptyList()
        if (ordered.zipWithNext().any { it.first.page >= it.second.page }) return emptyList()

        val duplicateCounts = HashMap<String, Int>()
        val result = mutableListOf<SongbookSong>()
        ordered.forEachIndexed { index, entry ->
            val endExclusive = ordered.getOrNull(index + 1)?.page ?: (lastPdfPage + 1)
            val rawBody = (entry.page until endExclusive)
                .mapNotNull { pages[it] }
                .joinToString("\n")
            val body = rawBody.lines()
                .filterNot { isPdfFooter(it) }
                .joinToString("\n")
                .trim()

            val (baseTitle, artist) = splitTitleAndArtist(entry.label)
            val key = baseTitle.lowercase(Locale.ROOT) + "|" + artist.lowercase(Locale.ROOT)
            val occurrence = (duplicateCounts[key] ?: 0) + 1
            duplicateCounts[key] = occurrence
            // Keep every numbered contents entry, including alternate arrangements with duplicate titles.
            val title = if (occurrence == 1) baseTitle else baseTitle + " (Eintrag " + entry.number + ")"
            val lyrics = body.ifBlank { "Inhalt auf PDF-Seite " + entry.page + " konnte nicht ausgelesen werden." }
            result += SongbookSong(
                title = title.take(120),
                artist = artist.take(100),
                lyrics = lyrics,
                chords = extractChords(body),
                source = source
            )
        }
        return result
    }

    private fun splitTitleAndArtist(label: String): Pair<String, String> {
        val clean = label.replace(Regex("""\s+"""), " ").trim()
        val parenthetical = Regex("""^(.*?)\s+\(([^()]*)\)\s*$""").matchEntire(clean)
        if (parenthetical != null && parenthetical.groupValues[1].isNotBlank()) {
            return parenthetical.groupValues[1].trim() to parenthetical.groupValues[2].trim()
        }
        val separator = clean.lastIndexOf(" - ")
        if (separator > 0 && separator < clean.length - 3) {
            return clean.substring(0, separator).trim() to clean.substring(separator + 3).trim()
        }
        return clean to "Unbekannter Künstler"
    }

    private fun isPdfFooter(line: String): Boolean {
        val value = line.trim()
        return value.contains("Songbook vom", ignoreCase = true) ||
            value.contains("Lyricsarchiv.de", ignoreCase = true) ||
            Regex("""(?i)\bseite\s+\d+\s+von\s+\d+\b""").containsMatchIn(value)
    }

    private fun extractChords(block: String): List<String> {
        val chords = linkedSetOf<String>()
        block.lines().forEach { line ->
            if (!looksLikeChordLine(line)) return@forEach
            line.trim().split(Regex("""\s+""")).forEach { token ->
                val cleaned = token.trim(',', ';', ':', '.', '|', '(', ')', '[', ']')
                if (chordPattern.matcher(cleaned).matches()) {
                    val chord = if (cleaned.length == 1 && cleaned[0] in 'a'..'g') {
                        cleaned.uppercase(Locale.ROOT) + "m"
                    } else {
                        cleaned.replaceFirstChar { it.uppercase() }
                    }
                    chords += chord
                }
            }
        }
        return chords.toList()
    }

    private fun looksLikeChordLine(line: String): Boolean {
        val words = line.trim().split(Regex("""\s+""")).filter { it.isNotBlank() }
        if (words.isEmpty() || words.size > 24) return false
        val matches = words.count { token ->
            val cleaned = token.trim(',', ';', ':', '.', '|', '(', ')', '[', ']')
            chordPattern.matcher(cleaned).matches()
        }
        return matches >= maxOf(1, (words.size + 1) / 2)
    }

    private fun parseHeuristically(text: String, source: String): List<SongbookSong> {
        val pages = splitPages(text)
        val blocks = mutableListOf<String>()
        pages.toSortedMap().values.forEach { page ->
            val lines = page.lines()
            val starts = mutableListOf<Int>()
            lines.forEachIndexed { index, raw ->
                val line = raw.trim()
                if (!isTitle(line)) return@forEachIndexed
                val numbered = line.matches(Regex("""(?i)^(?:(?:lied|song)\s*)?\d{1,3}\s*[.)\-:]?\s+\S.*$"""))
                val marked = raw.trimStart().startsWith("#") || line.startsWith("♪") || line.startsWith("♫")
                val upper = line.count { it.isLetter() } >= 3 && line.filter { it.isLetter() }.all { !it.isLowerCase() }
                val before = index == 0 || lines.getOrNull(index - 1).isNullOrBlank() ||
                    lines.getOrNull(index - 1)?.trim()?.matches(Regex("""[-_=*~•·]{3,}""")) == true
                val after = lines.getOrNull(index + 1).isNullOrBlank()
                val score = (if (before) 1 else 0) + (if (after) 1 else 0) +
                    (if (numbered) 3 else 0) + (if (marked) 3 else 0) +
                    (if (upper) 2 else 0) +
                    (if (line.length <= 58 && !line.endsWith(".") && !line.endsWith(",")) 1 else 0)
                val hasBody = lines.drop(index + 1).take(5).any { it.trim().length >= 12 }
                if (score >= 3 && hasBody && (before || numbered || marked || upper)) starts += index
            }
            val boundaries = starts.distinct().sorted()
            if (boundaries.isEmpty()) {
                if (page.trim().length >= 20) blocks += page.trim()
            } else {
                boundaries.forEachIndexed { index, start ->
                    val end = boundaries.getOrNull(index + 1) ?: lines.size
                    val block = lines.subList(start, end).joinToString("\n").trim()
                    if (block.length >= 20) blocks += block
                }
            }
        }

        val result = mutableListOf<SongbookSong>()
        val seen = HashSet<String>()
        blocks.forEach { block ->
            val lines = block.lines().map { it.trim() }.filter { it.isNotBlank() }
            if (lines.isEmpty()) return@forEach
            val title = lines.firstOrNull { isTitle(it) }
                ?.trim('#', '*', '-', '♪', '♫', ' ')?.trim()?.take(120) ?: return@forEach
            val artist = lines.firstOrNull {
                it.startsWith("Von:", true) || it.startsWith("Artist:", true) ||
                    it.startsWith("Interpret:", true) || it.startsWith("Künstler:", true)
            }?.substringAfter(':')?.trim()?.takeIf { it.isNotBlank() } ?: "Unbekannter Künstler"
            val key = title.lowercase(Locale.ROOT) + "|" + artist.lowercase(Locale.ROOT)
            if (seen.add(key)) {
                result += SongbookSong(title=title, artist=artist, lyrics=block, chords=extractChords(block), source=source)
            }
        }
        if (result.isEmpty()) {
            val all = pages.values.joinToString("\n\n").trim()
            if (all.length >= 20) {
                val title = all.lines().firstOrNull { it.isNotBlank() }?.trim()?.take(120) ?: "PDF-Inhalt prüfen"
                result += SongbookSong(title=title, artist="Unbekannter Künstler", lyrics=all, chords=extractChords(all), source=source)
            }
        }
        return result
    }

    private fun isTitle(value: String): Boolean {
        val line = value.trim().trim('#', '*', '♪', '♫', ' ').trim()
        if (line.length !in 2..100 || line.count { it.isLetter() } < 2) return false
        if (line.matches(Regex("""(?i)(seite|page)\s+\d+""")) || line.matches(Regex("""\d{1,4}"""))) return false
        if (line.contains("www.") || line.contains("http://") || line.contains("https://")) return false
        val words = line.split(Regex("""\s+"""))
        val chordWords = words.count { it.matches(Regex("""[A-Ga-g](?:#|b)?(?:m|maj7|7|sus4|sus2|dim|aug)?""")) }
        return !(chordWords >= maxOf(1, (words.size + 1) / 2) && words.size <= 12)
    }
}'''

s = s[:start] + kotlin + s[end:]

db_marker = "    fun importedPdfs(): List<ImportedSongbookPdf> {"
db_method = r'''    fun replacePdfSongs(uri: String, songs: List<SongbookSong>): Int {
        db.beginTransaction()
        try {
            val oldIds = linkedSetOf<Long>()
            db.rawQuery("SELECT song_id FROM song_pdf_sources WHERE pdf_uri=?", arrayOf(uri)).use { cursor ->
                while (cursor.moveToNext()) oldIds += cursor.getLong(0)
            }
            val newIds = linkedSetOf<Long>()
            songs.forEach { newIds += upsert(it) }
            db.delete("song_pdf_sources", "pdf_uri=?", arrayOf(uri))
            newIds.forEach { id ->
                db.execSQL("INSERT OR IGNORE INTO song_pdf_sources(song_id,pdf_uri) VALUES(?,?)", arrayOf(id, uri))
            }
            (oldIds - newIds).forEach { id ->
                val referenceCount = db.rawQuery(
                    "SELECT COUNT(*) FROM song_pdf_sources WHERE song_id=?",
                    arrayOf(id.toString())
                ).use { cursor -> if (cursor.moveToFirst()) cursor.getInt(0) else 0 }
                if (referenceCount == 0) db.delete("songs", "id=?", arrayOf(id.toString()))
            }
            db.setTransactionSuccessful()
            return newIds.size
        } finally {
            db.endTransaction()
        }
    }
'''
if "fun replacePdfSongs(uri: String, songs: List<SongbookSong>): Int" not in s:
    if s.count(db_marker) != 1:
        raise SystemExit("FEHLER: Einfügepunkt für PDF-Song-Abgleich nicht eindeutig.")
    s = s.replace(db_marker, db_method + "\n" + db_marker, 1)

old_save = "val savedCount = songs.count { song -> db.upsert(song) > 0L }"
new_save = "val savedCount = db.replacePdfSongs(uri.toString(), songs)"
if old_save in s:
    s = s.replace(old_save, new_save, 1)
elif new_save not in s:
    raise SystemExit("FEHLER: PDF-Speicherstelle nicht gefunden.")

s = s.replace(
    'put("youtube_id", song.youtubeId); put("youtube_confidence", song.youtubeConfidence)',
    'song.youtubeId?.let { put("youtube_id", it); put("youtube_confidence", song.youtubeConfidence) }'
)

required = [
    "private fun parseFromContents(",
    "val indexed = parseFromContents(pages, source)",
    "fun replacePdfSongs(uri: String, songs: List<SongbookSong>): Int",
    "val savedCount = db.replacePdfSongs(uri.toString(), songs)",
    "SongbookParser.parse(extracted, uri.toString())",
]
missing = [token for token in required if token not in s]
if missing:
    raise SystemExit("FEHLER: PDF-Indexintegration unvollständig: " + ", ".join(missing))

songbook.write_text(s, encoding="utf-8")
print("SONGBOOK-PDF-INDEX: PASS – Inhaltsverzeichnis, Seitenbereiche, Dubletten und Neuimport-Abgleich integriert.")
