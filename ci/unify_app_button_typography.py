#!/usr/bin/env python3
"""Apply one accessible, consistent button system to every app fragment."""
from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

# Register a recursive fragment lifecycle hook so dynamically created screens
# and nested fragments receive the same treatment, not just buttons made by
# the shared helper.
marker = "        setupBackNavigation()"
hook = """        supportFragmentManager.registerFragmentLifecycleCallbacks(
            object : androidx.fragment.app.FragmentManager.FragmentLifecycleCallbacks() {
                override fun onFragmentViewCreated(
                    fm: androidx.fragment.app.FragmentManager,
                    fragment: Fragment,
                    view: View,
                    savedInstanceState: Bundle?
                ) {
                    super.onFragmentViewCreated(fm, fragment, view, savedInstanceState)
                    applySaitenwerkButtonStyle(view)
                }
            },
            true
        )
"""
if "registerFragmentLifecycleCallbacks(" not in s:
    if s.count(marker) != 1:
        raise SystemExit("FEHLER: Lifecycle-Einstiegspunkt nicht eindeutig.")
    s = s.replace(marker, hook + marker, 1)

# Central reusable style. Include font padding and generous vertical padding:
# Android's default font metrics otherwise clip descenders on compact buttons.
style_marker = "    private fun show(fragment: Fragment, addToBackStack: Boolean = true) {"
style_fn = """    private fun applySaitenwerkButtonStyle(root: View) {
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
if "private fun applySaitenwerkButtonStyle(root: View)" not in s:
    if s.count(style_marker) != 1:
        raise SystemExit("FEHLER: Button-Stil-Einfügepunkt nicht eindeutig.")
    s = s.replace(style_marker, style_fn + style_marker, 1)

# Improve the common constructor too, so buttons are correct even before the
# fragment lifecycle callback runs.
old = """        textSize = 15f
        minHeight = dp(48)
        minimumHeight = dp(48)
"""
new = """        textSize = 14f
        typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
        gravity = Gravity.CENTER
        includeFontPadding = true
        minLines = 1
        maxLines = 2
        setLineSpacing(dp(2).toFloat(), 1.05f)
        setPadding(dp(14), dp(10), dp(14), dp(10))
        minHeight = dp(52)
        minimumHeight = dp(52)
"""
if old in s:
    s = s.replace(old, new, 1)
elif 'includeFontPadding = true' not in s[s.find("fun button(value: String)"):s.find("fun spinnerAdapter")]:
    raise SystemExit("FEHLER: Gemeinsamer Button-Konstruktor nicht gefunden.")

# Verify lifecycle coverage and all anti-clipping safeguards.
checks = [
    "registerFragmentLifecycleCallbacks(",
    "applySaitenwerkButtonStyle(view)",
    "root.textSize = 14f",
    "root.gravity = Gravity.CENTER",
    "root.includeFontPadding = true",
    "root.setPadding(dp(14), dp(10), dp(14), dp(10))",
    "root.minHeight = dp(52)",
    "root.setLineSpacing(dp(2).toFloat(), 1.05f)",
    "setColor(getColor(R.color.sw_surface2))",
    "setStroke(dp(1), getColor(R.color.sw_copper))",
]
missing = [token for token in checks if token not in s]
if missing:
    raise SystemExit("FEHLER: Button-Design unvollständig: " + ", ".join(missing))
if s.count("private fun applySaitenwerkButtonStyle(root: View)") != 1:
    raise SystemExit("FEHLER: Button-Stilfunktion doppelt vorhanden.")
main.write_text(s, encoding="utf-8")
print("APPWEITE BUTTON-OPTIMIERUNG: PASS")
print("Alle Fragment-Buttons: 14sp, Kupfer, mittig, 52dp Mindesthöhe, Font-Padding und Unterlängen-Schutz.")
