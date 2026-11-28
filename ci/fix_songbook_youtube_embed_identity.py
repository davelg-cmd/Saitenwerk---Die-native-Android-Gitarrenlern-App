#!/usr/bin/env python3
"""Fix YouTube embed identity/referrer metadata for Android WebView playback."""
from pathlib import Path
import os

root=Path(os.environ["PROJECT_DIR"])
p=root/"app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
s=p.read_text(encoding="utf-8")

old_base='loadDataWithBaseURL("https://www.youtube.com",songbookPlayerHtml(song.youtubeId),"text/html","UTF-8",null)'
new_base='loadDataWithBaseURL("https://www.youtube-nocookie.com",songbookPlayerHtml(song.youtubeId),"text/html","UTF-8",null)'
if old_base not in s:
    if new_base not in s:
        raise SystemExit("FEHLER: YouTube-WebView-BaseURL nicht gefunden.")
else:
    s=s.replace(old_base,new_base,1)

old_html='''        <!doctype html><html><body style="margin:0;background:#000"><div id="player" style="width:100%;height:210px"></div>
        <script src="https://www.youtube.com/iframe_api"></script><script>var player;
        function onYouTubeIframeAPIReady(){player=new YT.Player('player',{videoId:'$id',playerVars:{playsinline:1,rel:0},events:{onReady:function(e){SaitenWerk.onReady(e.target.getDuration());setInterval(function(){try{SaitenWerk.onTime(player.getCurrentTime());}catch(x){}},250);}}});}
        </script></body></html>'''
new_html='''        <!doctype html><html><head>
        <meta name="referrer" content="strict-origin-when-cross-origin">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        </head><body style="margin:0;background:#000"><div id="player" style="width:100%;height:210px"></div>
        <script src="https://www.youtube.com/iframe_api"></script><script>var player;
        function onYouTubeIframeAPIReady(){player=new YT.Player('player',{videoId:'$id',playerVars:{playsinline:1,rel:0,origin:'https://www.youtube-nocookie.com'},events:{onReady:function(e){SaitenWerk.onReady(e.target.getDuration());setInterval(function(){try{SaitenWerk.onTime(player.getCurrentTime());}catch(x){}},250);}}});}
        </script></body></html>'''
if old_html not in s:
    if 'origin:\'https://www.youtube-nocookie.com\'' not in s:
        raise SystemExit("FEHLER: YouTube-Player-HTML-Anker nicht gefunden.")
else:
    s=s.replace(old_html,new_html,1)

if 'https://www.youtube-nocookie.com' not in s or 'strict-origin-when-cross-origin' not in s:
    raise SystemExit("FEHLER: YouTube-Embed-Identität konnte nicht vollständig gesetzt werden.")

p.write_text(s,encoding="utf-8")
(root/"YOUTUBE_EMBED_IDENTITY_V1.txt").write_text(
    "YouTube embedded player now declares a stable HTTPS base origin and strict referrer policy.\n",
    encoding="utf-8")
print("YOUTUBE-EMBED-IDENTITY-V1: PASS")
