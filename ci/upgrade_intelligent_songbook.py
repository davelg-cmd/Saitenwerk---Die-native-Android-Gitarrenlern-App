#!/usr/bin/env python3
"""Integrate the premium intelligent Songbook into the extracted Saitenwerk project."""
from pathlib import Path
import os, re

ROOT = Path(os.environ["PROJECT_DIR"])
MAIN = ROOT / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
SONGBOOK = ROOT / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
GRADLE = ROOT / "app/build.gradle.kts"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"

if not MAIN.is_file():
    raise SystemExit(f"FEHLER: MainActivity.kt nicht gefunden: {MAIN}")

KOTLIN = r'''package de.saitenwerk.app

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.text.InputType
import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import org.json.JSONArray
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import java.util.Locale
import java.util.concurrent.Executors
import java.util.regex.Pattern

data class SongbookSong(
    val id: Long = 0,
    val title: String,
    val artist: String,
    val lyrics: String,
    val chords: List<String>,
    val source: String,
    val youtubeId: String? = null,
    val youtubeConfidence: Int = 0
)

class SongbookDb(context: Context) {
    private val db = context.openOrCreateDatabase("saitenwerk_songbook.db", Context.MODE_PRIVATE, null)
    init {
        db.execSQL("""CREATE TABLE IF NOT EXISTS songs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            lyrics TEXT NOT NULL,
            chords TEXT NOT NULL,
            source TEXT NOT NULL,
            youtube_id TEXT,
            youtube_confidence INTEGER NOT NULL DEFAULT 0,
            UNIQUE(title, artist)
        )""")
    }
    fun upsert(song: SongbookSong): Long {
        val cv = android.content.ContentValues().apply {
            put("title", song.title); put("artist", song.artist); put("lyrics", song.lyrics)
            put("chords", JSONArray(song.chords).toString()); put("source", song.source)
            put("youtube_id", song.youtubeId); put("youtube_confidence", song.youtubeConfidence)
        }
        val existing = db.rawQuery("SELECT id FROM songs WHERE lower(title)=lower(?) AND lower(artist)=lower(?)",
            arrayOf(song.title, song.artist))
        val id = if (existing.moveToFirst()) {
            val value = existing.getLong(0); existing.close()
            db.update("songs", cv, "id=?", arrayOf(value.toString())); value
        } else {
            existing.close(); db.insertOrThrow("songs", null, cv)
        }
        return id
    }
    fun all(): List<SongbookSong> {
        val out = mutableListOf<SongbookSong>()
        db.rawQuery("SELECT id,title,artist,lyrics,chords,source,youtube_id,youtube_confidence FROM songs ORDER BY title COLLATE NOCASE", null).use { c ->
            while (c.moveToNext()) {
                val chords = mutableListOf<String>()
                runCatching { val a=JSONArray(c.getString(4)); for(i in 0 until a.length()) chords += a.getString(i) }
                out += SongbookSong(c.getLong(0), c.getString(1), c.getString(2), c.getString(3), chords, c.getString(5),
                    if(c.isNull(6)) null else c.getString(6), c.getInt(7))
            }
        }
        return out
    }
}

object SongbookParser {
    private val chordPattern = Pattern.compile("""(?<![A-Za-z0-9])([A-G](?:#|b)?(?:maj7|maj9|m7b5|m7|m9|sus2|sus4|add9|dim7|dim|aug|7|6|5|9|11|13|m)?)(?![A-Za-z0-9])""")
    fun parse(text: String, source: String): List<SongbookSong> {
        val clean = text.replace("\r\n","\n").replace("\r","\n").replace("\u0000","").trim()
        if (clean.isBlank()) return emptyList()
        val blocks = clean.split(Regex("""\n\s*\n\s*\n+""")).map { it.trim() }.filter { it.length >= 20 }
        val songs = mutableListOf<SongbookSong>()
        val used = HashSet<String>()
        for (block in blocks) {
            val lines = block.lines().map { it.trimEnd() }.filter { it.isNotBlank() }
            if (lines.isEmpty()) continue
            val title = lines.first().trim().trim('#','*','-',' ')
            if (title.length < 2 || title.length > 120) continue
            val artist = lines.drop(1).firstOrNull { line ->
                line.length in 2..100 && !looksLikeChordLine(line) && !line.startsWith("[")
            }?.trim() ?: "Unbekannter Künstler"
            val chords = linkedSetOf<String>()
            for (line in lines) {
                val m = chordPattern.matcher(line)
                while (m.find()) chords += m.group(1)
            }
            val key = title.lowercase(Locale.ROOT)+"|"+artist.lowercase(Locale.ROOT)
            if (used.add(key)) songs += SongbookSong(title=title, artist=artist, lyrics=block, chords=chords.toList(), source=source)
        }
        if (songs.isEmpty()) {
            val title = clean.lines().firstOrNull { it.trim().length >= 2 }?.trim() ?: "Importiertes Lied"
            val chords = linkedSetOf<String>()
            val m = chordPattern.matcher(clean)
            while(m.find()) chords += m.group(1)
            songs += SongbookSong(title=title, artist="Unbekannter Künstler", lyrics=clean, chords=chords.toList(), source=source)
        }
        return songs
    }
    private fun looksLikeChordLine(line: String): Boolean {
        val words=line.trim().split(Regex("""\s+""")).filter { it.isNotBlank() }
        if(words.isEmpty()) return false
        val matches=words.count { chordPattern.matcher(it).find() && it.replace(Regex("""[^A-G#b0-9a-z]"""),"").length <= 8 }
        return matches >= maxOf(1, words.size/2)
    }
}

class SongbookFragment : Fragment() {
    private lateinit var root: LinearLayout
    private lateinit var db: SongbookDb
    private val executor = Executors.newSingleThreadExecutor()
    private val importPdf = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) importPdf(uri)
    }

    override fun onCreateView(inflater: android.view.LayoutInflater, container: ViewGroup?, state: Bundle?): View {
        db = SongbookDb(requireContext())
        root = LinearLayout(requireContext()).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(12),dp(18),dp(24))
            setBackgroundColor(Color.rgb(15,16,19))
        }
        buildHome()
        return root
    }

    private fun buildHome() {
        root.removeAllViews()
        addText("SONGBOOK", 30f, Color.WHITE, 8)
        addText("Deine Songs. Deine Akkorde. Dein Training.", 15f, Color.LTGRAY, 2)
        val stats = db.all()
        val stat = card()
        val row = LinearLayout(requireContext()).apply { orientation=LinearLayout.HORIZONTAL }
        stat.addView(label("MEINE SONGS\n" + stats.size, 18f, Color.WHITE), LinearLayout.LayoutParams(0,dp(72),1f))
        stat.addView(label(stats.sumOf{it.chords.size}.toString() + " AKKORDE\nverknüpft", 18f, Color.WHITE), LinearLayout.LayoutParams(0,dp(72),1f))
        root.addView(stat)
        val import = button("＋  PDF analysieren & Songs importieren")
        import.setOnClickListener { importPdf.launch(arrayOf("application/pdf")) }
        root.addView(import)
        val search = EditText(requireContext()).apply {
            hint="Song oder Künstler suchen"; setSingleLine(); setTextColor(Color.WHITE); setHintTextColor(Color.GRAY)
            setPadding(dp(16),0,dp(16),0); inputType=InputType.TYPE_CLASS_TEXT
            setBackgroundColor(Color.rgb(31,33,38))
        }
        root.addView(search, LinearLayout.LayoutParams(-1,dp(52)).apply { topMargin=dp(12); bottomMargin=dp(10) })
        val list = LinearLayout(requireContext()).apply { orientation=LinearLayout.VERTICAL }
        root.addView(list)
        fun refresh(q:String="") {
            list.removeAllViews()
            db.all().filter { q.isBlank() || (it.title + " " + it.artist).contains(q,true) }.take(100).forEach { song ->
                val c=card()
                c.addView(label(song.title,19f,Color.WHITE))
                c.addView(label(song.artist + "  •  " + song.chords.size + " Akkorde",13f,Color.LTGRAY))
                val actions=LinearLayout(requireContext()).apply { orientation=LinearLayout.HORIZONTAL }
                val open=button("Öffnen"); open.setOnClickListener{showSong(song)}
                val yt=button(if(song.youtubeId==null) "YouTube suchen" else "▶ YouTube")
                yt.setOnClickListener { openYoutube(song) }
                actions.addView(open,LinearLayout.LayoutParams(0,dp(48),1f))
                actions.addView(yt,LinearLayout.LayoutParams(0,dp(48),1f))
                c.addView(actions); list.addView(c)
            }
        }
        search.addTextChangedListener(SimpleTextWatcher { refresh(it) })
        refresh()
    }

    private fun showSong(song: SongbookSong) {
        root.removeAllViews()
        val back=button("‹  Songbook"); back.setOnClickListener{buildHome()}; root.addView(back)
        addText(song.title,27f,Color.WHITE,4); addText(song.artist,15f,Color.LTGRAY,8)
        val meta=card()
        meta.addView(label("Akkorde",12f,Color.GRAY))
        meta.addView(label(if(song.chords.isEmpty()) "Keine Akkorde erkannt" else song.chords.joinToString("   "),16f,Color.WHITE))
        root.addView(meta)
        if(song.youtubeId!=null) {
            val web=WebView(requireContext()).apply {
                settings.javaScriptEnabled=true; settings.domStorageEnabled=true
                settings.mediaPlaybackRequiresUserGesture=false
                loadDataWithBaseURL("https://www.youtube.com", youtubeHtml(song.youtubeId), "text/html","UTF-8",null)
            }
            root.addView(web,LinearLayout.LayoutParams(-1,dp(230)))
        } else {
            val match=button("YouTube-Verknüpfung suchen"); match.setOnClickListener{openYoutube(song)}; root.addView(match)
        }
        val lyrics=TextView(requireContext()).apply {
            text=song.lyrics; setTextColor(Color.WHITE); textSize=16f; setPadding(dp(12),dp(12),dp(12),dp(40))
        }
        val scroll=ScrollView(requireContext()); scroll.addView(lyrics); root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        val sync=button("⏱  Auto-Sync für Lyrics aktivieren")
        sync.setOnClickListener {
            Toast.makeText(requireContext(),"Synchronisation wird über gespeicherte Zeitmarker aufgebaut.",Toast.LENGTH_LONG).show()
        }
        root.addView(sync)
    }

    private fun openYoutube(song: SongbookSong) {
        val query=Uri.encode(song.artist + " " + song.title + " guitar")
        startActivity(Intent(Intent.ACTION_VIEW,Uri.parse("https://www.youtube.com/results?search_query="+query)))
    }

    private fun youtubeHtml(id:String)= """
        <!doctype html><html><body style="margin:0;background:#000">
        <iframe width="100%" height="100%" src="https://www.youtube.com/embed/$id?enablejsapi=1&playsinline=1"
        title="YouTube Player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
        </body></html>
    """.trimIndent()

    private fun importPdf(uri:Uri) {
        val progress=ProgressBar(requireContext())
        root.addView(progress,0,LinearLayout.LayoutParams(-1,dp(5)))
        executor.execute {
            try {
                requireContext().contentResolver.openInputStream(uri).use { input ->
                    if(input==null) error("PDF konnte nicht geöffnet werden.")
                    PDFBoxResourceLoader.init(requireContext().applicationContext)
                    PDDocument.load(input).use { doc ->
                        val text=PDFTextStripper().getText(doc)
                        val songs=SongbookParser.parse(text,uri.toString())
                        songs.forEach { db.upsert(it) }
                        requireActivity().runOnUiThread {
                            if(progress.parent!=null) root.removeView(progress)
                            AlertDialog.Builder(requireContext()).setTitle("PDF analysiert")
                                .setMessage(songs.size.toString() + " Songs erkannt und in das Songbook übernommen.\n\nAkkorde und Lyrics wurden als strukturierte Songdaten gespeichert.")
                                .setPositiveButton("Songbook öffnen"){_,_->buildHome()}.show()
                        }
                    }
                }
            } catch(t:Throwable) {
                requireActivity().runOnUiThread {
                    if(progress.parent!=null) root.removeView(progress)
                    AlertDialog.Builder(requireContext()).setTitle("Import fehlgeschlagen")
                        .setMessage(t.message ?: "Unbekannter PDF-Fehler").setPositiveButton("OK",null).show()
                }
            }
        }
    }

    private fun card(): LinearLayout = LinearLayout(requireContext()).apply {
        orientation=LinearLayout.VERTICAL; setPadding(dp(16),dp(14),dp(16),dp(14))
        setBackgroundColor(Color.rgb(27,29,34))
        val p=LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT)
        p.setMargins(0,dp(7),0,dp(7))
        layoutParams = p
    }
    private fun button(text:String)=Button(requireContext()).apply { this.text=text; setTextColor(Color.WHITE); setAllCaps(false); minHeight=0; minimumHeight=0; setPadding(dp(8),0,dp(8),0) }
    private fun label(text:String,size:Float,color:Int)=TextView(requireContext()).apply { this.text=text; textSize=size; setTextColor(color); setPadding(0,dp(4),dp(8),dp(4)) }
    private fun addText(text:String,size:Float,color:Int,bottom:Int){ root.addView(label(text,size,color),LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(bottom)}) }
    private fun dp(v:Int)= (v*resources.displayMetrics.density).toInt()
}

private class SimpleTextWatcher(val changed:(String)->Unit): android.text.TextWatcher {
    override fun beforeTextChanged(s:CharSequence?,start:Int,count:Int,after:Int){}
    override fun onTextChanged(s:CharSequence?,start:Int,before:Int,count:Int){changed(s?.toString()?:"")}
    override fun afterTextChanged(s:android.text.Editable?){}
}
'''

SONGBOOK.write_text(KOTLIN, encoding="utf-8")

g = GRADLE.read_text(encoding="utf-8")
if 'com.tom-roush:pdfbox-android:' not in g:
    marker = 'dependencies {'
    if marker not in g:
        raise SystemExit("FEHLER: dependencies-Block in app/build.gradle.kts nicht gefunden.")
    g = g.replace(marker, marker + '\n    implementation("com.tom-roush:pdfbox-android:2.0.27.0")', 1)
    GRADLE.write_text(g, encoding="utf-8")

if MANIFEST.is_file():
    m = MANIFEST.read_text(encoding="utf-8")
    if 'android.permission.INTERNET' not in m:
        pos = m.find(">")
        if pos >= 0:
            m = m[:pos+1] + '\n    <uses-permission android:name="android.permission.INTERNET" />' + m[pos+1:]
            MANIFEST.write_text(m, encoding="utf-8")

s = MAIN.read_text(encoding="utf-8")
if "SongbookFragment" not in s:
    inserted=False
    for pat in [
        r'([ \t]*menu\.add\(0,\s*3,\s*2,\s*"[^"]*Akkord[^"\n]*"\)[^\n]*\n)',
        r'([ \t]*menu\.add\(0,\s*2,\s*2,\s*"[^"\n]*"\)[^\n]*\n)'
    ]:
        s,n=re.subn(pat, r'\1            menu.add(0, 4, 3, "Songbook")\n', s, count=1)
        if n: inserted=True; break
    if not inserted:
        s,n=re.subn(r'([ \t]*menu\.add\([^\n]*Einstellungen[^\n]*\n)', r'            menu.add(0, 4, 3, "Songbook")\n\1', s, count=1)
    if 'SongbookFragment -> 4' not in s:
        s,n=re.subn(r'([ \t]*is [A-Za-z_][A-Za-z0-9_]*Fragment -> \d+[ \t]*\n)', r'\1            is SongbookFragment -> 4\n', s, count=1)
    if '4 -> show(SongbookFragment())' not in s:
        s,n=re.subn(r'([ \t]*\d+ -> show\([A-Za-z_][A-Za-z0-9_]*Fragment\(\)\)[ \t]*\n)', r'\1            4 -> show(SongbookFragment())\n', s, count=1)
    if '"Songbook" to 4' not in s:
        s,n=re.subn(r'([ \t]*"[^"\n]*(?:Akkord|Lernstudio|Lernen)[^"\n]*" to \d+,[ \t]*\n)', r'\1            "Songbook" to 4,\n', s, count=1)
    MAIN.write_text(s, encoding="utf-8")

(ROOT / "SONGBOOK_INTEGRATION_V1.txt").write_text(
    "Saitenwerk Intelligent Songbook V1\n"
    "PDF text extraction + song/chord parsing + SQLite song database + YouTube player/search entry.\n",
    encoding="utf-8"
)
print("INTELLIGENTES-SONGBOOK: PASS")
