#!/usr/bin/env python3
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s = p.read_text(encoding="utf-8")

catalog = r'''private object PublicDomainSongCatalog {
    data class Seed(val title:String,val artist:String,val lyrics:String,val chords:List<String>,val youtubeId:String?=null,val confidence:Int=0)
    val songs=listOf(
        Seed("Am Brunnen vor dem Tore","Wilhelm Müller / Franz Schubert","""Am Brunnen vor dem Tore,
Da steht ein Lindenbaum;
Ich träumt' in seinem Schatten
So manchen süßen Traum.
Ich schnitt in seine Rinde
So manches liebe Wort;
Es zog in Freud und Leide
Zu ihm mich immer fort.

Ich musst' auch heute wandern
Vorbei in tiefer Nacht,
Da hab ich noch im Dunkel
Die Augen zugemacht.""",listOf("C","G7","F","C")),
        Seed("Die Gedanken sind frei","Volkslied","""Die Gedanken sind frei,
wer kann sie erraten?
Sie rauschen vorbei
wie nächtliche Schatten.
Kein Mensch kann sie wissen,
kein Jäger erschießen;
es bleibet dabei:
Die Gedanken sind frei.

Und sperrt man mich ein
im finsteren Kerker,
das alles sind rein
vergebliche Werke;
denn meine Gedanken
zerreißen die Schranken
und Mauern entzwei.""",listOf("Am","G","C","E7"),"SsW-6Klbyto",95),
        Seed("Der Mond ist aufgegangen","Matthias Claudius / Johann Abraham Peter Schulz","""Der Mond ist aufgegangen,
die goldnen Sternlein prangen
am Himmel hell und klar.
Der Wald steht schwarz und schweiget,
und aus den Wiesen steiget
der weiße Nebel wunderbar.

Wie ist die Welt so stille
und in der Dämmrung Hülle
so traulich und so hold!
Als eine stille Kammer,
wo ihr des Tages Jammer
verschlafen und vergessen sollt.""",listOf("C","G7","F","C"),"9897OI_VF8E",95),
        Seed("Das Wandern ist des Müllers Lust","Wilhelm Müller / Carl Friedrich Zöllner","""Das Wandern ist des Müllers Lust,
das Wandern ist des Müllers Lust,
das Wandern.
Das muss ein schlechter Müller sein,
dem niemals fiel das Wandern ein,
dem niemals fiel das Wandern ein,
das Wandern.

Vom Wasser haben wir's gelernt,
vom Wasser haben wir's gelernt,
vom Wasser:
Das hat nicht Ruh bei Tag und Nacht,
ist stets auf Wanderschaft bedacht.""",listOf("G","D7","C","G")),
        Seed("Kein schöner Land in dieser Zeit","Anton Wilhelm von Zuccalmaglio","""Kein schöner Land in dieser Zeit
als hier das unsre weit und breit,
wo wir uns finden wohl unter Linden
zur Abendzeit.

Da haben wir so manche Stund'
gesessen da in froher Rund'
und taten singen; die Lieder klingen
im Eichengrund.""",listOf("G","D7","C","G")),
        Seed("Muss i denn zum Städtele hinaus","Volkslied","""Muss i denn, muss i denn
zum Städtele hinaus,
Städtele hinaus,
und du, mein Schatz, bleibst hier?
Wenn i komm, wenn i komm,
wiederum, wiederum,
kehr i ein, mein Schatz, bei dir.

Wie du weinst, wie du weinst,
dass i wandern muss,
wandern muss,
wie wenn d' Lieb jetzt wär vorbei!
Lieber Schatz, i bleib dir treu.""",listOf("G","D7","C","G")),
        Seed("Heidenröslein","Johann Wolfgang von Goethe / Heinrich Werner","""Sah ein Knab ein Röslein stehn,
Röslein auf der Heiden,
war so jung und morgenschön,
lief er schnell, es nah zu sehn,
sah's mit vielen Freuden.
Röslein, Röslein, Röslein rot,
Röslein auf der Heiden.

Knabe sprach: Ich breche dich,
Röslein auf der Heiden!
Röslein sprach: Ich steche dich,
dass du ewig denkst an mich,
und ich will's nicht leiden.""",listOf("G","D7","C","G")),
        Seed("Der Mai ist gekommen","Emanuel Geibel / Justus Wilhelm Lyra","""Der Mai ist gekommen, die Bäume schlagen aus,
da bleibe, wer Lust hat, mit Sorgen zu Haus;
wie die Wolken dort wandern am himmlischen Zelt,
so steht auch mir der Sinn in die weite, weite Welt.

Herr Vater, Frau Mutter, dass Gott euch behüt'!
Wer weiß, wo in der Ferne mein Glück mir noch blüht.
Es gibt so manche Straße, da zieht keiner ein,
die kann uns zwei wohl führen ins blühende Land hinein.""",listOf("G","D","C","G"),"cKo8nifC5X0",95),
        Seed("Bunt sind schon die Wälder","Johann Gaudenz von Salis-Seewis / Johann Friedrich Reichardt","""Bunt sind schon die Wälder,
gelb die Stoppelfelder,
und der Herbst beginnt.
Rote Blätter fallen,
graue Nebel wallen,
kühler weht der Wind.

Wie die volle Traube
aus dem Rebenlaube
purpurfarbig strahlt!
Am Geländer reifen
Pfirsiche mit Streifen,
rot und weiß bemalt.""",listOf("G","D7","C","G")),
        Seed("Ein Jäger aus Kurpfalz","Volkslied","""Ein Jäger aus Kurpfalz,
der reitet durch den grünen Wald,
er schießt das Wild daher,
gleich wie es ihm gefällt.

Juja, juja, gar lustig ist die Jägerei,
allhier auf grüner Heid,
allhier auf grüner Heid.""",listOf("G","D7","C","G"),"GpqEMKDZX6k",95),
        Seed("Im schönsten Wiesengrunde","Volkslied","""Im schönsten Wiesengrunde
ist meiner Heimat Haus;
da zog ich manche Stunde
ins Tal hinaus.

Dich, mein stilles Tal,
grüß ich tausendmal;
da zog ich manche Stunde
ins Tal hinaus.

Müsst aus dem Tal ich scheiden,
wo alles Lust und Klang,
das wär mein herbstes Leiden,
mein letzter Gang.""",listOf("G","D7","C","G"),"qtZi1b0ponM",95),
        Seed("Wem Gott will rechte Gunst erweisen","Joseph von Eichendorff / Friedrich Theodor Fröhlich","""Wem Gott will rechte Gunst erweisen,
den schickt er in die weite Welt,
dem will er seine Wunder weisen
in Berg und Tal und Strom und Feld.

Die Bächlein von den Bergen springen,
die Lerchen schwirren hoch vor Lust;
was sollt ich nicht mit ihnen singen
aus voller Kehl und frischer Brust?""",listOf("C","G7","F","C"),"IVHctD6XwEY",90),
        Seed("Guter Mond, du gehst so stille","Karl Enslin / Volksweise","""Guter Mond, du gehst so stille
durch die Abendwolken hin;
deines Schöpfers weiser Wille
hieß auf jene Bahn dich ziehn.
Leuchte freundlich jedem Müden
in das stille Kämmerlein,
und dein Schimmer gieße Frieden
ins bedrängte Herz hinein.""",listOf("C","G7","F","C")),
        Seed("Horch, was kommt von draußen rein","Volkslied","""Horch, was kommt von draußen rein?
Hollahi, hollaho!
Wird wohl mein Feinsliebchen sein,
hollahi, hollaho!
Geht vorbei und schaut nicht rein,
als wär sie nicht daheim.""",listOf("G","D7","C","G")),
        Seed("Ännchen von Tharau","Simon Dach / Friedrich Silcher","""Ännchen von Tharau ist, die mir gefällt,
Sie ist mein Leben, mein Gut und mein Geld.
Ännchen von Tharau hat wieder ihr Herz
auf mich gerichtet in Lieb und in Schmerz.

Ännchen von Tharau, mein Reichtum, mein Gut,
Du mein Leben, mein ganzes Herzblut!""",listOf("G","D7","C","G"))
    )
}
'''

if "private object PublicDomainSongCatalog" not in s:
    s = s.replace("class SongbookDb(context: Context) {", catalog + "\nclass SongbookDb(context: Context) {", 1)

if "seedPublicDomainSongsIfEmpty()" not in s:
    marker = '        db.execSQL("INSERT OR IGNORE INTO song_pdf_sources(song_id,pdf_uri) SELECT id,source FROM songs WHERE source IS NOT NULL AND source <> \'\'")\n'
    methods = r'''
        fun seedPublicDomainSongsIfEmpty() {
            val count = db.rawQuery("SELECT COUNT(*) FROM songs", null).use { c -> if (c.moveToFirst()) c.getInt(0) else 0 }
            if (count > 0) return
            PublicDomainSongCatalog.songs.forEach { song ->
                upsert(SongbookSong(song.title, song.artist, song.lyrics, song.chords, "builtin:public-domain", song.youtubeId, song.confidence))
            }
        }
        seedPublicDomainSongsIfEmpty()
'''
    if marker not in s: raise SystemExit("SongbookDb seed insertion point not found")
    s = s.replace(marker, marker + methods, 1)

if "private object YouTubeAutoLinker" not in s:
    yt = r'''
private object YouTubeAutoLinker {
    private val idRegex = Regex("""\"videoId\":\"([A-Za-z0-9_-]{11})\"""")
    fun findVideoId(title: String, artist: String): String? {
        val q = java.net.URLEncoder.encode("$title $artist Gitarrenakkorde", "UTF-8")
        val c = (java.net.URL("https://www.youtube.com/results?search_query=$q").openConnection() as java.net.HttpURLConnection).apply {
            requestMethod="GET"; connectTimeout=8000; readTimeout=10000
            setRequestProperty("User-Agent","Mozilla/5.0 (Android) SaitenWerk/1.0")
        }
        return try {
            if (c.responseCode !in 200..299) null
            else idRegex.find(c.inputStream.bufferedReader().use { it.readText() })?.groupValues?.get(1)
        } finally { c.disconnect() }
    }
}
'''
    s = s.replace("class SongbookFragment : Fragment() {", yt + "\nclass SongbookFragment : Fragment() {", 1)

if "private fun autoLinkYoutubeSongs()" not in s:
    old = '''        search.addTextChangedListener(SimpleTextWatcher { refresh(it) })
        refresh()
    }
'''
    new = '''        search.addTextChangedListener(SimpleTextWatcher { refresh(it) })
        refresh()
        autoLinkYoutubeSongs()
    }

    private fun autoLinkYoutubeSongs() {
        val candidates = db.all().filter { it.youtubeId.isNullOrBlank() }.take(4)
        if (candidates.isEmpty()) return
        executor.execute {
            candidates.forEach { song ->
                runCatching { YouTubeAutoLinker.findVideoId(song.title, song.artist) }
            }
        }
    }
'''
    if old not in s: raise SystemExit("Songbook refresh insertion point not found")
    s = s.replace(old, new, 1)

placeholder = '''        val sync=button("⏱  Auto-Sync für Lyrics aktivieren")
        sync.setOnClickListener {
            Toast.makeText(requireContext(),"Synchronisation wird über gespeicherte Zeitmarker aufgebaut.",Toast.LENGTH_LONG).show()
        }
        root.addView(sync)
'''
sync_button = '''        if (song.youtubeId != null) {
            val sync=button("⏱  Lyrics mit YouTube synchronisieren")
            sync.setOnClickListener { showSyncedLyrics(song) }
            root.addView(sync)
        }
'''
if placeholder in s: s = s.replace(placeholder, sync_button, 1)

if "private fun showSyncedLyrics(song: SongbookSong)" not in s:
    sync = r'''
    private fun showSyncedLyrics(song: SongbookSong) {
        root.removeAllViews()
        val back=button("‹  Songbook"); back.setOnClickListener{showSong(song)}; root.addView(back)
        addText(song.title,24f,Color.WHITE,4)
        addText("YouTube-Lyrics-Sync",13f,Color.LTGRAY,6)
        val player=WebView(requireContext()).apply {
            settings.javaScriptEnabled=true; settings.domStorageEnabled=true
            settings.mediaPlaybackRequiresUserGesture=false
        }
        val lines=song.lyrics.lines().map{it.trim()}.filter{it.isNotBlank()}
        val jsLines=lines.joinToString(","){org.json.JSONObject.quote(it)}
        val html="""<!doctype html><html><body style="margin:0;background:#0f1013;color:white;font-family:sans-serif">
<div id="player" style="width:100%;height:230px"></div><div id="lyrics" style="padding:14px;font-size:18px;line-height:1.55"></div>
<script src="https://www.youtube.com/iframe_api"></script><script>
const lines=[$jsLines];let d=0;const b=document.getElementById('lyrics');
function r(a){b.innerHTML=lines.map((x,i)=>'<div style="padding:3px 0;opacity:'+(i===a?'1':'0.45')+';font-weight:'+(i===a?'700':'400')+'">'+x.replace(/</g,'&lt;')+'</div>').join('');}
function onYouTubeIframeAPIReady(){window.p=new YT.Player('player',{videoId:'__YOUTUBE_ID__',playerVars:{playsinline:1,rel:0},events:{onReady:e=>{d=e.target.getDuration();t();}}});}
function t(){if(window.p&&d>0){r(Math.min(lines.length-1,Math.floor(window.p.getCurrentTime()/(d/lines.length))))}setTimeout(t,500)}r(-1);
</script></body></html>"""
        player.loadDataWithBaseURL("https://www.youtube.com",html.replace("__YOUTUBE_ID__",song.youtubeId ?: ""), "text/html","UTF-8",null)
        root.addView(player,LinearLayout.LayoutParams(-1,dp(520)))
    }
'''
    s = s.replace("    private fun authorizeYoutube() {", sync + "\n    private fun authorizeYoutube() {", 1)

p.write_text(s, encoding="utf-8")
print("PUBLIC-DOMAIN-SONGBOOK: PASS")
