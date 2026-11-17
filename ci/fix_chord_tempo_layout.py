#!/usr/bin/env python3
"""Put compact BPM label beside slider and narrow the meter selector."""
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

pattern = re.compile(
    r'''        tempoLabel\.gravity = .*?'''
    r'''        addView\(meterTempoRow, LayoutParams\(-1, host\.dp\(58\)\)\.apply \{\n'''
    r'''            bottomMargin = host\.dp\(4\)\n'''
    r'''        \}\)''',
    re.S
)
m = pattern.search(s)
if not m:
    raise SystemExit("FEHLER: Tempo-/Taktauswahl-Block nicht gefunden.")

replacement = '''        tempoLabel.gravity = Gravity.CENTER
        tempoLabel.text = "BPM " + bpm
        tempoLabel.isSingleLine = true
        tempoLabel.includeFontPadding = false
        tempoLabel.textSize = 18f
        tempoLabel.setTextColor(Color.WHITE)
        tempoLabel.setPadding(host.dp(12), 0, host.dp(12), 0)
        tempoLabel.contentDescription = "BPM-Regler: " + bpm + ". Horizontal ziehen zum Ändern."
        tempoLabel.setOnTouchListener { view, event ->
            when (event.action) {
                android.view.MotionEvent.ACTION_DOWN,
                android.view.MotionEvent.ACTION_MOVE -> {
                    val width = (view.width - view.paddingLeft - view.paddingRight).coerceAtLeast(1)
                    val fraction = ((event.x - view.paddingLeft) / width).coerceIn(0f, 1f)
                    bpm = (50 + (fraction * 110f).toInt()).coerceIn(50, 160)
                    tempoLabel.text = "BPM " + bpm
                    tempoLabel.contentDescription = "BPM-Regler: " + bpm
                    prefs.edit().putInt("chord_training_bpm", bpm).apply()
                    true
                }
                android.view.MotionEvent.ACTION_UP -> { view.performClick(); true }
                android.view.MotionEvent.ACTION_CANCEL -> true
                else -> false
            }
        }
        tempoLabel.setOnClickListener { }

        val tempoColumn = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(host.dp(8), 0, 0, 0)
        }
        tempoColumn.addView(tempoLabel, LayoutParams(-1, host.dp(48)))
        val meterTempoRow = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            clipChildren = false
            clipToPadding = false
        }
        // Der BPM-Schriftzug ist selbst der Regler; kein separater SeekBar.
        meterTempoRow.addView(meterButton, LayoutParams(0, host.dp(52), 0.68f))
        meterTempoRow.addView(tempoColumn, LayoutParams(0, host.dp(56), 1.32f))
        addView(meterTempoRow, LayoutParams(-1, host.dp(60)).apply {
            bottomMargin = host.dp(4)
        })'''
s = s[:m.start()] + replacement + s[m.end():]
p.write_text(s, encoding="utf-8")
if 'tempoLabel.text = "BPM " + bpm' not in s or 'tempoLabel.setOnTouchListener' not in s:
    raise SystemExit("FEHLER: BPM-Layout nicht korrekt geschrieben.")
print("BPM-SLIDER-LAYOUT: PASS")
