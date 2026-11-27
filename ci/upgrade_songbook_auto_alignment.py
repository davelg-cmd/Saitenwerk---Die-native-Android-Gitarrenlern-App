#!/usr/bin/env python3
"""Automatically align imported lyrics with YouTube caption timestamps when available."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s = p.read_text(encoding="utf-8")

anchor = '        status=label("Synchronisierung: ${times.length()} von ${lines.size} Zeilen markiert",13f,Color.LTGRAY);root.addView(status)\n'
if anchor not in s:
    raise SystemExit("FEHLER: Songbook-Synchronisierungsstatus nicht gefunden.")
if "autoAlignLyricsFromYoutube" not in s:
    injection = r"""
        if (!song.youtubeId.isNullOrBlank() && times.length() < lines.size) {
            status?.text = "Suche automatisch nach passenden YouTube-Untertiteln …"
            Thread {
                val aligned = runCatching { autoAlignLyricsFromYoutube(song.youtubeId!!, lines) }.getOrElse { org.json.JSONObject() }
                activity?.runOnUiThread {
                    if (aligned.length() > 0) {
                        val keys = aligned.keys()
                        while (keys.hasNext()) {
                            val key = keys.next()
                            if (!times.has(key)) times.put(key, aligned.optDouble(key))
                        }
                        prefs.edit().putString(timeKey, times.toString()).apply()
                        status?.text = "Automatisch synchronisiert: ${times.length()} von ${lines.size} Zeilen"
                    } else {
                        status?.text = "Keine passenden Untertitel gefunden – manuelle Zeitmarken bleiben verfügbar."
                    }
                }
            }.start()
        }
"""
    s = s.replace(anchor, anchor + injection, 1)

helper_anchor = '    private fun songbookPlayerHtml(id:String)= """\n'
if helper_anchor not in s:
    raise SystemExit("FEHLER: Einfügepunkt für YouTube-Player nicht gefunden.")
if "private fun autoAlignLyricsFromYoutube" not in s:
    helper = r'''
    private fun autoAlignLyricsFromYoutube(videoId:String, lines:List<String>):org.json.JSONObject {
        val result=org.json.JSONObject()
        fun words(value:String)=value.lowercase(java.util.Locale.ROOT)
            .replace(Regex("[^\\p{L}\\p{N} ]")," ")
            .split(Regex("\\s+")).filter{it.length>2}.toSet()
        for (language in listOf("de","en")) {
            val url="https://www.youtube.com/api/timedtext?v="+
                java.net.URLEncoder.encode(videoId,"UTF-8")+
                "&lang="+language+"&kind=asr&fmt=json3"
            val connection=(java.net.URL(url).openConnection() as java.net.HttpURLConnection).apply {
                connectTimeout=7000;readTimeout=9000
                setRequestProperty("User-Agent","Mozilla/5.0 (Android) SaitenWerk")
            }
            val events=try {
                if(connection.responseCode !in 200..299) continue
                val body=connection.inputStream.bufferedReader().use{it.readText()}
                val array=org.json.JSONObject(body).optJSONArray("events") ?: continue
                val captions=mutableListOf<Pair<Double,String>>()
                for(i in 0 until array.length()) {
                    val event=array.optJSONObject(i) ?: continue
                    val segments=event.optJSONArray("segs") ?: continue
                    val text=buildString {
                        for(j in 0 until segments.length()) append(segments.optJSONObject(j)?.optString("utf8","") ?: "")
                    }.trim()
                    val start=event.optDouble("tStartMs",-1.0)/1000.0
                    if(start>=0 && text.isNotBlank()) captions += start to text
                }
                captions
            } catch (_:Throwable) { emptyList() } finally { connection.disconnect() }
            if(events.isEmpty()) continue

            var cursor=0
            for(lineIndex in lines.indices) {
                val target=words(lines[lineIndex])
                if(target.size<2) continue
                var bestScore=0.0
                var bestStart=-1.0
                var bestEnd=cursor
                for(start in cursor until events.size) {
                    val combined=StringBuilder()
                    for(end in start until minOf(events.size,start+9)) {
                        if(events[end].first-events[start].first>11.0) break
                        combined.append(' ').append(events[end].second)
                        val spoken=words(combined.toString())
                        val score=target.count{it in spoken}.toDouble()/target.size
                        if(score>bestScore) {
                            bestScore=score;bestStart=events[start].first;bestEnd=end+1
                        }
                    }
                    if(bestScore>=0.82) break
                }
                if(bestStart>=0 && bestScore>=0.52) {
                    result.put(lineIndex.toString(),bestStart)
                    cursor=maxOf(cursor,bestEnd)
                }
            }
            if(result.length()>=maxOf(2,lines.size/5)) return result
            result.keys().asSequence().toList().forEach{result.remove(it)}
        }
        return result
    }

'''
    s = s.replace(helper_anchor, helper + helper_anchor, 1)

p.write_text(s, encoding="utf-8")
print("SONGBOOK-AUTO-CAPTION-ALIGNMENT: PASS")
