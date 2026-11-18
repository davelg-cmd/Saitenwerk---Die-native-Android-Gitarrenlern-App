#!/usr/bin/env python3
from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
source = main.read_text(encoding="utf-8")

old = '''            val button = a.button("$letter  ▾").apply {
                textSize = 14f
                isEnabled = chords.isNotEmpty()
                alpha = if (chords.isNotEmpty()) 1f else .4f
            }
            button.setOnClickListener { anchor ->
                val popup = android.widget.PopupMenu(a, anchor)
                chords.forEachIndexed { index, chord ->
                    popup.menu.add(android.view.Menu.NONE, index, index, chord.name)
                }
                popup.setOnMenuItemClickListener { item ->
                    chords.getOrNull(item.itemId)?.let { showChordSelection?.invoke(it) }
                    true
                }
                popup.show()
            }'''

new = '''            val button = a.button("$letter  ▾").apply {
                textSize = 14f
                isEnabled = chords.isNotEmpty()
                alpha = if (chords.isNotEmpty()) 1f else .4f
                setTextColor(a.getColor(R.color.sw_copper))
                typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
                background = android.graphics.drawable.GradientDrawable().apply {
                    cornerRadius = a.dp(13).toFloat()
                    setColor(a.getColor(R.color.sw_surface2))
                    setStroke(a.dp(1), a.getColor(R.color.sw_copper))
                }
            }
            button.setOnClickListener { anchor ->
                val dropdown = LinearLayout(a).apply {
                    orientation = LinearLayout.VERTICAL
                    setPadding(a.dp(5), a.dp(5), a.dp(5), a.dp(5))
                    background = android.graphics.drawable.GradientDrawable().apply {
                        cornerRadius = a.dp(16).toFloat()
                        setColor(a.getColor(R.color.sw_surface))
                        setStroke(a.dp(1), a.getColor(R.color.sw_copper))
                    }
                }
                val scrollMenu = ScrollView(a).apply {
                    isFillViewport = false
                    isVerticalScrollBarEnabled = chords.size > 6
                    addView(dropdown)
                }
                lateinit var dropdownPopup: android.widget.PopupWindow
                chords.forEachIndexed { index, chord ->
                    val item = TextView(a).apply {
                        text = chord.name
                        textSize = 16f
                        typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
                        setTextColor(a.getColor(R.color.sw_copper))
                        gravity = Gravity.CENTER_VERTICAL
                        setPadding(a.dp(16), 0, a.dp(16), 0)
                        minHeight = a.dp(48)
                        isClickable = true
                        isFocusable = true
                        background = android.graphics.drawable.GradientDrawable().apply {
                            cornerRadius = a.dp(10).toFloat()
                            setColor(a.getColor(R.color.sw_surface))
                        }
                    }
                    item.setOnClickListener {
                        dropdownPopup.dismiss()
                        showChordSelection?.invoke(chord)
                    }
                    dropdown.addView(item, LinearLayout.LayoutParams(-1, a.dp(48)).apply {
                        if (index > 0) topMargin = a.dp(2)
                    })
                }
                dropdownPopup = android.widget.PopupWindow(
                    scrollMenu,
                    maxOf(anchor.width, a.dp(132)),
                    minOf(chords.size * a.dp(50) + a.dp(10), a.dp(320)),
                    true
                ).apply {
                    setBackgroundDrawable(android.graphics.drawable.ColorDrawable(android.graphics.Color.TRANSPARENT))
                    isOutsideTouchable = true
                    elevation = a.dp(12).toFloat()
                    animationStyle = android.R.style.Animation_Dialog
                }
                dropdownPopup.showAsDropDown(anchor, 0, a.dp(4))
            }'''

if old in source:
    source = source.replace(old, new)
elif 'android.widget.PopupWindow(' not in source[source.find("class ChordsFragment") : source.find("class GuitarFretboardView")]:
    raise SystemExit("FEHLER: Akkord-Dropdown nicht gefunden; Quellstand unverändert.")
main.write_text(source, encoding="utf-8")

values = root / "app/src/main/res/values"
colors = values / "colors.xml"
cs = colors.read_text(encoding="utf-8")
for name, color in {
    "sw_text": "#F0C29F",
    "sw_muted": "#C18A68",
    "sw_nav_icon": "#D99A70",
    "sw_nav_text": "#E8B18A",
}.items():
    cs, count = re.subn(
        r'(<color name="' + name + r'">)[^<]+(</color>)',
        lambda m: m.group(1) + color + m.group(2), cs
    )
    if count != 1:
        raise SystemExit("FEHLER: Typografie-Farbe fehlt oder doppelt: " + name)
colors.write_text(cs, encoding="utf-8")

themes = values / "themes.xml"
th = themes.read_text(encoding="utf-8")
old_theme = '<item name="android:fontFamily">sans</item><item name="android:windowLightStatusBar">false</item>'
new_theme = '''<item name="android:fontFamily">sans-serif</item>
    <item name="fontFamily">sans-serif</item>
    <item name="android:textColorPrimary">@color/sw_text</item>
    <item name="android:textColorSecondary">@color/sw_muted</item>
    <item name="android:textColorHint">@color/sw_muted</item>
    <item name="colorOnSurface">@color/sw_text</item>
    <item name="colorOnSurfaceVariant">@color/sw_muted</item>
    <item name="android:windowLightStatusBar">false</item>'''
if old_theme in th:
    th = th.replace(old_theme, new_theme)
elif '<item name="android:textColorPrimary">@color/sw_text</item>' not in th:
    raise SystemExit("FEHLER: App-Theme konnte nicht auf Kupfer-Typografie umgestellt werden.")
themes.write_text(th, encoding="utf-8")

styles = values / "styles.xml"
st = styles.read_text(encoding="utf-8")
st = st.replace(
    '<item name="colorPrimary">@color/sw_copper</item>',
    '<item name="colorPrimary">@color/sw_copper</item>\n        <item name="android:fontFamily">sans-serif</item>\n        <item name="fontFamily">sans-serif</item>\n        <item name="android:textColorPrimary">@color/sw_text</item>\n        <item name="android:textColorSecondary">@color/sw_muted</item>'
)
styles.write_text(st, encoding="utf-8")

spinner = root / "app/src/main/res/layout/sw_spinner_item.xml"
if spinner.exists():
    text = spinner.read_text(encoding="utf-8")
    text = text.replace('@color/sw_text', '@color/sw_copper').replace('android:fontFamily="sans"', 'android:fontFamily="sans-serif-medium"')
    spinner.write_text(text, encoding="utf-8")

check = main.read_text(encoding="utf-8")
chords = check[check.find("class ChordsFragment") : check.find("class GuitarFretboardView")]
if "android.widget.PopupWindow(" not in chords or "PopupMenu(a, anchor)" in chords:
    raise SystemExit("FEHLER: Akkord-Dropdown-Validierung fehlgeschlagen.")
if "#F0C29F" not in cs or "#C18A68" not in cs or "android:textColorPrimary" not in th:
    raise SystemExit("FEHLER: Kupfer-Typografie-Validierung fehlgeschlagen.")
print("AKKORD-DROPDOWNS UND KUPFER-TYPOGRAFIE: PASS")
