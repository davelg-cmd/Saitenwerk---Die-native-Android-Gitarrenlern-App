#!/usr/bin/env python3
from pathlib import Path
import os
root=Path(os.environ["PROJECT_DIR"])
p=root/"app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s=p.read_text(encoding="utf-8")
s=s.replace("        seedPublicDomainSongsIfEmpty()\n","",1)
a=s.find("    private fun buildHome() {")
if a < 0: raise SystemExit("buildHome anchor missing")
b=s.find("    private fun showAddSongDialog() {
        val form=LinearLayout(requireContext()).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(dp(20),dp(8),dp(20),0)
        }
        fun field(hintText:String,multiline:Boolean=false):EditText {
            return EditText(requireContext()).apply {
                hint=hintText
                setTextColor(Color.WHITE)
                setHintTextColor(Color.LTGRAY)
                setPadding(dp(12),dp(10),dp(12),dp(10))
                setBackgroundColor(Color.rgb(31,36,43))
                if(multiline) {
                    minLines=5
                    gravity=android.view.Gravity.TOP
                    inputType=android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE or android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
                } else {
                    setSingleLine(true)
                    inputType=android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
                }
            }
        }
        val title=field("Liedtitel")
        val artist=field("Interpret")
        val lyrics=field("Liedtext – Akkorde kannst du direkt eintragen, z. B. [G]Heute ist ein schöner Tag")
        val chordText=field("Akkorde (optional, z. B. G, D, Em, C)")
        form.addView(title,LinearLayout.LayoutParams(-1,dp(52)).apply{bottomMargin=dp(8)})
        form.addView(artist,LinearLayout.LayoutParams(-1,dp(52)).apply{bottomMargin=dp(8)})
        form.addView(lyrics,LinearLayout.LayoutParams(-1,dp(180)).apply{bottomMargin=dp(8)})
        form.addView(chordText,LinearLayout.LayoutParams(-1,dp(52)))
        val scroll=ScrollView(requireContext()).apply{addView(form)}
        val dialog=androidx.appcompat.app.AlertDialog.Builder(requireContext())
            .setTitle("Eigenes Lied anlegen")
            .setView(scroll)
            .setNegativeButton("Abbrechen",null)
            .setPositiveButton("Speichern",null)
            .create()
        dialog.setOnShowListener {
            dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val songTitle=title.text.toString().trim()
                val songArtist=artist.text.toString().trim().ifBlank{"Unbekannter Künstler"}
                val songLyrics=lyrics.text.toString().trim()
                if(songTitle.isBlank()) {
                    title.error="Bitte einen Liedtitel eingeben"
                    return@setOnClickListener
                }
                if(songLyrics.isBlank()) {
                    lyrics.error="Bitte den Liedtext eintragen"
                    return@setOnClickListener
                }
                val chordPattern=Regex("""(?<![A-Za-z0-9])([A-H](?:#|b)?(?:maj7|maj9|m7b5|m7|m9|sus2|sus4|add9|dim7|dim|aug|7|6|5|9|11|13|m)?)(?![A-Za-z0-9])""",RegexOption.IGNORE_CASE)
                val found=(chordPattern.findAll(songLyrics+"\n"+chordText.text.toString()).map{it.groupValues[1]}).toMutableSet()
                val song=SongbookSong(
                    title=songTitle,
                    artist=songArtist,
                    lyrics=songLyrics,
                    chords=found.toList(),
                    source="manual"
                )
                db.upsert(song)
                dialog.dismiss()
                buildHome()
                Toast.makeText(requireContext(),"„$songTitle“ wurde gespeichert.",Toast.LENGTH_LONG).show()
            }
        }
        dialog.show()
    }

    private fun autoLinkYoutubeSongs() {",a)
if a<0 or b<0: raise SystemExit("Songbook home anchors missing")
home=r'''    private fun buildHome() {
        root.removeAllViews()
        val prefs=requireContext().getSharedPreferences("songbook_library_v2",Context.MODE_PRIVATE)
        var shelf="mine"
        addText("SONGBOOK",28f,Color.WHITE,2)
        addText("Deine Musikbibliothek – offline und jederzeit griffbereit.",14f,Color.LTGRAY,8)
        val mine=db.all().filter{it.source!="builtin:public-domain"}
        val summary=card()
        val metrics=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL}
        metrics.addView(label(mine.size.toString()+"\nEIGENE SONGS",17f,Color.WHITE),LinearLayout.LayoutParams(0,dp(62),1f))
        metrics.addView(label(mine.sumOf{it.chords.size}.toString()+"\nAKKORDE",15f,Color.WHITE),LinearLayout.LayoutParams(0,dp(62),1f))
        summary.addView(metrics);root.addView(summary)
        val addSong=button("＋  Lied manuell hinzufügen")
        addSong.setOnClickListener{showAddSongDialog()};root.addView(addSong)
        val search=EditText(requireContext()).apply{hint="Song oder Künstler suchen";setSingleLine();setTextColor(Color.WHITE);setHintTextColor(Color.LTGRAY);setPadding(dp(14),0,dp(14),0);setBackgroundColor(Color.rgb(25,38,48))}
        root.addView(search,LinearLayout.LayoutParams(-1,dp(50)).apply{topMargin=dp(10);bottomMargin=dp(8)})
        val tabs=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL}
        val content=LinearLayout(requireContext()).apply{orientation=LinearLayout.VERTICAL}
        val scroll=ScrollView(requireContext());scroll.addView(content)
        root.addView(tabs);root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        fun refresh(q:String=""){
            content.removeAllViews()
            val favorites=(prefs.getStringSet("favorites",emptySet())?:emptySet())
            val allSongs=if(shelf=="classic") PublicDomainSongCatalog.songs.map{seed->SongbookSong(id=seed.title.hashCode().toLong(),title=seed.title,artist=seed.artist,lyrics=seed.lyrics,chords=seed.chords,source="builtin:public-domain",youtubeId=seed.youtubeId,youtubeConfidence=seed.confidence)} else db.all()
            val songs=allSongs.filter{song->
                val classic=song.source=="builtin:public-domain"
                (when(shelf){"classic"->classic;"favorites"->!classic&&song.id.toString() in favorites;else->!classic}) &&
                (q.isBlank()||(song.title+" "+song.artist).contains(q,true))
            }
            if(songs.isEmpty())content.addView(label(when(shelf){"favorites"->"Noch keine Favoriten. Markiere Songs mit ☆.";"classic"->"Keine Klassiker vorhanden." ;else->"Dein Songbook ist leer. Tippe auf „Lied manuell hinzufügen“, um dein erstes Lied anzulegen."},15f,Color.LTGRAY))
            songs.forEach{song->
                val c=card();c.addView(label(song.title,18f,Color.WHITE));c.addView(label(song.artist+" · "+song.chords.size+" Akkorde",12f,Color.LTGRAY))
                val actions=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL}
                val open=button("Song öffnen");open.setOnClickListener{showSong(song)}
                actions.addView(open,LinearLayout.LayoutParams(0,dp(46),1f))
                if(!song.source.startsWith("builtin:")){
                    val star=button(if(song.id.toString() in favorites)"★" else "☆")
                    star.setOnClickListener{val updated=favorites.toMutableSet();if(!updated.add(song.id.toString()))updated.remove(song.id.toString());prefs.edit().putStringSet("favorites",updated).apply();refresh(search.text.toString())}
                    actions.addView(star,LinearLayout.LayoutParams(dp(54),dp(46)))
                }
                c.addView(actions);content.addView(c)
            }
        }
        fun drawTabs(){
            tabs.removeAllViews()
            listOf("mine" to "Meine Songs","favorites" to "Favoriten","classic" to "Klassiker").forEach{(key,title)->
                val t=button(title);t.textSize=11f;t.setTextColor(if(shelf==key)Color.rgb(255,184,92)else Color.LTGRAY)
                t.setOnClickListener{shelf=key;drawTabs();refresh(search.text.toString())}
                tabs.addView(t,LinearLayout.LayoutParams(0,dp(44),1f))
            }
        }
        search.addTextChangedListener(SimpleTextWatcher{refresh(it)})
        drawTabs();refresh()
    }

'''
s=s[:a]+home+s[b:]
# no background guessing or auto-linking; user confirms video selection.
s=s.replace("        autoLinkYoutubeSongs()\n","",1)
# Replace embedded WebView song screen with an offline-native lyric/chord practice screen.
a=s.find("    private fun showSong(song: SongbookSong) {")
b=s.find("    private fun renderSongbookLines(",a)
if a<0 or b<0: raise SystemExit("Song player anchors missing")
player=r'''    private fun showSong(song: SongbookSong) {
        root.removeAllViews()
        val prefs=requireContext().getSharedPreferences("songbook_player_v2",Context.MODE_PRIVATE)
        val lines=song.lyrics.lines().map{it.trim()}.filter{it.isNotBlank()}
        val chords=runCatching{org.json.JSONObject(prefs.getString("chords_"+song.id,"{}")?:"{}")}.getOrElse{org.json.JSONObject()}
        var active=0
        var transpose=prefs.getInt("transpose_"+song.id,0)
        val back=button("‹  Songbook");back.setOnClickListener{buildHome()};root.addView(back)
        addText(song.title,26f,Color.WHITE,2);addText(song.artist,14f,Color.LTGRAY,8)
        val current=card()
        current.addView(label("AKTUELLER AKKORD",12f,Color.LTGRAY))
        val currentChord=label("—",30f,Color.rgb(255,184,92));current.addView(currentChord)
        val diagram=SongbookChordDiagram(requireContext());current.addView(diagram,LinearLayout.LayoutParams(-1,dp(132)));root.addView(current)
        val transposeRow=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL}
        val down=button("−");val key=button("Tonart 0");val up=button("+")
        fun chordForLine():String{
            val raw=chords.optString(active.toString(),song.chords.getOrNull(active%song.chords.size.coerceAtLeast(1))?:"")
            return transposeChord(raw,transpose)
        }
        fun updateChord(){val value=chordForLine();currentChord.text=value.ifBlank{"—"};diagram.setChord(value);key.text="Tonart "+(if(transpose>0)"+" else "")+transpose;prefs.edit().putInt("transpose_"+song.id,transpose).apply()}
        down.setOnClickListener{transpose=(transpose-1).coerceAtLeast(-6);updateChord()}
        up.setOnClickListener{transpose=(transpose+1).coerceAtMost(6);updateChord()}
        transposeRow.addView(down,LinearLayout.LayoutParams(dp(54),dp(44)));transposeRow.addView(key,LinearLayout.LayoutParams(0,dp(44),1f));transposeRow.addView(up,LinearLayout.LayoutParams(dp(54),dp(44)));root.addView(transposeRow)
        val lyricScroll=ScrollView(requireContext())
        val lyricColumn=LinearLayout(requireContext()).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(4),dp(8),dp(4),dp(28))}
        lyricScroll.addView(lyricColumn);root.addView(lyricScroll,LinearLayout.LayoutParams(-1,0,1f))
        val rows=mutableListOf<TextView>()
        fun redraw(){
            rows.forEachIndexed{i,v->v.setBackgroundColor(if(i==active)Color.rgb(73,52,34)else Color.rgb(22,31,40))}
            updateChord()
        }
        lines.forEachIndexed{index,line->
            val row=TextView(requireContext()).apply{text=(if(chords.optString(index.toString()).isNotBlank())transposeChord(chords.optString(index.toString()),transpose)+"\n" else "")+line;textSize=17f;setTextColor(Color.WHITE);setPadding(dp(12),dp(12),dp(12),dp(12));setBackgroundColor(Color.rgb(22,31,40));setOnClickListener{active=index;redraw();lyricScroll.smoothScrollTo(0,top)}}
            lyricColumn.addView(row,LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(5)});rows.add(row)
        }
        val controls=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL}
        val previous=button("‹ Zurück");val assign=button("Akkord setzen");val next=button("Weiter ›")
        fun select(index:Int){active=index.coerceIn(0,(lines.size-1).coerceAtLeast(0));redraw();if(active<rows.size)lyricScroll.smoothScrollTo(0,rows[active].top)}
        previous.setOnClickListener{select(active-1)};next.setOnClickListener{select(active+1)}
        assign.setOnClickListener{
            val options=(song.chords+listOf("C","D","Dm","E","Em","F","G","Am","A7","D7","G7","Bm","B7")).distinct().toTypedArray()
            androidx.appcompat.app.AlertDialog.Builder(requireContext()).setTitle("Akkord für diese Textzeile").setItems(options){_,which->chords.put(active.toString(),options[which]);prefs.edit().putString("chords_"+song.id,chords.toString()).apply();redraw()}
                .setNeutralButton("Entfernen"){_,_->chords.remove(active.toString());prefs.edit().putString("chords_"+song.id,chords.toString()).apply();redraw()}
                .setNegativeButton("Abbrechen",null).show()
        }
        controls.addView(previous,LinearLayout.LayoutParams(0,dp(48),1f));controls.addView(assign,LinearLayout.LayoutParams(0,dp(48),1.2f));controls.addView(next,LinearLayout.LayoutParams(0,dp(48),1f));root.addView(controls)
        val video=button("YouTube optional extern öffnen");video.setOnClickListener{openYoutube(song)};root.addView(video)
        redraw()
    }

    private fun transposeChord(chord:String,semitones:Int):String{
        if(chord.isBlank()||semitones==0)return chord
        val roots=listOf("C","C#","D","D#","E","F","F#","G","G#","A","A#","B")
        val flat=mapOf("Db" to "C#","Eb" to "D#","Gb" to "F#","Ab" to "G#","Bb" to "A#")
        val match=Regex("^([A-G](?:#|b)?)(.*)$").matchEntire(chord)?:return chord
        val root=flat[match.groupValues[1]]?:match.groupValues[1]
        val index=roots.indexOf(root);if(index<0)return chord
        return roots[(index+semitones+120)%12]+match.groupValues[2]
    }

'''
s=s[:a]+player+s[b:]
# Add state after replacing the player, so the splice cannot discard it.
helper=s.find("    private fun renderSongbookLines(",a)
if helper<0: raise SystemExit("renderSongbookLines anchor missing after player replacement")
s=s[:helper] + "    private var songbookActiveLine: Int = 0\n" + s[helper:]
(root/"SONGBOOK_REDESIGN_V2.txt").write_text("V2: personal library starts empty; separate public-domain shelf; favorites; native offline lyrics practice; chord assignment; transpose; external optional YouTube only.\n",encoding="utf-8")
p.write_text(s,encoding="utf-8")
print("SONGBOOK_REDESIGN_V2: PASS")
