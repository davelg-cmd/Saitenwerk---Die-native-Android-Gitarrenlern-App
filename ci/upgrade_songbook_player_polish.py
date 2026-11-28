#!/usr/bin/env python3
"""Add a current chord card and OAuth-free public YouTube search to the Songbook."""
from pathlib import Path
import os

root=Path(os.environ["PROJECT_DIR"])
path=root/"app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s=path.read_text(encoding="utf-8")
if "SAITENWERK_PLAYER_POLISH_V1" in s:
    print("SAITENWERK-PLAYER-POLISH-V1: already applied")
    raise SystemExit(0)

status_line = next((line for line in s.splitlines(True) if "status=label(" in line and "Synchronisierung:" in line), None)
if not status_line: raise SystemExit("FEHLER: Player-Status-Anker fehlt.")
card = r'''        val currentChordLabel = label("—",32f,Color.rgb(255,158,35))
        val currentChordCard = card().apply { orientation=LinearLayout.HORIZONTAL; gravity=android.view.Gravity.CENTER_VERTICAL }
        val currentDiagram = SongbookChordDiagram(requireContext())
        currentChordCard.addView(currentDiagram,LinearLayout.LayoutParams(dp(112),dp(112)))
        val currentInfo = LinearLayout(requireContext()).apply { orientation=LinearLayout.VERTICAL }
        currentInfo.addView(label("JETZT SPIELEN",11f,Color.LTGRAY))
        currentInfo.addView(currentChordLabel)
        currentInfo.addView(label("Aktueller Akkord",13f,Color.WHITE))
        currentChordCard.addView(currentInfo,LinearLayout.LayoutParams(0,-2,1f))
        root.addView(currentChordCard)
'''
s=s.replace(status_line,status_line+card,1)

old="updateSongbookLine(seconds,times,lines,lineViews,scroll,status)"
new="updateSongbookLine(seconds,times,chords,lines,lineViews,scroll,status,currentChordLabel,currentDiagram)"
if old not in s: raise SystemExit("FEHLER: Player-Zeitcallback fehlt.")
s=s.replace(old,new,1)
old_sig="private fun updateSongbookLine(seconds:Double,times:org.json.JSONObject,lines:List<String>,views:List<View>,scroll:ScrollView,status:TextView?)"
new_sig="private fun updateSongbookLine(seconds:Double,times:org.json.JSONObject,chords:org.json.JSONObject,lines:List<String>,views:List<View>,scroll:ScrollView,status:TextView?,currentChord:TextView,diagram:SongbookChordDiagram)"
if old_sig not in s: raise SystemExit("FEHLER: updateSongbookLine-Signatur fehlt.")
s=s.replace(old_sig,new_sig,1)
needle="        status?.text="
pos=s.find(needle,s.find(new_sig))
if pos<0: raise SystemExit("FEHLER: Statusaktualisierung fehlt.")
s=s[:pos]+'        val activeChord = if(next>=0) chords.optString(next.toString(),"") else ""\n        currentChord.text=activeChord.ifBlank { "—" }\n        diagram.setChord(activeChord)\n'+s[pos:]

a=s.find("    private fun searchYoutubeForSong(song: SongbookSong) {")
if a<0: raise SystemExit("FEHLER: YouTube-Suchfunktion fehlt.")
b=s.find("\n    }",a)+len("\n    }")
if b<=a: raise SystemExit("FEHLER: YouTube-Suchfunktion konnte nicht abgegrenzt werden.")
replacement=r'''    private fun searchYoutubeForSong(song: SongbookSong) {
        val query=Uri.encode(song.artist+" "+song.title+" guitar")
        val intent=Intent(Intent.ACTION_VIEW,Uri.parse("https://www.youtube.com/results?search_query="+query))
        runCatching { startActivity(intent) }.onFailure {
            Toast.makeText(requireContext(),"YouTube konnte nicht geöffnet werden.",Toast.LENGTH_LONG).show()
        }
        Toast.makeText(requireContext(),"Wähle das passende Video und füge danach den Link über „Link manuell eintragen“ ein.",Toast.LENGTH_LONG).show()
    }'''
s=s[:a]+replacement+s[b:]

diagram=r'''
private class SongbookChordDiagram(context: Context) : View(context) {
    private val p=android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG)
    private var chord=""
    fun setChord(value:String) { if(chord!=value){chord=value;invalidate()} }
    override fun onDraw(canvas:android.graphics.Canvas) {
        super.onDraw(canvas)
        val l=width*.18f; val r=width*.88f; val t=height*.12f; val b=height*.82f
        val dx=(r-l)/5f; val dy=(b-t)/5f
        p.color=Color.WHITE; p.strokeWidth=2f
        for(i in 0..5){canvas.drawLine(l+i*dx,t,l+i*dx,b,p);canvas.drawLine(l,t+i*dy,r,t+i*dy,p)}
        p.strokeWidth=5f;canvas.drawLine(l,t,r,t,p)
        val dots=when(chord){
            "C"->listOf(5 to 3,4 to 2,2 to 1)
            "D"->listOf(3 to 2,2 to 3,1 to 2)
            "Dm"->listOf(3 to 2,2 to 3,1 to 1)
            "E"->listOf(5 to 2,4 to 2,3 to 1)
            "Em"->listOf(5 to 2,4 to 2)
            "G"->listOf(6 to 3,5 to 2,1 to 3)
            "Am"->listOf(4 to 2,3 to 2,2 to 1)
            "A"->listOf(4 to 2,3 to 2,2 to 2)
            else->emptyList()
        }
        p.style=android.graphics.Paint.Style.FILL;p.color=Color.rgb(255,158,35)
        for((string,fret) in dots)canvas.drawCircle(l+(6-string)*dx,t+(fret-.5f)*dy,5.5f,p)
        p.color=Color.WHITE;p.textSize=11f;p.textAlign=android.graphics.Paint.Align.CENTER
        canvas.drawText(chord.ifBlank{"—"},width/2f,height-2f,p)
    }
}
'''
if "private class SongbookChordDiagram" not in s:
    i=s.find("private class SimpleTextWatcher")
    if i<0: raise SystemExit("FEHLER: SimpleTextWatcher-Klassenanker fehlt.")
    s=s[:i]+diagram+"\n"+s[i:]

s += "\n// SAITENWERK_PLAYER_POLISH_V1\n"
path.write_text(s,encoding="utf-8")
(root/"SONGBOOK_PLAYER_POLISH_V1.txt").write_text(
    "SaitenWerk player polish V1: current chord card/diagram synchronized to lyric line; public YouTube search without OAuth.\n",
    encoding="utf-8")
print("SAITENWERK-PLAYER-POLISH-V1: PASS")
