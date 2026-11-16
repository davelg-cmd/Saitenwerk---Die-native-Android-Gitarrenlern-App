from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")
start = s.find("class ChordTrainingPanel(private val host: MainActivity) : LinearLayout(host) {")
end = s.find("\ndata class Song(", start)
if start < 0 or end < 0:
    raise SystemExit("FEHLER: ChordTrainingPanel nicht eindeutig gefunden.")

replacement = r'''class ChordTrainingPanel(private val host: MainActivity) : LinearLayout(host) {
    private val handler = Handler(Looper.getMainLooper())
    private val tone = ToneGenerator(AudioManager.STREAM_MUSIC, 55)
    private val prefs = host.getSharedPreferences("saitenwerk", 0)
    private val defaultSequence = listOf("C", "G", "Am", "F")
    private val availableChords = ChordLibrary.all.map { it.name }.distinct().sorted()
    private var sequence = loadSequence()
    private var bpm = 72
    private var beat = 0
    private var changes = 0
    private var running = false
    private val current = TextView(host)
    private val status = TextView(host)
    private val sequenceLabel = TextView(host)
    private val chooseChords = host.button("Akkorde auswählen")
    private val start = host.button("Training starten")
    private val tempo = SeekBar(host)
    private val tempoLabel = TextView(host)
    private val stats = TextView(host)

    private fun loadSequence(): List<String> {
        val validNames = ChordLibrary.all.map { it.name }.toSet()
        val saved = prefs.getStringSet("chord_training_selected_chords", null)
        val valid = saved?.filter { it in validNames } ?: emptyList()
        return if (valid.size >= 2) valid.sorted() else defaultSequence
    }

    private fun refreshSequenceLabel() {
        sequenceLabel.text = "Deine Trainingsakkorde: " + sequence.joinToString(" · ")
        current.text = sequence.firstOrNull() ?: "—"
    }

    private fun openChordPicker() {
        if (running) {
            Toast.makeText(host, "Bitte stoppe das Training zuerst, um die Akkorde zu ändern.", Toast.LENGTH_SHORT).show()
            return
        }
        val names = availableChords
        val checked = names.map { it in sequence }.toBooleanArray()
        androidx.appcompat.app.AlertDialog.Builder(host)
            .setTitle("Trainingsakkorde auswählen")
            .setMultiChoiceItems(names.toTypedArray(), checked) { _, which, isChecked ->
                checked[which] = isChecked
            }
            .setPositiveButton("Übernehmen") { _, _ ->
                val selected = names.filterIndexed { index, _ -> checked[index] }
                if (selected.size < 2) {
                    Toast.makeText(host, "Wähle mindestens zwei Akkorde aus.", Toast.LENGTH_LONG).show()
                    return@setPositiveButton
                }
                sequence = selected
                prefs.edit().putStringSet("chord_training_selected_chords", selected.toSet()).apply()
                beat = 0
                changes = 0
                refreshSequenceLabel()
                stats.text = "Akkordwechsel: 0 · Tempo: " + bpm + " BPM"
                status.text = selected.size.toString() + " Akkorde für dein Training gespeichert."
            }
            .setNegativeButton("Abbrechen", null)
            .show()
    }

    private val tick = object : Runnable {
        override fun run() {
            if (!running) return
            tone.startTone(if (beat % 4 == 0) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP, 65)
            if (beat % 4 == 0) {
                current.text = sequence[changes % sequence.size]
                changes++
                stats.text = "Akkordwechsel: " + (changes - 1) + " · Tempo: " + bpm + " BPM"
            }
            beat++
            handler.postDelayed(this, (60000L / bpm).coerceAtLeast(100L))
        }
    }

    init {
        orientation = VERTICAL
        setPadding(host.dp(16), host.dp(16), host.dp(16), host.dp(16))
        setBackgroundColor(host.getColor(R.color.sw_surface))
        addView(TextView(host).apply {
            text = "Akkordwechsel-Training"
            textSize = 20f
            setTextColor(host.getColor(R.color.sw_copper))
            setTypeface(typeface, 1)
        })
        sequenceLabel.apply {
            setTextColor(host.getColor(R.color.sw_muted))
            setPadding(0, host.dp(5), 0, host.dp(4))
            textSize = 13f
        }
        addView(sequenceLabel, LayoutParams(-1, -2))
        chooseChords.setOnClickListener { openChordPicker() }
        addView(chooseChords, LayoutParams(-1, host.dp(44)).apply { bottomMargin = host.dp(6) })
        current.apply {
            textSize = 40f
            gravity = Gravity.CENTER
            setTextColor(host.getColor(R.color.sw_text))
            setTypeface(typeface, 1)
        }
        addView(current, LayoutParams(-1, host.dp(76)))
        status.apply {
            text = "Bereit? Starte das Metronom."
            setTextColor(host.getColor(R.color.sw_muted))
            textSize = 13f
        }
        addView(status, LayoutParams(-1, -2))
        tempoLabel.apply {
            text = "Tempo: 72 BPM"
            setTextColor(host.getColor(R.color.sw_text))
            setPadding(0, host.dp(10), 0, 0)
        }
        addView(tempoLabel)
        tempo.max = 110
        tempo.progress = 22
        tempo.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(v: SeekBar?, progress: Int, fromUser: Boolean) {
                bpm = 50 + progress
                tempoLabel.text = "Tempo: " + bpm + " BPM"
            }
            override fun onStartTrackingTouch(v: SeekBar?) {}
            override fun onStopTrackingTouch(v: SeekBar?) {}
        })
        addView(tempo, LayoutParams(-1, host.dp(42)))
        start.setOnClickListener { if (running) stop() else begin() }
        addView(start, LayoutParams(-1, host.dp(48)))
        stats.apply {
            text = "Akkordwechsel: 0 · Tempo: 72 BPM"
            setTextColor(host.getColor(R.color.sw_muted))
            setPadding(0, host.dp(8), 0, host.dp(6))
        }
        addView(stats)
        val row = LinearLayout(host).apply { orientation = HORIZONTAL }
        val mastered = host.button("✓ Sitzt")
        val practice = host.button("↻ Weiter üben")
        mastered.setOnClickListener { saveRating(true) }
        practice.setOnClickListener { saveRating(false) }
        row.addView(mastered, LayoutParams(0, host.dp(44), 1f))
        row.addView(practice, LayoutParams(0, host.dp(44), 1f).apply { leftMargin = host.dp(6) })
        addView(row)
        refreshSequenceLabel()
        status.text = "Bisher: " + prefs.getInt("chord_training_mastered", 0) +
            " gemeisterte Bewertungen aus " + prefs.getInt("chord_training_sessions", 0) + " Einträgen."
    }

    private fun begin() {
        if (sequence.size < 2) {
            status.text = "Bitte wähle mindestens zwei Akkorde aus."
            return
        }
        running = true
        beat = 0
        changes = 0
        start.text = "Training stoppen"
        chooseChords.isEnabled = false
        status.text = "Läuft · auf den ersten Schlag achten"
        handler.removeCallbacks(tick)
        handler.post(tick)
    }

    fun stop() {
        running = false
        handler.removeCallbacks(tick)
        start.text = "Training starten"
        chooseChords.isEnabled = true
        try { tone.stopTone() } catch (_: Exception) {}
    }

    private fun saveRating(mastered: Boolean) {
        val sessions = prefs.getInt("chord_training_sessions", 0) + 1
        val wins = prefs.getInt("chord_training_mastered", 0) + if (mastered) 1 else 0
        prefs.edit().putInt("chord_training_sessions", sessions)
            .putInt("chord_training_mastered", wins).apply()
        status.text = if (mastered) "Als gemeistert markiert · " + wins + " von " + sessions
            else "Für weitere Übung vorgemerkt · " + wins + " von " + sessions
    }

    override fun onDetachedFromWindow() {
        stop()
        try { tone.release() } catch (_: Exception) {}
        super.onDetachedFromWindow()
    }
}
'''
s = s[:start] + replacement + s[end:]
path.write_text(s, encoding="utf-8")
print("AKKORDWECHSEL-TRAINING: Akkordauswahl integriert und dauerhaft speicherbar.")
