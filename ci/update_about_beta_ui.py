from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")
s = main.read_text(encoding="utf-8")

# Einstellungen: Beschreibung und technische App-Informationen trennen.
settings_start = s.find("class SettingsFragment : Fragment() {")
about_start = s.find('        section("Über Saitenwerk"', settings_start)
settings_return = s.find("        return ScrollView(a).apply { clipToPadding=false; addView(page) }", about_start)
if min(settings_start, about_start, settings_return) < 0:
    raise SystemExit("FEHLER: Einstellungsbereich oder Über-Saitenwerk-Abschnitt nicht gefunden.")

replacement = r'''        val aboutText = "Saitenwerk ist mehr als nur eine Gitarren-App – es ist ein Experiment.\n\n" +
            "Die Idee hinter diesem Projekt war von Anfang an eine ganz bestimmte: Ich wollte zeigen, dass man keine Programmierkenntnisse oder jahrelange Erfahrung in der Softwareentwicklung benötigt, um eine eigene App auf die Beine zu stellen.\n\n" +
            "Mit Neugier, Ausdauer und der Unterstützung künstlicher Intelligenz ist Saitenwerk entstanden – von der ersten Idee bis hin zu einer eigenständigen Android-App.\n\n" +
            "Man muss nicht alles können, um etwas Eigenes zu erschaffen. Man muss nur anfangen."
        val aboutCard = a.card().apply { radius = a.dp(18).toFloat(); strokeColor = a.getColor(R.color.sw_outline); strokeWidth = a.dp(1) }
        val aboutBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(18), a.dp(17), a.dp(18), a.dp(17)) }
        aboutBox.addView(TextView(a).apply {
            text = "Über Saitenwerk"
            textSize = 17f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
        })
        aboutBox.addView(TextView(a).apply {
            text = aboutText
            textSize = 14f
            setLineSpacing(a.dp(2).toFloat(), 1f)
            setTextColor(a.getColor(R.color.sw_muted))
            setPadding(0, a.dp(7), 0, 0)
        })
        aboutCard.addView(aboutBox)
        page.addView(aboutCard, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = a.dp(13) })

        val buildNumber = version.substringAfterLast(".")
        val appInfoCard = a.card().apply { radius = a.dp(18).toFloat(); strokeColor = a.getColor(R.color.sw_outline); strokeWidth = a.dp(1) }
        val appInfoBox = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(18), a.dp(17), a.dp(18), a.dp(17)) }
        appInfoBox.addView(TextView(a).apply {
            text = "App-Informationen"
            textSize = 17f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
        })
        fun infoRow(label: String, value: String) {
            val line = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL; setPadding(0, a.dp(8), 0, a.dp(4)) }
            line.addView(TextView(a).apply {
                text = label
                textSize = 13f
                setTextColor(a.getColor(R.color.sw_muted))
            }, LinearLayout.LayoutParams(0, -2, 1f))
            line.addView(TextView(a).apply {
                text = value
                textSize = 13f
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setTextColor(a.getColor(R.color.sw_text))
                gravity = Gravity.END
            })
            appInfoBox.addView(line)
        }
        infoRow("Version", version)
        infoRow("Build-Nummer", buildNumber)
        infoRow("Version-Code", code.toString())
        infoRow("Release-Kanal", "Beta")
        infoRow("Plattform", "Android")
        infoRow("Paket-ID", a.packageName)
        infoRow("Mindestversion", "Android 8.0 (API 26)")
        appInfoBox.addView(TextView(a).apply {
            text = "Changelog"
            textSize = 16f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
            setPadding(0, a.dp(16), 0, a.dp(4))
        })
        val changes = listOf(
            "18.11.2026 · Build $buildNumber" to "Schnellstart im Lernstudio nach oben verschoben. Über Saitenwerk und App-Informationen übersichtlich getrennt.",
            "18.11.2026 · Build 350" to "Premium-Akkord-Dropdowns, einheitliche Kupfer-Typografie und überarbeitete Menüs.",
            "18.11.2026 · Build 347" to "Gitarrenklänge und musikalische Wiedergabe weiter verbessert.",
            "18.11.2026 · Build 346" to "Lernstudio, Trainingsabläufe und Fortschrittsanzeige optimiert.",
            "17.11.2026 · Build 335" to "Songpraxis und Bedienabläufe überarbeitet."
        )
        changes.forEach { (date, description) ->
            val entry = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(0, a.dp(8), 0, a.dp(8)) }
            entry.addView(TextView(a).apply {
                text = date
                textSize = 13f
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setTextColor(a.getColor(R.color.sw_text))
            })
            entry.addView(TextView(a).apply {
                text = description
                textSize = 13f
                setLineSpacing(a.dp(1).toFloat(), 1f)
                setTextColor(a.getColor(R.color.sw_muted))
                setPadding(0, a.dp(3), 0, 0)
            })
            appInfoBox.addView(entry)
        }
        appInfoCard.addView(appInfoBox)
        page.addView(appInfoCard, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = a.dp(13) })

'''
s = s[:about_start] + replacement + s[settings_return:]

# Lernstudio: Schnellstart muss direkt nach Titel und Einleitung stehen.
learn_start = s.find("class LearnFragment : Fragment() {")
learn_end = s.find("\\nclass PathFragment : Fragment() {", learn_start)
if learn_start < 0 or learn_end < 0:
    raise SystemExit("FEHLER: Lernstudio-Klasse nicht gefunden.")
learn = s[learn_start:learn_end]
overview_start = learn.find("        overviewAction = {")
intro_anchor = '            content.addView(a.body("Dein persönlicher Trainingsbereich für Akkorde, Rhythmus, Timing, Schlagmuster und Songs."))'
intro_pos = learn.find(intro_anchor, overview_start)
quick_start = learn.find("            val quick = roundedCard()", overview_start)
quick_end = learn.find("            val path = roundedCard()", quick_start)
if min(overview_start, intro_pos, quick_start, quick_end) < 0:
    raise SystemExit("FEHLER: Schnellstart oder Lernstudio-Einstieg nicht gefunden.")
quick_block = learn[quick_start:quick_end]
learn = learn[:quick_start] + learn[quick_end:]
intro_pos = learn.find(intro_anchor, overview_start)
insert_at = intro_pos + len(intro_anchor)
learn = learn[:insert_at] + "\\n\\n" + quick_block.rstrip() + learn[insert_at:]
s = s[:learn_start] + learn + s[learn_end:]

# Strenge Positionsprüfung: Schnellstart muss unmittelbar nach der Einleitung und vor Level/Statistik stehen.
learn_start = s.find("class LearnFragment : Fragment() {")
learn_end = s.find("\\nclass PathFragment : Fragment() {", learn_start)
learn = s[learn_start:learn_end]
overview_start = learn.find("        overviewAction = {")
intro_pos = learn.find("Dein persönlicher Trainingsbereich für Akkorde, Rhythmus, Timing, Schlagmuster und Songs.", overview_start)
quick_pos = learn.find("val quick = roundedCard()", overview_start)
xp_pos = learn.find("val xp = prefs.getInt", overview_start)
quick_add_pos = learn.find("content.addView(quick)", quick_pos)
if min(overview_start, intro_pos, quick_pos, xp_pos, quick_add_pos) < 0 or not (intro_pos < quick_pos < xp_pos) or quick_add_pos < quick_pos:
    raise SystemExit("FEHLER: Schnellstart steht nicht direkt am Anfang des Lernstudio-Inhalts.")
print("LERNSTUDIO: PASS – Schnellstart steht direkt nach Titel und Einleitung, vor Level, Statistik und Empfehlungen.")

# Einstellungen prüfen: technische Angaben bleiben im separaten App-Informationen-Bereich.
settings_start = s.find("class SettingsFragment : Fragment() {")
settings_return = s.find("        return ScrollView(a).apply { clipToPadding=false; addView(page) }", settings_start)
settings = s[settings_start:settings_return]
if "Über Saitenwerk" not in settings or "App-Informationen" not in settings or "Changelog" not in settings:
    raise SystemExit("FEHLER: Beschreibung, App-Informationen oder Changelog fehlen.")
main.write_text(s, encoding="utf-8")
print("EINSTELLUNGEN: PASS – Beschreibung getrennt; Version, Build, technische Daten und Changelog ausgelagert.")
print("LERNSTUDIO: PASS – vollständige Schnellstart-Karte steht vor der Fokus-Empfehlung.")
