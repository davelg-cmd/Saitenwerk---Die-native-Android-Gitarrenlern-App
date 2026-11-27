from pathlib import Path
import os
ROOT = Path(os.environ["PROJECT_DIR"])
p = ROOT / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
if not p.is_file():
    raise SystemExit("FEHLER: IntelligentSongbook.kt fehlt.")
marker = ROOT / "SONGBOOK_PDF_MANAGEMENT_OCR_V1.txt"
if marker.is_file():
    print("SONGBOOK-PDF-MANAGEMENT: bereits integriert")
    raise SystemExit(0)
s=p.read_text()
# Imports
s=s.replace('import android.graphics.Color\n', 'import android.graphics.Color\nimport android.graphics.Bitmap\nimport android.graphics.pdf.PdfRenderer\nimport android.os.ParcelFileDescriptor\n')
s=s.replace('import android.net.Uri\n', 'import android.net.Uri\nimport android.provider.OpenableColumns\n')
s=s.replace('import org.json.JSONArray\n', 'import org.json.JSONArray\nimport com.google.android.gms.tasks.Tasks\nimport com.google.mlkit.vision.common.InputImage\nimport com.google.mlkit.vision.text.TextRecognition\nimport com.google.mlkit.vision.text.latin.TextRecognizerOptions\n')
# Imported-PDF model and database tracking
s=s.replace('class SongbookDb(context: Context) {', '''data class ImportedSongbookPdf(
    val uri: String,
    val displayName: String,
    val importedAt: Long,
    val songCount: Int
)

class SongbookDb(context: Context) {''')
needle='''            UNIQUE(title, artist)
        )""")
    }
    fun upsert(song: SongbookSong): Long {'''
repl='''            UNIQUE(title, artist)
        )""")
        db.execSQL("""CREATE TABLE IF NOT EXISTS imported_pdfs(
            uri TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            imported_at INTEGER NOT NULL,
            song_count INTEGER NOT NULL DEFAULT 0
        )""")
        db.execSQL("""CREATE TABLE IF NOT EXISTS song_pdf_sources(
            song_id INTEGER NOT NULL,
            pdf_uri TEXT NOT NULL,
            PRIMARY KEY(song_id, pdf_uri)
        )""")
        db.execSQL("INSERT OR IGNORE INTO song_pdf_sources(song_id,pdf_uri) SELECT id,source FROM songs WHERE source IS NOT NULL AND source <> ''")
    }
    fun registerPdf(uri: String, displayName: String, songCount: Int) {
        val cv = android.content.ContentValues().apply {
            put("uri", uri); put("display_name", displayName)
            put("imported_at", System.currentTimeMillis()); put("song_count", songCount)
        }
        db.insertWithOnConflict("imported_pdfs", null, cv, android.database.sqlite.SQLiteDatabase.CONFLICT_REPLACE)
    }
    fun importedPdfs(): List<ImportedSongbookPdf> {
        val out = mutableListOf<ImportedSongbookPdf>()
        db.rawQuery("SELECT uri,display_name,imported_at,song_count FROM imported_pdfs ORDER BY imported_at DESC", null).use { c ->
            while (c.moveToNext()) out += ImportedSongbookPdf(c.getString(0), c.getString(1), c.getLong(2), c.getInt(3))
        }
        return out
    }
    fun removePdf(uri: String): Int {
        db.beginTransaction()
        try {
            db.delete("song_pdf_sources", "pdf_uri=?", arrayOf(uri))
            val removed = db.delete("songs", "id NOT IN (SELECT song_id FROM song_pdf_sources)", null)
            db.delete("imported_pdfs", "uri=?", arrayOf(uri))
            db.setTransactionSuccessful()
            return removed
        } finally { db.endTransaction() }
    }
    fun upsert(song: SongbookSong): Long {'''
if needle not in s: raise SystemExit("FEHLER: Songbook-Datenbankstruktur hat sich unerwartet geändert.")
s=s.replace(needle,repl)
s=s.replace('''        }
        return id
    }
    fun all(): List<SongbookSong> {''','''        }
        db.execSQL("INSERT OR IGNORE INTO song_pdf_sources(song_id,pdf_uri) VALUES(?,?)", arrayOf(id, song.source))
        return id
    }
    fun all(): List<SongbookSong> {''',1)
# Imported PDF list and remove action
needle='''        val import = button("＋  PDF analysieren & Songs importieren")
        import.setOnClickListener { importPdf.launch(arrayOf("application/pdf")) }
        root.addView(import)
        val youtube = button(if (youtubeConnected) {'''
repl='''        val import = button("＋  PDF analysieren & Songs importieren")
        import.setOnClickListener { importPdf.launch(arrayOf("application/pdf")) }
        root.addView(import)
        val pdfs = db.importedPdfs()
        if (pdfs.isNotEmpty()) {
            addText("MEINE IMPORTIERTEN PDFS", 13f, Color.rgb(205,145,91), 2)
            pdfs.forEach { pdf ->
                val pdfCard = card()
                pdfCard.addView(label("▤  " + pdf.displayName, 16f, Color.WHITE))
                pdfCard.addView(label(pdf.songCount.toString() + " erkannte Songs", 12f, Color.LTGRAY))
                val remove = button("PDF aus Songbook entfernen")
                remove.setOnClickListener {
                    AlertDialog.Builder(requireContext())
                        .setTitle("Importiertes PDF entfernen?")
                        .setMessage("\\\"${pdf.displayName}\\\" und die ausschließlich daraus importierten Songs werden aus SaitenWerk entfernt. Die Originaldatei auf deinem Gerät bleibt erhalten.")
                        .setNegativeButton("Abbrechen", null)
                        .setPositiveButton("Entfernen") { _, _ ->
                            db.removePdf(pdf.uri)
                            runCatching {
                                requireContext().contentResolver.releasePersistableUriPermission(
                                    Uri.parse(pdf.uri), Intent.FLAG_GRANT_READ_URI_PERMISSION
                                )
                            }
                            buildHome()
                            Toast.makeText(requireContext(), "PDF und zugehörige Songs entfernt.", Toast.LENGTH_LONG).show()
                        }.show()
                }
                pdfCard.addView(remove)
                root.addView(pdfCard)
            }
        }
        val youtube = button(if (youtubeConnected) {'''
if needle not in s: raise SystemExit("FEHLER: Songbook-Importschaltfläche nicht gefunden.")
s=s.replace(needle,repl)
# Replace import implementation with page-wise extraction and OCR fallback
start=s.index('    private fun importPdf(uri:Uri) {')
end=s.index('    private fun card(): LinearLayout', start)
method='''    private fun importPdf(uri:Uri) {
        val progress=ProgressBar(requireContext())
        root.addView(progress,0,LinearLayout.LayoutParams(-1,dp(5)))
        executor.execute {
            try {
                val context = requireContext().applicationContext
                runCatching {
                    requireContext().contentResolver.takePersistableUriPermission(
                        uri, Intent.FLAG_GRANT_READ_URI_PERMISSION
                    )
                }
                val displayName = queryPdfDisplayName(uri)
                PDFBoxResourceLoader.init(context)
                val extracted = requireContext().contentResolver.openInputStream(uri).use { input ->
                    if(input==null) error("PDF konnte nicht geöffnet werden.")
                    PDDocument.load(input).use { doc ->
                        val pages = mutableListOf<String>()
                        val renderer = runCatching {
                            val descriptor = requireContext().contentResolver.openFileDescriptor(uri, "r")
                                ?: error("PDF-Datei kann nicht für die Texterkennung geöffnet werden.")
                            PdfRenderer(descriptor)
                        }.getOrNull()
                        val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
                        try {
                            for (pageIndex in 0 until doc.numberOfPages) {
                                val stripper = PDFTextStripper().apply {
                                    sortByPosition = true
                                    lineSeparator = "\\n"
                                    startPage = pageIndex + 1
                                    endPage = pageIndex + 1
                                }
                                var pageText = stripper.getText(doc).trim()
                                val usefulChars = pageText.count { it.isLetterOrDigit() }
                                if (usefulChars < 24 && renderer != null && pageIndex < renderer.pageCount) {
                                    val ocrText = renderer.openPage(pageIndex).use { page ->
                                        val bitmap = Bitmap.createBitmap(
                                            (page.width * 2).coerceAtLeast(1),
                                            (page.height * 2).coerceAtLeast(1),
                                            Bitmap.Config.ARGB_8888
                                        )
                                        try {
                                            page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                                            Tasks.await(recognizer.process(InputImage.fromBitmap(bitmap, 0))).text
                                        } finally { bitmap.recycle() }
                                    }
                                    if (ocrText.isNotBlank()) pageText = ocrText
                                }
                                if (pageText.isNotBlank()) pages += "[[SAITENWERK_SEITE_${pageIndex + 1}]]\\n" + pageText
                            }
                        } finally {
                            recognizer.close()
                            renderer?.close()
                        }
                        pages.joinToString("\\n\\n")
                    }
                }
                val songs = SongbookParser.parse(extracted, uri.toString())
                if (songs.isEmpty()) error("Es konnten keine Songs erkannt werden. Bitte prüfe, ob die PDF lesbaren Text oder gut erkennbare Noten-/Akkordseiten enthält.")
                val savedCount = songs.count { song -> db.upsert(song) > 0L }
                if (savedCount == 0) error("Songs erkannt, aber kein Song konnte gespeichert werden.")
                db.registerPdf(uri.toString(), displayName, savedCount)
                requireActivity().runOnUiThread {
                    if(progress.parent!=null) root.removeView(progress)
                    buildHome()
                    AlertDialog.Builder(requireContext()).setTitle("PDF analysiert")
                        .setMessage(savedCount.toString() + " Songs erkannt und gespeichert. Das Songbook wurde aktualisiert.\\n\\nText-PDFs werden direkt ausgelesen; gescannte Seiten werden zusätzlich per Texterkennung (OCR) verarbeitet.")
                        .setPositiveButton("OK", null).show()
                }
            } catch(t:Throwable) {
                requireActivity().runOnUiThread {
                    if(progress.parent!=null) root.removeView(progress)
                    AlertDialog.Builder(requireContext()).setTitle("Import fehlgeschlagen")
                        .setMessage(t.cause?.message ?: t.message ?: "Unbekannter PDF-Fehler").setPositiveButton("OK",null).show()
                }
            }
        }
    }

    private fun queryPdfDisplayName(uri: Uri): String {
        var name = "Songbook-PDF"
        requireContext().contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
            if (c.moveToFirst()) name = c.getString(0)?.takeIf { it.isNotBlank() } ?: name
        }
        return name
    }

'''
s=s[:start]+method+s[end:]
# Page-aware title/artist/chord parsing
start=s.index('object SongbookParser {')
end=s.index('\nclass SongbookFragment : Fragment() {', start)
parser='''object SongbookParser {
    private val chordPattern = Pattern.compile("""(?<![A-Za-z0-9])([A-G](?:#|b)?(?:maj(?:7|9|11|13)?|m(?:aj7|7|9|11|13)?|m9|sus[24]?|add9|dim7?|aug|[0-9]{1,2})?(?:/[A-G](?:#|b)?)?)(?![A-Za-z0-9])""")
    fun parse(text: String, source: String): List<SongbookSong> {
        val normalized = text.replace("\\r\\n", "\\n").replace('\\r', '\\n').filter { it.code != 0 }.trim()
        if (normalized.isBlank()) return emptyList()
        val pages = normalized.split(Regex("""\[\[SAITENWERK_SEITE_\d+]]""")).filter { it.isNotBlank() }
        val blocks = mutableListOf<String>()
        pages.forEach { page ->
            val lines = page.lines()
            val starts = mutableListOf<Int>()
            lines.forEachIndexed { i, raw ->
                val line = raw.trim()
                if (!isTitle(line)) return@forEachIndexed
                val numbered = line.matches(Regex("""(?i)^(?:(?:lied|song)\s*)?\d{1,3}\s*[.)\-:]?\s+\S.*$"""))
                val marked = raw.trimStart().startsWith("#") || line.startsWith("♪") || line.startsWith("♫")
                val upper = line.count { it.isLetter() } >= 3 && line.filter { it.isLetter() }.all { !it.isLowerCase() }
                val before = i == 0 || lines.getOrNull(i - 1).isNullOrBlank() || lines.getOrNull(i - 1)?.trim()?.matches(Regex("""[-_=*~•·]{3,}""")) == true
                val after = lines.getOrNull(i + 1).isNullOrBlank()
                val score = (if (before) 1 else 0) + (if (after) 1 else 0) + (if (numbered) 3 else 0) + (if (marked) 3 else 0) + (if (upper) 2 else 0) + (if (line.length <= 58 && !line.endsWith(".") && !line.endsWith(",")) 1 else 0)
                val hasBody = lines.drop(i + 1).take(5).any { it.trim().length >= 12 }
                if (score >= 3 && hasBody && (before || numbered || marked || upper)) starts += i
            }
            val boundaries = starts.distinct().sorted()
            if (boundaries.isEmpty()) {
                if (page.trim().length >= 20) blocks += page.trim()
            } else boundaries.forEachIndexed { index, start ->
                val end = boundaries.getOrNull(index + 1) ?: lines.size
                val block = lines.subList(start, end).joinToString("\\n").trim()
                if (block.length >= 20) blocks += block
            }
        }
        val result = mutableListOf<SongbookSong>()
        val seen = HashSet<String>()
        blocks.forEach { block ->
            val lines = block.lines().map { it.trim() }.filter { it.isNotBlank() }
            if (lines.isEmpty()) return@forEach
            val title = lines.firstOrNull { isTitle(it) }?.trim('#','*','-','♪','♫',' ')?.trim()?.take(120) ?: return@forEach
            val artist = lines.firstOrNull { it.startsWith("Von:", true) || it.startsWith("Artist:", true) || it.startsWith("Interpret:", true) || it.startsWith("Künstler:", true) }?.substringAfter(':')?.trim()?.takeIf { it.isNotBlank() } ?: "Unbekannter Künstler"
            val chords = linkedSetOf<String>()
            val matcher = chordPattern.matcher(block)
            while (matcher.find()) if (matcher.group(1).length <= 8) chords += matcher.group(1)
            val key = title.lowercase(Locale.ROOT) + "|" + artist.lowercase(Locale.ROOT)
            if (seen.add(key)) result += SongbookSong(title=title, artist=artist, lyrics=block, chords=chords.toList(), source=source)
        }
        if (result.isEmpty()) {
            val all = pages.joinToString("\\n\\n").trim()
            if (all.length >= 20) result += SongbookSong(title=all.lines().firstOrNull { it.isNotBlank() }?.trim()?.take(120) ?: "PDF-Inhalt prüfen", artist="Unbekannter Künstler", lyrics=all, chords=emptyList(), source=source)
        }
        return result
    }
    private fun isTitle(value: String): Boolean {
        val line = value.trim().trim('#','*','♪','♫',' ').trim()
        if (line.length !in 2..100 || line.count { it.isLetter() } < 2) return false
        if (line.matches(Regex("""(?i)(seite|page)\s+\d+""")) || line.matches(Regex("""\d{1,4}"""))) return false
        if (line.contains("www.") || line.contains("http://") || line.contains("https://")) return false
        val words = line.split(Regex("""\s+"""))
        val chordWords = words.count { it.matches(Regex("""[A-G](?:#|b)?(?:m|maj7|7|sus4|sus2|dim|aug)?""")) }
        return !(chordWords >= maxOf(1, (words.size + 1) / 2) && words.size <= 12)
    }
}
'''
s=s[:start]+parser+s[end:]
p.write_text(s)
# OCR dependency
gradle = ROOT / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
if 'com.google.mlkit:text-recognition:16.0.1' not in g:
    if "dependencies {" not in g:
        raise SystemExit("FEHLER: Gradle-dependencies-Block fehlt.")
    g = g.replace("dependencies {", 'dependencies {\n    implementation("com.google.mlkit:text-recognition:16.0.1")', 1)
    gradle.write_text(g, encoding="utf-8")
# Navigation icon
main = ROOT / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
ms = main.read_text(encoding="utf-8")
old = 'menu.add(0, 4, 3, "Songbook")'
new = 'menu.add(0, 4, 3, "Songbook").setIcon(R.drawable.ic_nav_songbook)'
if old in ms:
    ms = ms.replace(old, new, 1)
elif new not in ms:
    raise SystemExit("FEHLER: Songbook-Menüeintrag in MainActivity.kt nicht gefunden.")
main.write_text(ms, encoding="utf-8")
icon = ROOT / "app/src/main/res/drawable/ic_nav_songbook.xml"
icon.parent.mkdir(parents=True, exist_ok=True)
icon.write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFFFF" android:pathData="M5,3.5C5,2.67 5.67,2 6.5,2H20v17H7c-1.1,0 -2,0.9 -2,2V3.5zM7,4v12.2c0.32,-0.13 0.65,-0.2 1,-0.2h10V4H7zM5,21c0,-1.1 0.9,-2 2,-2h13v2H7c-0.55,0 -1,0.45 -1,1H5v-1zM9,6h7v1.6H9zM9,9h7v1.6H9zM9,12h5v1.6H9z" />
</vector>
''', encoding="utf-8")
marker.write_text("Saitenwerk Songbook PDF management + OCR V1\n", encoding="utf-8")
print("SONGBOOK-PDF-MANAGEMENT: PASS – Seitenweise PDF-Auslesung, OCR-Fallback, verbesserte Song-/Akkorderkennung, PDF-Verwaltung und Navigation-Icon integriert.")
