from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not path.exists():
    raise SystemExit("FEHLER: MainActivity.kt fehlt.")
s = path.read_text(encoding="utf-8")
start = s.find("class ChordTrainingPanel(private val host: MainActivity) : LinearLayout(host) {")
end = s.find("\ndata class Song(", start)
if start < 0 or end < 0:
    raise SystemExit("FEHLER: ChordTrainingPanel nicht gefunden.")

replacement = r'''class ChordTrainingPanel(private val host: MainActivity) : LinearLayout(host) {
    private val handler = Handler(Looper.getMainLooper())
    private val tone = ToneGenerator(AudioManager.STREAM_MUSIC, 62)
    private val prefs = host.getSharedPreferences("saitenwerk", 0)
    private val defaultSequence = listOf("C", "G", "Am", "F")
    private val availableChords = ChordLibrary.all.map { it.name.trim() }.filter { it.isNotEmpty() }.distinct().sorted().ifEmpty { defaultSequence }
    private var sequence = loadSequence()
    private var bpm = prefs.getInt("chord_training_bpm", 72).coerceIn(50, 160)
    private val meters = listOf("2/4", "3/4", "4/4", "6/8")
    private var meter = prefs.getString("chord_training_meter", "4/4")?.takeIf { it in meters } ?: "4/4"
    private val beatsPerBar: Int get() = meter.substringBefore("/").toInt()
    private var beat = 0
    private var changes = 0
    private var bars = 0
    private var streak = 0
    private var bestStreak = prefs.getInt("chord_training_best_streak", 0)
    private var sessionSeconds = 0
    private var running = false

    private val current = TextView(host)
    private val next = TextView(host)
    private val status = TextView(host)
    private val sequenceLabel = TextView(host)
    private val chooseChords = host.button("Akkorde auswählen")
    private val meterButton = host.button("Taktart · 4/4")
    private val randomize = host.button("↻ Reihenfolge mischen")
    private val start = host.button("Training starten")
    private val tempo = SeekBar(host)
    private val tempoLabel = TextView(host)
    private val stats = TextView(host)
    private val progress = ProgressBar(host, null, android.R.attr.progressBarStyleHorizontal)
    private val sessionTimer = TextView(host)

    private fun loadSequence(): List<String> {
        val validNames = ChordLibrary.all.map { it.name }.toSet()
        val saved = prefs.getStringSet("chord_training_selected_chords", null)
        val valid = saved?.filter { it in validNames } ?: emptyList()
        return if (valid.size >= 2) valid.sorted() else defaultSequence
    }

    private fun refreshSequenceLabel() {
        sequenceLabel.text = "Trainingsakkorde · " + sequence.joinToString(" · ")
        current.text = sequence.firstOrNull() ?: "—"
        next.text = if (sequence.size > 1)
            "Als Nächstes · " + sequence[1]
        else ""
    }

    private fun openChordPicker() {
        if (running) {
            Toast.makeText(host, "Bitte stoppe das Training zuerst, um die Akkorde zu ändern.", Toast.LENGTH_SHORT).show()
            return
        }
        // Eigene scrollbare Checkbox-Liste: Auswahl wird explizit übernommen.
        val scroll = android.widget.ScrollView(host).apply {
            isFillViewport = true
            setPadding(host.dp(20), host.dp(4), host.dp(20), host.dp(4))
        }
        val list = LinearLayout(host).apply { orientation = VERTICAL }
        val checks = linkedMapOf<String, android.widget.CheckBox>()
        availableChords.forEach { chordName ->
            val check = android.widget.CheckBox(host).apply {
                text = ""
                contentDescription = chordName
                isChecked = chordName in sequence
                minWidth = host.dp(44)
                minHeight = host.dp(44)
                buttonTintList = android.content.res.ColorStateList.valueOf(host.getColor(R.color.sw_copper))
            }
            val label = TextView(host).apply {
                text = chordName
                textSize = 18f
                setTextColor(host.getColor(R.color.sw_copper))
                setTypeface(typeface, android.graphics.Typeface.BOLD)
                gravity = Gravity.CENTER_VERTICAL
                includeFontPadding = true
                setPadding(host.dp(10), 0, host.dp(8), 0)
                isClickable = false
            }
            val row = LinearLayout(host).apply {
                orientation = HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                minimumHeight = host.dp(54)
                setPadding(host.dp(4), host.dp(2), host.dp(4), host.dp(2))
                isClickable = true
                setOnClickListener { check.isChecked = !check.isChecked }
            }
            row.addView(check, LayoutParams(host.dp(48), host.dp(54)))
            row.addView(label, LayoutParams(0, -1, 1f))
            checks[chordName] = check
            list.addView(row, LayoutParams(-1, host.dp(54)))
        }
        scroll.addView(list)
        val dialog = androidx.appcompat.app.AlertDialog.Builder(host)
            .setTitle("Trainingsakkorde auswählen")
            .setMessage("Markiere mindestens zwei Akkorde und tippe anschließend auf Übernehmen.")
            .setView(scroll)
            .setPositiveButton("Übernehmen", null)
            .setNegativeButton("Abbrechen", null)
            .create()
        dialog.setOnShowListener {
            dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val selected = checks.filterValues { it.isChecked }.keys.toList()
                if (selected.size < 2) {
                    Toast.makeText(host, "Wähle mindestens zwei Akkorde aus.", Toast.LENGTH_LONG).show()
                    return@setOnClickListener
                }
                sequence = selected
                prefs.edit().putStringSet("chord_training_selected_chords", selected.toSet()).apply()
                resetSession()
                refreshSequenceLabel()
                status.text = selected.size.toString() + " Akkorde gespeichert. Bereit zum Start."
                dialog.dismiss()
            }
        }
        dialog.show()
    }

    private fun openMeterPicker() {
        if (running) return
        val selectedIndex = meters.indexOf(meter).coerceAtLeast(0)
        androidx.appcompat.app.AlertDialog.Builder(host)
            .setTitle("Taktart auswählen")
            .setSingleChoiceItems(meters.toTypedArray(), selectedIndex) { dialog, which ->
                meter = meters[which]
                prefs.edit().putString("chord_training_meter", meter).apply()
                meterButton.text = "Taktart · " + meter
                resetSession()
                status.text = "Taktart " + meter + " gewählt · " + beatsPerBar + " Schläge pro Takt."
                dialog.dismiss()
            }
            .setNegativeButton("Abbrechen", null)
            .show()
    }

    private fun shuffleSequence() {
        if (running) return
        sequence = sequence.shuffled()
        resetSession()
        refreshSequenceLabel()
        status.text = "Neue Reihenfolge bereit."
    }

    private fun resetSession() {
        stop()
        beat = 0
        changes = 0
        bars = 0
        streak = 0
        sessionSeconds = 0
        progress.progress = 0
        stats.text = "0 Wechsel · 0 Takte · Beste Serie " + bestStreak
        sessionTimer.text = "00:00"
    }

    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            val beatInBar = beat % beatsPerBar
            val isBarStart = beatInBar == 0
            try {
                tone.startTone(
                    if (isBarStart) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP,
                    if (isBarStart) 80 else 45
                )
            } catch (_: Exception) {}

            if (isBarStart) {
                val index = changes % sequence.size
                current.text = sequence[index]
                next.text = "Als Nächstes · " + sequence[(index + 1) % sequence.size]
                if (changes > 0) streak++
                changes++
                bars++
                bestStreak = maxOf(bestStreak, streak)
                prefs.edit().putInt("chord_training_best_streak", bestStreak).apply()
                stats.text = changes.toString() + " Wechsel · " + bars + " Takte · Serie " +
                    streak + " · Bestwert " + bestStreak
                progress.progress = (changes % 16) * 100 / 16
            }

            beat++
            handler.postDelayed(this, (60000L / bpm).coerceAtLeast(100L))
        }
    }

    private val timerTick = object : Runnable {
        override fun run() {
            if (!running) return
            sessionSeconds++
            sessionTimer.text = String.format("%02d:%02d", sessionSeconds / 60, sessionSeconds % 60)
            handler.postDelayed(this, 1000L)
        }
    }

    init {
        orientation = VERTICAL
        setPadding(host.dp(18), host.dp(18), host.dp(18), host.dp(18))
        background = android.graphics.drawable.GradientDrawable().apply {
            cornerRadius = host.dp(22).toFloat()
            setColor(host.getColor(R.color.sw_surface))
            setStroke(host.dp(1), host.getColor(R.color.sw_outline))
        }
        elevation = host.dp(2).toFloat()

        addView(TextView(host).apply {
            text = "Akkordwechsel-Training"
            textSize = 21f
            setTextColor(host.getColor(R.color.sw_copper))
            setTypeface(typeface, 1)
        })
        addView(TextView(host).apply {
            text = "Wechsle sauber im Takt. Geschwindigkeit kommt erst danach."
            textSize = 13f
            setTextColor(host.getColor(R.color.sw_muted))
            setPadding(0, host.dp(4), 0, host.dp(12))
        })

        sequenceLabel.apply {
            setTextColor(host.getColor(R.color.sw_text))
            textSize = 13f
        }
        addView(sequenceLabel, LayoutParams(-1, -2))

        val controls = LinearLayout(host).apply { orientation = HORIZONTAL }
        chooseChords.setOnClickListener { openChordPicker() }
        randomize.setOnClickListener { shuffleSequence() }
        controls.addView(chooseChords, LayoutParams(0, host.dp(44), 1f))
        controls.addView(randomize, LayoutParams(0, host.dp(44), 1f).apply {
            leftMargin = host.dp(6)
        })
        addView(controls, LayoutParams(-1, host.dp(44)).apply {
            bottomMargin = host.dp(8)
        })

        val stage = LinearLayout(host).apply {
            orientation = VERTICAL
            gravity = Gravity.CENTER
            setPadding(host.dp(12), host.dp(10), host.dp(12), host.dp(8))
            background = android.graphics.drawable.GradientDrawable().apply {
                cornerRadius = host.dp(18).toFloat()
                setColor(host.getColor(R.color.sw_surface2))
            }
        }

        current.apply {
            textSize = 48f
            gravity = Gravity.CENTER
            setTextColor(host.getColor(R.color.sw_text))
            setTypeface(typeface, 1)
        }
        stage.addView(current, LayoutParams(-1, host.dp(66)))

        next.apply {
            textSize = 12f
            setTextColor(host.getColor(R.color.sw_muted))
            gravity = Gravity.CENTER
        }
        stage.addView(next, LayoutParams(-1, host.dp(28)))
        addView(stage, LayoutParams(-1, host.dp(104)).apply {
            bottomMargin = host.dp(8)
        })

        val infoRow = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        status.apply {
            textSize = 12f
            setTextColor(host.getColor(R.color.sw_muted))
        }
        infoRow.addView(status, LayoutParams(0, -2, 1f))

        sessionTimer.apply {
            textSize = 12f
            setTextColor(host.getColor(R.color.sw_copper))
            gravity = Gravity.END
        }
        infoRow.addView(sessionTimer, LayoutParams(host.dp(52), -2))
        addView(infoRow, LayoutParams(-1, -2))

        tempoLabel.apply {
            textSize = 13f
            setTextColor(host.getColor(R.color.sw_text))
            setPadding(0, host.dp(8), 0, 0)
        }
        meterButton.text = "Takt · " + meter
        // Text im orangefarbenen Auswahlrahmen vertikal etwas nach oben setzen.
        meterButton.gravity = Gravity.CENTER
        meterButton.includeFontPadding = false
        meterButton.setPadding(
            meterButton.paddingLeft,
            host.dp(0),
            meterButton.paddingRight,
            host.dp(5)
        )
        meterButton.setOnClickListener { openMeterPicker() }
        tempoLabel.gravity = Gravity.CENTER_VERTICAL or Gravity.START
        tempoLabel.text = "Tempo · " + bpm + " BPM"
        tempo.max = 110
        tempo.progress = bpm - 50
        tempo.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(v: SeekBar?, p: Int, fromUser: Boolean) {
                bpm = (50 + p).coerceIn(50, 160)
                tempoLabel.text = "Tempo · " + bpm + " BPM"
                prefs.edit().putInt("chord_training_bpm", bpm).apply()
            }
            override fun onStartTrackingTouch(v: SeekBar?) {}
            override fun onStopTrackingTouch(v: SeekBar?) {}
        })

        val tempoColumn = LinearLayout(host).apply {
            orientation = VERTICAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(host.dp(8), 0, 0, 0)
        }
        tempoColumn.addView(tempoLabel, LayoutParams(-1, host.dp(22)))
        tempoColumn.addView(tempo, LayoutParams(-1, host.dp(36)))
        val meterTempoRow = LinearLayout(host).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        meterTempoRow.addView(meterButton, LayoutParams(0, host.dp(48), 0.9f))
        meterTempoRow.addView(tempoColumn, LayoutParams(0, host.dp(56), 1.1f))
        addView(meterTempoRow, LayoutParams(-1, host.dp(58)).apply {
            bottomMargin = host.dp(4)
        })

        progress.max = 100
        progress.progress = 0
        addView(progress, LayoutParams(-1, host.dp(8)).apply {
            bottomMargin = host.dp(8)
        })

        start.setOnClickListener {
            if (running) stop() else begin()
        }
        addView(start, LayoutParams(-1, host.dp(48)))

        stats.apply {
            textSize = 12f
            setTextColor(host.getColor(R.color.sw_muted))
            setPadding(0, host.dp(8), 0, host.dp(6))
        }
        addView(stats)

        val ratingRow = LinearLayout(host).apply { orientation = HORIZONTAL }
        val mastered = host.button("✓ Sitzt")
        val practice = host.button("↻ Weiter üben")
        mastered.setOnClickListener { saveRating(true) }
        practice.setOnClickListener { saveRating(false) }
        ratingRow.addView(mastered, LayoutParams(0, host.dp(44), 1f))
        ratingRow.addView(practice, LayoutParams(0, host.dp(44), 1f).apply {
            leftMargin = host.dp(6)
        })
        addView(ratingRow)

        refreshSequenceLabel()
        tempoLabel.text = "Tempo · " + bpm + " BPM"
        stats.text = "0 Wechsel · 0 Takte · Beste Serie " + bestStreak
        status.text = "Bereit · " + beatsPerBar + " Schläge pro Takt"
        sessionTimer.text = "00:00"
    }

    private fun begin() {
        if (sequence.size < 2) {
            status.text = "Bitte mindestens zwei Akkorde wählen."
            return
        }

        running = true
        beat = 0
        changes = 0
        bars = 0
        streak = 0
        sessionSeconds = 0

        start.text = "Training stoppen"
        chooseChords.isEnabled = false
        randomize.isEnabled = false
        status.text = "Läuft · jeder Akkord bleibt einen Takt (" + meter + ")"
        progress.progress = 0

        handler.removeCallbacks(tick)
        handler.removeCallbacks(timerTick)
        handler.post(tick)
        handler.post(timerTick)
    }

    fun stop() {
        handler.removeCallbacks(tick)
        handler.removeCallbacks(timerTick)

        if (!running) return

        running = false
        start.text = "Training starten"
        chooseChords.isEnabled = true
        randomize.isEnabled = true
        status.text = "Pause · " + changes + " Wechsel in " + sessionSeconds + "s"

        try {
            tone.stopTone()
        } catch (_: Exception) {}
    }

    private fun saveRating(mastered: Boolean) {
        val sessions = prefs.getInt("chord_training_sessions", 0) + 1
        val wins = prefs.getInt("chord_training_mastered", 0) + if (mastered) 1 else 0
        prefs.edit()
            .putInt("chord_training_sessions", sessions)
            .putInt("chord_training_mastered", wins)
            .apply()

        status.text = if (mastered) {
            "Als gemeistert markiert · " + wins + " von " + sessions
        } else {
            "Für weitere Übung vorgemerkt · " + wins + " von " + sessions
        }
    }

    override fun onDetachedFromWindow() {
        stop()
        try {
            tone.release()
        } catch (_: Exception) {}
        super.onDetachedFromWindow()
    }
}
'''

s = s[:start] + replacement + s[end:]
path.write_text(s, encoding="utf-8")
print("AKKORDWECHSEL-TRAINING: optimierte Version integriert.")
