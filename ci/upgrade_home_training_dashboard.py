#!/usr/bin/env python3
"""Add a compact, data-driven daily practice dashboard to the Saitenwerk home screen."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
source = main.read_text(encoding="utf-8")

anchor = """        page.addView(top)
        val hero=a.card()"""
if "DEIN HEUTIGES TRAINING" in source:
    print("HOME-TRAININGSDASHBOARD: bereits vorhanden")
    raise SystemExit(0)
if anchor not in source:
    raise SystemExit("FEHLER: HomeFragment-Einfügepunkt nicht gefunden; keine Änderung vorgenommen.")

dashboard = r'''        page.addView(top)

        // Persönlicher Tagesüberblick: nutzt ausschließlich vorhandene Lernfortschrittsdaten.
        val todayKey = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.GERMANY).format(java.util.Date())
        val weekCalendar = java.util.Calendar.getInstance()
        val weekKey = weekCalendar.get(java.util.Calendar.YEAR).toString() + "-" + weekCalendar.get(java.util.Calendar.WEEK_OF_YEAR).toString()
        val routineDone = if (prefs.getString("learn_routine_day", "") == todayKey) Integer.bitCount(prefs.getInt("learn_routine_done", 0)) else 0
        val routineTotal = 5
        val dailySeconds = if (prefs.getString("learn_daily_day", "") == todayKey) prefs.getInt("learn_daily_seconds", prefs.getInt("learn_daily_minutes", 0) * 60) else 0
        val weeklySeconds = if (prefs.getString("learn_week_key", "") == weekKey) prefs.getInt("learn_week_seconds", 0) else 0
        val streak = prefs.getInt("learn_streak", 0)
        val pathStages = listOf("Erste Akkorde", "Saubere Griffbilder", "Flüssige Wechsel", "Rhythmus festigen", "Erste Songs begleiten", "Selbstständig spielen")
        val pathMask = prefs.getInt("learning_path_done", 0)
        val nextPathIndex = pathStages.indices.firstOrNull { (pathMask and (1 shl it)) == 0 }
        val nextPath = nextPathIndex?.let { pathStages[it] } ?: "Alle Lernstufen geschafft"

        val todayCard = a.card().apply {
            radius = a.dp(20).toFloat()
            strokeColor = a.getColor(R.color.sw_outline)
            strokeWidth = a.dp(1)
            cardElevation = a.dp(2).toFloat()
        }
        val todayBox = LinearLayout(a).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(a.dp(17), a.dp(16), a.dp(17), a.dp(16))
        }
        val todayHeader = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        todayHeader.addView(TextView(a).apply {
            text = "DEIN HEUTIGES TRAINING"
            textSize = 11f
            letterSpacing = 0.12f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
        }, LinearLayout.LayoutParams(0, -2, 1f))
        todayHeader.addView(TextView(a).apply {
            text = if (routineDone == routineTotal) "GESCHAFFT" else "$routineDone / $routineTotal"
            textSize = 12f
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(a.getColor(R.color.sw_copper))
        })
        todayBox.addView(todayHeader)
        todayBox.addView(TextView(a).apply {
            text = if (routineDone == routineTotal) "Stark – deine Tagesroutine ist erledigt." else "Ein paar gezielte Minuten bringen dich weiter."
            textSize = 14f
            setTextColor(a.getColor(R.color.sw_text))
            setPadding(0, a.dp(7), 0, a.dp(10))
        })
        val todayProgress = ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = routineTotal
            progress = routineDone
            progressTintList = android.content.res.ColorStateList.valueOf(a.getColor(R.color.sw_copper))
            progressBackgroundTintList = android.content.res.ColorStateList.valueOf(a.getColor(R.color.sw_outline))
        }
        todayBox.addView(todayProgress, LinearLayout.LayoutParams(-1, a.dp(7)))
        val metrics = LinearLayout(a).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, a.dp(12), 0, a.dp(12))
        }
        fun metric(value: String, label: String) {
            val item = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; gravity = Gravity.CENTER }
            item.addView(TextView(a).apply {
                text = value
                textSize = 17f
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                setTextColor(a.getColor(R.color.sw_text))
                gravity = Gravity.CENTER
            })
            item.addView(TextView(a).apply {
                text = label
                textSize = 10f
                setTextColor(a.getColor(R.color.sw_muted))
                gravity = Gravity.CENTER
                setPadding(0, a.dp(2), 0, 0)
            })
            metrics.addView(item, LinearLayout.LayoutParams(0, -2, 1f))
        }
        metric(String.format(java.util.Locale.GERMANY, "%.0f min", dailySeconds / 60.0), "Heute")
        metric(String.format(java.util.Locale.GERMANY, "%.0f min", weeklySeconds / 60.0), "Diese Woche")
        metric("$streak Tage", "Serie")
        todayBox.addView(metrics)
        todayBox.addView(TextView(a).apply {
            text = "Als Nächstes: $nextPath"
            textSize = 12f
            setTextColor(a.getColor(R.color.sw_muted))
            setPadding(0, 0, 0, a.dp(12))
        })
        val todayActions = LinearLayout(a).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        todayActions.addView(Button(a).apply {
            tag = "saitenwerk-primary"
            text = "Training starten"
            isAllCaps = false
            setOnClickListener { a.openSection(5) }
        }, LinearLayout.LayoutParams(0, a.dp(50), 1f).apply { rightMargin = a.dp(6) })
        todayActions.addView(a.button("Lernpfad").apply {
            setOnClickListener { a.openSection(6) }
        }, LinearLayout.LayoutParams(0, a.dp(50), 1f).apply { leftMargin = a.dp(6) })
        todayBox.addView(todayActions)
        todayCard.addView(todayBox)
        page.addView(todayCard, LinearLayout.LayoutParams(-1, -2).apply { topMargin = a.dp(16) })

        val hero=a.card()'''
source = source.replace(anchor, dashboard, 1)
main.write_text(source, encoding="utf-8")

# Fail fast if the patch accidentally duplicates or omits key UI elements.
check = main.read_text(encoding="utf-8")
for required in ["DEIN HEUTIGES TRAINING", "Training starten", "Diese Woche", "learning_path_done", "a.openSection(5)", "a.openSection(6)"]:
    if required not in check:
        raise SystemExit("FEHLER: Home-Dashboard-Prüfung fehlgeschlagen: " + required)
print("HOME-TRAININGSDASHBOARD: PASS (Tagesroutine, Übungszeit, Wochenzeit, Serie und Lernpfad)")
