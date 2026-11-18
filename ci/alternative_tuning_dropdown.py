from pathlib import Path
import os

p = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

if "private var alternativeSpinner: TextView? = null" in s:
    print("ALTERNATIVE STIMMUNGEN DROPDOWN: bereits vorhanden")
    raise SystemExit(0)

if "private var alternativeSpinner: Spinner? = null" not in s:
    raise SystemExit("FEHLER: Alternativ-Stimmungs-Auswahl nicht gefunden.")

s = s.replace("private var alternativeSpinner: Spinner? = null",
              "private var alternativeSpinner: TextView? = null", 1)

start = s.find("        alternativeSpinner = Spinner(a).apply {")
if start < 0:
    raise SystemExit("FEHLER: Spinner-UI für alternative Stimmungen nicht gefunden.")
end_marker = "        selector.addView(alternativeSpinner, LinearLayout.LayoutParams(-1, a.dp(52)))"
end = s.find(end_marker, start)
if end < 0:
    raise SystemExit("FEHLER: Ende der Spinner-UI nicht gefunden.")
end += len(end_marker)

replacement = """        alternativeSpinner = TextView(a).apply {
            // Match the instrument Spinner's selected-value row exactly:
            // 14sp medium, 52dp, 14dp radius, surface2 + outline, same insets.
            textSize = 14f
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
            setTextColor(a.getColor(R.color.sw_text))
            gravity = Gravity.CENTER_VERTICAL
            includeFontPadding = true
            maxLines = 2
            setPadding(a.dp(16), a.dp(8), a.dp(42), a.dp(8))
            background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = a.dp(14).toFloat()
                setColor(a.getColor(R.color.sw_surface2))
                setStroke(a.dp(1), a.getColor(R.color.sw_outline))
            }
            minHeight = a.dp(52)
            minimumHeight = a.dp(52)
            isClickable = true
            isFocusable = true
            contentDescription = "Alternative Stimmung auswählen"
            setOnClickListener {
                val options = availableTunings
                if (options.isEmpty()) return@setOnClickListener
                androidx.appcompat.app.AlertDialog.Builder(a)
                    .setTitle("Alternative Stimmung")
                    .setItems(options.map { it.label }.toTypedArray()) { _, which ->
                        val chosen = options.getOrNull(which) ?: return@setItems
                        selectedAlternative = chosen
                        text = chosen.label
                        targetView?.text = targetHint()
                        rebuildStringButtons()
                    }
                    .setNegativeButton("Abbrechen", null)
                    .show()
            }
        }
        selector.addView(alternativeSpinner, LinearLayout.LayoutParams(-1, a.dp(52)))"""
s = s[:start] + replacement + s[end:]

if "private data class AlternativeTuning" not in s:
    enum_start = s.find("    private enum class AlternativeTuning(")
    if enum_start < 0:
        raise SystemExit("FEHLER: AlternativeTuning-Modell nicht gefunden.")
    enum_end = s.find("\n    override fun onCreateView", enum_start)
    if enum_end < 0:
        raise SystemExit("FEHLER: AlternativeTuning-Block konnte nicht abgegrenzt werden.")
    model = """    private data class AlternativeTuning(val label: String, val notes: List<String>)
    private var availableTunings = listOf(
        AlternativeTuning("Standard E", listOf("E2","A2","D3","G3","B3","E4"))
    )

    private fun tuningsFor(mode: TuningMode): List<AlternativeTuning> = when (mode) {
        TuningMode.GUITAR -> listOf(
            AlternativeTuning("Standard E", listOf("E2","A2","D3","G3","B3","E4")),
            AlternativeTuning("Drop D", listOf("D2","A2","D3","G3","B3","E4")),
            AlternativeTuning("Drop C", listOf("C2","G2","C3","F3","A3","D4")),
            AlternativeTuning("Double Drop D", listOf("D2","A2","D3","G3","B3","D4")),
            AlternativeTuning("DADGAD", listOf("D2","A2","D3","G3","A3","D4")),
            AlternativeTuning("Open E", listOf("E2","B2","E3","G#3","B3","E4")),
            AlternativeTuning("Open G", listOf("D2","G2","D3","G3","B3","D4")),
            AlternativeTuning("CGCFCE", listOf("C2","G2","C3","F3","C4","E4"))
        )
        TuningMode.BASS -> listOf(
            AlternativeTuning("4-Saiter · E–A–D–G", listOf("E1","A1","D2","G2")),
            AlternativeTuning("4-Saiter · Drop D", listOf("D1","A1","D2","G2")),
            AlternativeTuning("5-Saiter · B–E–A–D–G", listOf("B0","E1","A1","D2","G2"))
        )
        TuningMode.UKULELE -> listOf(
            AlternativeTuning("C-Stimmung · High G", listOf("G4","C4","E4","A4")),
            AlternativeTuning("C-Stimmung · Low G", listOf("G3","C4","E4","A4")),
            AlternativeTuning("D-Stimmung · A–D–F#–B", listOf("A4","D4","F#4","B4"))
        )
        TuningMode.VIOLIN -> listOf(
            AlternativeTuning("Standard · G–D–A–E", listOf("G3","D4","A4","E5")),
            AlternativeTuning("Cross · A–E–A–E", listOf("A3","E4","A4","E5"))
        )
        TuningMode.VIOLA -> listOf(
            AlternativeTuning("Standard · C–G–D–A", listOf("C3","G3","D4","A4")),
            AlternativeTuning("D-Stimmung · D–A–E–B", listOf("D3","A3","E4","B4"))
        )
        TuningMode.CELLO -> listOf(
            AlternativeTuning("Standard · C–G–D–A", listOf("C2","G2","D3","A3")),
            AlternativeTuning("D-Stimmung · D–A–D–A", listOf("D2","A2","D3","A3"))
        )
        TuningMode.CHROMATIC -> emptyList()
    )
"""
    s = s[:enum_start] + model + s[enum_end:]

fn_start = s.find("    private fun configureAlternativeTunings() {")
if fn_start < 0:
    raise SystemExit("FEHLER: configureAlternativeTunings() nicht gefunden.")
fn_end = s.find("\n    private fun targetHint()", fn_start)
if fn_end < 0:
    raise SystemExit("FEHLER: Ende von configureAlternativeTunings() nicht gefunden.")

fn = """    private fun configureAlternativeTunings() {
        val options = tuningsFor(selectedMode)
        availableTunings = options
        val chosen = options.firstOrNull()
        selectedAlternative = chosen ?: AlternativeTuning("Chromatisch", emptyList())
        val selector = alternativeSpinner ?: return
        selector.text = chosen?.label ?: "Keine alternative Stimmung"
        selector.isEnabled = options.isNotEmpty()
        selector.alpha = if (options.isNotEmpty()) 1f else 0.5f
    }
"""
s = s[:fn_start] + fn + s[fn_end:]

s = s.replace("AlternativeTuning.values().map { it.label }", "availableTunings.map { it.label }")
s = s.replace("AlternativeTuning.values()[position]", "availableTunings.getOrNull(position) ?: selectedAlternative")

required = [
    "private var alternativeSpinner: TextView? = null",
    "Alternative Stimmung auswählen",
    "private fun tuningsFor(mode: TuningMode)",
    "TuningMode.CELLO",
    "configureAlternativeTunings()",
    "setItems(options.map { it.label }.toTypedArray())",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("FEHLER: Dropdown-Validierung fehlgeschlagen: " + ", ".join(missing))

p.write_text(s, encoding="utf-8")
print("ALTERNATIVE STIMMUNGEN DROPDOWN: PASS")
