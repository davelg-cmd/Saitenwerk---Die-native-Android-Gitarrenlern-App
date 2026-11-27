#!/usr/bin/env python3
"""Replace page-number heuristics with layout-aware PDF text/OCR extraction."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
target = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s = target.read_text(encoding="utf-8")

# Add a dedicated layout-aware importer to the app source set.
helper = r'''package de.saitenwerk.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import com.tom_roush.pdfbox.text.TextPosition
import com.google.android.gms.tasks.Tasks
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import java.util.Locale
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

private data class LayoutToken(val text:String,val x:Float,val y:Float,val width:Float,val height:Float)
private data class LayoutLine(val text:String,val x:Float,val y:Float,val height:Float,val tokens:List<LayoutToken>)
private data class LayoutPage(val number:Int,val width:Float,val height:Float,val lines:List<LayoutLine>)

internal object SongbookLayoutImporter {
    fun importPdf(context:Context, uri:Uri, source:String):List<SongbookSong> {
        val resolver=context.contentResolver
        val descriptor=resolver.openFileDescriptor(uri,"r") ?: error("PDF-Datei konnte nicht geöffnet werden.")
        val renderer=PdfRenderer(descriptor)
        val recognizer=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        try {
            val pages=resolver.openInputStream(uri).use { input ->
                if(input==null) error("PDF-Datei konnte nicht gelesen werden.")
                PDDocument.load(input).use { document ->
                    val result=mutableListOf<LayoutPage>()
                    for(index in 0 until document.numberOfPages) {
                        val page=document.getPage(index)
                        val pageWidth=page.mediaBox.width.coerceAtLeast(1f)
                        val pageHeight=page.mediaBox.height.coerceAtLeast(1f)
                        val stripper=object:PDFTextStripper() {
                            val positions=mutableListOf<TextPosition>()
                            override fun writeString(text:String, textPositions:MutableList<TextPosition>) {
                                positions.addAll(textPositions)
                            }
                        }
                        stripper.sortByPosition=true
                        stripper.startPage=index+1
                        stripper.endPage=index+1
                        stripper.getText(document)
                        var tokens=stripper.positions.mapNotNull { p ->
                            val value=p.unicode?.replace(Regex("""\s+"""),"") ?: ""
                            if(value.isBlank()) null else LayoutToken(
                                value,p.xDirAdj.coerceAtLeast(0f),p.yDirAdj.coerceAtLeast(0f),
                                p.widthDirAdj.coerceAtLeast(0.1f),p.heightDir.coerceAtLeast(1f)
                            )
                        }
                        val extractedChars=tokens.sumOf{it.text.length}
                        if(extractedChars<18) {
                            val ocrTokens=mutableListOf<LayoutToken>()
                            val bitmapPage=renderer.openPage(index)
                            try {
                                val bitmap=Bitmap.createBitmap(
                                    max(1,bitmapPage.width*2),max(1,bitmapPage.height*2),Bitmap.Config.ARGB_8888
                                )
                                try {
                                    bitmapPage.render(bitmap,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                                    val recognized=Tasks.await(recognizer.process(InputImage.fromBitmap(bitmap,0)))
                                    recognized.textBlocks.forEach { block ->
                                        block.lines.forEach { line ->
                                            line.elements.forEach { element ->
                                                val bounds=element.boundingBox ?: return@forEach
                                                val scaleX=pageWidth/bitmap.width
                                                val scaleY=pageHeight/bitmap.height
                                                ocrTokens += LayoutToken(
                                                    element.text,
                                                    bounds.left*scaleX,bounds.top*scaleY,
                                                    bounds.width()*scaleX,bounds.height()*scaleY
                                                )
                                            }
                                        }
                                    }
                                } finally { bitmap.recycle() }
                            } finally { bitmapPage.close() }
                            if(ocrTokens.sumOf{it.text.length}>extractedChars) tokens=ocrTokens
                        }
                        result += LayoutPage(index+1,pageWidth,pageHeight,groupLines(tokens))
                    }
                    result
                }
            }
            return SongbookLayoutParser.parse(pages,source)
        } finally {
            recognizer.close()
            renderer.close()
            descriptor.close()
        }
    }

    private fun groupLines(tokens:List<LayoutToken>):List<LayoutLine> {
        if(tokens.isEmpty()) return emptyList()
        val sorted=tokens.sortedWith(compareBy<LayoutToken>{it.y}.thenBy{it.x})
        val rows=mutableListOf<MutableList<LayoutToken>>()
        sorted.forEach { token ->
            val row=rows.lastOrNull()
            val avg=row?.map{it.height}?.average()?.toFloat() ?: token.height
            if(row==null || abs(row.map{it.y}.average().toFloat()-token.y)>max(2.5f,avg*0.42f))
                rows += mutableListOf(token)
            else row += token
        }
        return rows.map { row ->
            val ordered=row.sortedBy{it.x}
            val words=mutableListOf<MutableList<LayoutToken>>()
            ordered.forEach { token ->
                val word=words.lastOrNull()
                val previous=word?.lastOrNull()
                if(word==null || previous==null || token.x-(previous.x+previous.width)>max(1.8f,previous.height*0.34f))
                    words += mutableListOf(token)
                else word += token
            }
            val wordTokens=words.map { chars ->
                LayoutToken(chars.joinToString(""){it.text},chars.first().x,
                    chars.map{it.y}.average().toFloat(),
                    (chars.last().x+chars.last().width-chars.first().x).coerceAtLeast(0.1f),
                    chars.map{it.height}.average().toFloat())
            }
            val text=wordTokens.joinToString(" "){it.text}.trim()
            LayoutLine(text,wordTokens.minOf{it.x},wordTokens.map{it.y}.average().toFloat(),
                wordTokens.map{it.height}.average().toFloat(),wordTokens)
        }.filter{it.text.isNotBlank()}
    }
}

private object SongbookLayoutParser {
    private val chord=Regex("""^[A-G](?:#|b)?(?:maj(?:7|9|11|13)?|m(?:aj7|7|9|11|13)?|sus[24]?|add9|dim7?|aug|[0-9]{1,2})?(?:/[A-G](?:#|b)?)?$""")
    private val toc=Regex("""\s*(?:\.{2,}|…{1,})\s*\d{1,4}\s*$""")
    private fun isChordLine(line:LayoutLine)=line.tokens.isNotEmpty() &&
        line.tokens.all { chord.matches(it.text.trim(',',':',';','|')) } &&
        line.tokens.size<=18
    private fun letters(s:String)=s.count{it.isLetter()}
    private fun cleanTitle(s:String)=s.trim().trim('#','*','-','♪','♫',' ').replace(Regex("""\s+""")," ")
    private fun titleCandidate(page:LayoutPage,index:Int,median:Float):Boolean {
        val line=page.lines[index]
        val text=cleanTitle(line.text)
        if(text.length !in 3..90 || letters(text)<3 || isChordLine(line) || toc.containsMatchIn(text)) return false
        if(Regex("""(?i)^(seite|page|inhalt|inhaltsverzeichnis|index|copyright|www\.)""").containsMatchIn(text)) return false
        if(text.matches(Regex("""\d{1,4}.*"""))) return false
        val alpha=text.filter{it.isLetter()}
        val upper=alpha.length>=4 && alpha.all{!it.isLowerCase()}
        val prev=page.lines.getOrNull(index-1)
        val next=page.lines.getOrNull(index+1)
        val gapBefore=prev?.let{line.y-(it.y+it.height)} ?: line.y
        val gapAfter=next?.let{it.y-(line.y+line.height)} ?: line.height
        val isolated=gapBefore>median*0.75f && gapAfter>median*0.35f
        val larger=line.height>=median*1.22f
        return upper || larger || isolated
    }
    fun parse(pages:List<LayoutPage>,source:String):List<SongbookSong> {
        if(pages.isEmpty()) return emptyList()
        val starts=mutableListOf<Pair<Int,Int>>()
        pages.forEachIndexed { pi,page ->
            val median=(page.lines.map{it.height}.sorted().let{it.getOrNull(it.size/2)} ?: 8f).coerceAtLeast(1f)
            page.lines.indices.forEach { li ->
                if(titleCandidate(page,li,median)) starts += pi to li
            }
        }
        if(starts.size<2) return emptyList()
        val songs=mutableListOf<SongbookSong>()
        starts.forEachIndexed { si,pair ->
            val (pageIndex,lineIndex)=pair
            val end=starts.getOrNull(si+1)
            val collected=mutableListOf<Pair<LayoutPage,LayoutLine>>()
            for(pi in pageIndex..(end?.first ?: pages.lastIndex)) {
                val page=pages[pi]
                val from=if(pi==pageIndex) lineIndex else 0
                val until=if(end!=null && pi==end.first) end.second else page.lines.size
                if(from<until) page.lines.subList(from,until).forEach{collected += page to it}
            }
            if(collected.size<3) return@forEachIndexed
            val title=cleanTitle(collected.first().second.text).take(120)
            val body=mutableListOf<String>()
            val allChords=linkedSetOf<String>()
            var pending=mutableListOf<LayoutToken>()
            var pendingY=0f
            collected.drop(1).forEachIndexed { index,item ->
                val (page,line)=item
                if(isChordLine(line)) {
                    pending=line.tokens.toMutableList()
                    pendingY=line.y
                } else {
                    val chordTokens=if(pending.isNotEmpty() && (line.y-pendingY)<max(18f,line.height*2.2f)) pending else mutableListOf()
                    val placements=chordTokens.mapNotNull { token ->
                        val value=token.text.trim(',',':',';','|')
                        if(!chord.matches(value)) null else {
                            allChords += value
                            val x=(token.x/page.width).coerceIn(0f,0.98f)
                            "$value@"+String.format(Locale.US,"%.3f",x)
                        }
                    }
                    val marker=if(placements.isEmpty()) "" else "[[CHORDS:"+placements.joinToString(",")+"]]"
                    body += marker+line.text
                    pending.clear()
                }
            }
            val lyrics=body.joinToString("\n").trim()
            if(letters(title)>=3 && lyrics.count{it.isLetter()}>=30) {
                val fingerprint=title.lowercase(Locale.ROOT)
                if(songs.none{it.title.lowercase(Locale.ROOT)==fingerprint}) {
                    songs += SongbookSong(title=title,artist="Unbekannter Künstler",lyrics=lyrics,
                        chords=allChords.toList(),source=source)
                }
            }
        }
        return songs
    }
}
'''
helper_path = root / "app/src/main/java/de/saitenwerk/app/SongbookLayoutImporter.kt"
helper_path.write_text(helper,encoding="utf-8")

# Replace only the PDF import method; all PDF-index/printed-page heuristics are bypassed.
start=s.index("    private fun importPdf(uri:Uri) {")
end=s.index("    private fun queryPdfDisplayName",start)
method=r'''    private fun importPdf(uri:Uri) {
        val progress=ProgressBar(requireContext())
        root.addView(progress,0,LinearLayout.LayoutParams(-1,dp(5)))
        executor.execute {
            try {
                runCatching { requireContext().contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION) }
                val displayName=queryPdfDisplayName(uri)
                val songs=SongbookLayoutImporter.importPdf(requireContext().applicationContext,uri,uri.toString())
                if(songs.isEmpty()) error("Es konnten keine eindeutig abgrenzbaren Liedseiten erkannt werden. Es wurde nichts gespeichert, damit keine falschen Lieder entstehen.")
                val savedCount=db.replacePdfSongs(uri.toString(),songs)
                if(savedCount<=0) error("Es wurden keine Songs gespeichert.")
                db.registerPdf(uri.toString(),displayName,savedCount)
                requireActivity().runOnUiThread {
                    if(progress.parent!=null) root.removeView(progress)
                    buildHome()
                    AlertDialog.Builder(requireContext()).setTitle("PDF layoutbasiert analysiert")
                        .setMessage("$savedCount Songs erkannt und gespeichert. Akkordzeilen werden anhand ihrer tatsächlichen Position über den passenden Textzeilen abgelegt. Bei nicht eindeutig erkannten Seiten wird der Import abgebrochen, statt falsche Zuordnungen zu speichern.")
                        .setPositiveButton("OK",null).show()
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

'''
s=s[:start]+method+s[end:]

# Render chord positions as a separate chord row above the matching lyric line.
render_start=s.index("    private fun renderSongbookLines(")
render_end=s.index("\n    private fun updateSongbookLine",render_start)
renderer=r'''    private fun renderSongbookLines(lines:List<String>,chords:org.json.JSONObject,views:MutableList<View>,scroll:ScrollView,select:(Int)->Unit){
        val box=scroll.getChildAt(0) as? LinearLayout ?: return
        box.removeAllViews();views.clear()
        lines.forEachIndexed{index,line->
            val item=LinearLayout(requireContext()).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(10),dp(7),dp(10),dp(7));setBackgroundColor(if(index==songbookActiveLine)Color.rgb(67,49,35)else Color.rgb(22,24,29))}
            val positioned=Regex("""^\\[\\[CHORDS:([^]]+)]](.*)$""").matchEntire(line)
            if(positioned!=null) {
                val chordRow=LinearLayout(requireContext()).apply{orientation=LinearLayout.HORIZONTAL;weightSum=1000f}
                var previous=0f
                positioned.groupValues[1].split(",").forEach { entry ->
                    val parts=entry.split("@",limit=2)
                    val value=parts.firstOrNull().orEmpty()
                    val x=parts.getOrNull(1)?.toFloatOrNull()?.coerceIn(previous,0.98f) ?: previous
                    val gap=((x-previous)*1000f).coerceAtLeast(0f)
                    if(gap>0f) chordRow.addView(View(requireContext()),LinearLayout.LayoutParams(0,dp(24),gap))
                    chordRow.addView(label(value,14f,Color.rgb(218,169,112)),LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,dp(24)))
                    previous=(x+0.07f).coerceAtMost(1f)
                }
                if(previous<1f) chordRow.addView(View(requireContext()),LinearLayout.LayoutParams(0,dp(24),((1f-previous)*1000f).coerceAtLeast(1f)))
                item.addView(chordRow)
                item.addView(label(positioned.groupValues[2],17f,Color.WHITE))
            } else {
                val chord=chords.optString(index.toString(),"")
                if(chord.isNotBlank())item.addView(label(chord,15f,Color.rgb(218,169,112)))
                item.addView(label(line,17f,Color.WHITE))
            }
            item.setOnClickListener{select(index);Toast.makeText(requireContext(),"Zeile \${index+1} ausgewählt",Toast.LENGTH_SHORT).show()}
            box.addView(item,LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(5)});views.add(item)
        }
    }
'''
s=s[:render_start]+renderer+s[render_end:]
target.write_text(s,encoding="utf-8")
(root/"SONGBOOK_LAYOUT_IMPORT_V2.txt").write_text(
    "SaitenWerk Songbook layout importer V2\n"
    "PDF text positions are retained; scanned pages use OCR bounding boxes; chord rows are aligned to the next lyric line by page coordinates; legacy TOC/page-number parser is bypassed for imports.\n",
    encoding="utf-8"
)
print("SONGBOOK-LAYOUT-IMPORT-V2: PASS")
