#!/usr/bin/env python3
from pathlib import Path
import os
root=Path(os.environ["PROJECT_DIR"])
p=root/"app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s=p.read_text(encoding="utf-8")
a=s.find("    private fun showSong(song: SongbookSong) {")
b=s.find("    private fun openYoutube(song: SongbookSong) {",a)
if a<0 or b<0: raise SystemExit("Songbook showSong/openYoutube not found")
new=r'''    private fun showSong(song: SongbookSong) {
        root.removeAllViews()
        songbookActiveLine=-1
        val back=button("‹  Songbook");back.setOnClickListener{buildHome()};root.addView(back)
        addText(song.title,27f,Color.WHITE,4);addText(song.artist,15f,Color.LTGRAY,8)
        val prefs=requireContext().getSharedPreferences("songbook_performance_v1",Context.MODE_PRIVATE)
        val timeKey="times_\${song.id}";val chordKey="line_chords_\${song.id}"
        val times=runCatching{org.json.JSONObject(prefs.getString(timeKey,"{}")?:"{}")}.getOrElse{org.json.JSONObject()}
        val chords=runCatching{org.json.JSONObject(prefs.getString(chordKey,"{}")?:"{}")}.getOrElse{org.json.JSONObject()}
        val lines=song.lyrics.lines().map{it.trim()}.filter{it.isNotBlank()}
        var selectedLine=0
        val lineViews=mutableListOf<View>()
        lateinit var scroll:ScrollView
        var status:TextView?=null
        var web:WebView?=null
        val playerCard=card()
        if(!song.youtubeId.isNullOrBlank()){
            web=WebView(requireContext()).apply{
                settings.javaScriptEnabled=true;settings.domStorageEnabled=true;settings.mediaPlaybackRequiresUserGesture=false
                addJavascriptInterface(object{
                    @android.webkit.JavascriptInterface fun onTime(seconds:Double){requireActivity().runOnUiThread{updateSongbookLine(seconds,times,lines,lineViews,scroll,status)}}
                    @android.webkit.JavascriptInterface fun onReady(duration:Double){requireActivity().runOnUiThread{status?.text="Video bereit · \${times.length()} von \${lines.size} Zeitmarken"}}
                },"SaitenWerk")
                loadDataWithBaseURL("https://www.youtube.com",songbookPlayerHtml(song.youtubeId),"text/html","UTF-8",null)
            }
            playerCard.addView(web,LinearLayout.LayoutParams(-1,dp(210)))
        }else{
            playerCard.addView(label("Noch kein bestätigtes YouTube-Video verknüpft.",14f,Color.LTGRAY))
            val find=button("YouTube-Suche öffnen");find.setOnClickListener{openYoutube(song)};playerCard.addView(find)
        }
        root.addView(playerCard)
        val playback=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL}
        val start=button("▶  Start");start.setOnClickListener{
            web?.evaluateJavascript("if(window.player){player.playVideo();}",null)
            if(times.length()==0)Toast.makeText(requireContext(),"Noch keine Zeitmarken. Spiele das Lied ab, wähle die jeweilige Textzeile und speichere ihre Zeitmarke.",Toast.LENGTH_LONG).show()
        }
        val pause=button("Ⅱ  Pause");pause.setOnClickListener{web?.evaluateJavascript("if(window.player){player.pauseVideo();}",null)}
        playback.addView(start,LinearLayout.LayoutParams(0,dp(48),1f));playback.addView(pause,LinearLayout.LayoutParams(0,dp(48),1f));root.addView(playback)
        status=label("Synchronisierung: \${times.length()} von \${lines.size} Zeilen markiert",13f,Color.LTGRAY);root.addView(status)
        val editing=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL}
        val mark=button("Zeitmarke setzen");mark.setOnClickListener{
            val view=web?:return@setOnClickListener
            view.evaluateJavascript("window.player ? String(player.getCurrentTime()) : '0'"){raw->
                val seconds=raw?.trim('"')?.toDoubleOrNull()
                if(seconds!=null){times.put(selectedLine.toString(),seconds);prefs.edit().putString(timeKey,times.toString()).apply();status?.text="Synchronisierung: \${times.length()} von \${lines.size} Zeilen markiert";Toast.makeText(requireContext(),"Zeitmarke für Zeile \${selectedLine+1} gespeichert.",Toast.LENGTH_SHORT).show()}
            }
        }
        val chord=button("Akkord setzen");chord.setOnClickListener{
            val choices=(song.chords+listOf("C","D","Dm","E","Em","F","G","Am","A7","D7","G7","Bm","B7")).distinct().toTypedArray()
            AlertDialog.Builder(requireContext()).setTitle("Akkord über Zeile \${selectedLine+1}").setItems(choices){_,which->
                chords.put(selectedLine.toString(),choices[which]);prefs.edit().putString(chordKey,chords.toString()).apply();renderSongbookLines(lines,chords,lineViews,scroll){selectedLine=it}
            }.setNeutralButton("Akkord entfernen"){_,_->chords.remove(selectedLine.toString());prefs.edit().putString(chordKey,chords.toString()).apply();renderSongbookLines(lines,chords,lineViews,scroll){selectedLine=it}}.setNegativeButton("Abbrechen",null).show()
        }
        editing.addView(mark,LinearLayout.LayoutParams(0,dp(48),1.1f));editing.addView(chord,LinearLayout.LayoutParams(0,dp(48),1f));root.addView(editing)
        scroll=ScrollView(requireContext());val lyrics=LinearLayout(requireContext()).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(8),dp(10),dp(8),dp(36))}
        scroll.addView(lyrics);root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        renderSongbookLines(lines,chords,lineViews,scroll){selectedLine=it}
    }

    private var songbookActiveLine:Int=-1
    private fun renderSongbookLines(lines:List<String>,chords:org.json.JSONObject,views:MutableList<View>,scroll:ScrollView,select:(Int)->Unit){
        val box=scroll.getChildAt(0) as? LinearLayout ?: return
        box.removeAllViews();views.clear()
        lines.forEachIndexed{index,line->
            val item=LinearLayout(requireContext()).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(10),dp(7),dp(10),dp(7));setBackgroundColor(if(index==songbookActiveLine)Color.rgb(67,49,35)else Color.rgb(22,24,29))}
            val chord=chords.optString(index.toString(),"");if(chord.isNotBlank())item.addView(label(chord,15f,Color.rgb(218,169,112)))
            item.addView(label(line,17f,Color.WHITE));item.setOnClickListener{select(index);Toast.makeText(requireContext(),"Zeile \${index+1} ausgewählt",Toast.LENGTH_SHORT).show()}
            box.addView(item,LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(5)});views.add(item)
        }
    }
    private fun updateSongbookLine(seconds:Double,times:org.json.JSONObject,lines:List<String>,views:List<View>,scroll:ScrollView,status:TextView?){
        var next=-1;var latest=-1.0
        for(i in lines.indices)if(times.has(i.toString())){val t=times.optDouble(i.toString(),-1.0);if(t<=seconds&&t>=latest){latest=t;next=i}}
        if(next>=0&&next!=songbookActiveLine){songbookActiveLine=next;views.forEachIndexed{i,v->v.setBackgroundColor(if(i==next)Color.rgb(67,49,35)else Color.rgb(22,24,29))};if(next<views.size)scroll.smoothScrollTo(0,views[next].top)}
        status?.text="Videoposition \${"%.1f".format(java.util.Locale.US,seconds)} s · \${times.length()} Zeitmarken"
    }
    private fun songbookPlayerHtml(id:String)= """
        <!doctype html><html><body style="margin:0;background:#000"><div id="player" style="width:100%;height:210px"></div>
        <script src="https://www.youtube.com/iframe_api"></script><script>var player;
        function onYouTubeIframeAPIReady(){player=new YT.Player('player',{videoId:'$id',playerVars:{playsinline:1,rel:0},events:{onReady:function(e){SaitenWerk.onReady(e.target.getDuration());setInterval(function(){try{SaitenWerk.onTime(player.getCurrentTime());}catch(x){}},250);}}});}
        </script></body></html>
    """.trimIndent()

'''
new=new.replace(r'\${','${')
s=s[:a]+new+s[b:]
p.write_text(s,encoding="utf-8")
print("SONGBOOK_PERFORMANCE_SYNC_V2: PASS")
