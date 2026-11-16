#!/usr/bin/env python3
from pathlib import Path
import os
root=Path(os.environ["PROJECT_DIR"])
p=root/"app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s=p.read_text(encoding="utf-8")
def replace_between(src,start,end,new):
    i=src.index(start); j=src.index(end,i)
    return src[:i]+new.rstrip()+"\n\n"+src[j:]
home=r'''class HomeFragment : Fragment() {
    override fun onCreateView(i: android.view.LayoutInflater, c: ViewGroup?, s: Bundle?): View {
        val a=requireActivity() as MainActivity
        val prefs=a.getSharedPreferences("saitenwerk",0)
        val page=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL; setPadding(a.dp(20),a.dp(14),a.dp(20),a.dp(28)) }
        val top=LinearLayout(a).apply { orientation=LinearLayout.HORIZONTAL; gravity=Gravity.CENTER_VERTICAL }
        val brand=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL }
        brand.addView(TextView(a).apply { text="SAITENWERK"; textSize=12f; letterSpacing=0.18f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_copper)) })
        brand.addView(TextView(a).apply { text="Dein Sound. Dein Fortschritt."; textSize=13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0,a.dp(3),0,0) })
        top.addView(brand,LinearLayout.LayoutParams(0,-2,1f))
        top.addView(TextView(a).apply {
            text="⚙"; textSize=22f; gravity=Gravity.CENTER; setTextColor(a.getColor(R.color.sw_text))
            background=android.graphics.drawable.GradientDrawable().apply { shape=android.graphics.drawable.GradientDrawable.OVAL; setColor(a.getColor(R.color.sw_surface2)); setStroke(a.dp(1),a.getColor(R.color.sw_outline)) }
            contentDescription="Einstellungen öffnen"; isClickable=true; isFocusable=true; setOnClickListener { a.openSettings() }
        },LinearLayout.LayoutParams(a.dp(46),a.dp(46)))
        page.addView(top)
        val hero=a.card().apply { radius=a.dp(24).toFloat(); strokeColor=a.getColor(R.color.sw_outline); strokeWidth=a.dp(1); elevation=a.dp(3).toFloat() }
        val box=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL; setPadding(a.dp(20),a.dp(18),a.dp(20),a.dp(18)) }
        box.addView(ImageView(a).apply { setImageResource(R.drawable.saitenwerk_original); contentDescription="Saitenwerk – Dein persönlicher Gitarrenbegleiter"; scaleType=ImageView.ScaleType.FIT_CENTER; adjustViewBounds=true },LinearLayout.LayoutParams(-1,a.dp(116)).apply { bottomMargin=a.dp(10) })
        box.addView(TextView(a).apply { text="DEIN MUSIKALISCHER BEGLEITER"; textSize=10f; letterSpacing=0.16f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_copper)) })
        box.addView(TextView(a).apply { text="Spiel. Lerne. Kling besser."; textSize=25f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_text)); setPadding(0,a.dp(7),0,a.dp(5)) })
        box.addView(TextView(a).apply { text="Alles, was du zum Stimmen, Üben und Weiterkommen brauchst – an einem Ort."; textSize=14f; setLineSpacing(a.dp(2).toFloat(),1f); setTextColor(a.getColor(R.color.sw_muted)) })
        box.addView(Button(a).apply {
            text="Stimmgerät öffnen   →"; isAllCaps=false; textSize=15f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_on_accent)); minHeight=a.dp(54); stateListAnimator=null
            background=android.graphics.drawable.GradientDrawable().apply { cornerRadius=a.dp(16).toFloat(); setColor(a.getColor(R.color.sw_copper)) }
            setOnClickListener { a.openSection(2) }
        },LinearLayout.LayoutParams(-1,a.dp(54)).apply { topMargin=a.dp(16) })
        hero.addView(box)
        page.addView(hero,LinearLayout.LayoutParams(-1,-2).apply { topMargin=a.dp(20) })
        page.addView(TextView(a).apply { text="DEIN WORKSPACE"; textSize=11f; letterSpacing=0.14f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_muted)); setPadding(a.dp(2),a.dp(24),0,a.dp(10)) })
        fun tile(symbol:String,title:String,detail:String,section:Int) {
            val card=a.card().apply { radius=a.dp(18).toFloat(); strokeColor=a.getColor(R.color.sw_outline); strokeWidth=a.dp(1); isClickable=true; isFocusable=true; setOnClickListener { a.openSection(section) } }
            val row=LinearLayout(a).apply { orientation=LinearLayout.HORIZONTAL; gravity=Gravity.CENTER_VERTICAL; setPadding(a.dp(15),a.dp(15),a.dp(14),a.dp(15)) }
            row.addView(TextView(a).apply { text=symbol; textSize=23f; gravity=Gravity.CENTER; setTextColor(a.getColor(R.color.sw_copper)); background=android.graphics.drawable.GradientDrawable().apply { cornerRadius=a.dp(13).toFloat(); setColor(a.getColor(R.color.sw_surface2)) } },LinearLayout.LayoutParams(a.dp(48),a.dp(48)))
            val texts=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL }
            texts.addView(TextView(a).apply { text=title; textSize=16f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_text)) })
            texts.addView(TextView(a).apply { text=detail; textSize=12f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0,a.dp(3),0,0) })
            row.addView(texts,LinearLayout.LayoutParams(0,-2,1f).apply { leftMargin=a.dp(13) })
            row.addView(TextView(a).apply { text="›"; textSize=25f; setTextColor(a.getColor(R.color.sw_muted)) })
            card.addView(row); page.addView(card,LinearLayout.LayoutParams(-1,-2).apply { bottomMargin=a.dp(10) })
        }
        tile("♬","Akkorde","Griffbilder entdecken und speichern",3)
        tile("✦","Lernstudio","Übungen, Rhythmus und tägliche Routine",5)
        tile("↗","Dein Lernpfad","Deinen Fortschritt Schritt für Schritt verfolgen",6)
        val stats=LinearLayout(a).apply { orientation=LinearLayout.HORIZONTAL; gravity=Gravity.CENTER_VERTICAL; setPadding(a.dp(2),a.dp(12),a.dp(2),0) }
        stats.addView(TextView(a).apply { text="LERNFORTSCHRITT"; textSize=10f; letterSpacing=0.12f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_muted)) },LinearLayout.LayoutParams(0,-2,1f))
        stats.addView(TextView(a).apply { text=prefs.getInt("learn_quiz_correct",0).toString()+" / "+prefs.getInt("learn_quiz_total",0)+" Quiz-Treffer"; textSize=12f; setTextColor(a.getColor(R.color.sw_copper)) })
        page.addView(stats)
        return ScrollView(a).apply { clipToPadding=false; isFillViewport=true; addView(page) }
    }
}'''
settings=r'''class SettingsFragment : Fragment() {
    override fun onCreateView(i: android.view.LayoutInflater, c: ViewGroup?, s: Bundle?): View {
        val a=requireActivity() as MainActivity
        val page=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL; setPadding(a.dp(20),a.dp(12),a.dp(20),a.dp(28)) }
        page.addView(TextView(a).apply { text="Einstellungen"; textSize=27f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_text)); setPadding(0,a.dp(8),0,a.dp(4)) })
        page.addView(TextView(a).apply { text="Saitenwerk an deinen Alltag anpassen."; textSize=14f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0,0,0,a.dp(20)) })
        fun section(title:String,description:String,actionLabel:String,action:()->Unit) {
            val card=a.card().apply { radius=a.dp(18).toFloat(); strokeColor=a.getColor(R.color.sw_outline); strokeWidth=a.dp(1) }
            val box=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL; setPadding(a.dp(18),a.dp(17),a.dp(18),a.dp(17)) }
            box.addView(TextView(a).apply { text=title; textSize=17f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_text)) })
            box.addView(TextView(a).apply { text=description; textSize=13f; setLineSpacing(a.dp(2).toFloat(),1f); setTextColor(a.getColor(R.color.sw_muted)); setPadding(0,a.dp(5),0,a.dp(14)) })
            box.addView(a.button(actionLabel).apply { textSize=14f; minHeight=a.dp(48); background=android.graphics.drawable.GradientDrawable().apply { cornerRadius=a.dp(14).toFloat(); setColor(a.getColor(R.color.sw_surface2)); setStroke(a.dp(1),a.getColor(R.color.sw_copper)) }; setOnClickListener { action() } },LinearLayout.LayoutParams(-1,a.dp(48)))
            card.addView(box); page.addView(card,LinearLayout.LayoutParams(-1,-2).apply { bottomMargin=a.dp(13) })
        }
        section("App-Updates","Prüfe manuell, ob eine neue Saitenwerk-Version verfügbar ist. Deine installierte Version bleibt erhalten, bis du das Update bestätigst.","Nach Updates suchen") { a.checkForUpdatesManually() }
        val info=a.packageManager.getPackageInfo(a.packageName,0)
        val version=info.versionName ?: "unbekannt"; val code=info.versionCode
        section("Über Saitenwerk","Version "+version+"  ·  Build "+code+"  ·  Beta\nApp-Informationen, technische Details und die Geschichte hinter dem Projekt.","Projektinformationen anzeigen") {
            val about="Saitenwerk ist mehr als nur eine Gitarren-App – es ist ein Experiment.\n\n"+
                "Die Idee hinter diesem Projekt war von Anfang an eine ganz bestimmte: Ich wollte zeigen, dass man keine Programmierkenntnisse oder jahrelange Erfahrung in der Softwareentwicklung benötigt, um eine eigene App auf die Beine zu stellen.\n\n"+
                "Mit Neugier, Ausdauer und der Unterstützung künstlicher Intelligenz ist Saitenwerk entstanden – von der ersten Idee bis hin zu einer eigenständigen Android-App.\n\n"+
                "Mir ging es dabei vor allem darum, zu zeigen, was heute möglich ist, wenn man bereit ist, neue Wege auszuprobieren und KI als Werkzeug zu nutzen. Nicht darum, zu beweisen, dass ich ein professioneller Entwickler bin, sondern dass die Einstiegshürden in die App-Entwicklung längst nicht mehr so hoch sind, wie viele vielleicht denken.\n\n"+
                "Saitenwerk ist deshalb auch ein Beispiel dafür, wie aus einer Idee mithilfe von KI Schritt für Schritt etwas Greifbares werden kann.\n\nMan muss nicht alles können, um etwas Eigenes zu erschaffen. Man muss nur anfangen."
            val details="Saitenwerk\nDie native Android-Gitarrenlern-App\n\nVersion: "+version+"\nBuild: "+code+"\nRelease-Kanal: Beta\nPaket-ID: "+a.packageName+"\nMindestversion: Android 8.0 (API 26)\nPlattform: Android\n\nÜber das Projekt\n"+about
            androidx.appcompat.app.AlertDialog.Builder(a).setTitle("Über Saitenwerk").setMessage(details).setPositiveButton("Schließen",null).show()
        }
        return ScrollView(a).apply { clipToPadding=false; addView(page) }
    }
}'''
s=replace_between(s,"class HomeFragment : Fragment() {","class SettingsFragment : Fragment() {",home)
s=replace_between(s,"class SettingsFragment : Fragment() {","class TunerFragment : Fragment() {",settings)
s=s.replace('text = value; setTextColor(getColor(R.color.sw_text)); textSize = 27f\n        setTypeface(typeface, android.graphics.Typeface.BOLD)\n        setPadding(dp(20), dp(22), dp(20), dp(12))','text = value; setTextColor(getColor(R.color.sw_text)); textSize = 26f\n        setTypeface(typeface, android.graphics.Typeface.BOLD)\n        setPadding(dp(20), dp(18), dp(20), dp(8))\n        letterSpacing = -0.02f')
s=s.replace('text = value; textSize = size; setTextColor(getColor(R.color.sw_muted)); setPadding(dp(20), 0, dp(20), dp(12))','text = value; textSize = size; setTextColor(getColor(R.color.sw_muted)); setPadding(dp(20), 0, dp(20), dp(14))\n        setLineSpacing(dp(2).toFloat(),1f)')
s=s.replace('setCardBackgroundColor(getColor(R.color.sw_surface)); radius = dp(18).toFloat()\n        strokeColor = getColor(R.color.sw_surface2); strokeWidth = dp(1)','setCardBackgroundColor(getColor(R.color.sw_surface)); radius = dp(20).toFloat()\n        strokeColor = getColor(R.color.sw_outline); strokeWidth = dp(1)\n        cardElevation = dp(2).toFloat()')
s=s.replace('setBackgroundColor(getColor(R.color.sw_nav_bar))\n            elevation = dp(10).toFloat()\n            setItemIconSize(dp(27))\n            itemPaddingTop = dp(8)\n            itemPaddingBottom = dp(8)','setBackgroundColor(getColor(R.color.sw_nav_bar))\n            elevation = dp(12).toFloat()\n            setItemIconSize(dp(24))\n            itemPaddingTop = dp(6)\n            itemPaddingBottom = dp(6)')
s=s.replace('root.addView(nav, LinearLayout.LayoutParams(-1, dp(84)))','root.addView(nav, LinearLayout.LayoutParams(-1, dp(76)))')
colors=root/"app/src/main/res/values/colors.xml"
cs=colors.read_text(encoding="utf-8")
if 'name="sw_outline"' not in cs:
    cs=cs.replace("</resources>",'    <color name="sw_outline">#203747</color>\n    <color name="sw_on_accent">#1B1713</color>\n</resources>')
colors.write_text(cs,encoding="utf-8")
p.write_text(s,encoding="utf-8")
for token in ["class HomeFragment : Fragment()","class SettingsFragment : Fragment()","Stimmgerät öffnen","class TunerFragment : Fragment()","class ChordsFragment : Fragment()"]:
    if token not in s: raise SystemExit("UI redesign validation failed: "+token)
print("PREMIUM UI REDESIGN: PASS")
