from pathlib import Path
import os
root=Path(os.environ["PROJECT_DIR"])/"app/src/main/java/de/saitenwerk/app"
p=root/"MainActivity.kt"; s=p.read_text(encoding="utf-8")
s=s.replace('''        VIOLIN("Violine · Standard · G–D–A–E")
    }''','''        VIOLIN("Violine · Standard · G–D–A–E"),
        VIOLA("Bratsche · Standard · C–G–D–A"),
        CELLO("Cello · Standard · C–G–D–A")
    }''')
s=s.replace('    private var selectedAlternative = AlternativeTuning.STANDARD','    private var selectedAlternative = AlternativeTuning("Standard E", listOf("E2", "A2", "D3", "G3", "B3", "E4"))')
s=s.replace('    private var selectedAlternative = AlternativeTuning("Standard E", listOf("E2", "A2", "D3", "G3", "B3", "E4"))\n', '    private var selectedAlternative = AlternativeTuning("Standard E", listOf("E2", "A2", "D3", "G3", "B3", "E4"))\n    private var availableTunings = listOf(selectedAlternative)\n')
start=s.index('    private enum class AlternativeTuning('); end=s.index('\n    override fun onCreateView',start)
new='''    private data class AlternativeTuning(val label: String, val notes: List<String>)
    private fun tuningsFor(mode: TuningMode): List<AlternativeTuning> = when (mode) {
        TuningMode.GUITAR -> listOf(
            AlternativeTuning("Standard E", listOf("E2","A2","D3","G3","B3","E4")),
            AlternativeTuning("Drop D", listOf("D2","A2","D3","G3","B3","E4")),
            AlternativeTuning("Drop C", listOf("C2","G2","C3","F3","A3","D4")),
            AlternativeTuning("Double Drop D", listOf("D2","A2","D3","G3","B3","D4")),
            AlternativeTuning("DADGAD", listOf("D2","A2","D3","G3","A3","D4")),
            AlternativeTuning("Nashville", listOf("E3","A3","D4","G4","B3","E4")),
            AlternativeTuning("Open E", listOf("E2","B2","E3","G#3","B3","E4")),
            AlternativeTuning("Open G", listOf("D2","G2","D3","G3","B3","D4")),
            AlternativeTuning("Nick Drake · CGCFCE", listOf("C2","G2","C3","F3","C4","E4")),
            AlternativeTuning("Rain Song · DGCGCD", listOf("D2","G2","C3","G3","C4","D4"))
        )
        TuningMode.BASS -> listOf(
            AlternativeTuning("4-Saiter · E–A–D–G", listOf("E1","A1","D2","G2")),
            AlternativeTuning("4-Saiter · Drop D", listOf("D1","A1","D2","G2")),
            AlternativeTuning("4-Saiter · Drop C", listOf("C1","G1","C2","F2")),
            AlternativeTuning("5-Saiter · B–E–A–D–G", listOf("B0","E1","A1","D2","G2")),
            AlternativeTuning("6-Saiter · B–E–A–D–G–C", listOf("B0","E1","A1","D2","G2","C3"))
        )
        TuningMode.UKULELE -> listOf(
            AlternativeTuning("C-Stimmung · High G", listOf("G4","C4","E4","A4")),
            AlternativeTuning("C-Stimmung · Low G", listOf("G3","C4","E4","A4")),
            AlternativeTuning("D-Stimmung · A–D–F#–B", listOf("A4","D4","F#4","B4")),
            AlternativeTuning("Bariton · D–G–B–E", listOf("D3","G3","B3","E4"))
        )
        TuningMode.VIOLIN -> listOf(
            AlternativeTuning("Standard · G–D–A–E", listOf("G3","D4","A4","E5")),
            AlternativeTuning("Cross · A–E–A–E", listOf("A3","E4","A4","E5")),
            AlternativeTuning("GDGD", listOf("G3","D4","G4","D5"))
        )
        TuningMode.VIOLA -> listOf(
            AlternativeTuning("Standard · C–G–D–A", listOf("C3","G3","D4","A4")),
            AlternativeTuning("D-Stimmung · D–A–E–B", listOf("D3","A3","E4","B4"))
        )
        TuningMode.CELLO -> listOf(
            AlternativeTuning("Standard · C–G–D–A", listOf("C2","G2","D3","A3")),
            AlternativeTuning("D-Stimmung · D–A–D–A", listOf("D2","A2","D3","A3")),
            AlternativeTuning("Drop G · C–G–D–G", listOf("C2","G2","D3","G3"))
        )
        TuningMode.CHROMATIC -> emptyList()
    }
'''
s=s[:start]+new+s[end:]
s=s.replace('''                    alternativeSpinner?.isEnabled = selectedMode == TuningMode.GUITAR
                    targetView?.text = targetHint()''','''                    configureAlternativeTunings()
                    targetView?.text = targetHint()''')
s=s.replace('val labels = AlternativeTuning.values().map { it.label }','val labels = tuningsFor(selectedMode).map { it.label }')
s=s.replace('''            setSelection(AlternativeTuning.values().indexOf(selectedAlternative))
            isEnabled = selectedMode == TuningMode.GUITAR''','''            setSelection(0)
            isEnabled = tuningsFor(selectedMode).isNotEmpty()''')
s=s.replace('selectedAlternative = AlternativeTuning.values()[position]','selectedAlternative = availableTunings.getOrNull(position) ?: selectedAlternative')
marker='    private fun targetHint(): String = when (selectedMode)'
helper='''    private fun configureAlternativeTunings() {
        val options = tuningsFor(selectedMode)
        availableTunings = options
        selectedAlternative = options.firstOrNull() ?: AlternativeTuning("Chromatisch", emptyList())
        val spinner = alternativeSpinner ?: return
        spinner.onItemSelectedListener = null
        spinner.adapter = ArrayAdapter<String>(requireContext(), android.R.layout.simple_spinner_item, options.map { it.label }).also {
            it.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }
        spinner.isEnabled = options.isNotEmpty()
        if (options.isNotEmpty()) spinner.setSelection(0, false)
        spinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                val chosen = availableTunings.getOrNull(position) ?: return
                selectedAlternative = chosen
                targetView?.text = targetHint()
                rebuildStringButtons()
            }
        }
    }

'''
s=s.replace(marker,helper+marker)

start=s.index('    private fun targetHint(): String = when (selectedMode)'); end=s.index('\n    private fun noteFrequency',start)
s=s[:start]+'''    private fun targetHint(): String =
        if (selectedMode == TuningMode.CHROMATIC) "Chromatisch: jeder Ton wird erkannt"
        else "Zielsaiten: " + targets().joinToString(" · ") { it.name }
'''+s[end:]
start=s.index('    private fun targets(): List<Target> {'); end=s.index('\n    private fun rebuildStringButtons()',start)
s=s[:start]+'''    private fun targets(): List<Target> {
        if (selectedMode == TuningMode.CHROMATIC) return emptyList()
        return selectedAlternative.notes.mapIndexed { index, note ->
            Target((selectedAlternative.notes.size - index).toString() + note.replace(Regex("[0-9]"), ""), noteFrequency(note))
        }
    }
'''+s[end:]
s=s.replace('Wähle oben zuerst dein Instrument und – bei der Gitarre – bei Bedarf eine alternative Stimmung.','Wähle oben dein Instrument und die passende Stimmung.')
if 'AlternativeTuning.values()' in s or 'TuningMode.CELLO' not in s: raise SystemExit("Tuner source validation failed")
s=s.replace('selector.addView(alternativeSpinner, LinearLayout.LayoutParams(-1, a.dp(52)))', 'selector.addView(alternativeSpinner, LinearLayout.LayoutParams(-1, a.dp(52)))\\n        configureAlternativeTunings()')
p.write_text(s,encoding="utf-8")
p=root/"AppUpdateManager.kt"; u=p.read_text(encoding="utf-8")
u=u.replace("Alpha channel's GitHub release","current Beta release").replace("fetchAlphaRelease()","fetchBetaRelease()").replace("Kein veröffentlichter Alpha-7-Release gefunden","Kein veröffentlichter Beta-Release gefunden").replace("Neue Alpha-Version wird heruntergeladen","Neue Beta-Version wird heruntergeladen")
start=u.index("    private fun fetchBetaRelease(): JSONObject? {"); end=u.index("\n    private fun showMessage",start)
fetch='''    private fun fetchBetaRelease(): JSONObject? {
        val connection = (URL(RELEASES_API).openConnection() as HttpURLConnection).apply {
            connectTimeout = 15000
            readTimeout = 15000
            instanceFollowRedirects = true
            requestMethod = "GET"
            setRequestProperty("Accept", "application/vnd.github+json")
            setRequestProperty("X-GitHub-Api-Version", "2022-11-28")
            setRequestProperty("User-Agent", "Saitenwerk-Android-App")
            setRequestProperty("Cache-Control", "no-cache")
        }
        return try {
            val code = connection.responseCode
            if (code !in 200..299) {
                val detail = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                val suffix = if (detail.isNotBlank()) ": $detail" else ""
                throw IllegalStateException("GitHub antwortet mit HTTP $code$suffix")
            }
            val release = JSONObject(connection.inputStream.bufferedReader().use { it.readText() })
            if (release.optString("tag_name") != RELEASE_TAG || release.optBoolean("draft", false)) null else release
        } finally { connection.disconnect() }
    }
'''
u=u[:start]+fetch+u[end:]
u=u.replace('''private const val RELEASES_API = "https://api.github.com/repos/davelg-cmd/Saitenwerk---Die-native-Android-Gitarrenlern-App/releases?per_page=20"
        private const val RELEASE_TAG = "alpha-latest"
        private const val APK_NAME = "saitenwerk-alpha7.apk"''','''private const val RELEASES_API = "https://api.github.com/repos/davelg-cmd/Saitenwerk---Die-native-Android-Gitarrenlern-App/releases/tags/beta-latest"
        private const val RELEASE_TAG = "beta-latest"
        private const val APK_NAME = "saitenwerk-beta.apk"''')
if 'alpha-latest' in u or 'saitenwerk-alpha7.apk' in u: raise SystemExit("Legacy alpha update endpoint remains")
p.write_text(u,encoding="utf-8")
print("TUNER/UPDATE PATCH PASS")
