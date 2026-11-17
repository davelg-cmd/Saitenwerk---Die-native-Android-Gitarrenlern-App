#!/usr/bin/env python3
"""Put compact BPM label beside slider and narrow the meter selector."""
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

pattern = re.compile(
    r'''        tempoLabel\.gravity = Gravity\.CENTER_VERTICAL or Gravity\.START\n'''
    r'''        tempoLabel\.text = "Tempo · " \+ bpm \+ " BPM"\n'''
    r'''        tempo\.max = 110\n'''
    r'''        tempo\.progress = bpm - 50\n'''
    r'''        tempo\.setOnSeekBarChangeListener\(object : SeekBar\.OnSeekBarChangeListener \{.*?'''
    r'''        val tempoColumn = LinearLayout\(host\)\.apply \{.*?'''
    r'''        addView\(meterTempoRow, LayoutParams\(-1, host\.dp\(72\)\)\.apply \{\n'''
    r'''            bottomMargin = host\.dp\(4\)\n'''
    r'''        \}\)''',
    re.S
)
m = pattern.search(s)
if not m:
    if 'BPM_LABEL_NEXT_TO_SLIDER' in s:
        print("BPM-SLIDER-LAYOUT: bereits aktuell")
        raise SystemExit(0)
    raise SystemExit("FEHLER: Tempo-/Taktauswahl-Layout nicht gefunden.")

replacement = '''        tempoLabel.gravity = Gravity.CENTER_VERTICAL or Gravity.START
        tempoLabel.text = "BPM " + bpm
        tempoLabel.isSingleLine = true
        tempoLabel.includeFontPadding = false
        tempo.max = 110
        tempo.progress = bpm - 50
        tempo.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(v: SeekBar?, p: Int, fromUser: Boolean) {
                bpm = (50 + p).coerceIn(50, 160)
                tempoLabel.text = "BPM " + bpm
                prefs.edit().putInt("chord_training_bpm", bpm).apply()
            }
            override fun onStartTrackingTouch(v: SeekBar?) {}
            override fun onStopTrackingTouch(v: SeekBar?) {}
        })

        val tempoColumn = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(host.dp(8), 0, 0, 0)
        }
        tempoColumn.addView(tempoLabel, LayoutParams(host.dp(54), host.dp(40)))
        tempoColumn.addView(tempo, LayoutParams(0, host.dp(48), 1f))
        val meterTempoRow = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            clipChildren = false
            clipToPadding = false
        }
        // Schmalere Taktauswahl, mehr nutzbare Breite für BPM und Regler.
        meterTempoRow.addView(meterButton, LayoutParams(0, host.dp(52), 0.68f))
        meterTempoRow.addView(tempoColumn, LayoutParams(0, host.dp(56), 1.32f))
        addView(meterTempoRow, LayoutParams(-1, host.dp(60)).apply {
            bottomMargin = host.dp(4)
        })'''
s = s[:m.start()] + replacement + s[m.end():]
p.write_text(s, encoding="utf-8")
if 'tempoLabel.text = "BPM " + bpm' not in s or 'host.dp(0.68f)' in s:
    raise SystemExit("FEHLER: BPM-Layout nicht korrekt geschrieben.")
print("BPM-SLIDER-LAYOUT: PASS")
