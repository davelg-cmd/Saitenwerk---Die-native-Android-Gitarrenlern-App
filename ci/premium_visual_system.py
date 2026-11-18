#!/usr/bin/env python3
"""Apply Saitenwerk's unified premium visual system to the extracted Android project."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")
if "fun premiumButtonBackground(primary: Boolean = false)" in s:
    print("Premium-Designsystem bereits vorhanden.")
    raise SystemExit(0)

old_style = """    private fun applySaitenwerkButtonStyle(root: View) {
        if (root is Button) {
            val density = resources.displayMetrics.density
            fun dp(value: Int) = (value * density + 0.5f).toInt()
            root.isAllCaps = false
            root.textSize = 14f
            root.typeface = android.graphics.Typeface.create(
                "sans-serif-medium", android.graphics.Typeface.NORMAL
            )
            root.setTextColor(getColor(R.color.sw_copper))
            root.gravity = Gravity.CENTER
            root.includeFontPadding = true
            root.minLines = 1
            root.maxLines = 2
            root.setLineSpacing(dp(2).toFloat(), 1.05f)
            root.setPadding(dp(14), dp(10), dp(14), dp(10))
            root.minHeight = dp(52)
            root.minimumHeight = dp(52)
            root.minimumWidth = 0
            root.stateListAnimator = null
            root.elevation = dp(2).toFloat()
            root.background = android.graphics.drawable.GradientDrawable().apply {
                shape = android.graphics.drawable.GradientDrawable.RECTANGLE
                cornerRadius = dp(16).toFloat()
                setColor(getColor(R.color.sw_surface2))
                setStroke(dp(1), getColor(R.color.sw_copper))
            }
            val params = root.layoutParams
            if (params != null && params.height > 0 && params.height < dp(52)) {
                params.height = dp(52)
                root.layoutParams = params
            }
        }
        if (root is ViewGroup) {
            for (index in 0 until root.childCount) {
                applySaitenwerkButtonStyle(root.getChildAt(index))
            }
        }
    }
"""
new_style = """    fun premiumButtonBackground(primary: Boolean = false): android.graphics.drawable.Drawable {
        val shape = android.graphics.drawable.GradientDrawable().apply {
            cornerRadius = dp(16).toFloat()
            setColor(getColor(if (primary) R.color.sw_copper else R.color.sw_surface2))
            if (!primary) setStroke(dp(1), getColor(R.color.sw_outline))
        }
        return android.graphics.drawable.RippleDrawable(
            android.content.res.ColorStateList.valueOf(getColor(R.color.sw_ripple)), shape, null
        )
    }

    fun premiumDropdownItemBackground(): android.graphics.drawable.Drawable {
        val shape = android.graphics.drawable.GradientDrawable().apply {
            cornerRadius = dp(12).toFloat()
            setColor(getColor(R.color.sw_surface2))
        }
        return android.graphics.drawable.RippleDrawable(
            android.content.res.ColorStateList.valueOf(getColor(R.color.sw_ripple)), shape, null
        )
    }

    private fun applySaitenwerkButtonStyle(root: View) {
        val density = resources.displayMetrics.density
        fun dp(value: Int) = (value * density + 0.5f).toInt()
        if (root is Button) {
            val primary = root.tag == "saitenwerk-primary"
            root.isAllCaps = false
            root.textSize = 14f
            root.typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            root.setTextColor(getColor(if (primary) R.color.sw_on_accent else R.color.sw_copper))
            root.gravity = Gravity.CENTER
            root.textAlignment = View.TEXT_ALIGNMENT_CENTER
            root.includeFontPadding = true
            root.minLines = 1
            root.maxLines = 2
            root.setLineSpacing(dp(2).toFloat(), 1.05f)
            root.setPadding(dp(16), dp(10), dp(16), dp(10))
            root.minHeight = dp(52)
            root.minimumHeight = dp(52)
            root.minimumWidth = 0
            root.stateListAnimator = null
            root.elevation = dp(1).toFloat()
            root.background = premiumButtonBackground(primary)
            val params = root.layoutParams
            if (params != null && params.height > 0 && params.height < dp(52)) {
                params.height = dp(52)
                root.layoutParams = params
            }
        }
        if (root is MaterialCardView) {
            root.radius = dp(20).toFloat()
            root.strokeColor = getColor(R.color.sw_outline)
            root.strokeWidth = dp(1)
            root.cardElevation = dp(2).toFloat()
            root.setCardBackgroundColor(getColor(R.color.sw_surface))
        }
        if (root is Spinner) {
            root.setPopupBackgroundDrawable(android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(16).toFloat()
                setColor(getColor(R.color.sw_surface))
                setStroke(dp(1), getColor(R.color.sw_outline))
            })
            root.dropDownVerticalOffset = dp(6)
            root.elevation = dp(1).toFloat()
        }
        if (root is ViewGroup) {
            for (index in 0 until root.childCount) applySaitenwerkButtonStyle(root.getChildAt(index))
        }
    }
"""
if old_style not in s:
    raise SystemExit("Button-Style-Funktion nicht gefunden; Abbruch ohne Teiländerung.")
s = s.replace(old_style, new_style, 1)

start = s.index("    fun button(value: String) = Button(this).apply {")
end = s.index("\n    fun spinnerAdapter", start)
s = s[:start] + """    fun button(value: String) = Button(this).apply {
        text = value
        isAllCaps = false
        setTextColor(getColor(R.color.sw_copper))
        textSize = 14f
        typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
        gravity = Gravity.CENTER
        textAlignment = View.TEXT_ALIGNMENT_CENTER
        includeFontPadding = true
        minLines = 1
        maxLines = 2
        setLineSpacing(dp(2).toFloat(), 1.05f)
        setPadding(dp(16), dp(10), dp(16), dp(10))
        minHeight = dp(52)
        minimumHeight = dp(52)
        minimumWidth = 0
        stateListAnimator = null
        elevation = dp(1).toFloat()
        background = premiumButtonBackground()
    }
""" + s[end:]

old_adapter = """        override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
            val v = super.getView(position, convertView, parent) as TextView
            v.setTextColor(getColor(R.color.sw_text))
            v.textSize = 14f
            v.setPadding(dp(14), 0, dp(14), 0)
            v.gravity = Gravity.CENTER_VERTICAL
            v.background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(24).toFloat()
                setColor(getColor(R.color.sw_surface2))
                setStroke(dp(1), getColor(R.color.sw_copper))
            }
            return v
        }
        override fun getDropDownView(position: Int, convertView: View?, parent: ViewGroup): View {
            val v = super.getDropDownView(position, convertView, parent) as TextView
            v.setTextColor(getColor(R.color.sw_text))
            v.textSize = 14f
            v.setPadding(dp(14), dp(10), dp(14), dp(10))
            v.setBackgroundColor(getColor(R.color.sw_surface))
            return v
        }
"""
new_adapter = """        override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
            val v = super.getView(position, convertView, parent) as TextView
            v.setTextColor(getColor(R.color.sw_text))
            v.textSize = 14f
            v.typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            v.gravity = Gravity.CENTER_VERTICAL
            v.includeFontPadding = true
            v.maxLines = 2
            v.setPadding(dp(16), dp(8), dp(42), dp(8))
            v.minHeight = dp(52)
            v.background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = dp(14).toFloat()
                setColor(getColor(R.color.sw_surface2))
                setStroke(dp(1), getColor(R.color.sw_outline))
            }
            return v
        }
        override fun getDropDownView(position: Int, convertView: View?, parent: ViewGroup): View {
            val v = super.getDropDownView(position, convertView, parent) as TextView
            v.setTextColor(getColor(R.color.sw_text))
            v.textSize = 14f
            v.typeface = android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.NORMAL)
            v.gravity = Gravity.CENTER_VERTICAL
            v.includeFontPadding = true
            v.maxLines = 2
            v.setPadding(dp(16), dp(12), dp(16), dp(12))
            v.minHeight = dp(52)
            v.background = premiumDropdownItemBackground()
            return v
        }
"""
if old_adapter not in s:
    raise SystemExit("Spinner-Adapter nicht gefunden; Abbruch ohne Teiländerung.")
s = s.replace(old_adapter, new_adapter, 1)

s = s.replace("""                    if (dropdown) {
                        setBackgroundColor(a.getColor(R.color.sw_surface))
                        minHeight = a.dp(48)
                    } else {
                        setBackground(android.graphics.drawable.GradientDrawable().apply {
                            setColor(a.getColor(R.color.sw_surface2))
                            cornerRadius = a.dp(12).toFloat()
                            setStroke(a.dp(1), a.getColor(R.color.sw_copper))
                        })
                        minHeight = a.dp(52)
                    }
""", """                    includeFontPadding = true
                    maxLines = 2
                    if (dropdown) {
                        background = a.premiumDropdownItemBackground()
                        minHeight = a.dp(52)
                    } else {
                        setBackground(android.graphics.drawable.GradientDrawable().apply {
                            setColor(a.getColor(R.color.sw_surface2))
                            cornerRadius = a.dp(14).toFloat()
                            setStroke(a.dp(1), a.getColor(R.color.sw_outline))
                        })
                        minHeight = a.dp(52)
                    }
""", 1)

s = s.replace("""                        textSize = 16f
                        typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
                        setTextColor(a.getColor(R.color.sw_copper))
                        gravity = Gravity.CENTER_VERTICAL
                        setPadding(a.dp(16), 0, a.dp(16), 0)
                        minHeight = a.dp(48)
""", """                        textSize = 14f
                        typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
                        setTextColor(a.getColor(R.color.sw_text))
                        gravity = Gravity.CENTER_VERTICAL
                        includeFontPadding = true
                        setPadding(a.dp(16), a.dp(8), a.dp(16), a.dp(8))
                        minHeight = a.dp(52)
""", 1)
s = s.replace("""                        background = android.graphics.drawable.GradientDrawable().apply {
                            cornerRadius = a.dp(10).toFloat()
                            setColor(a.getColor(R.color.sw_surface))
                        }
""", """                        background = a.premiumDropdownItemBackground()
""", 1)
s = s.replace("""                    dropdown.addView(item, LinearLayout.LayoutParams(-1, a.dp(48)).apply {
                        if (index > 0) topMargin = a.dp(2)
                    })
""", """                    dropdown.addView(item, LinearLayout.LayoutParams(-1, a.dp(52)).apply {
                        if (index > 0) topMargin = a.dp(3)
                    })
""", 1)
s = s.replace("minOf(chords.size * a.dp(50) + a.dp(10), a.dp(320))", "minOf(chords.size * a.dp(55) + a.dp(10), a.dp(360))", 1)

s = s.replace("""        box.addView(Button(a).apply {
            text="Stimmgerät öffnen   →";""", """        box.addView(Button(a).apply {
            tag = "saitenwerk-primary"
            text="Stimmgerät öffnen   →";""", 1)

main.write_text(s, encoding="utf-8")

(root / "app/src/main/res/values/colors.xml").write_text("""<resources>
    <color name="sw_navy">#07131E</color>
    <color name="sw_surface">#0D202D</color>
    <color name="sw_surface2">#142B3A</color>
    <color name="sw_surface3">#1B3545</color>
    <color name="sw_copper">#DDA27A</color>
    <color name="sw_copper_bright">#E9B88F</color>
    <color name="sw_blue">#79CEFF</color>
    <color name="sw_text">#F5E2D2</color>
    <color name="sw_muted">#BDA18E</color>
    <color name="sw_nav_bar">#040C13</color>
    <color name="sw_nav_icon">#DDA27A</color>
    <color name="sw_nav_text">#D7B397</color>
    <color name="sw_outline">#294354</color>
    <color name="sw_on_accent">#24180F</color>
    <color name="sw_ripple">#55DDA27A</color>
    <color name="sw_success">#86C9A0</color>
    <color name="sw_danger">#E58E82</color>
</resources>
""", encoding="utf-8")

(root / "app/src/main/res/values/styles.xml").write_text("""<resources>
    <style name="SaitenwerkBottomNavLabel" parent="TextAppearance.Material3.LabelMedium">
        <item name="android:textSize">12sp</item>
        <item name="android:textStyle">normal</item>
        <item name="android:letterSpacing">0.01</item>
        <item name="android:fontFamily">sans-serif-medium</item>
    </style>
    <style name="SaitenwerkBottomNavLabelActive" parent="TextAppearance.Material3.LabelMedium">
        <item name="android:textSize">12sp</item>
        <item name="android:textStyle">bold</item>
        <item name="android:letterSpacing">0.01</item>
        <item name="android:fontFamily">sans-serif-medium</item>
    </style>
    <style name="Widget.Saitenwerk.Dialog.ActionButton" parent="Widget.Material3.Button.TextButton">
        <item name="android:textColor">@color/sw_copper</item>
        <item name="android:textSize">14sp</item>
        <item name="android:fontFamily">sans-serif-medium</item>
        <item name="android:minHeight">48dp</item>
        <item name="android:insetTop">0dp</item>
        <item name="android:insetBottom">0dp</item>
    </style>
    <style name="ThemeOverlay.Saitenwerk.Dialog" parent="ThemeOverlay.Material3.MaterialAlertDialog">
        <item name="colorSurface">@color/sw_surface</item>
        <item name="colorOnSurface">@color/sw_text</item>
        <item name="colorPrimary">@color/sw_copper</item>
        <item name="colorOnSurfaceVariant">@color/sw_muted</item>
        <item name="android:fontFamily">sans-serif</item>
        <item name="fontFamily">sans-serif</item>
        <item name="android:textColorPrimary">@color/sw_text</item>
        <item name="android:textColorSecondary">@color/sw_muted</item>
        <item name="android:colorAccent">@color/sw_copper</item>
        <item name="android:colorBackground">@color/sw_surface</item>
        <item name="android:windowBackground">@drawable/sw_dialog_background</item>
        <item name="android:windowMinWidthMajor">88%</item>
        <item name="android:windowMinWidthMinor">88%</item>
        <item name="android:windowIsFloating">true</item>
        <item name="buttonBarPositiveButtonStyle">@style/Widget.Saitenwerk.Dialog.ActionButton</item>
        <item name="buttonBarNegativeButtonStyle">@style/Widget.Saitenwerk.Dialog.ActionButton</item>
        <item name="buttonBarNeutralButtonStyle">@style/Widget.Saitenwerk.Dialog.ActionButton</item>
    </style>
    <style name="Widget.Saitenwerk.PopupMenu" parent="Widget.Material3.PopupMenu">
        <item name="android:popupBackground">@drawable/sw_popup_background</item>
        <item name="android:textColor">@color/sw_text</item>
        <item name="android:fontFamily">sans-serif-medium</item>
    </style>
</resources>
""", encoding="utf-8")

(root / "app/src/main/res/values/themes.xml").write_text("""<resources>
    <style name="Theme.Saitenwerk" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="android:fontFamily">sans-serif</item>
        <item name="fontFamily">sans-serif</item>
        <item name="android:textColorPrimary">@color/sw_text</item>
        <item name="android:textColorSecondary">@color/sw_muted</item>
        <item name="android:textColorHint">@color/sw_muted</item>
        <item name="colorOnSurface">@color/sw_text</item>
        <item name="colorOnSurfaceVariant">@color/sw_muted</item>
        <item name="colorPrimary">@color/sw_copper</item>
        <item name="colorOnPrimary">@color/sw_on_accent</item>
        <item name="colorSecondary">@color/sw_blue</item>
        <item name="colorOutline">@color/sw_outline</item>
        <item name="popupMenuStyle">@style/Widget.Saitenwerk.PopupMenu</item>
        <item name="android:popupBackground">@drawable/sw_popup_background</item>
        <item name="android:windowBackground">@color/sw_navy</item>
        <item name="android:windowLightStatusBar">false</item>
        <item name="android:statusBarColor">@color/sw_navy</item>
        <item name="android:navigationBarColor">@color/sw_nav_bar</item>
    </style>
</resources>
""", encoding="utf-8")

(root / "app/src/main/res/drawable/sw_popup_background.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="@color/sw_surface" />
    <corners android:radius="18dp" />
    <stroke android:width="1dp" android:color="@color/sw_outline" />
</shape>
""", encoding="utf-8")
(root / "app/src/main/res/drawable/sw_dialog_background.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="@color/sw_surface" />
    <corners android:radius="24dp" />
    <stroke android:width="1dp" android:color="@color/sw_outline" />
</shape>
""", encoding="utf-8")

required = ["premiumButtonBackground(primary)", "premiumDropdownItemBackground()", "saitenwerk-primary"]
if any(token not in main.read_text(encoding="utf-8") for token in required):
    raise SystemExit("Premium-Designprüfung fehlgeschlagen.")
print("Premium-Designsystem erfolgreich angewendet.")
