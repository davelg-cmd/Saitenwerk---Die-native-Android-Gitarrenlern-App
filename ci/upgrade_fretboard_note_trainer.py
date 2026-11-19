from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

view = r'''
/** Interaktives Griffbrett für das Finden einzelner Töne. */
class FretboardNoteView(context: android.content.Context) : View(context) {
    private val grid = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(92, 104, 120); strokeWidth = dp(1f)
        style = android.graphics.Paint.Style.STROKE
    }
    private val stringPaint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(205, 209, 214); strokeWidth = dp(1.6f)
    }
    private val accent = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(217, 154, 112); style = android.graphics.Paint.Style.FILL
    }
    private val text = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
        color = android.graphics.Color.rgb(224, 226, 229); textAlign = android.graphics.Paint.Align.CENTER
        textSize = dp(10f); typeface = android.graphics.Typeface.create("sans-serif-medium", 0)
    }
    var onNoteTap: ((Int, Int) -> Unit)? = null
    var highlighted: Pair<Int, Int>? = null
        set(value) { field = value; invalidate() }

    private val strings = arrayOf("E", "A", "D", "G", "H", "e")
    private val frets = 12

    override fun onDraw(canvas: android.graphics.Canvas) {
        super.onDraw(canvas)
        val left = dp(34f); val right = width - dp(12f)
        val top = dp(30f); val bottom = height - dp(34f)
        if (right <= left || bottom <= top) return
        val fw = (right - left) / frets.toFloat()
        val sg = (bottom - top) / 5f
        for (fret in 0..frets) {
            val x = left + fret * fw
            grid.strokeWidth = dp(if (fret == 0) 4f else 1.15f)
            canvas.drawLine(x, top, x, bottom, grid)
        }
        for (string in 0..5) {
            val y = bottom - string * sg
            stringPaint.strokeWidth = dp(1.25f + string * .16f)
            canvas.drawLine(left, y, right, y, stringPaint)
            canvas.drawText(strings[string], dp(15f), y + dp(4f), text)
        }
        for (fret in 1..frets) {
            val x = left + (fret - .5f) * fw
            if (fret == 3 || fret == 5 || fret == 7 || fret == 9) canvas.drawCircle(x, (top + bottom) / 2f, dp(4f), accent)
            if (fret == 12) {
                canvas.drawCircle(x, top + (bottom-top)*.34f, dp(4f), accent)
                canvas.drawCircle(x, top + (bottom-top)*.66f, dp(4f), accent)
            }
            canvas.drawText(fret.toString(), x, height - dp(12f), text)
        }
        highlighted?.let { (string, fret) ->
            val x = left + (fret.coerceIn(0, frets) + .5f) * fw
            val y = bottom - string.coerceIn(0, 5) * sg
            canvas.drawCircle(x, y, dp(10f), accent)
        }
    }

    override fun onTouchEvent(event: android.view.MotionEvent): Boolean {
        if (event.action != android.view.MotionEvent.ACTION_UP) return true
        val left = dp(34f); val right = width - dp(12f)
        val top = dp(30f); val bottom = height - dp(34f)
        if (right <= left || bottom <= top) return true
        val fw = (right - left) / frets.toFloat()
        val sg = (bottom - top) / 5f
        val string = ((bottom - event.y) / sg).toInt().coerceIn(0, 5)
        val fret = ((event.x - left) / fw).toInt().coerceIn(0, frets)
        onNoteTap?.invoke(string, fret)
        performClick()
        return true
    }
    override fun performClick(): Boolean { super.performClick(); return true }
    private fun dp(v: Float) = v * resources.displayMetrics.density
}

'''
if "class FretboardNoteView(context: android.content.Context)" not in s:
    marker = "class LearnFragment : Fragment()"
    if marker not in s: raise SystemExit("FEHLER: LearnFragment-Marker fehlt")
    s = s.replace(marker, view + marker, 1)

trainer = r'''
        fun showFretboard() {
            finishQuizSession(); chordTraining?.stop(); chordTraining = null; stopRhythm(); stopStrumming()
            content.removeAllViews()
            val card = roundedCard()
            val box = LinearLayout(a).apply { orientation = LinearLayout.VERTICAL; setPadding(a.dp(14), a.dp(14), a.dp(14), a.dp(14)) }
            box.addView(TextView(a).apply {
                text = "🎸 Griffbrett entdecken"; textSize = 21f; setTypeface(typeface, 1); setTextColor(a.getColor(R.color.sw_text))
            })
            box.addView(a.body("Finde den gesuchten Ton auf dem Griffbrett. Spiele ihn direkt an und trainiere Orientierung, Gehör und Notennamen.", 13f))
            val target = TextView(a).apply {
                textSize = 25f; setTypeface(typeface, 1); gravity = Gravity.CENTER
                setTextColor(a.getColor(R.color.sw_copper)); setPadding(0, a.dp(10), 0, a.dp(8))
            }
            box.addView(target)
            val feedback = TextView(a).apply {
                textSize = 13f; gravity = Gravity.CENTER; setTextColor(a.getColor(R.color.sw_muted)); minLines = 2
            }
            box.addView(feedback)
            val stats = TextView(a).apply { textSize = 12f; gravity = Gravity.CENTER; setTextColor(a.getColor(R.color.sw_text)); setPadding(0, a.dp(4), 0, a.dp(8)) }
            box.addView(stats)
            val fretboard = FretboardNoteView(a).apply { contentDescription = "Interaktives Gitarrengriffbrett, zwölf Bünde" }
            box.addView(fretboard, LinearLayout.LayoutParams(-1, a.dp(230)).apply { topMargin = a.dp(4) })
            val progress = ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal).apply { max = 10 }
            box.addView(progress, LinearLayout.LayoutParams(-1, a.dp(8)).apply { topMargin = a.dp(8) })
            val next = a.button("Nächsten Ton anzeigen").apply { tag = "saitenwerk-primary" }
            box.addView(next, LinearLayout.LayoutParams(-1, a.dp(52)).apply { topMargin = a.dp(10) })
            val reset = a.button("Runde neu starten")
            box.addView(reset, LinearLayout.LayoutParams(-1, a.dp(48)).apply { topMargin = a.dp(6) })
            card.addView(box); content.addView(card)

            val natural = arrayOf("C", "D", "E", "F", "G", "A", "H")
            val semitones = arrayOf("C", "Cis", "D", "Dis", "E", "F", "Fis", "G", "Gis", "A", "B", "H")
            val openMidi = intArrayOf(40, 45, 50, 55, 59, 64)
            val random = java.util.Random()
            var targetName = natural[random.nextInt(natural.size)]
            var round = 0; var correct = 0; var streak = 0
            var best = prefs.getInt("learn_fretboard_best_streak", 0)

            fun noteAt(string: Int, fret: Int) = semitones[(openMidi[string] + fret) % 12]
            fun update() {
                target.text = "Gesucht:  $targetName"
                stats.text = "Runde $round/10   ·   Treffer $correct   ·   Serie $streak   ·   Bestwert $best"
                progress.progress = round.coerceAtMost(10)
            }
            fun newTarget() {
                targetName = natural[random.nextInt(natural.size)]
                fretboard.highlighted = null
                feedback.text = "Tippe eine Saite und einen Bund an."
                update()
            }
            fun finishRound() {
                best = maxOf(best, streak, prefs.getInt("learn_fretboard_best_streak", 0))
                prefs.edit().putInt("learn_fretboard_best_streak", best).putInt("learn_fretboard_best_score", correct).apply()
                feedback.text = "Runde geschafft · $correct/10 Treffer · beste Serie $best"
                next.text = "Neue Runde starten"; progress.progress = 10
            }
            fretboard.onNoteTap = { string, fret ->
                if (round < 10) {
                    val found = noteAt(string, fret)
                    GuitarAudioEngine.playString(a, string, fret, 0.68f)
                    if (found == targetName) {
                        correct++; streak++; best = maxOf(best, streak); round++
                        fretboard.highlighted = Pair(string, fret)
                        feedback.text = "✓ Richtig · " + found + " auf Saite " + (string + 1) + ", Bund " + fret
                        if (round >= 10) finishRound() else newTarget()
                    } else {
                        streak = 0; fretboard.highlighted = Pair(string, fret)
                        feedback.text = "Noch nicht · du hast " + found + " getroffen. Gesucht ist " + targetName + "."
                        update()
                    }
                }
            }
            next.setOnClickListener {
                if (round >= 10) { round = 0; correct = 0; streak = 0; next.text = "Nächsten Ton anzeigen"; newTarget() }
                else newTarget()
            }
            reset.setOnClickListener {
                round = 0; correct = 0; streak = 0; next.text = "Nächsten Ton anzeigen"; newTarget()
                Toast.makeText(a, "Griffbrett-Training zurückgesetzt", Toast.LENGTH_SHORT).show()
            }
            update(); newTarget()
        }

'''
if "fun showFretboard()" not in s:
    marker = "        fun showSongPractice()"
    if marker not in s: raise SystemExit("FEHLER: showSongPractice-Marker fehlt")
    s = s.replace(marker, trainer + marker, 1)

button = '''            actionBox.addView(a.button("🎸 Griffbrett entdecken").apply { setOnClickListener { showFretboard() } },
                LinearLayout.LayoutParams(-1, a.dp(46)).apply { bottomMargin = a.dp(8) })
'''
anchor = '''            actionBox.addView(a.button("↘ Schlagmuster trainieren").apply { setOnClickListener { showStrumming() } },
'''
if 'a.button("🎸 Griffbrett entdecken")' not in s:
    if anchor not in s: raise SystemExit("FEHLER: Lernstudio-Aktionsbereich fehlt")
    s = s.replace(anchor, button + anchor, 1)

main.write_text(s, encoding="utf-8")
print("FRETTBRETT-NOTENTRAINER: PASS")
