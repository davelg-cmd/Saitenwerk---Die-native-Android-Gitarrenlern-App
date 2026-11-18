from pathlib import Path
import os
main = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")
start = s.index("class TunerFragment : Fragment() {")
end = s.index("\nclass TunerGaugeView", start)
t = s[start:end]
selector_add = '        root.addView(selectorCard, LinearLayout.LayoutParams(-1, -2).apply { setMargins(a.dp(16), 0, a.dp(16), a.dp(10)) })'
display_add = '        root.addView(displayCard, LinearLayout.LayoutParams(-1, -2).apply { setMargins(a.dp(16), 0, a.dp(16), a.dp(14)) })'
if t.count(selector_add) != 1 or t.count(display_add) != 1: raise SystemExit("Tuner card insertion points not unique")
t = t.replace(selector_add + "\n", "").replace(display_add, display_add + "\n" + selector_add)
old = '''        gauge = TunerGaugeView(a)
        display.addView(gauge, LinearLayout.LayoutParams(-1, a.dp(230)))

        noteView = TextView(a).apply {
            text = "—"
            textSize = 64f
            gravity = Gravity.CENTER
            setTextColor(a.getColor(R.color.sw_text))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        display.addView(noteView, LinearLayout.LayoutParams(-1, a.dp(76)))'''
new = '''        noteView = TextView(a).apply {
            text = "—"
            textSize = 68f
            gravity = Gravity.CENTER
            setTextColor(a.getColor(R.color.sw_text))
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            contentDescription = "Erkannter Ton"
        }
        display.addView(noteView, LinearLayout.LayoutParams(-1, a.dp(78)))

        gauge = TunerGaugeView(a).apply {
            contentDescription = "Stimmungsanzeige: links zu tief, Mitte gestimmt, rechts zu hoch"
        }
        display.addView(gauge, LinearLayout.LayoutParams(-1, a.dp(190)))'''
if old in t:
    t = t.replace(old,new)
elif 'contentDescription = "Erkannter Ton"' not in t or 'a.dp(190)' not in t:
    raise SystemExit("Note/gauge layout neither original nor optimized")
old = '''            statusView?.setTextColor(requireContext().getColor(when (tone) {
                -1 -> R.color.sw_copper
                1 -> R.color.sw_copper
                else -> R.color.sw_copper
            }))'''
new = '''            val statusColor = when (tone) {
                -1 -> android.graphics.Color.rgb(218, 174, 76)
                1 -> android.graphics.Color.rgb(210, 105, 98)
                else -> android.graphics.Color.rgb(92, 175, 142)
            }
            statusView?.setTextColor(statusColor)
            noteView?.setTextColor(if (tone == 0) statusColor else requireContext().getColor(R.color.sw_text))'''
if old in t:
    t = t.replace(old,new)
elif "android.graphics.Color.rgb(92, 175, 142)" not in t:
    raise SystemExit("Status color block neither original nor optimized")
t = t.replace('text = "Instrument & Stimmung"','text = "INSTRUMENT"').replace('text = "Alternative Stimmungen"','text = "STIMMUNG"')
t = t.replace('text = "0 Cent"','text = "0 Cent · möglichst nahe an 0 stimmen"')
t = t.replace('text = "Warte auf einen Ton"','text = "— Hz"')
t = t.replace('text = "BEREIT ZUM STIMMEN"','text = "BEREIT · SAITE ANSCHLAGEN"')
t = t.replace('''        stringPanel = LinearLayout(a).apply {
            orientation = LinearLayout.HORIZONTAL''','''        selector.addView(TextView(a).apply {
            text = "Referenztöne · Saite antippen zum Anhören"
            textSize = 12f
            setTextColor(a.getColor(R.color.sw_muted))
            setPadding(0, a.dp(8), 0, a.dp(2))
        })
        stringPanel = LinearLayout(a).apply {
            orientation = LinearLayout.HORIZONTAL''')
t = t.replace('''            minHeight = a.dp(52)
            isClickable = true
            isFocusable = true
            setOnClickListener {''','''            minHeight = a.dp(52)
            isClickable = true
            isFocusable = true
            contentDescription = "Stimmung auswählen"
            setOnClickListener {''',1)
t = t.replace('''        selector.addView(instrumentSpinner, LinearLayout.LayoutParams(-1, a.dp(52)))''','''        instrumentSpinner?.contentDescription = "Instrument auswählen"
        selector.addView(instrumentSpinner, LinearLayout.LayoutParams(-1, a.dp(52)))''')
t = t.replace('''        root.addView(a.body("Spiele eine einzelne Saite an. Die Anzeige zeigt den erkannten Ton, die Abweichung in Cent und die passende Zielsaite. Wähle oben dein Instrument und die passende Stimmung."))''','''        root.addView(a.body("Spiele eine Saite einzeln an. Die Nadel zeigt die Abweichung: links = zu tief, rechts = zu hoch. Stimmen ist erreicht, wenn die Nadel mittig steht."))''')
# Remove the redundant explanatory paragraph below the tuner.
tuner_hint = 'root.addView(a.body("Spiele eine Saite einzeln an. Die Nadel zeigt die Abweichung: links = zu tief, rechts = zu hoch. Stimmen ist erreicht, wenn die Nadel mittig steht."))'
if tuner_hint in t:
    t = "\n".join(line for line in t.splitlines() if tuner_hint not in line)
if tuner_hint in t:
    raise SystemExit("TUNER UI: explanatory paragraph was not removed")

required = ['root.addView(displayCard','root.addView(selectorCard','contentDescription = "Erkannter Ton"','contentDescription = "Stimmungsanzeige:'android.graphics.Color.rgb(92, 175, 142)','Referenztöne · Saite antippen zum Anhören']
missing = [x for x in required if x not in t]
if missing: raise SystemExit("Tuner UI validation failed: " + ", ".join(missing))
main.write_text(s[:start] + t + s[end:], encoding="utf-8")
print("STIMMGERÄT UI: PASS")
