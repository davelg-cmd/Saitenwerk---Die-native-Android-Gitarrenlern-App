package de.saitenwerk.app

import android.content.Context
import android.net.Uri
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.pdmodel.PDDocument
import com.tom_roush.pdfbox.text.PDFTextStripper
import org.json.JSONArray
import java.io.File
import java.util.Locale

object SongbookPdfImporter {
    private const val EXPECTED_SONGS=452
    private const val PDF_FILE="songbook.pdf"
    private const val CATALOG_FILE="songbook_catalog.json"
    fun importPdf(context:Context,uri:Uri){
        PDFBoxResourceLoader.init(context.applicationContext)
        val temp=File(context.cacheDir,"songbook-import.pdf")
        context.contentResolver.openInputStream(uri).use{input->requireNotNull(input){"PDF konnte nicht gelesen werden."};temp.outputStream().use{output->input.copyTo(output)}}
        val songs=parse(temp);require(songs.size==EXPECTED_SONGS){"Erwartet wurden $EXPECTED_SONGS Songs, erkannt wurden ${songs.size}."}
        temp.copyTo(File(context.filesDir,PDF_FILE),true)
        val ar=JSONArray();songs.forEach{s->ar.put(org.json.JSONObject().put("title",s.title).put("artist",s.artist).put("genre",s.genre).put("sourcePageStart",s.sourcePageStart).put("sourcePageEnd",s.sourcePageEnd).put("importedContent",s.importedContent))}
        File(context.filesDir,CATALOG_FILE).writeText(ar.toString());temp.delete()
    }
    private fun parse(file:File):List<Song>{
        PDDocument.load(file).use{doc->
            val stripper=PDFTextStripper().apply{sortByPosition=true}
            val pages=stripper.getText(doc).split("\u000C")
            val index=pages.take(8).joinToString("\\n")
            val entries=Regex("(?m)^\\s*(\\d{1,3})\\.\\s*(.+?)\\.{3,}\\s*(\\d{1,3})\\s*$").findAll(index)
                .map{Triple(it.groupValues[1].toInt(),it.groupValues[2].trim(),it.groupValues[3].toInt())}.filter{it.first in 1..EXPECTED_SONGS}.distinctBy{it.first}.toList()
            require(entries.size==EXPECTED_SONGS){"Inhaltsverzeichnis konnte nicht vollständig gelesen werden (${entries.size}/$EXPECTED_SONGS)."}
            val out=mutableListOf<Song>()
            for(i in entries.indices){val e=entries[i];val end=if(i+1<entries.size)entries[i+1].third-1 else doc.numberOfPages;val c=extract(stripper,doc,e.third,end);val ta=split(e.second);out.add(Song(ta.first,ta.second,"PDF-Songbook",false,e.third,end,normalize(c)))}
            return out
        }
    }
    private fun extract(s:PDFTextStripper,d:PDDocument,a:Int,b:Int)=run{s.startPage=a.coerceAtLeast(1);s.endPage=b.coerceAtMost(d.numberOfPages);s.getText(d).replace("\u000C","\n").trim()}
    private fun split(raw:String):Pair<String,String>{val s=raw.replace(Regex("\\s+")," ").trim();Regex("^(.+?)\\s*\\(([^()]+)\\)$").find(s)?.let{return it.groupValues[1].trim() to it.groupValues[2].trim()};Regex("^(.+?)\\s+-\\s+(.+)$").find(s)?.let{return it.groupValues[1].trim() to it.groupValues[2].trim()};return s to ""}
    private fun normalize(raw:String):String{
        val lines=raw.lines().map{it.trimEnd()};val out=mutableListOf<String>();var i=0
        val chordLine=Regex("^\\s*(?:[A-H](?:is|es|#|b)?(?:m|maj|sus|dim|aug|add|7|9|11|13|/)?[0-9]*(?:/[A-H](?:is|es|#|b)?)?)(?:\\s+[A-H](?:is|es|#|b)?(?:m|maj|sus|dim|aug|add|7|9|11|13|/)?[0-9]*(?:/[A-H](?:is|es|#|b)?)?)*\\s*[;,.]?\\s*$",RegexOption.IGNORE_CASE)
        while(i<lines.size){val l=lines[i];if(chordLine.matches(l)&&i+1<lines.size&&lines[i+1].isNotBlank()){val cs=l.replace(";"," ").replace(","," ").trim().split(Regex("\\s+")).filter{it.isNotBlank()};if(cs.isNotEmpty()){out.add(cs.joinToString(" "){"[\${norm(it)}]"}+lines[i+1]);i+=2;continue}};out.add(l);i++}
        return out.joinToString("\\n").replace(Regex("(?m)^Songbook vom.*$"),"").replace(Regex("(?m)^http://www\\.Lyricsarchiv\\.de.*$"),"").replace(Regex("(?m)^\\s*Seite\\s+\\d+\\s+von\\s+\\d+.*$"),"").trim()
    }
    private fun norm(c:String):String{var x=c.trim().replace("H","B");if(x.length==1&&x[0].isLowerCase())x=x.uppercase(Locale.getDefault())+"m";return x}
}
