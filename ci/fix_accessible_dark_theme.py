#!/usr/bin/env python3
"""Force a consistent high-contrast dark theme and accessible Songbook controls."""
from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
theme_file = root / "app/src/main/res/values/themes.xml"
if not theme_file.is_file():
    raise SystemExit("FEHLER: themes.xml fehlt.")
theme = theme_file.read_text(encoding="utf-8")
theme = theme.replace(
    'parent="Theme.Material3.DayNight.NoActionBar"',
    'parent="Theme.Material3.Dark.NoActionBar"'
)
if 'parent="Theme.Material3.Dark.NoActionBar"' not in theme:
    raise SystemExit("FEHLER: SaitenWerk-Haupttheme konnte nicht auf Dark umgestellt werden.")

style_pattern = re.compile(r'(<style name="Theme\.Saitenwerk"[^>]*>)(.*?)(</style>)', re.S)
match = style_pattern.search(theme)
if not match:
    raise SystemExit("FEHLER: Theme.Saitenwerk-Style nicht gefunden.")
body = match.group(2)
items = [
    '<item name="colorSurface">@color/sw_surface</item>',
    '<item name="colorOnSurface">@color/sw_text</item>',
    '<item name="colorSurfaceVariant">@color/sw_surface2</item>',
    '<item name="colorOnSurfaceVariant">@color/sw_muted</item>',
    '<item name="colorOnPrimary">@color/sw_on_accent</item>',
    '<item name="android:colorAccent">@color/sw_copper</item>',
    '<item name="android:forceDarkAllowed">false</item>',
]
for item in items:
    attr_name = re.search(r'<item name="([^"]+)">', item).group(1)
    if not re.search(r'<item name="' + re.escape(attr_name) + r'">', body):
        body += "\n        " + item
theme = theme[:match.start(2)] + body + theme[match.end(2):]
theme_file.write_text(theme, encoding="utf-8")

songbook = root / "app/src/main/java/de/saitenwerk/app/IntelligentSongbook.kt"
if not songbook.is_file():
    raise SystemExit("FEHLER: IntelligentSongbook.kt fehlt.")
s = songbook.read_text(encoding="utf-8")
s = s.replace("import android.app.AlertDialog", "import androidx.appcompat.app.AlertDialog")
s = s.replace(
    "AlertDialog.Builder(requireContext())",
    "AlertDialog.Builder(requireContext(), R.style.ThemeOverlay_Saitenwerk_Dialog)"
)
s = s.replace("setHintTextColor(Color.GRAY)", "setHintTextColor(Color.rgb(189,161,142))")
s = s.replace("setBackgroundColor(Color.rgb(15,16,19))", "setBackgroundColor(Color.rgb(7,19,30))")
s = s.replace("setBackgroundColor(Color.rgb(31,33,38))", "setBackgroundColor(Color.rgb(20,43,58))")
s = s.replace("setBackgroundColor(Color.rgb(27,29,34))", "setBackgroundColor(Color.rgb(13,32,45))")
s = s.replace('label("Akkorde",12f,Color.GRAY)', 'label("Akkorde",12f,Color.LTGRAY)')

old_button = 'private fun button(text:String)=Button(requireContext()).apply { this.text=text; setTextColor(Color.WHITE); setAllCaps(false); minHeight=0; minimumHeight=0; setPadding(dp(8),0,dp(8),0) }'
new_button = r'''private fun button(text:String)=Button(requireContext()).apply {
        this.text=text
        setTextColor(Color.rgb(221,162,122))
        setAllCaps(false)
        textSize=14f
        typeface=android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
        gravity=android.view.Gravity.CENTER
        includeFontPadding=true
        minLines=1
        maxLines=2
        minHeight=dp(52)
        minimumHeight=dp(52)
        setPadding(dp(16),dp(10),dp(16),dp(10))
        background=android.graphics.drawable.GradientDrawable().apply {
            cornerRadius=dp(16).toFloat()
            setColor(Color.rgb(20,43,58))
            setStroke(dp(1),Color.rgb(41,67,84))
        }
    }'''
if old_button in s:
    s = s.replace(old_button, new_button, 1)
elif "private fun button(text:String)" not in s or "minHeight=dp(52)" not in s:
    raise SystemExit("FEHLER: Songbook-Button-Stil konnte nicht barrierearm angepasst werden.")

if "import androidx.appcompat.app.AlertDialog" in s and "AlertDialog.Builder(requireContext())" in s:
    raise SystemExit("FEHLER: Unge-stalteter Songbook-Dialog verblieben.")
songbook.write_text(s, encoding="utf-8")

print("SAITENWERK-KONTRAST-UI: PASS – Dark-Theme, Dialoge, Buttons und Eingabefelder vereinheitlicht.")
