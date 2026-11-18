from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
java_root = root / "app/src/main"
main = java_root / "java/de/saitenwerk/app/MainActivity.kt"
if not main.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")
s = main.read_text(encoding="utf-8")

# Vorhandene Über-Karte und App-Informationsbereich sauber voneinander trennen.
credits_start = s.find("        val credits = a.card()")
return_start = s.find("        return ScrollView(a).apply { addView(content) }", credits_start)
if credits_start < 0 or return_start < 0:
    raise SystemExit("FEHLER: Über-Karte oder Rückgabe des Einstellungsbildschirms nicht gefunden.")

replacement = r'''        val appInfo = a.packageManager.getPackageInfo(a.packageName, 0)
        val appVersionName = appInfo.versionName ?: "unbekannt"
        val appVersionCode = appInfo.longVersionCode
        val credits = a.card()
        val creditsContent = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(18), a.dp(16), a.dp(18), a.dp(16))
        }
        creditsContent.addView(TextView(a).apply {
            text = "Über Saitenwerk"
            textSize = 18f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
        })
        creditsContent.addView(TextView(a).apply {
            text = "Saitenwerk ist mehr als nur eine Gitarren-App – es ist ein Experiment.\n\n" +
                "Die Idee hinter diesem Projekt war von Anfang an eine ganz bestimmte: Ich wollte zeigen, dass man keine Programmierkenntnisse oder jahrelange Erfahrung in der Softwareentwicklung benötigt, um eine eigene App auf die Beine zu stellen.\n\n" +
                "Mit Neugier, Ausdauer und der Unterstützung künstlicher Intelligenz ist Saitenwerk entstanden – von der ersten Idee bis hin zu einer eigenständigen Android-App.\n\n" +
                "Man muss nicht alles können, um etwas Eigenes zu erschaffen. Man muss nur anfangen."
            textSize = 14f
            setTextColor(a.getColor(R.color.sw_muted))
            setPadding(0, a.dp(8), 0, 0)
        })
        credits.addView(creditsContent)
        content.addView(credits, LinearLayout.LayoutParams(-1, -2).apply {
            setMargins(0, a.dp(14), 0, 0)
        })

        val appInfoCard = a.card()
        val appInfoContent = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(18), a.dp(16), a.dp(18), a.dp(16))
        }
        appInfoContent.addView(TextView(a).apply {
            text = "App-Informationen"
            textSize = 18f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
        })
        fun infoRow(label: String, value: String) {
            val line = LinearLayout(a).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setPadding(0, a.dp(8), 0, a.dp(4))
            }
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
            appInfoContent.addView(line)
        }
        infoRow("Version", appVersionName)
        infoRow("Build-Nummer", appVersionCode.toString())
        infoRow("Release-Kanal", "Beta")
        infoRow("Plattform", "Android")
        infoRow("Paket-ID", a.packageName)
        infoRow("Mindestversion", "Android 8.0")
        appInfoContent.addView(TextView(a).apply {
            text = "Changelog"
            textSize = 16f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
            setPadding(0, a.dp(16), 0, a.dp(4))
        })
        val changes = listOf(
            "18.11.2026 · Build 348" to "Premium-Akkord-Dropdowns, einheitliche Kupfer-Typografie und überarbeitete Menüs.",
            "18.11.2026 · Build 347" to "Gitarrenklänge und musikalische Wiedergabe weiter verbessert.",
            "18.11.2026 · Build 346" to "Lernstudio, Trainingsabläufe und Fortschrittsanzeige optimiert.",
            "17.11.2026 · Build 335" to "Songpraxis und Bedienabläufe überarbeitet."
        )
        changes.forEach { (date, description) ->
            val entry = LinearLayout(a).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(0, a.dp(8), 0, a.dp(8))
            }
            entry.addView(TextView(a).apply {
                text = date
                textSize = 13f
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setTextColor(a.getColor(R.color.sw_text))
            })
            entry.addView(TextView(a).apply {
                text = description
                textSize = 13f
                setTextColor(a.getColor(R.color.sw_muted))
                setPadding(0, a.dp(3), 0, 0)
            })
            appInfoContent.addView(entry)
        }
        appInfoCard.addView(appInfoContent)
        content.addView(appInfoCard, LinearLayout.LayoutParams(-1, -2).apply {
            setMargins(0, a.dp(14), 0, 0)
        })

'''
s = s[:credits_start] + replacement + s[return_start:]

# Diagnoseausgabe: zeigt den tatsächlichen Schnellstart-Code im Lernstudio,
# damit die anschließende Verschiebung an der realen Implementierung ansetzt.
learn_start = s.find("class LearnFragment : Fragment() {")
learn_end = s.find("\\nclass PathFragment : Fragment() {", learn_start)
learn = s[learn_start:learn_end] if learn_start >= 0 and learn_end > learn_start else ""
for term in ("Schnellstart", "quickStart", "quickstart", "Quickstart"):
    pos = learn.find(term)
    if pos >= 0:
        print("QUICKSTART_SOURCE_CONTEXT [" + term + "]:")
        print(learn[max(0, pos - 1400):min(len(learn), pos + 2200)])
        break
else:
    print("QUICKSTART_SOURCE_CONTEXT: kein eindeutiger Schnellstart-Anker im LearnFragment gefunden.")

settings_start = s.find("class SettingsFragment")
settings_end = s.find("\\nclass ", settings_start + 10)
settings = s[settings_start:settings_end if settings_end >= 0 else len(s)]
if "Über Saitenwerk" not in settings or "App-Informationen" not in settings or "Changelog" not in settings:
    raise SystemExit("FEHLER: Über-Bereich oder App-Informationen/Changelog fehlen.")
if 'Version: $appVersionName' in settings or 'Build: $appVersionCode' in settings:
    raise SystemExit("FEHLER: Versionsdaten stehen weiterhin im Über-Bereich.")
main.write_text(s, encoding="utf-8")
print("EINSTELLUNGEN: PASS – Über Saitenwerk ist getrennt; Versionsdaten und Changelog sind ausgelagert.")
