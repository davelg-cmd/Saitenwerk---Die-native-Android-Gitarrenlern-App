from pathlib import Path
import os
import re

ROOT=Path(os.environ["PROJECT_DIR"])
MAIN=ROOT/"app/src/main/java/de/saitenwerk/app/MainActivity.kt"
GRADLE=ROOT/"app/build.gradle.kts"
s=MAIN.read_text(encoding="utf-8")

def rep(old,new,label):
    global s
    if old not in s: raise SystemExit(f"PATCH FEHLER: {label} nicht gefunden")
    s=s.replace(old,new,1)

if 'menu.add(0, 4, 3, "Lieder").setIcon(R.drawable.ic_nav_songs)' not in s:
    marker='menu.add(0, 3, 2, "Akkorde").setIcon(R.drawable.ic_nav_chords)'
    pos=s.find(marker)
    if pos<0: raise SystemExit("PATCH FEHLER: Navigation nicht gefunden")
    line_end=s.find("\n",pos)
    s=s[:line_end+1]+'            menu.add(0, 4, 3, "Lieder").setIcon(R.drawable.ic_nav_songs)\n'+s[line_end+1:]
if 'is SongsFragment -> 4' not in s:
    rep('''            is ChordsFragment -> 3
            is LearnFragment -> 5''','''            is ChordsFragment -> 3
            is SongsFragment -> 4
            is LearnFragment -> 5''',"Navigation-Sync")
if '4 -> current is SongsFragment' not in s:
    rep('''            3 -> current is ChordsFragment
            5 -> current is LearnFragment''','''            3 -> current is ChordsFragment
            4 -> current is SongsFragment
            5 -> current is LearnFragment''',"Navigation-Routing")
if '4 -> show(SongsFragment())' not in s:
    rep('''            3 -> show(ChordsFragment())
            5 -> show(LearnFragment())''','''            3 -> show(ChordsFragment())
            4 -> show(SongsFragment())
            5 -> show(LearnFragment())''',"Navigation-Ziel")

start=s.index("data class Song(")
end=s.index("class SongDetailFragment : Fragment()")
new=r'''data class Song(
    val title:String,val artist:String="",val genre:String="",val custom:Boolean=false,
    val sourcePageStart:Int=0,val sourcePageEnd:Int=0,val importedContent:String=""
)
object SongRepository {
    private const val PREFS="saitenwerk"; private const val CATALOG="songbook_catalog.json"
    private fun prefs(a:MainActivity)=a.getSharedPreferences(PREFS,0)
    fun key(song:Song)=(song.title.trim()+"|"+song.artist.trim()).lowercase()
    fun load(a:MainActivity):MutableList<Song>{
        val base=try{
            val f=File(a.filesDir,CATALOG)
            if(!f.isFile()) mutableListOf() else { val ar=JSONArray(f.readText()); MutableList(ar.length()){i->
                val o=ar.getJSONObject(i); Song(o.optString("title"),o.optString("artist"),o.optString("genre"),false,
                    o.optInt("sourcePageStart"),o.optInt("sourcePageEnd"),o.optString("importedContent"))}}
        }catch(_:Exception){mutableListOf()}
        val custom=try{val ar=JSONArray(prefs(a).getString("custom_songs","[]"));MutableList(ar.length()){i->
            ar.getJSONObject(i).let{Song(it.optString("title"),it.optString("artist"),it.optString("genre","Eigene Songs"),true)}}}catch(_:Exception){mutableListOf()}
        val seen=base.map{key(it)}.toMutableSet();base.addAll(custom.filter{seen.add(key(it))});return base
    }
    fun saveImported(a:MainActivity,songs:List<Song>){
        val ar=JSONArray();songs.forEach{ar.put(org.json.JSONObject().put("title",it.title).put("artist",it.artist).put("genre",it.genre)
            .put("sourcePageStart",it.sourcePageStart).put("sourcePageEnd",it.sourcePageEnd).put("importedContent",it.importedContent))}
        File(a.filesDir,CATALOG).writeText(ar.toString())
    }
    private fun set(a:MainActivity,n:String)=prefs(a).getStringSet(n,emptySet())?.toMutableSet()?:mutableSetOf()
    fun isFavorite(a:MainActivity,s:Song)=key(s) in set(a,"song_favorites")
    fun toggleFavorite(a:MainActivity,s:Song):Boolean{val x=set(a,"song_favorites");val k=key(s);val now=if(x.remove(k))false else{x.add(k);true};prefs(a).edit().putStringSet("song_favorites",x).apply();return now}
    fun inSetlist(a:MainActivity,s:Song)=key(s) in set(a,"song_setlist")
    fun toggleSetlist(a:MainActivity,s:Song):Boolean{val x=set(a,"song_setlist");val k=key(s);val now=if(x.remove(k))false else{x.add(k);true};prefs(a).edit().putStringSet("song_setlist",x).apply();return now}
    fun addRecent(a:MainActivity,s:Song){val x=prefs(a).getString("song_recent","")!!.split("\n").filter{it.isNotBlank()}.toMutableList();x.remove(key(s));x.add(0,key(s));prefs(a).edit().putString("song_recent",x.take(30).joinToString("\n")).apply()}
    fun isRecent(a:MainActivity,s:Song)=key(s) in prefs(a).getString("song_recent","")!!.split("\n")
    fun hasSongSheet(a:MainActivity,s:Song)=s.importedContent.isNotBlank()||s.custom||run{val p="song_arrangement_${s.title}|${s.artist}_";listOf("Intro","Strophe 1","Strophe 2","Strophe 3","Refrain","Bridge","Solo","Outro").any{q->val r=prefs(a).getString(p+q,"{}")?:"{}";try{org.json.JSONObject(r).optString("content").isNotBlank()||org.json.JSONObject(r).optString("chords").isNotBlank()}catch(_:Exception){false}}}
    fun addCustom(a:MainActivity,s:Song){val ar=try{JSONArray(prefs(a).getString("custom_songs","[]"))}catch(_:Exception){JSONArray()};if(load(a).any{key(it)==key(s)})return;ar.put(org.json.JSONObject().put("title",s.title).put("artist",s.artist).put("genre",s.genre.ifBlank{"Eigene Songs"}));prefs(a).edit().putString("custom_songs",ar.toString()).apply()}
}
class SongsFragment : Fragment(){
    private var currentSongs=mutableListOf<Song>()
    private val pdfPicker=registerForActivityResult(ActivityResultContracts.OpenDocument()){uri->
        if(uri==null)return@registerForActivityResult
        val a=requireActivity() as MainActivity
        try{requireActivity().contentResolver.takePersistableUriPermission(uri,android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)}catch(_:Exception){}
        val d=android.app.ProgressDialog(a).apply{setMessage("Songbook wird vollständig eingelesen …");setCancelable(false);show()}
        Thread{try{SongbookPdfImporter.importPdf(a,uri);a.runOnUiThread{d.dismiss();Toast.makeText(a,"Songbook erfolgreich importiert · 452 Songs offline verfügbar",Toast.LENGTH_LONG).show();parentFragmentManager.beginTransaction().replace(id,SongsFragment()).commit()}}
        catch(t:Throwable){a.runOnUiThread{d.dismiss();Toast.makeText(a,"PDF-Import fehlgeschlagen: ${t.message}",Toast.LENGTH_LONG).show()}}}.start()
    }
    override fun onCreateView(i:android.view.LayoutInflater,c:ViewGroup?,s:Bundle?):View{
        val a=requireActivity() as MainActivity;val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL};root.addView(a.title("Liederbuch"))
        val hero=a.card();val box=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(18),a.dp(16),a.dp(18),a.dp(16))}
        box.addView(TextView(a).apply{text="🎸  Dein persönliches Premium-Songbook";textSize=20f;setTypeface(typeface,android.graphics.Typeface.BOLD);setTextColor(a.getColor(R.color.sw_copper))})
        box.addView(a.body("Das komplette private PDF-Songbook wird auf dem Gerät eingelesen. Texte und Akkorde bleiben lokal; das Original-PDF bleibt ebenfalls privat."))
        box.addView(TextView(a).apply{text="452 Songs · vollständige Songseiten · offline";textSize=13f;setTextColor(a.getColor(R.color.sw_muted));setPadding(0,a.dp(8),0,0)})
        hero.addView(box);root.addView(hero,LinearLayout.LayoutParams(-1,-2).apply{setMargins(a.dp(16),a.dp(6),a.dp(16),a.dp(10))})
        val imp=a.button("⬆  Eigenes Songbook-PDF importieren").apply{tag="saitenwerk-primary"};imp.setOnClickListener{pdfPicker.launch(arrayOf("application/pdf"))}
        root.addView(imp,LinearLayout.LayoutParams(-1,a.dp(52)).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(8))})
        val info=a.body("Importiert wird das vollständige PDF einschließlich Inhaltsverzeichnis, aller Songseiten, Text-/Akkorddaten und Originalseiten. Der Import ersetzt das bisherige lokale Songbook.");root.addView(info)
        val search=EditText(a).apply{hint="Titel, Künstler, Text oder Akkord suchen";setSingleLine();setTextColor(a.getColor(R.color.sw_text));setHintTextColor(a.getColor(R.color.sw_muted));setPadding(a.dp(16),0,a.dp(16),0);background=android.graphics.drawable.GradientDrawable().apply{setColor(a.getColor(R.color.sw_surface));cornerRadius=a.dp(14).toFloat();setStroke(a.dp(1),a.getColor(R.color.sw_surface2))}}
        root.addView(search,LinearLayout.LayoutParams(-1,a.dp(50)).apply{setMargins(a.dp(16),a.dp(8),a.dp(16),a.dp(8))})
        val list=RecyclerView(a).apply{layoutManager=LinearLayoutManager(a)};val adapter=SongAdapter(emptyList(),a){a.openSong(it)};list.adapter=adapter;root.addView(list,LinearLayout.LayoutParams(-1,0,1f))
        fun refresh(){currentSongs=SongRepository.load(a);val q=search.text.toString().trim().lowercase();val f=if(q.isBlank())currentSongs else currentSongs.filter{listOf(it.title,it.artist,it.genre,it.importedContent).joinToString(" ").lowercase().contains(q)};adapter.submit(f);info.text=if(currentSongs.isEmpty())"Noch kein privates Songbook importiert. Wähle dein PDF oben aus." else "${currentSongs.size} Songs lokal verfügbar · Suche durchsucht Titel, Künstler, Text und Akkorde."}
        search.addTextChangedListener(object:TextWatcher{override fun beforeTextChanged(s:CharSequence?,st:Int,count:Int,after:Int){};override fun onTextChanged(s:CharSequence?,st:Int,b:Int,c:Int){refresh()};override fun afterTextChanged(e:Editable?){}});refresh();return root
    }
}
class SongAdapter(private val all:List<Song>,private val host:MainActivity,private val onClick:(Song)->Unit):RecyclerView.Adapter<SongAdapter.Holder>(){
    private var data=all.toList();class Holder(v:View):RecyclerView.ViewHolder(v)
    override fun onCreateViewHolder(parent:ViewGroup,viewType:Int):Holder{val card=MaterialCardView(host).apply{setCardBackgroundColor(host.getColor(R.color.sw_surface));radius=host.dp(14).toFloat();strokeColor=host.getColor(R.color.sw_surface2);strokeWidth=host.dp(1);addView(LinearLayout(host).apply{orientation=LinearLayout.VERTICAL;setPadding(host.dp(16),host.dp(12),host.dp(16),host.dp(12))})};return Holder(card)}
    override fun getItemCount()=data.size
    override fun onBindViewHolder(h:Holder,p:Int){val s=data[p];val c=h.itemView as MaterialCardView;val t=c.getChildAt(0) as LinearLayout;t.removeAllViews();t.addView(TextView(host).apply{text=(if(SongRepository.isFavorite(host,s))"★  " else "♫  ")+s.title;setTextColor(host.getColor(R.color.sw_text));textSize=16f;setTypeface(typeface,android.graphics.Typeface.BOLD)});t.addView(TextView(host).apply{text=listOf(s.artist.ifBlank{"Künstler unbekannt"},"Seite ${s.sourcePageStart}${if(s.sourcePageEnd>s.sourcePageStart)"–${s.sourcePageEnd}" else ""}").joinToString("   ·   ");setTextColor(host.getColor(R.color.sw_muted));textSize=12f;setPadding(0,host.dp(4),0,0)});c.setOnClickListener{onClick(s)};c.layoutParams=RecyclerView.LayoutParams(-1,-2).apply{setMargins(host.dp(12),host.dp(4),host.dp(12),host.dp(4))}}
    fun submit(items:List<Song>){data=items;notifyDataSetChanged()}
}
'''
s=s[:start]+new+s[end:]
bundle_fields = """
                putInt("sourcePageStart", song.sourcePageStart)
                putInt("sourcePageEnd", song.sourcePageEnd)
                putString("importedContent", song.importedContent)"""
if 'putString("importedContent", song.importedContent)' not in s:
    genre_match = re.search(r'(?m)^(\s*)putString\(\s*"genre"\s*,\s*song\.genre\s*\)\s*$', s)
    if genre_match:
        at = genre_match.end()
        s = s[:at] + bundle_fields + s[at:]
    else:
        artist_match = re.search(r'(?m)^(\s*)putString\(\s*"artist"\s*,\s*song\.artist\s*\)\s*$', s)
        if not artist_match:
            raise SystemExit("PATCH FEHLER: Song-Bundle: weder Genre- noch Künstlerfeld im Speicherblock gefunden")
        at = artist_match.end()
        s = s[:at] + bundle_fields + s[at:]
old_bundle_read = '''            Song(it.getString("title").orEmpty(), it.getString("artist").orEmpty(), it.getString("genre").orEmpty())
        } ?: Song("Unbekannter Titel")'''
new_bundle_read = '''            Song(it.getString("title").orEmpty(), it.getString("artist").orEmpty(), it.getString("genre").orEmpty(), false,
                it.getInt("sourcePageStart",0), it.getInt("sourcePageEnd",0), it.getString("importedContent").orEmpty())
        } ?: Song("Unbekannter Titel")'''
if old_bundle_read in s:
    rep(old_bundle_read, new_bundle_read, "Song-Bundle-Auslesen")
else:
    marker = 'val song = arguments?.let {'
    start_bundle = s.find(marker)
    end_bundle = s.find('} ?: Song("Unbekannter Titel")', start_bundle)
    if start_bundle < 0 or end_bundle < 0:
        raise SystemExit("PATCH FEHLER: Song-Bundle-Block nicht gefunden")
    bundle_reader = s[start_bundle:end_bundle]
    required_bundle_fields = [
        'it.getInt("sourcePageStart",0)',
        'it.getInt("sourcePageEnd",0)',
        'it.getString("importedContent").orEmpty()'
    ]
    missing_bundle_fields = [field for field in required_bundle_fields if field not in bundle_reader]
    if missing_bundle_fields:
        raise SystemExit("PATCH FEHLER: Song-Bundle-Felder fehlen: " + ", ".join(missing_bundle_fields))
    print("SONG-BUNDLE: vorhandene PDF-Felder bereits korrekt – keine doppelte Änderung nötig")
rep('''        val bundledSheet = try {
            val raw = a.assets.open("public_domain_sheets.json").bufferedReader().use { it.readText() }
            val arr = JSONArray(raw)
            (0 until arr.length()).asSequence()
                .map { arr.getJSONObject(it) }
                .firstOrNull { it.optString("title") == song.title && it.optString("artist") == song.artist }
                ?: org.json.JSONObject()
        } catch (_: Exception) { org.json.JSONObject() }

        fun loadSection(name: String): org.json.JSONObject {''','''        val importedSheet = if(song.importedContent.isNotBlank()) org.json.JSONObject().put("content",song.importedContent) else org.json.JSONObject()

        fun loadSection(name: String): org.json.JSONObject {''',"Legacy-Sheet")
rep('''            if (name == "Gesamter Song" && bundledSheet.optString("content").isNotBlank()) {
                return org.json.JSONObject().put("content", bundledSheet.optString("content"))
                    .put("capo", bundledSheet.optInt("capo", 0))
                    .put("transpose", bundledSheet.optInt("transpose", 0))
                    .put("formatVersion", 4)
            }''','''            if(name=="Gesamter Song"&&importedSheet.optString("content").isNotBlank()){
                return org.json.JSONObject().put("content",importedSheet.optString("content")).put("formatVersion",5)
            }''',"Legacy-Laden")
rep('''        var playerTempo = bundledSheet.optInt("tempo", 72).coerceIn(40, 160)''','''        var playerTempo = 72''',"Legacy-Tempo")
needle='''        root.addView(TextView(a).apply {
            text = listOf(song.artist, song.genre).filter { it.isNotBlank() }.joinToString(" · ")
            textSize = 14f
            setTextColor(a.getColor(R.color.sw_copper))
            setPadding(a.dp(20), 0, a.dp(20), a.dp(10))
        })'''
rep(needle,needle+'''\n        if(song.sourcePageStart>0){val original=a.button("▣  Original-PDF-Seiten ansehen");original.setOnClickListener{SongbookPdfViewer.show(a,song.sourcePageStart,song.sourcePageEnd)};root.addView(original,LinearLayout.LayoutParams(-1,a.dp(48)).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(8))})}''',"Original-PDF-Button")
MAIN.write_text(s,encoding="utf-8")
g=GRADLE.read_text(encoding="utf-8")
if "pdfbox-android:2.0.27.0" not in g:g=g.replace('implementation("com.google.android.material:material:1.12.0")','implementation("com.google.android.material:material:1.12.0")\n    implementation("com.tom-roush:pdfbox-android:2.0.27.0")')
GRADLE.write_text(g,encoding="utf-8")
for rel in ["app/src/main/assets/saitenwerk_legacy.html","app/src/main/assets/songs.json","app/src/main/assets/public_domain_sheets.json","SONGBOOK_PUBLIC_DOMAIN.md","CHANGELOG_ALPHA7_LIEDERBUCH.md","UPDATE_ALPHA7_SONGREADER_V3.md","fix_v3.py","UPDATEFIX_README.md"]:
    p=ROOT/rel
    if p.exists():p.unlink()
(ROOT/"app/src/main/java/de/saitenwerk/app/SongbookPdfImporter.kt").write_text((Path(os.environ["GITHUB_WORKSPACE"])/"ci/songbook_pdf_importer.kt").read_text(),encoding="utf-8")
(ROOT/"app/src/main/java/de/saitenwerk/app/SongbookPdfViewer.kt").write_text((Path(os.environ["GITHUB_WORKSPACE"])/"ci/songbook_pdf_viewer.kt").read_text(),encoding="utf-8")
(ROOT/"app/src/main/res/drawable/ic_nav_songs.xml").write_text((Path(os.environ["GITHUB_WORKSPACE"])/"ci/ic_nav_songs.xml").read_text(),encoding="utf-8")
p=ROOT/"app/src/main/java/de/saitenwerk/app/MainActivity.kt";s=p.read_text(encoding="utf-8")
if '"25.11.2026 · Build $buildNumber"' not in s:
    s=s.replace('''        val changes = listOf(
            "20.11.2026 · Build $buildNumber"''','''        val changes = listOf(
            "25.11.2026 · Build $buildNumber" to "Persönliches Premium-Songbook vollständig neu aufgebaut: altes gemeinfreies/Legacy-Liederbuch entfernt. Das private PDF wird mit allen 452 Songs, vollständigen Songseiten und Inhaltsverzeichnis auf dem Gerät importiert und lokal katalogisiert. Suche durchsucht Titel, Künstler, Text und Akkorde; Original-PDF-Seiten bleiben pro Song aufrufbar. Favoriten, Setlisten, Songpraxis, Transponierung, Kapodaster und Songplayer bleiben mit dem neuen Katalog verbunden. PDF und Songdaten werden nicht als öffentliche Repository-Assets ausgeliefert.",
            "20.11.2026 · Build $buildNumber"''',1)
    p.write_text(s,encoding="utf-8")
(Path(os.environ["PROJECT_DIR"])/"UPLOAD_INSTRUCTIONS.md").write_text("# Saitenwerk – Premium-Songbook\n\nDer Quellstand basiert auf Build 436. Das persönliche PDF wird vollständig auf dem Gerät importiert: 452 Songs, vollständige Songseiten, Text/Akkorde und Original-PDF-Seiten. Die PDF-Datei selbst bleibt absichtlich außerhalb des öffentlichen Repositorys.\n\nNach Installation: Lieder → Eigenes Songbook-PDF importieren.\n",encoding="utf-8")
print("PREMIUM_SONGBOOK_PATCH_OK")