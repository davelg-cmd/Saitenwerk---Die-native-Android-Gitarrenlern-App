#!/usr/bin/env python3
"""Make the BPM label a precise relative-drag control with a readable value bubble."""
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_DIR"])
p = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

pattern = re.compile(
    r'''        tempoLabel\.gravity = .*?'''
    r'''        addView\(meterTempoRow, LayoutParams\(-1, host\.dp\(\d+\)\).*?\n'''
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
        tempoLabel.setTextColor(android.graphics.Color.WHITE)
        tempoLabel.setPadding(host.dp(12), 0, host.dp(12), host.dp(8))
        tempoLabel.background = null
        // Sichtbare Sliderbahn mit Fortschrittslinie und beweglichem Reglerknopf.
        val bpmSliderTrack = object : View(host) {
            private val rail = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                color = android.graphics.Color.rgb(83, 94, 111)
                strokeWidth = host.dp(4).toFloat()
                strokeCap = android.graphics.Paint.Cap.ROUND
            }
            private val progress = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                color = android.graphics.Color.rgb(77, 166, 255)
                strokeWidth = host.dp(4).toFloat()
                strokeCap = android.graphics.Paint.Cap.ROUND
            }
            private val knob = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                color = android.graphics.Color.rgb(77, 166, 255)
                style = android.graphics.Paint.Style.FILL
            }
            private val knobOutline = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                color = android.graphics.Color.WHITE
                style = android.graphics.Paint.Style.STROKE
                strokeWidth = host.dp(2).toFloat()
            }
            override fun onDraw(canvas: android.graphics.Canvas) {
                super.onDraw(canvas)
                val left = host.dp(14).toFloat()
                val right = (width - host.dp(14)).toFloat()
                val y = (height - host.dp(9)).toFloat()
                val fraction = ((bpm - 50).toFloat() / 110f).coerceIn(0f, 1f)
                val x = left + (right - left) * fraction
                canvas.drawLine(left, y, right, y, rail)
                canvas.drawLine(left, y, x, y, progress)
                canvas.drawCircle(x, y, host.dp(7).toFloat(), knob)
                canvas.drawCircle(x, y, host.dp(7).toFloat(), knobOutline)
            }
        }
        tempoLabel.contentDescription = "BPM-Regler: " + bpm + ". Horizontal ziehen zum Ändern."
        // Relative Bewegung statt absoluter Fingerposition: feinere, kontrollierbare Schritte.
        var bpmDragStartX = 0f
        var bpmDragStartValue = bpm
        val bpmBubbleText = TextView(host).apply {
            text = "BPM " + bpm
            textSize = 16f
            setTextColor(android.graphics.Color.WHITE)
            setPadding(host.dp(12), host.dp(7), host.dp(12), host.dp(7))
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(android.graphics.Color.rgb(35, 42, 54))
                cornerRadius = host.dp(12).toFloat()
                setStroke(host.dp(1), android.graphics.Color.rgb(105, 175, 255))
            }
        }
        val bpmBubble = android.widget.PopupWindow(
            bpmBubbleText, android.view.ViewGroup.LayoutParams.WRAP_CONTENT,
            android.view.ViewGroup.LayoutParams.WRAP_CONTENT, false
        ).apply { isTouchable = false; isClippingEnabled = false }
        fun updateBpmFromDrag(event: android.view.MotionEvent) {
            val density = host.resources.displayMetrics.density
            val deltaDp = (event.rawX - bpmDragStartX) / density
            // 2 dp pro BPM verhindert große Sprünge und erlaubt trotzdem den ganzen Bereich.
            val next = (bpmDragStartValue + (deltaDp / 2f).toInt()).coerceIn(50, 160)
            if (next != bpm) {
                bpm = next
                tempoLabel.text = "BPM " + bpm
                tempoLabel.contentDescription = "BPM-Regler: " + bpm
                bpmBubbleText.text = "BPM " + bpm
                bpmSliderTrack.invalidate()
                prefs.edit().putInt("chord_training_bpm", bpm).apply()
            }
            val x = (event.rawX - host.dp(34)).toInt().coerceAtLeast(0)
            val y = (event.rawY - host.dp(62)).toInt().coerceAtLeast(0)
            if (bpmBubble.isShowing) bpmBubble.update(x, y, -1, -1)
        }
        tempoLabel.setOnTouchListener { view, event ->
            when (event.actionMasked) {
                android.view.MotionEvent.ACTION_DOWN -> {
                    bpmDragStartX = event.rawX
                    bpmDragStartValue = bpm
                    bpmBubbleText.text = "BPM " + bpm
                    val x = (event.rawX - host.dp(34)).toInt().coerceAtLeast(0)
                    val y = (event.rawY - host.dp(62)).toInt().coerceAtLeast(0)
                    bpmBubble.showAtLocation(view, android.view.Gravity.TOP or android.view.Gravity.START, x, y)
                    true
                }
                android.view.MotionEvent.ACTION_MOVE -> {
                    updateBpmFromDrag(event)
                    true
                }
                android.view.MotionEvent.ACTION_UP -> {
                    updateBpmFromDrag(event)
                    if (bpmBubble.isShowing) bpmBubble.dismiss()
                    view.performClick()
                    true
                }
                android.view.MotionEvent.ACTION_CANCEL -> {
                    if (bpmBubble.isShowing) bpmBubble.dismiss()
                    true
                }
                else -> false
            }
        }
        tempoLabel.setOnClickListener { }

        val tempoColumn = android.widget.FrameLayout(host).apply {
            setPadding(host.dp(8), 0, 0, 0)
            clipChildren = false
            clipToPadding = false
        }
        tempoColumn.addView(bpmSliderTrack, android.widget.FrameLayout.LayoutParams(-1, host.dp(56)))
        tempoColumn.addView(tempoLabel, android.widget.FrameLayout.LayoutParams(-1, host.dp(56)))
        val meterTempoRow = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            clipChildren = false
            clipToPadding = false
        }
        // Der BPM-Schriftzug bleibt der Regler; die Sprechblase hält den Wert über dem Finger sichtbar.
        meterTempoRow.addView(meterButton, LayoutParams(0, host.dp(52), 0.68f))
        meterTempoRow.addView(tempoColumn, LayoutParams(0, host.dp(56), 1.32f))
        addView(meterTempoRow, LayoutParams(-1, host.dp(60)).apply {
            bottomMargin = host.dp(4)
        })'''
s = s[:m.start()] + replacement + s[m.end():]
required = [
    'tempoLabel.setOnTouchListener',
    'bpmDragStartValue',
    'bpmBubble.showAtLocation',
    'deltaDp / 2f',
    'tempoLabel.text = "BPM " + bpm',
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("FEHLER: BPM-Regler nicht korrekt geschrieben: " + ", ".join(missing))
p.write_text(s, encoding="utf-8")
print("BPM-REGLER MIT FEINEM RELATIV-DRAG UND SICHTBARER WERTANZEIGE: PASS")
