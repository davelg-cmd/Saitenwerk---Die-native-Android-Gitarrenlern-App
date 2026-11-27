#!/usr/bin/env python3
"""Make Songbook TOC parsing tolerant of real-world PDF layouts and page offsets."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s = path.read_text(encoding="utf-8")
start = s.index("    private val tocLinePattern = ")
end = s.index("\n    private val chordPattern", start)
s = s[:start] + r'''    private val tocLinePattern = Regex("""^\s*(\d{1,4})\s*[.)]?\s*(.+?)\s*(?:[.·…]{2,}\s*)?(\d{1,4})\s*$""")''' + s[end:]

start = s.index("    private fun parseFromContents(")
end = s.index("\n    private fun splitTitleAndArtist(", start)
replacement = r'''    private fun parseFromContents(pages: Map<Int, String>, source: String): List<SongbookSong> {
        val entries = mutableListOf<TocEntry>()
        var lastContentsPage = 0
        var pending: Pair<Int, String>? = null
        for ((pageNumber, pageText) in pages.toSortedMap()) {
            if (pageNumber > 20) break
            var foundOnPage = false
            for (rawLine in pageText.lines()) {
                val line = rawLine.replace('\u00A0', ' ').replace(Regex("""\s+"""), " ").trim()
                if (line.isBlank()) continue
                val match = tocLinePattern.matchEntire(line)
                if (match != null) {
                    val number = match.groupValues[1].toIntOrNull() ?: continue
                    val label = match.groupValues[2].trim().trim('.', '·', '…', ' ')
                    val songPage = match.groupValues[3].toIntOrNull() ?: continue
                    if (number > 0 && songPage > 1 && label.count { it.isLetter() } >= 2) {
                        entries += TocEntry(number, label, songPage)
                        foundOnPage = true
                        pending = null
                        continue
                    }
                }
                // Some PDF extractors put the title and its page number on separate lines.
                val head = Regex("""^(\d{1,4})\s*[.)]\s*(.{2,})$""").matchEntire(line)
                if (head != null) {
                    val number = head.groupValues[1].toIntOrNull()
                    val label = head.groupValues[2].trim().trim('.', '·', '…')
                    if (number != null && label.count { it.isLetter() } >= 2) pending = number to label
                } else if (pending != null && line.matches(Regex("""^\d{1,4}$"""))) {
                    val page = line.toIntOrNull()
                    if (page != null && page > 1) {
                        entries += TocEntry(pending!!.first, pending!!.second, page)
                        foundOnPage = true
                    }
                    pending = null
                }
            }
            if (foundOnPage) lastContentsPage = pageNumber
        }

        val ordered = entries.distinctBy { it.number }.sortedBy { it.number }
        if (ordered.size < 3) return emptyList()
        val lastPdfPage = pages.keys.maxOrNull() ?: return emptyList()
        val contentPages = pages.keys.filter { it <= maxOf(lastContentsPage, 1) }.toSet()

        fun words(value: String): Set<String> =
            Regex("""[\p{L}\p{N}]{3,}""").findAll(value.lowercase(Locale.ROOT))
                .map { it.value }.filterNot { it in setOf("der","die","das","und","von","mit","the","and","for","song","lied") }
                .toSet()

        // Printed page numbers frequently differ from physical PDF page indices.
        // Infer the constant offset from pages whose extracted heading resembles a TOC title.
        val offsets = mutableListOf<Int>()
        for (entry in ordered) {
            val titleWords = words(entry.label)
            if (titleWords.isEmpty()) continue
            var bestPage = -1
            var bestScore = 0.0
            for ((physicalPage, pageText) in pages) {
                if (physicalPage in contentPages) continue
                val pageWords = words(pageText.take(1800))
                val score = titleWords.count { it in pageWords }.toDouble() / titleWords.size
                if (score > bestScore) { bestScore = score; bestPage = physicalPage }
            }
            if (bestPage > 0 && bestScore >= 0.34) offsets += bestPage - entry.page
        }
        val offset = offsets.groupingBy { it }.eachCount().maxByOrNull { it.value }?.key ?: 0
        val mapped = ordered.mapNotNull { entry ->
            val physical = entry.page + offset
            if (physical in pages && physical > lastContentsPage) entry to physical else null
        }
        if (mapped.size < 3) return emptyList()
        val monotonic = mapped.zipWithNext().count { it.first.second <= it.second.second }
        if (monotonic < (mapped.size * 0.75).toInt()) return emptyList()

        val usable = mapped.sortedBy { it.first.number }
        val duplicateCounts = HashMap<String, Int>()
        val result = mutableListOf<SongbookSong>()
        usable.forEachIndexed { index, pair ->
            val entry = pair.first
            val startPage = pair.second
            val nextPage = usable.drop(index + 1).firstOrNull { it.second > startPage }?.second
                ?: (lastPdfPage + 1)
            val rawBody = (startPage until nextPage).mapNotNull { pages[it] }.joinToString("\n")
            val body = rawBody.lines().filterNot { isPdfFooter(it) }.joinToString("\n").trim()
            val (baseTitle, artist) = splitTitleAndArtist(entry.label)
            val key = baseTitle.lowercase(Locale.ROOT) + "|" + artist.lowercase(Locale.ROOT)
            val occurrence = (duplicateCounts[key] ?: 0) + 1
            duplicateCounts[key] = occurrence
            val title = if (occurrence == 1) baseTitle else baseTitle + " (Eintrag " + entry.number + ")"
            if (body.isNotBlank()) {
                result += SongbookSong(
                    title = title.take(120), artist = artist.take(100), lyrics = body,
                    chords = extractChords(body), source = source
                )
            }
        }
        return result.takeIf { it.size >= 3 } ?: emptyList()
    }'''
s = s[:start] + replacement + s[end:]
required = ["val offsets = mutableListOf<Int>()", "val physical = entry.page + offset", "private fun parseFromContents("]
if any(x not in s for x in required):
    raise SystemExit("Robuste TOC-Erkennung konnte nicht vollständig integriert werden.")
path.write_text(s, encoding="utf-8")
print("SONGBOOK-TOC-ROBUST: PASS")
