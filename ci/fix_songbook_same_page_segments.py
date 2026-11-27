#!/usr/bin/env python3
"""Split multiple TOC entries that begin on the same PDF page instead of duplicating whole pages."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s = path.read_text(encoding="utf-8")

start = s.index("        val usable = mapped.sortedBy { it.first.number }")
end = s.index("        return result.takeIf { it.size >= 3 } ?: emptyList()", start) + len("        return result.takeIf { it.size >= 3 } ?: emptyList()")

replacement = r'''        val usable = mapped.sortedWith(compareBy<Pair<TocEntry, Int>> { it.second }.thenBy { it.first.number })
        val entriesByPage = usable.groupBy { it.second }
        val startLines = HashMap<Int, Int>()

        // When several songs start on one physical page, locate each printed title
        // inside that page. Otherwise the previous parser assigned the same full
        // page text to every entry on that page.
        for ((physicalPage, pageEntries) in entriesByPage) {
            val pageLines = pages[physicalPage].orEmpty().lines()
            val found = mutableListOf<Pair<Int, Int>>()
            for ((entryIndex, pair) in usable.withIndex()) {
                if (pair.second != physicalPage) continue
                val titleWords = words(pair.first.label)
                if (titleWords.isEmpty()) continue
                var bestLine = -1
                var bestScore = 0.0
                pageLines.forEachIndexed { lineIndex, line ->
                    val cleanLine = line.trim()
                    if (cleanLine.length !in 2..150 || cleanLine.count { it.isLetter() } < 2) return@forEachIndexed
                    val lineWords = words(cleanLine)
                    val score = titleWords.count { it in lineWords }.toDouble() / titleWords.size
                    if (score > bestScore) {
                        bestScore = score
                        bestLine = lineIndex
                    }
                }
                if (bestLine >= 0 && bestScore >= 0.34) found += entryIndex to bestLine
            }
            if (pageEntries.size > 1) {
                if (found.size != pageEntries.size || found.map { it.second }.distinct().size != pageEntries.size) {
                    // Do not silently duplicate a page into multiple songs.
                    return emptyList()
                }
                val lineOrder = found.sortedBy { it.first }
                if (lineOrder.zipWithNext().any { it.first.second >= it.second.second }) return emptyList()
            }
            found.forEach { (entryIndex, lineIndex) -> startLines[entryIndex] = lineIndex }
        }

        val duplicateCounts = HashMap<String, Int>()
        val result = mutableListOf<SongbookSong>()
        usable.forEachIndexed { index, pair ->
            val entry = pair.first
            val startPage = pair.second
            val pageLines = pages[startPage].orEmpty().lines()
            val startLine = startLines[index] ?: 0
            val nextPair = usable.getOrNull(index + 1)
            val samePageEnd = if (nextPair != null && nextPair.second == startPage) {
                startLines[index + 1] ?: return emptyList()
            } else {
                pageLines.size
            }
            if (samePageEnd <= startLine) return emptyList()

            val bodyLines = mutableListOf<String>()
            bodyLines += pageLines.subList(startLine, samePageEnd)
            val nextPage = nextPair?.second ?: (lastPdfPage + 1)
            if (nextPage > startPage + 1) {
                for (page in (startPage + 1) until nextPage) {
                    pages[page]?.lines()?.let { bodyLines += it }
                }
            }
            val body = bodyLines.filterNot { isPdfFooter(it) }.joinToString("\n").trim()
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
        return result.takeIf { it.size >= 3 } ?: emptyList()'''
s = s[:start] + replacement + s[end:]

required = [
    "val entriesByPage = usable.groupBy { it.second }",
    "Do not silently duplicate a page into multiple songs.",
    "val startLine = startLines[index] ?: 0",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("FEHLER: Seitengenaue Songsegmentierung unvollständig: " + ", ".join(missing))

path.write_text(s, encoding="utf-8")
(root / "SONGBOOK_SAME_PAGE_SEGMENTATION_V1.txt").write_text(
    "SaitenWerk PDF parser: per-page TOC entry segmentation\n"
    "Multiple songs on one physical page are separated by matching their TOC titles to page headings; ambiguous cases are rejected instead of duplicating page text.\n",
    encoding="utf-8"
)
print("SONGBOOK-SAME-PAGE-SEGMENTATION: PASS")
