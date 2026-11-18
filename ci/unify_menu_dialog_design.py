#!/usr/bin/env python3
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

# One consistent dark, rounded Saitenwerk surface for all native dialogs.
s = s.replace(
    "androidx.appcompat.app.AlertDialog.Builder(a)",
    "androidx.appcompat.app.AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)"
)
s = s.replace(
    "androidx.appcompat.app.AlertDialog.Builder(host)",
    "androidx.appcompat.app.AlertDialog.Builder(host, R.style.ThemeOverlay_Saitenwerk_Dialog)"
)
s = s.replace("android.R.layout.simple_spinner_item, values", "R.layout.sw_spinner_item, values")
s = s.replace("android.R.layout.simple_spinner_item, labels", "R.layout.sw_spinner_item, labels")
s = s.replace("android.R.layout.simple_spinner_dropdown_item", "R.layout.sw_spinner_item")
main.write_text(s, encoding="utf-8")

values = root / "app/src/main/res/values"
styles = values / "styles.xml"
st = styles.read_text(encoding="utf-8")
if "ThemeOverlay.Saitenwerk.Dialog" not in st:
    st = st.replace("</resources>", """    <style name="ThemeOverlay.Saitenwerk.Dialog" parent="ThemeOverlay.Material3.MaterialAlertDialog">
        <item name="colorSurface">@color/sw_surface</item>
        <item name="colorOnSurface">@color/sw_text</item>
        <item name="colorPrimary">@color/sw_copper</item>
        <item name="android:colorBackground">@color/sw_surface</item>
        <item name="android:windowBackground">@drawable/sw_dialog_background</item>
        <item name="android:windowMinWidthMajor">88%</item>
        <item name="android:windowMinWidthMinor">88%</item>
        <item name="android:windowIsFloating">true</item>
    </style>
    <style name="Widget.Saitenwerk.PopupMenu" parent="Widget.Material3.PopupMenu">
        <item name="android:popupBackground">@drawable/sw_popup_background</item>
    </style>
</resources>""")
styles.write_text(st, encoding="utf-8")

themes = values / "themes.xml"
th = themes.read_text(encoding="utf-8")
if 'name="popupMenuStyle"' not in th:
    th = th.replace(
        '<item name="colorSecondary">@color/sw_blue</item>',
        '<item name="colorSecondary">@color/sw_blue</item>\\n    <item name="popupMenuStyle">@style/Widget.Saitenwerk.PopupMenu</item>\\n    <item name="android:popupBackground">@drawable/sw_popup_background</item>'
    )
themes.write_text(th, encoding="utf-8")

layout = root / "app/src/main/res/layout"
layout.mkdir(parents=True, exist_ok=True)
(layout / "sw_spinner_item.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<TextView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="48dp"
    android:gravity="center_vertical"
    android:paddingStart="14dp"
    android:paddingEnd="14dp"
    android:textColor="@color/sw_text"
    android:textSize="14sp"
    android:fontFamily="sans"
    android:background="@drawable/sw_spinner_item_background" />
""", encoding="utf-8")

drawable = root / "app/src/main/res/drawable"
drawable.mkdir(parents=True, exist_ok=True)
(drawable / "sw_dialog_background.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="@color/sw_surface" />
    <corners android:radius="24dp" />
    <stroke android:width="1dp" android:color="@color/sw_outline" />
</shape>
""", encoding="utf-8")
(drawable / "sw_popup_background.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="@color/sw_surface" />
    <corners android:radius="16dp" />
    <stroke android:width="1dp" android:color="@color/sw_outline" />
</shape>
""", encoding="utf-8")
(drawable / "sw_spinner_item_background.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true">
        <shape><solid android:color="@color/sw_surface2" /><corners android:radius="10dp" /></shape>
    </item>
    <item>
        <shape><solid android:color="@color/sw_surface" /><corners android:radius="10dp" /></shape>
    </item>
</selector>
""", encoding="utf-8")

check = main.read_text(encoding="utf-8")
for token in [
    "AlertDialog.Builder(a, R.style.ThemeOverlay_Saitenwerk_Dialog)",
    "AlertDialog.Builder(host, R.style.ThemeOverlay_Saitenwerk_Dialog)",
    "R.layout.sw_spinner_item",
    "PopupMenu(a, anchor)",
]:
    if token not in check:
        raise SystemExit("UI-MENÜ-VALIDIERUNG FEHLGESCHLAGEN: " + token)
if "androidx.appcompat.app.AlertDialog.Builder(a)" in check or "androidx.appcompat.app.AlertDialog.Builder(host)" in check:
    raise SystemExit("Nicht gestalteter AlertDialog-Aufruf verblieben.")
if "Widget.Material3.ListPopupWindow" in th or "dropDownListViewStyle" in th:
    raise SystemExit("Nicht unterstützter Popup-Style verblieben.")
print("SAITENWERK MENÜ-, DROPDOWN- UND DIALOG-DESIGN: PASS")
