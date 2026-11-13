package de.saitenwerk.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.View
import android.widget.*
import android.media.ToneGenerator
import android.media.AudioRecord
import android.media.AudioFormat
import android.media.MediaRecorder
import android.media.AudioManager
import android.os.Handler
import android.os.Looper
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.card.MaterialCardView
import com.google.android.material.color.DynamicColors
import org.json.JSONArray
import kotlin.math.roundToInt
import kotlin.math.pow

class MainActivity : AppCompatActivity() {
    private var micGrantedAction: (() -> Unit)? = null
    private val requestMic = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) { Toast.makeText(this, "Mikrofon freigegeben", Toast.LENGTH_SHORT).show(); micGrantedAction?.invoke() }
        else Toast.makeText(this, "Für das Stimmgerät wird Mikrofonzugriff benötigt.", Toast.LENGTH_LONG).show()
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        DynamicColors.applyIfAvailable(this)
        setContentView(buildRoot())
        if (savedInstanceState == null) show(HomeFragment())
    }
    private fun buildRoot(): View {
        val root = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL; setBackgroundColor(getColor(R.color.sw_navy)) }
        val frame = FrameLayout(this).apply { id=View.generateViewId() }
        root.addView(frame, LinearLayout.LayoutParams(-1,0,1f))
        val nav = BottomNavigationView(this).apply {
            setBackgroundColor(getColor(R.color.sw_surface)); itemIconTintList=null
            menu.add(0,1,0,"Start").setIcon(android.R.drawable.ic_menu_view)
            menu.add(0,2,1,"Stimmen").setIcon(android.R.drawable.ic_btn_speak_now)
            menu.add(0,3,2,"Akkorde").setIcon(android.R.drawable.ic_menu_edit)
            menu.add(0,4,3,"Lieder").setIcon(android.R.drawable.ic_menu_agenda)
            menu.add(0,5,4,"Lernen").setIcon(android.R.drawable.ic_media_play)
            menu.add(0,6,5,"Pfad").setIcon(android.R.drawable.ic_menu_sort_by_size)
            setOnItemSelectedListener { item -> when(item.itemId){1->show(HomeFragment());2->show(TunerFragment());3->show(ChordsFragment());4->show(SongsFragment());5->show(LearnFragment());6->show(PathFragment())}; true }
        }
        root.addView(nav, LinearLayout.LayoutParams(-1, dp(72)))
        return root
    }
    private fun show(f: Fragment) { supportFragmentManager.beginTransaction().replace(findFrame(), f).commit() }
    fun openSection(id:Int) { when(id){1->show(HomeFragment());2->show(TunerFragment());3->show(ChordsFragment());4->show(SongsFragment());5->show(LearnFragment());6->show(PathFragment())} }
    fun openSong(song:Song) { show(SongDetailFragment().apply { arguments=Bundle().apply { putString("title",song.title); putString("artist",song.artist); putString("genre",song.genre) } }) }
    private fun findFrame(): Int = (window.decorView as ViewGroup).let { findFrameRecursive(it) }
    private fun findFrameRecursive(v: ViewGroup): Int { for(i in 0 until v.childCount){ val c=v.getChildAt(i); if(c is FrameLayout && c.id!=View.NO_ID)return c.id; if(c is ViewGroup){val id=findFrameRecursive(c); if(id!=0)return id}}; return 0 }
    fun askMic(onGranted: () -> Unit){
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED) onGranted()
        else { micGrantedAction=onGranted; requestMic.launch(Manifest.permission.RECORD_AUDIO) }
    }
    fun dp(v:Int)= (v*resources.displayMetrics.density).toInt()
    fun title(text:String)=TextView(this).apply{this.text=text;setTextColor(getColor(R.color.sw_text));textSize=28f;setTypeface(typeface,1);setPadding(dp(20),dp(24),dp(20),dp(12))}
    fun card():MaterialCardView=MaterialCardView(this).apply{setCardBackgroundColor(getColor(R.color.sw_surface));radius=dp(18).toFloat();strokeColor=getColor(R.color.sw_surface2);strokeWidth=1}
    fun button(text:String)=Button(this).apply{this.text=text;setAllCaps(false);setTextColor(getColor(R.color.sw_text));setBackgroundColor(getColor(R.color.sw_surface2))}
}

class HomeFragment: Fragment(){ override fun onCreateView(i:android.view.LayoutInflater,c:android.view.ViewGroup?,s:Bundle?):View{
 val a=requireActivity() as MainActivity; val l=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL}; l.addView(a.title("Heute Gitarre spielen."));
 val p=TextView(a).apply{text="Dein persönlicher Gitarrenbegleiter – stimmen, Akkorde lernen, Songs spielen und Schritt für Schritt besser werden.";setTextColor(a.getColor(R.color.sw_muted));textSize=16f;setPadding(a.dp(20),0,a.dp(20),a.dp(18))};l.addView(p)
 val c=a.card(); val box=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(18),a.dp(18),a.dp(18),a.dp(18))}; box.addView(TextView(a).apply{text="500+ Lernlieder";textSize=22f;setTextColor(a.getColor(R.color.sw_copper))});box.addView(TextView(a).apply{text="Offline • persönliche Fortschritte • native Android-Oberfläche";setTextColor(a.getColor(R.color.sw_muted))});c.addView(box);l.addView(c,LinearLayout.LayoutParams(-1,a.dp(120)).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(12))})
 val actions=listOf("🎸  Stimmgerät","◉  Akkorde lernen","♫  Liederbuch","◆  Lernstudio","↗  Lernpfad"); actions.forEachIndexed{index,t->val b=a.button(t);b.setOnClickListener{a.openSection(listOf(2,3,4,5,6)[index])};l.addView(b,LinearLayout.LayoutParams(-1,a.dp(52)).apply{setMargins(a.dp(16),a.dp(5),a.dp(16),a.dp(5))})};return ScrollView(a).apply{addView(l)}} }

class TunerFragment:Fragment(){
 private var recorder:AudioRecord?=null; @Volatile private var active=false; private var worker:Thread?=null
 private lateinit var noteView:TextView; private lateinit var hzView:TextView; private lateinit var centsView:TextView; private lateinit var startButton:Button; private lateinit var meter:ProgressBar
 override fun onCreateView(i:android.view.LayoutInflater,c:android.view.ViewGroup?,s:Bundle?):View{
  val a=requireActivity() as MainActivity;val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL}
  root.addView(a.title("Stimmgerät"));root.addView(TextView(a).apply{text="Chromatischer Tuner · Standardstimmung E–A–D–G–B–E";setTextColor(a.getColor(R.color.sw_muted));setPadding(a.dp(20),0,a.dp(20),a.dp(16))})
  val card=a.card();val box=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;gravity=android.view.Gravity.CENTER;setPadding(a.dp(20),a.dp(22),a.dp(20),a.dp(22))}
  noteView=TextView(a).apply{text="—";textSize=64f;gravity=android.view.Gravity.CENTER;setTextColor(a.getColor(R.color.sw_copper));setTypeface(typeface,1)}
  hzView=TextView(a).apply{text="Warte auf einen Ton";textSize=18f;gravity=android.view.Gravity.CENTER;setTextColor(a.getColor(R.color.sw_text))}
  centsView=TextView(a).apply{text="0 Cent";textSize=16f;gravity=android.view.Gravity.CENTER;setTextColor(a.getColor(R.color.sw_muted));setPadding(0,a.dp(8),0,a.dp(8))}
  meter=ProgressBar(a,null,android.R.attr.progressBarStyleHorizontal).apply{max=100;progress=50}
  startButton=a.button("Stimmen starten");startButton.setOnClickListener{if(active)stopTuner() else a.askMic{startTuner()}}
  box.addView(noteView,LayoutParams(-1,a.dp(88)));box.addView(hzView,LayoutParams(-1,a.dp(34)));box.addView(centsView,LayoutParams(-1,a.dp(32)));box.addView(meter,LayoutParams(-1,a.dp(12)));box.addView(startButton,LayoutParams(-1,a.dp(52)).apply{topMargin=a.dp(22)})
  card.addView(box);root.addView(card,LinearLayout.LayoutParams(-1,-2).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(16))})
  root.addView(TextView(a).apply{text="Tipp: Spiele eine einzelne Saite möglichst gleichmäßig an und dämpfe die übrigen Saiten.";setTextColor(a.getColor(R.color.sw_muted));textSize=14f;setPadding(a.dp(20),0,a.dp(20),0)})
  return ScrollView(a).apply{addView(root)}
 }
 private fun startTuner(){
  if(active)return
  val rate=44100;val size=AudioRecord.getMinBufferSize(rate,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT).coerceAtLeast(4096)
  try{val r=AudioRecord(MediaRecorder.AudioSource.MIC,rate,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT,size);if(r.state!=AudioRecord.STATE_INITIALIZED){r.release();throw IllegalStateException("AudioRecord konnte nicht initialisiert werden")};recorder=r;r.startRecording();active=true;startButton.text="Stimmen stoppen"
   worker=Thread{val samples=ShortArray(4096);while(active){val n=r.read(samples,0,samples.size);if(n>2048){val f=estimatePitch(samples,n,rate);if(f in 65.0..1100.0){val midi=(69+12*kotlin.math.ln(f/440.0)/kotlin.math.ln(2.0)).roundToInt();val target=440.0*2.0.pow((midi-69)/12.0);val cents=(1200*kotlin.math.ln(f/target)/kotlin.math.ln(2.0)).roundToInt();val names=arrayOf("C","C♯","D","D♯","E","F","F♯","G","G♯","A","A♯","B");val name=names[(midi%12+12)%12]+(midi/12-1);activity?.runOnUiThread{if(active){noteView.text=name;hzView.text="%.1f Hz".format(f);centsView.text=if(cents>0)"+${cents} Cent · zu hoch" else if(cents<0)"${cents} Cent · zu tief" else "0 Cent · gestimmt";meter.progress=(50+cents/2).coerceIn(0,100)}}}}};}.also{it.name="Saitenwerk-Tuner";it.start()}
  }catch(e:Exception){active=false;startButton.text="Erneut versuchen";Toast.makeText(requireContext(),"Mikrofonfehler: ${e.message}",Toast.LENGTH_LONG).show()}
 }
 private fun estimatePitch(x:ShortArray,n:Int,sr:Int):Double{val minLag=sr/1100;val maxLag=(sr/60).coerceAtMost(n/2);var bestLag=0;var best=Double.NEGATIVE_INFINITY;for(lag in minLag..maxLag step 2){var sum=0.0;for(i in 0 until n-lag step 3)sum+=x[i].toDouble()*x[i+lag].toDouble();if(sum>best){best=sum;bestLag=lag}};return if(bestLag>0)sr.toDouble()/bestLag else -1.0}
 private fun stopTuner(){active=false;try{recorder?.stop()}catch(_:Exception){};recorder?.release();recorder=null;worker=null;if(::startButton.isInitialized)startButton.text="Stimmen starten"}
 override fun onPause(){stopTuner();super.onPause()};override fun onDestroyView(){stopTuner();super.onDestroyView()}
}

data class ChordShape(val name:String,val quality:String,val fingers:IntArray,val baseFret:Int=1,val note:String="")

object ChordLibrary {
    val all = listOf(
        ChordShape("C","Dur", intArrayOf(-1,3,2,0,1,0),note="Offener C-Dur-Griff"),
        ChordShape("G","Dur", intArrayOf(3,2,0,0,0,3),note="Offener G-Dur-Griff"),
        ChordShape("D","Dur", intArrayOf(-1,-1,0,2,3,2),note="Offener D-Dur-Griff"),
        ChordShape("A","Dur", intArrayOf(-1,0,2,2,2,0),note="Offener A-Dur-Griff"),
        ChordShape("E","Dur", intArrayOf(0,2,2,1,0,0),note="Offener E-Dur-Griff"),
        ChordShape("F","Dur", intArrayOf(1,3,3,2,1,1),note="Barré-Griff im 1. Bund"),
        ChordShape("Am","Moll", intArrayOf(-1,0,2,2,1,0),note="Offener A-Moll-Griff"),
        ChordShape("Em","Moll", intArrayOf(0,2,2,0,0,0),note="Offener E-Moll-Griff"),
        ChordShape("Dm","Moll", intArrayOf(-1,-1,0,2,3,1),note="Offener D-Moll-Griff"),
        ChordShape("Bm","Moll", intArrayOf(-1,2,4,4,3,2),baseFret=2,note="Barré-Griff im 2. Bund"),
        ChordShape("C7","Septakkord", intArrayOf(-1,3,2,3,1,0)),
        ChordShape("D7","Septakkord", intArrayOf(-1,-1,0,2,1,2)),
        ChordShape("E7","Septakkord", intArrayOf(0,2,0,1,0,0)),
        ChordShape("G7","Septakkord", intArrayOf(3,2,0,0,0,1)),
        ChordShape("Am7","Septakkord", intArrayOf(-1,0,2,0,1,0)),
        ChordShape("Em7","Septakkord", intArrayOf(0,2,0,0,0,0)),
        ChordShape("Dsus2","Sus-Akkord", intArrayOf(-1,-1,0,2,3,0)),
        ChordShape("Dsus4","Sus-Akkord", intArrayOf(-1,-1,0,2,3,3)),
        ChordShape("Asus2","Sus-Akkord", intArrayOf(-1,0,2,2,0,0)),
        ChordShape("Asus4","Sus-Akkord", intArrayOf(-1,0,2,2,3,0))
    )
}

class ChordDiagramView(context: android.content.Context, private val shape:ChordShape):View(context) {
    private val line=android.graphics.Paint(3).apply{color=android.graphics.Color.LTGRAY;strokeWidth=2f}
    private val text=android.graphics.Paint(3).apply{color=android.graphics.Color.WHITE;textSize=28f;textAlign=android.graphics.Paint.Align.CENTER}
    private val dot=android.graphics.Paint(3).apply{color=android.graphics.Color.rgb(217,154,112);style=android.graphics.Paint.Style.FILL}
    override fun onDraw(canvas:android.graphics.Canvas){super.onDraw(canvas);val w=width.toFloat();val top=dp(42f);val bottom=height-dp(28f);val left=w*.20f;val right=w*.80f;val dx=(right-left)/5f;val dy=(bottom-top)/4f
        for(i in 0..5)canvas.drawLine(left+i*dx,top,left+i*dx,bottom,line)
        for(i in 0..4)canvas.drawLine(left,top+i*dy,right,top+i*dy,line)
        if(shape.baseFret==1)canvas.drawRect(left-3,top-5,right+3,top+1,line) else canvas.drawText("${shape.baseFret}fr",left-dp(26f),top+dy,text)
        val labels=arrayOf("E","A","D","G","B","e")
        for(i in 0..5){val f=shape.fingers[i];val x=left+i*dx;val label=if(f<0)"×" else if(f==0)"○" else "";if(label.isNotEmpty())canvas.drawText(label,x,top-dp(12f),text);if(f>0){val y=top+(f-shape.baseFret+.5f)*dy;if(y>=top&&y<=bottom)canvas.drawCircle(x,y,dp(10f),dot)}}
        for(i in 0..5)canvas.drawText(labels[i],left+i*dx,height-dp(5f),text)
    }
    private fun dp(v:Float)=v*resources.displayMetrics.density
}

class ChordsFragment:Fragment(){
 private var trainingPanel: ChordTrainingPanel? = null
 override fun onDestroyView(){ trainingPanel?.stop(); trainingPanel=null; super.onDestroyView() }
 override fun onCreateView(i:android.view.LayoutInflater,c:android.view.ViewGroup?,s:Bundle?):View{
  val a=requireActivity() as MainActivity
  val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL}
  root.addView(a.title("Akkorde"))
  root.addView(TextView(a).apply{text="Griffbilder · Akkordwissen · Wechseltraining";setTextColor(a.getColor(R.color.sw_muted));setPadding(a.dp(20),0,a.dp(20),a.dp(12))})
  val search=EditText(a).apply{hint="Akkord suchen (z. B. Am, G7 …)";setSingleLine();setTextColor(a.getColor(R.color.sw_text));setHintTextColor(a.getColor(R.color.sw_muted));setPadding(a.dp(16),0,a.dp(16),0);background=a.getDrawable(android.R.drawable.edit_text)}
  root.addView(search,LinearLayout.LayoutParams(-1,a.dp(52)).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(10))})
  val filters=LinearLayout(a).apply{orientation=LinearLayout.HORIZONTAL;setPadding(a.dp(12),0,a.dp(12),a.dp(8))}
  val categories=listOf("Alle","Dur","Moll","Septakkord","Sus-Akkord");var category="Alle"
  val grid=GridLayout(a).apply{columnCount=3;setPadding(a.dp(12),a.dp(4),a.dp(12),a.dp(12))}
  val detail=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(18),a.dp(12),a.dp(18),a.dp(20))}
  val detailCard=a.card();detailCard.addView(detail);detailCard.visibility=View.GONE
  fun showChord(ch:ChordShape){detail.removeAllViews();detail.addView(TextView(a).apply{text=ch.name;setTextColor(a.getColor(R.color.sw_copper));textSize=30f;setTypeface(typeface,1)});detail.addView(TextView(a).apply{text="${ch.quality} · ${ch.note}";setTextColor(a.getColor(R.color.sw_muted));textSize=14f});detail.addView(ChordDiagramView(a,ch),LinearLayout.LayoutParams(-1,a.dp(230)));detail.addView(TextView(a).apply{text="Von links nach rechts: E – A – D – G – H – e\n× = nicht anschlagen · ○ = leere Saite";setTextColor(a.getColor(R.color.sw_muted));textSize=13f});val fav=a.getSharedPreferences("saitenwerk",0);val key="fav_chords";val set=fav.getStringSet(key, emptySet())?.toMutableSet()?:mutableSetOf();val b=a.button(if(set.contains(ch.name))"★ Favorit entfernen" else "☆ Als Favorit speichern");b.setOnClickListener{val current=fav.getStringSet(key, emptySet())?.toMutableSet()?:mutableSetOf();if(!current.add(ch.name))current.remove(ch.name);fav.edit().putStringSet(key,current).apply();b.text=if(current.contains(ch.name))"★ Favorit entfernen" else "☆ Als Favorit speichern"};detail.addView(b,LinearLayout.LayoutParams(-1,a.dp(48)).apply{topMargin=a.dp(8)}) ;detailCard.visibility=View.VISIBLE}
  fun render(){grid.removeAllViews();val q=search.text.toString().trim().lowercase();val list=ChordLibrary.all.filter{(category=="Alle"||it.quality==category)&&it.name.lowercase().contains(q)};list.forEach{ch->val b=a.button(ch.name);b.setOnClickListener{showChord(ch)};val lp=GridLayout.LayoutParams().apply{width=0;height=a.dp(54);columnSpec=GridLayout.spec(GridLayout.UNDEFINED,1f);setMargins(a.dp(4),a.dp(4),a.dp(4),a.dp(4))};grid.addView(b,lp)};if(list.isEmpty())grid.addView(TextView(a).apply{text="Kein passender Akkord gefunden.";setTextColor(a.getColor(R.color.sw_muted))})}
  categories.forEach{cat->val b=a.button(cat);b.setOnClickListener{category=cat;render()};filters.addView(b,LinearLayout.LayoutParams(0,a.dp(42),1f).apply{setMargins(a.dp(2),0,a.dp(2),0)})}
  search.addTextChangedListener(object:android.text.TextWatcher{override fun beforeTextChanged(s:CharSequence?,st:Int,count:Int,after:Int){};override fun onTextChanged(s:CharSequence?,st:Int,before:Int,count:Int){render()};override fun afterTextChanged(e:android.text.Editable?){}})
  root.addView(filters);val scroll=ScrollView(a);val content=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;addView(detailCard,LinearLayout.LayoutParams(-1,-2).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(12))});addView(grid);trainingPanel=ChordTrainingPanel(a);addView(trainingPanel,LinearLayout.LayoutParams(-1,-2).apply{setMargins(a.dp(16),a.dp(12),a.dp(16),a.dp(24))})};scroll.addView(content);root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f));render();return root
 }
}


/** Interaktives natives Akkordwechseltraining mit Metronom, Fortschritt und lokaler Selbstbewertung. */
class ChordTrainingPanel(private val host: MainActivity): LinearLayout(host) {
    private val handler = Handler(Looper.getMainLooper())
    private val tone = ToneGenerator(AudioManager.STREAM_MUSIC, 55)
    private val sequence = listOf("C", "G", "Am", "F")
    private var bpm = 72
    private var beat = 0
    private var changeCount = 0
    private var running = false
    private val current = TextView(host)
    private val status = TextView(host)
    private val start = host.button("Training starten")
    private val tempo = SeekBar(host)
    private val stats = TextView(host)
    private val tick = object: Runnable { override fun run() {
        if (!running) return
        tone.startTone(if (beat % 4 == 0) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP, 65)
        if (beat % 4 == 0) {
            current.text = sequence[(changeCount) % sequence.size]
            changeCount++
            stats.text = "Akkordwechsel: ${changeCount-1}  ·  Tempo: ${bpm} BPM"
        }
        beat++
        handler.postDelayed(this, (60000L / bpm).coerceAtLeast(100L))
    }}
    init {
        orientation = VERTICAL
        setPadding(host.dp(18),host.dp(18),host.dp(18),host.dp(18))
        setBackgroundColor(host.getColor(R.color.sw_surface))
        addView(TextView(host).apply { text="Akkordwechsel-Training"; setTextColor(host.getColor(R.color.sw_copper)); textSize=21f; setTypeface(typeface,1) })
        addView(TextView(host).apply { text="Wechsle im Takt: C · G · Am · F"; setTextColor(host.getColor(R.color.sw_muted)); textSize=14f; setPadding(0,host.dp(5),0,host.dp(12)) })
        current.text = "C"; current.textSize=42f; current.setTypeface(current.typeface,1); current.setTextColor(host.getColor(R.color.sw_text)); current.gravity=android.view.Gravity.CENTER
        addView(current, LayoutParams(-1,host.dp(82)))
        status.text = "Bereit? Starte das Metronom und wechsle alle vier Schläge."; status.setTextColor(host.getColor(R.color.sw_muted)); status.textSize=13f
        addView(status,LayoutParams(-1,-2))
        addView(TextView(host).apply{text="Tempo: 72 BPM";setTextColor(host.getColor(R.color.sw_text));textSize=14f;tag="tempoLabel";setPadding(0,host.dp(12),0,0)})
        tempo.max=110;tempo.progress=22
        tempo.setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener{
            override fun onProgressChanged(v:SeekBar?,progress:Int,fromUser:Boolean){bpm=50+progress; (getChildAt(4) as TextView).text="Tempo: ${bpm} BPM"}
            override fun onStartTrackingTouch(v:SeekBar?){}
            override fun onStopTrackingTouch(v:SeekBar?){}
        })
        addView(tempo,LayoutParams(-1,host.dp(42)))
        start.setOnClickListener { if(running) stop() else begin() }
        addView(start,LayoutParams(-1,host.dp(50)))
        stats.text="Akkordwechsel: 0  ·  Tempo: 72 BPM";stats.setTextColor(host.getColor(R.color.sw_muted));stats.setPadding(0,host.dp(10),0,host.dp(6));addView(stats)
        val row=LinearLayout(host).apply{orientation=HORIZONTAL}
        val mastered=host.button("✓ Sitzt")
        val practice=host.button("↻ Weiter üben")
        mastered.setOnClickListener{saveRating(true)};practice.setOnClickListener{saveRating(false)}
        row.addView(mastered,LayoutParams(0,host.dp(46),1f));row.addView(practice,LayoutParams(0,host.dp(46),1f).apply{leftMargin=host.dp(8)})
        addView(row,LayoutParams(-1,-2))
        val pref=host.getSharedPreferences("saitenwerk",0)
        val wins=pref.getInt("chord_training_mastered",0);val sessions=pref.getInt("chord_training_sessions",0)
        status.text="Bisher: $wins gemeisterte Übungsbewertungen aus $sessions Einträgen. Bewertung ist deine Selbsteinschätzung."
    }
    private fun begin(){running=true;beat=0;changeCount=0;start.text="Training stoppen";status.text="Läuft · auf den ersten Schlag achten";handler.removeCallbacks(tick);handler.post(tick)}
    fun stop(){running=false;handler.removeCallbacks(tick);start.text="Training starten";tone.stopTone()}
    private fun saveRating(mastered:Boolean){val pref=host.getSharedPreferences("saitenwerk",0);val sessions=pref.getInt("chord_training_sessions",0)+1;val wins=pref.getInt("chord_training_mastered",0)+(if(mastered)1 else 0);pref.edit().putInt("chord_training_sessions",sessions).putInt("chord_training_mastered",wins).apply();status.text=if(mastered)"Als gemeistert markiert · $wins von $sessions Bewertungen" else "Für weitere Übung vorgemerkt · $wins von $sessions Bewertungen"}
}

class SongsFragment:Fragment(){
 override fun onCreateView(i:android.view.LayoutInflater,c:android.view.ViewGroup?,s:Bundle?):View{
  val a=requireActivity() as MainActivity
  val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL}
  root.addView(a.title("Liederbuch"))
  val data=SongRepository.load(a)
  val count=TextView(a).apply{text="${data.size} Songs · offline verfügbar";setTextColor(a.getColor(R.color.sw_muted));setPadding(a.dp(20),0,a.dp(20),a.dp(10))}
  root.addView(count)
  val q=EditText(a).apply{hint="Lied oder Künstler suchen";setSingleLine(true);setTextColor(a.getColor(R.color.sw_text));setHintTextColor(a.getColor(R.color.sw_muted));setPadding(a.dp(20),0,a.dp(20),0)}
  root.addView(q,LinearLayout.LayoutParams(-1,a.dp(54)).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(8))})
  var favoritesOnly=false
  val filters=LinearLayout(a).apply{orientation=LinearLayout.HORIZONTAL}
  val allButton=a.button("Alle Songs");val favButton=a.button("★ Favoriten")
  filters.addView(allButton,LinearLayout.LayoutParams(0,a.dp(44),1f).apply{setMargins(a.dp(16),0,a.dp(4),a.dp(8))})
  filters.addView(favButton,LinearLayout.LayoutParams(0,a.dp(44),1f).apply{setMargins(a.dp(4),0,a.dp(16),a.dp(8))})
  root.addView(filters)
  val rv=RecyclerView(a).apply{layoutManager=LinearLayoutManager(a)}
  val adapter=SongAdapter(data,a){song->a.openSong(song)}
  rv.adapter=adapter
  fun update(){adapter.filter(q.text.toString(),favoritesOnly);count.text="${adapter.itemCount} von ${data.size} Songs${if(favoritesOnly)" · Favoriten" else " · offline verfügbar"}"}
  allButton.setOnClickListener{favoritesOnly=false;update()}
  favButton.setOnClickListener{favoritesOnly=true;update()}
  q.addTextChangedListener(object:android.text.TextWatcher{override fun beforeTextChanged(s:CharSequence?,st:Int,c:Int,after:Int){};override fun onTextChanged(s:CharSequence?,st:Int,b:Int,c:Int){update()};override fun afterTextChanged(e:android.text.Editable?){}})
  root.addView(rv,LinearLayout.LayoutParams(-1,0,1f));update()
  return root
 }
}

data class Song(val title:String,val artist:String="",val genre:String="")
object SongRepository{
 fun load(a:MainActivity):MutableList<Song>{return try{val raw=a.assets.open("songs.json").bufferedReader().readText();val ar=JSONArray(raw);MutableList(ar.length()){i->val o=ar.getJSONObject(i);Song(o.optString("title"),o.optString("artist"),o.optString("genre"))}}catch(e:Exception){mutableListOf()}}
 fun favoriteIds(a:MainActivity):MutableSet<String> = a.getSharedPreferences("saitenwerk",0).getStringSet("song_favorites", emptySet())?.toMutableSet() ?: mutableSetOf()
 fun isFavorite(a:MainActivity,song:Song)=favoriteIds(a).contains(song.title+"|"+song.artist)
 fun toggleFavorite(a:MainActivity,song:Song):Boolean{val ids=favoriteIds(a);val key=song.title+"|"+song.artist;val now=if(ids.contains(key)){ids.remove(key);false}else{ids.add(key);true};a.getSharedPreferences("saitenwerk",0).edit().putStringSet("song_favorites",ids).apply();return now}
}
class SongAdapter(private val all:MutableList<Song>,private val host:MainActivity,private val onClick:(Song)->Unit):RecyclerView.Adapter<SongAdapter.VH>(){
 private var data=all.toMutableList()
 class VH(v:View):RecyclerView.ViewHolder(v)
 override fun onCreateViewHolder(p:android.view.ViewGroup,t:Int)=VH(TextView(p.context).apply{setTextColor(p.context.getColor(R.color.sw_text));textSize=16f;setPadding(20,16,20,16);isClickable=true;isFocusable=true})
 override fun getItemCount()=data.size
 override fun onBindViewHolder(h:VH,pos:Int){val song=data[pos];val fav=SongRepository.isFavorite(host,song);(h.itemView as TextView).apply{text=(if(fav)"★  " else "♫  ")+song.title+"\n"+song.artist+"  ·  "+song.genre;setOnClickListener{onClick(song)}}}
 fun filter(q:String,favoritesOnly:Boolean=false){val x=q.trim().lowercase();data=all.filter{(x.isEmpty()||it.title.lowercase().contains(x)||it.artist.lowercase().contains(x)||it.genre.lowercase().contains(x))&&(!favoritesOnly||SongRepository.isFavorite(host,it))}.toMutableList();notifyDataSetChanged()}
}
class SongDetailFragment:Fragment(){
 override fun onCreateView(i:android.view.LayoutInflater,c:android.view.ViewGroup?,s:Bundle?):View{
  val a=requireActivity() as MainActivity
  val song=arguments?.let{Song(it.getString("title").orEmpty(),it.getString("artist").orEmpty(),it.getString("genre").orEmpty())} ?: Song("Unbekannter Titel")
  val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL}
  val back=a.button("‹  Zurück zum Liederbuch");back.setOnClickListener{a.openSection(4)}
  root.addView(back,LinearLayout.LayoutParams(-1,a.dp(52)).apply{setMargins(a.dp(16),a.dp(12),a.dp(16),0)})
  root.addView(a.title(song.title))
  fun line(value:String,size:Float=17f,color:Int=R.color.sw_text)=TextView(a).apply{text=value;textSize=size;setTextColor(a.getColor(color));setPadding(a.dp(20),a.dp(7),a.dp(20),a.dp(7))}
  root.addView(line(song.artist,20f,R.color.sw_copper));root.addView(line("Genre: ${song.genre}"))
  val favorite=a.button(if(SongRepository.isFavorite(a,song))"★ Aus Favoriten entfernen" else "☆ Zu Favoriten hinzufügen")
  favorite.setOnClickListener{val now=SongRepository.toggleFavorite(a,song);favorite.text=if(now)"★ Aus Favoriten entfernen" else "☆ Zu Favoriten hinzufügen";Toast.makeText(a,if(now)"Als Favorit gespeichert" else "Aus Favoriten entfernt",Toast.LENGTH_SHORT).show()}
  root.addView(favorite,LinearLayout.LayoutParams(-1,a.dp(52)).apply{setMargins(a.dp(16),a.dp(18),a.dp(16),a.dp(18))})
  val info=a.card();val content=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(18),a.dp(18),a.dp(18),a.dp(18))}
  content.addView(line("Song-Informationen",19f,R.color.sw_copper))
  content.addView(line("Die Datenbank enthält derzeit Titel, Künstler und Genre. Akkorde, Tonart, Capo und vollständige Songarrangements sind für diesen Eintrag noch nicht hinterlegt.",15f,R.color.sw_muted))
  content.addView(line("Musikalische Details folgen bei der Arrangement-Migration.",14f,R.color.sw_muted));info.addView(content)
  root.addView(info,LinearLayout.LayoutParams(-1,-2).apply{setMargins(a.dp(16),0,a.dp(16),0)})
  return ScrollView(a).apply{addView(root)}
 }
}
class LearnFragment:Fragment(){
 private var chordTraining:ChordTrainingPanel?=null
 private var rhythmTone:ToneGenerator?=null
 private var rhythmHandler:Handler?=null
 private var rhythmRunning=false
 private var rhythmBeat=0
 private var rhythmBpm=80
 override fun onDestroyView(){chordTraining?.stop();chordTraining=null;stopRhythm();super.onDestroyView()}
 override fun onCreateView(i:android.view.LayoutInflater,c:android.view.ViewGroup?,s:Bundle?):View{
  val a=requireActivity() as MainActivity
  val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL}
  root.addView(a.title("Lernstudio"))
  root.addView(TextView(a).apply{text="Kurze, praktische Einheiten für Akkorde, Wechsel und Rhythmus. Dein Fortschritt wird auf diesem Gerät gespeichert.";setTextColor(a.getColor(R.color.sw_muted));setPadding(a.dp(20),0,a.dp(20),a.dp(14))})
  val prefs=a.getSharedPreferences("saitenwerk",0)
  val summary=TextView(a).apply{text="Akkord-Quiz: ${prefs.getInt("learn_quiz_correct",0)} richtige Antworten · ${prefs.getInt("learn_quiz_total",0)} Versuche";setTextColor(a.getColor(R.color.sw_copper));setPadding(a.dp(20),0,a.dp(20),a.dp(12))};root.addView(summary)
  val tabs=LinearLayout(a).apply{orientation=LinearLayout.HORIZONTAL;setPadding(a.dp(10),0,a.dp(10),a.dp(8))}
  val content=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(16),a.dp(4),a.dp(16),a.dp(24))}
  val scroll=ScrollView(a);scroll.addView(content)
  fun panel(title:String,description:String):MaterialCardView{val card=a.card();val box=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(16),a.dp(16),a.dp(16),a.dp(16))};box.addView(TextView(a).apply{text=title;textSize=20f;setTypeface(typeface,1);setTextColor(a.getColor(R.color.sw_copper))});box.addView(TextView(a).apply{text=description;textSize=14f;setTextColor(a.getColor(R.color.sw_muted));setPadding(0,a.dp(6),0,a.dp(8))});card.addView(box);return card}
 fun showQuiz(){chordTraining?.stop();chordTraining=null;stopRhythm();content.removeAllViews();val card=panel("Akkord-Blitztrainer","Erkenne Griffbilder und festige die wichtigsten offenen Akkorde.");val box=card.getChildAt(0) as LinearLayout
  val prompt=TextView(a).apply{text="Welcher Akkord ist das?";textSize=18f;setTextColor(a.getColor(R.color.sw_text));gravity=android.view.Gravity.CENTER};box.addView(prompt)
  val diagramHolder=FrameLayout(a);box.addView(diagramHolder,LinearLayout.LayoutParams(-1,a.dp(220)))
  val choices=GridLayout(a).apply{columnCount=2};box.addView(choices,LinearLayout.LayoutParams(-1,-2))
  val feedback=TextView(a).apply{text="Wähle den passenden Akkord.";setTextColor(a.getColor(R.color.sw_muted));gravity=android.view.Gravity.CENTER;setPadding(0,a.dp(10),0,a.dp(6))};box.addView(feedback)
  val next=a.button("Nächster Akkord");box.addView(next,LinearLayout.LayoutParams(-1,a.dp(48)))
  var answer="";var locked=false
  fun newQuestion(){val shape=ChordLibrary.all.filter{it.name in listOf("C","G","D","A","E","F","Am","Em","Dm")}.random();answer=shape.name;locked=false;feedback.text="Wähle den passenden Akkord.";diagramHolder.removeAllViews();diagramHolder.addView(ChordDiagramView(a,shape),FrameLayout.LayoutParams(-1,-1));choices.removeAllViews();val options=(listOf(answer)+ChordLibrary.all.filter{it.name!=answer&&it.name in listOf("C","G","D","A","E","F","Am","Em","Dm")}.shuffled().take(3).map{it.name}).shuffled();options.forEach{name->val b=a.button(name);b.setOnClickListener{if(!locked){locked=true;val correct=name==answer;val total=prefs.getInt("learn_quiz_total",0)+1;val score=prefs.getInt("learn_quiz_correct",0)+(if(correct)1 else 0);prefs.edit().putInt("learn_quiz_total",total).putInt("learn_quiz_correct",score).apply();summary.text="Akkord-Quiz: $score richtige Antworten · $total Versuche";feedback.text=if(correct)"Richtig! $answer sauber erkannt." else "Noch nicht ganz – gesucht war $answer. Schau dir die Fingerpositionen an.";feedback.setTextColor(a.getColor(if(correct)R.color.sw_copper else R.color.sw_muted));for(j in 0 until choices.childCount)choices.getChildAt(j).isEnabled=false}};choices.addView(b,GridLayout.LayoutParams().apply{width=0;height=a.dp(48);columnSpec=GridLayout.spec(GridLayout.UNDEFINED,1f);setMargins(a.dp(3),a.dp(3),a.dp(3),a.dp(3))})}}
  next.setOnClickListener{newQuestion()};newQuestion();content.addView(card)
 }
 fun showChanges(){stopRhythm();content.removeAllViews();content.addView(TextView(a).apply{text="Wechsle C · G · Am · F im gleichmäßigen Puls. Starte langsam und steigere das Tempo erst, wenn jeder Griff sauber klingt.";setTextColor(a.getColor(R.color.sw_muted));textSize=15f;setPadding(0,0,0,a.dp(12))});chordTraining=ChordTrainingPanel(a);content.addView(chordTraining,LinearLayout.LayoutParams(-1,-2))}
 fun showRhythm(){chordTraining?.stop();chordTraining=null;stopRhythm();content.removeAllViews();val card=panel("Rhythmus & Timing","Übe einen gleichmäßigen Viertelpuls. Der erste Schlag jedes Taktes wird stärker markiert.");val box=card.getChildAt(0) as LinearLayout;val bpmLabel=TextView(a).apply{text="Tempo: 80 BPM";setTextColor(a.getColor(R.color.sw_text));textSize=17f};box.addView(bpmLabel);val bpm=SeekBar(a).apply{max=110;progress=30};bpm.setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener{override fun onProgressChanged(v:SeekBar?,p:Int,from:Boolean){rhythmBpm=50+p;bpmLabel.text="Tempo: $rhythmBpm BPM"};override fun onStartTrackingTouch(v:SeekBar?){};override fun onStopTrackingTouch(v:SeekBar?){}});box.addView(bpm);val beat=TextView(a).apply{text="Bereit";textSize=34f;gravity=android.view.Gravity.CENTER;setTextColor(a.getColor(R.color.sw_copper));setPadding(0,a.dp(12),0,a.dp(12))};box.addView(beat,LinearLayout.LayoutParams(-1,a.dp(76)));val start=a.button("Metronom starten");box.addView(start,LinearLayout.LayoutParams(-1,a.dp(50)));start.setOnClickListener{if(rhythmRunning){stopRhythm();start.text="Metronom starten";beat.text="Pausiert"}else{rhythmRunning=true;rhythmBeat=0;rhythmTone=ToneGenerator(AudioManager.STREAM_MUSIC,65);rhythmHandler=Handler(Looper.getMainLooper());start.text="Metronom stoppen";val task=object:Runnable{override fun run(){if(!rhythmRunning)return;val strong=rhythmBeat%4==0;rhythmTone?.startTone(if(strong)ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP,70);beat.text=if(strong)"1  ·  TAKT" else "${rhythmBeat%4+1}";rhythmBeat++;rhythmHandler?.postDelayed(this,(60000L/rhythmBpm).coerceAtLeast(100L))}};rhythmHandler?.post(task)}};content.addView(card)}
 fun showRoutine(){chordTraining?.stop();chordTraining=null;stopRhythm();content.removeAllViews();val card=panel("Deine tägliche 10-Minuten-Routine","Hake die Einheiten ab, wenn du sie erledigt hast. Der Tagesstand wird lokal gespeichert.");val box=card.getChildAt(0) as LinearLayout;val day=java.text.SimpleDateFormat("yyyy-MM-dd",java.util.Locale.GERMANY).format(java.util.Date());val savedDay=prefs.getString("learn_routine_day","");if(savedDay!=day)prefs.edit().putString("learn_routine_day",day).putInt("learn_routine_done",0).apply();val tasks=listOf("2 Min. Akkordgriffe sauber aufsetzen","3 Min. Wechsel C – G – Am – F","3 Min. Rhythmus mit Metronom","2 Min. Lieblingssong spielen");val done=prefs.getInt("learn_routine_done",0);val progress=ProgressBar(a,null,android.R.attr.progressBarStyleHorizontal).apply{max=tasks.size;this.progress=Integer.bitCount(done)};box.addView(TextView(a).apply{text="Heute erledigt: ${Integer.bitCount(done)} von ${tasks.size}";setTextColor(a.getColor(R.color.sw_text))});box.addView(progress,LinearLayout.LayoutParams(-1,a.dp(10)).apply{topMargin=a.dp(8);bottomMargin=a.dp(8)});tasks.forEachIndexed{idx,label->val cb=CheckBox(a).apply{text=label;setTextColor(a.getColor(R.color.sw_text));isChecked=(done and (1 shl idx))!=0};cb.setOnCheckedChangeListener{_,checked->var mask=prefs.getInt("learn_routine_done",0);mask=if(checked)mask or (1 shl idx) else mask and (1 shl idx).inv();prefs.edit().putInt("learn_routine_done",mask).apply();progress.progress=Integer.bitCount(mask);val count=Integer.bitCount(mask);(box.getChildAt(2) as TextView).text="Heute erledigt: $count von ${tasks.size}"};box.addView(cb)};content.addView(card)}
 val modes=listOf("Blitztrainer","Wechsel","Rhythmus","Tagesroutine");val actions=listOf({showQuiz()},{showChanges()},{showRhythm()},{showRoutine()});modes.forEachIndexed{idx,label->val b=a.button(label);b.textSize=12f;b.setOnClickListener{actions[idx]()};tabs.addView(b,LinearLayout.LayoutParams(0,a.dp(44),1f).apply{setMargins(a.dp(2),0,a.dp(2),0)})};root.addView(tabs);root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f));showQuiz();return root
 }
 private fun stopRhythm(){rhythmRunning=false;rhythmHandler?.removeCallbacksAndMessages(null);rhythmHandler=null;try{rhythmTone?.stopTone();rhythmTone?.release()}catch(_:Exception){};rhythmTone=null}
}
class PathFragment:Fragment(){
 override fun onCreateView(i:android.view.LayoutInflater,c:android.view.ViewGroup?,s:Bundle?):View{
  val a=requireActivity() as MainActivity
  val prefs=a.getSharedPreferences("saitenwerk",0)
  val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL}
  root.addView(a.title("Dein Lernpfad"))
  root.addView(TextView(a).apply{text="Vom ersten Griff bis zum selbstständigen Spielen ganzer Songs. Du bestimmst dein Tempo – dein Fortschritt bleibt auf diesem Gerät gespeichert.";setTextColor(a.getColor(R.color.sw_muted));textSize=15f;setPadding(a.dp(20),0,a.dp(20),a.dp(16))})
  val stages=listOf(
   "Erste Akkorde" to "Lerne C, G, D, A, E sowie Am und Em kennen. Ziel: jeden Griff ruhig und einzeln aufsetzen.",
   "Saubere Griffbilder" to "Achte auf gekrümmte Finger, kurze Fingernägel und darauf, dass jede Saite klar klingt.",
   "Flüssige Wechsel" to "Verbinde zwei Akkorde zunächst langsam. Steigere das Tempo erst, wenn der Wechsel sicher sitzt.",
   "Rhythmus festigen" to "Halte einen gleichmäßigen Viertelpuls und übe den Wechsel ohne den Schlagfluss zu unterbrechen.",
   "Erste Songs begleiten" to "Wähle ein einfaches Lied und spiele die Akkordfolge langsam im passenden Takt.",
   "Selbstständig spielen" to "Spiele einen Song vom Anfang bis zum Ende und finde bei Bedarf selbst zurück in den Ablauf."
  )
  val doneKey="learning_path_done"
  val progressLabel=TextView(a).apply{setTextColor(a.getColor(R.color.sw_copper));textSize=17f;setTypeface(typeface,1);setPadding(a.dp(20),a.dp(8),a.dp(20),a.dp(8))}
  val progress=ProgressBar(a,null,android.R.attr.progressBarStyleHorizontal).apply{max=stages.size}
  fun refresh(){val mask=prefs.getInt(doneKey,0);val count=Integer.bitCount(mask);progress.progress=count;progressLabel.text="${count} von ${stages.size} Lernstufen abgeschlossen · ${count*100/stages.size}%"}
  root.addView(progressLabel);root.addView(progress,LinearLayout.LayoutParams(-1,a.dp(10)).apply{setMargins(a.dp(20),0,a.dp(20),a.dp(16))})
  val goalCard=a.card();val goalBox=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(16),a.dp(14),a.dp(16),a.dp(14))}
  goalBox.addView(TextView(a).apply{text="Mein persönliches Lernziel";textSize=19f;setTypeface(typeface,1);setTextColor(a.getColor(R.color.sw_copper))})
  val goalInput=EditText(a).apply{setText(prefs.getString("learning_path_goal",""));hint="z. B. In vier Wochen drei Songs begleiten";setTextColor(a.getColor(R.color.sw_text));setHintTextColor(a.getColor(R.color.sw_muted));setSingleLine(false);minLines=2}
  goalBox.addView(goalInput,LinearLayout.LayoutParams(-1,-2).apply{topMargin=a.dp(8)})
  val saveGoal=a.button("Lernziel speichern");saveGoal.setOnClickListener{prefs.edit().putString("learning_path_goal",goalInput.text.toString().trim()).apply();Toast.makeText(a,"Lernziel gespeichert",Toast.LENGTH_SHORT).show()}
  goalBox.addView(saveGoal,LinearLayout.LayoutParams(-1,a.dp(46)).apply{topMargin=a.dp(8)});goalCard.addView(goalBox)
  root.addView(goalCard,LinearLayout.LayoutParams(-1,-2).apply{setMargins(a.dp(16),0,a.dp(16),a.dp(14))})
  val nextLabel=TextView(a).apply{setTextColor(a.getColor(R.color.sw_text));textSize=16f;setPadding(a.dp(20),0,a.dp(20),a.dp(12))}
  root.addView(nextLabel)
  stages.forEachIndexed{index,pair->
   val card=a.card();val box=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(14),a.dp(12),a.dp(14),a.dp(12))}
   val heading=TextView(a).apply{text="${index+1}. ${pair.first}";textSize=18f;setTypeface(typeface,1);setTextColor(a.getColor(R.color.sw_text))};box.addView(heading)
   box.addView(TextView(a).apply{text=pair.second;textSize=14f;setTextColor(a.getColor(R.color.sw_muted));setPadding(0,a.dp(5),0,a.dp(8))})
   val check=CheckBox(a).apply{text="Lernstufe abgeschlossen";setTextColor(a.getColor(R.color.sw_text));isChecked=(prefs.getInt(doneKey,0) and (1 shl index))!=0}
   check.setOnCheckedChangeListener{_,checked->var mask=prefs.getInt(doneKey,0);mask=if(checked)mask or (1 shl index) else mask and (1 shl index).inv();prefs.edit().putInt(doneKey,mask).apply();refresh();val first=(0 until stages.size).firstOrNull{(mask and (1 shl it))==0};nextLabel.text=if(first==null)"Geschafft! Du hast alle Lernstufen markiert. Zeit für deinen nächsten Song!" else "Dein nächster Schritt: ${stages[first].first}"}
   box.addView(check)
   val practice=a.button("Im Lernstudio üben");practice.setOnClickListener{a.openSection(5)};box.addView(practice,LinearLayout.LayoutParams(-1,a.dp(44)).apply{topMargin=a.dp(5)})
   card.addView(box);root.addView(card,LinearLayout.LayoutParams(-1,-2).apply{setMargins(a.dp(16),a.dp(5),a.dp(16),a.dp(5))})
  }
  val reset=a.button("Lernpfad zurücksetzen");reset.setOnClickListener{prefs.edit().putInt(doneKey,0).apply();for(j in 0 until root.childCount){val v=root.getChildAt(j);if(v is MaterialCardView){val inner=v.getChildAt(0) as? LinearLayout;inner?.let{for(k in 0 until it.childCount){val child=it.getChildAt(k);if(child is CheckBox)child.isChecked=false}}}};refresh();nextLabel.text="Nächster Schritt: ${stages[0].first}";Toast.makeText(a,"Lernpfad zurückgesetzt",Toast.LENGTH_SHORT).show()}
  root.addView(reset,LinearLayout.LayoutParams(-1,a.dp(48)).apply{setMargins(a.dp(16),a.dp(12),a.dp(16),a.dp(24))})
  refresh();val mask=prefs.getInt(doneKey,0);val first=(0 until stages.size).firstOrNull{(mask and (1 shl it))==0};nextLabel.text=if(first==null)"Geschafft! Alle Lernstufen sind abgeschlossen." else "Dein nächster Schritt: ${stages[first].first}"
  return ScrollView(a).apply{addView(root)}
 }
}
