from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")
required_resources = [
    "app/src/main/res/raw/guitar_string_6e.ogg",
    "app/src/main/res/raw/guitar_string_5a.ogg",
    "app/src/main/res/raw/guitar_string_4d.ogg",
    "app/src/main/res/raw/guitar_string_3g.ogg",
    "app/src/main/res/raw/guitar_string_2b.ogg",
    "app/src/main/res/raw/guitar_string_1e.ogg",
]
missing = [p for p in required_resources if not (root / p).is_file()]
if missing:
    raise SystemExit("FEHLER: Original-Gitarrenaufnahmen fehlen: " + ", ".join(missing))

engine = r'''
/** Gemeinsame Sample-Engine für authentische Gitarrenklänge in der gesamten App. */
object GuitarAudioEngine {
    private val handler = Handler(Looper.getMainLooper())
    private var pool: SoundPool? = null
    private val sampleIds = IntArray(6)
    private val loadedIds = mutableSetOf<Int>()
    private val activeStreams = mutableSetOf<Int>()
    private val scheduled = mutableSetOf<Runnable>()
    private val pendingActions = mutableListOf<() -> Unit>()
    private var progressionTask: Runnable? = null
    private val openFrequencies = doubleArrayOf(82.4069, 110.0, 146.832, 196.0, 246.942, 329.628)

    @Synchronized
    private fun initialize(context: android.content.Context) {
        if (pool != null) return
        val attributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
            .build()
        val created = SoundPool.Builder().setMaxStreams(16).setAudioAttributes(attributes).build()
        pool = created
        created.setOnLoadCompleteListener { _, sampleId, status ->
            if (status == 0) loadedIds.add(sampleId)
            if (loadedIds.size == 6) {
                val ready = pendingActions.toList()
                pendingActions.clear()
                ready.forEach { it.invoke() }
            }
        }
        val resources = intArrayOf(
            R.raw.guitar_string_6e, R.raw.guitar_string_5a, R.raw.guitar_string_4d,
            R.raw.guitar_string_3g, R.raw.guitar_string_2b, R.raw.guitar_string_1e
        )
        resources.forEachIndexed { index, resourceId ->
            sampleIds[index] = created.load(context.applicationContext, resourceId, 1)
        }
    }

    private fun whenReady(context: android.content.Context, action: () -> Unit) {
        initialize(context)
        if (loadedIds.size == 6) action() else pendingActions.add(action)
    }

    private fun playStringNow(index: Int, fret: Int, volume: Float, fadeMs: Long = 0L): Int {
        val player = pool ?: return 0
        if (index !in 0..5) return 0
        val rate = (2.0.pow(fret.coerceIn(0, 24) / 12.0)).coerceIn(0.5, 2.0).toFloat()
        val safeVolume = volume.coerceIn(0f, 1f)
        val stream = player.play(sampleIds[index], safeVolume, safeVolume, 1, 0, rate)
        if (stream != 0) {
            activeStreams.add(stream)
            if (fadeMs > 0L) {
                val steps = 5
                for (step in 1..steps) {
                    val task = Runnable {
                        val level = safeVolume * (1f - step.toFloat() / steps)
                        try {
                            player.setVolume(stream, level, level)
                            if (step == steps) {
                                player.stop(stream)
                                activeStreams.remove(stream)
                            }
                        } catch (_: Exception) { }
                        scheduled.removeIf { it === this }
                    }
                    scheduled.add(task)
                    handler.postDelayed(task, fadeMs * step / steps)
                }
            }
        }
        return stream
    }

    fun playTunedString(context: android.content.Context, stringNumber: Int, frequency: Double, volume: Float = 0.86f) {
        if (stringNumber !in 1..6 || !frequency.isFinite() || frequency !in 20.0..2000.0) return
        val index = 6 - stringNumber
        val rate = (frequency / openFrequencies[index]).coerceIn(0.5, 2.0).toFloat()
        whenReady(context) {
            stopAll()
            val player = pool ?: return@whenReady
            val stream = player.play(sampleIds[index], volume.coerceIn(0f, 1f), volume.coerceIn(0f, 1f), 2, 0, rate)
            if (stream != 0) activeStreams.add(stream)
        }
    }

    fun playString(context: android.content.Context, index: Int, fret: Int = 0, volume: Float = 0.6f, fadeMs: Long = 0L) {
        whenReady(context) { playStringNow(index, fret, volume, fadeMs) }
    }

    /** Kurzer, echter Saitenanschlag als musikalischer Metronom-Puls. */
    fun playTick(context: android.content.Context, accented: Boolean) {
        playString(context, if (accented) 0 else 5, 0, if (accented) 0.62f else 0.38f, 145L)
    }

    /** Zupft die Saiten eines Akkords mit leicht versetztem Anschlag. */
    fun playChord(
        context: android.content.Context,
        shape: ChordShape,
        downstroke: Boolean = true,
        volume: Float = 0.72f,
        replace: Boolean = false
    ) {
        if (replace) stopAll()
        whenReady(context) {
            val order = if (downstroke) (0..5).toList() else (5 downTo 0).toList()
            order.forEachIndexed { position, stringIndex ->
                val fret = shape.frets.getOrNull(stringIndex) ?: -1
                if (fret >= 0) {
                    val task = Runnable {
                        playStringNow(stringIndex, fret, volume * if (stringIndex == 0 || stringIndex == 5) 0.88f else 1f)
                        scheduled.removeIf { it === this }
                    }
                    scheduled.add(task)
                    handler.postDelayed(task, position * 15L)
                }
            }
        }
    }

    /** Spielt eine Song-Akkordfolge mit vier gleichmäßigen Schlägen pro Akkord. */
    fun playProgression(context: android.content.Context, chordNames: List<String>, bpm: Int = 80, onFinished: (() -> Unit)? = null) {
        val shapes = chordNames.mapNotNull { name -> ChordLibrary.all.firstOrNull { it.name == name.trim() } }
        if (shapes.isEmpty()) return
        stopAll()
        whenReady(context) {
            var index = 0
            val interval = (240000L / bpm.coerceIn(40, 180)).coerceAtLeast(500L)
            val task = object : Runnable {
                override fun run() {
                    if (index >= shapes.size) {
                        progressionTask = null
                        onFinished?.invoke()
                        return
                    }
                    playChord(context, shapes[index], downstroke = true, volume = 0.78f)
                    index++
                    handler.postDelayed(this, interval)
                }
            }
            progressionTask = task
            handler.post(task)
        }
    }

    fun stopAll() {
        progressionTask?.let { handler.removeCallbacks(it) }
        progressionTask = null
        scheduled.toList().forEach { handler.removeCallbacks(it) }
        scheduled.clear()
        pendingActions.clear()
        val player = pool
        activeStreams.toList().forEach { stream ->
            try { player?.stop(stream) } catch (_: Exception) { }
        }
        activeStreams.clear()
    }
}
'''

anchor = "open class ChordDiagramView(context: android.content.Context, initialShape: ChordShape? = null) : View(context) {"
if "object GuitarAudioEngine {" not in s:
    if anchor not in s: raise SystemExit("FEHLER: Einfügepunkt für gemeinsame Soundengine fehlt.")
    s = s.replace(anchor, engine + "\n" + anchor, 1)

# Replace the generated Karplus-Strong chord renderer with the recorded-string player.
a = s.find("object ChordPreviewPlayer {")
b = s.find("\nclass ChordsFragment", a)
if a < 0 or b < 0: raise SystemExit("FEHLER: ChordPreviewPlayer nicht gefunden.")
s = s[:a] + '''object ChordPreviewPlayer {
    fun play(shape: ChordShape, context: android.content.Context) {
        GuitarAudioEngine.playChord(context, shape, downstroke = true, volume = 0.88f, replace = true)
    }
    fun stop() = GuitarAudioEngine.stopAll()
}
''' + s[b:]
s = s.replace("ChordPreviewPlayer.play(ch)", "ChordPreviewPlayer.play(ch, a)")

# The tuner now uses the same global sample engine as the rest of the app.
for old in [
'''    private var referenceSoundPool: SoundPool? = null
    private val referenceSampleIds = mutableMapOf<String, Int>()
    private val loadedReferenceSamples = mutableSetOf<Int>()
    private var pendingReference: Pair<String, Double>? = null
    private var referenceStreamId = 0
''',
'''    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prepareReferenceSamples()
    }

    private fun prepareReferenceSamples() {
        val ctx = context ?: return
        val attributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
            .build()
        val pool = SoundPool.Builder().setMaxStreams(2).setAudioAttributes(attributes).build()
        referenceSoundPool = pool
        pool.setOnLoadCompleteListener { _, sampleId, status ->
            if (status == 0) {
                loadedReferenceSamples.add(sampleId)
                if (loadedReferenceSamples.size == 6) {
                    pendingReference?.let { (string, hz) ->
                        pendingReference = null
                        playRecordedReference(string, hz)
                    }
                }
            }
        }
        referenceSampleIds["6"] = pool.load(ctx, R.raw.guitar_string_6e, 1)
        referenceSampleIds["5"] = pool.load(ctx, R.raw.guitar_string_5a, 1)
        referenceSampleIds["4"] = pool.load(ctx, R.raw.guitar_string_4d, 1)
        referenceSampleIds["3"] = pool.load(ctx, R.raw.guitar_string_3g, 1)
        referenceSampleIds["2"] = pool.load(ctx, R.raw.guitar_string_2b, 1)
        referenceSampleIds["1"] = pool.load(ctx, R.raw.guitar_string_1e, 1)
    }

''',
'''    private fun playReferenceTone(frequency: Double = referenceA4) {
        stopReferenceTone()
        if (!frequency.isFinite() || frequency !in 20.0..2000.0) return
        val string = selectedReferenceName?.take(1) ?: return
        if (referenceSoundPool == null) prepareReferenceSamples()
        val sampleId = referenceSampleIds[string] ?: return
        if (!loadedReferenceSamples.contains(sampleId)) {
            pendingReference = string to frequency
            return
        }
        playRecordedReference(string, frequency)
    }

    private fun playRecordedReference(string: String, frequency: Double) {
        val pool = referenceSoundPool ?: return
        val sampleId = referenceSampleIds[string] ?: return
        if (!loadedReferenceSamples.contains(sampleId)) return
        val openStringHz = mapOf(
            "6" to 82.4069, "5" to 110.0, "4" to 146.832,
            "3" to 196.0, "2" to 246.942, "1" to 329.628
        )[string] ?: return
        // Kleine Pitch-Anpassung für alternative Stimmungen; der Klang bleibt eine echte Aufnahme.
        val playbackRate = (frequency / openStringHz).coerceIn(0.5, 2.0).toFloat()
        referenceStreamId = pool.play(sampleId, 0.88f, 0.88f, 1, 0, playbackRate)
    }

    private fun stopReferenceTone() {
        pendingReference = null
        if (referenceStreamId != 0) {
            try { referenceSoundPool?.stop(referenceStreamId) } catch (_: Exception) { }
            referenceStreamId = 0
        }
    }
''',
'''    override fun onDestroy() {
        stopReferenceTone()
        try { referenceSoundPool?.release() } catch (_: Exception) { }
        referenceSoundPool = null
        referenceSampleIds.clear()
        loadedReferenceSamples.clear()
        super.onDestroy()
    }
'''
]:
    if old not in s: raise SystemExit("FEHLER: Erwarteter Tuner-Audioabschnitt nicht gefunden: " + old[:70])
    if "private var referenceSoundPool" in old:
        s = s.replace(old, "", 1)
    elif "override fun onCreate(savedInstanceState" in old:
        s = s.replace(old, "", 1)
    elif "private fun playReferenceTone" in old:
        s = s.replace(old, '''    private fun playReferenceTone(frequency: Double = referenceA4) {
        if (!frequency.isFinite() || frequency !in 20.0..2000.0) return
        val stringNumber = selectedReferenceName?.take(1)?.toIntOrNull() ?: return
        GuitarAudioEngine.playTunedString(requireContext(), stringNumber, frequency, 0.88f)
    }

    private fun stopReferenceTone() {
        GuitarAudioEngine.stopAll()
    }
''', 1)
    else:
        s = s.replace(old, "", 1)

# Chord-change training now plays the actual target chord instead of electronic beeps.
s = s.replace('    private val tone = ToneGenerator(AudioManager.STREAM_MUSIC, 62)\n', '')
old_tick = '''            try {
                tone.startTone(
                    if (isBarStart) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP,
                    if (isBarStart) 80 else 45
                )
            } catch (_: Exception) {}

'''
if old_tick not in s: raise SystemExit("FEHLER: Akkordtrainer-Metronom nicht gefunden.")
s = s.replace(old_tick, "", 1)
needle = '''            beat++
            handler.postDelayed(this, (60000L / bpm).coerceAtLeast(100L))
'''
repl = '''            val activeShape = ChordLibrary.all.firstOrNull { it.name == current.text.toString() }
            if (activeShape != null) {
                GuitarAudioEngine.playChord(
                    host, activeShape, downstroke = beatInBar % 2 == 0,
                    volume = if (isBarStart) 0.80f else 0.52f
                )
            }

            beat++
            handler.postDelayed(this, (60000L / bpm).coerceAtLeast(100L))
'''
if needle not in s: raise SystemExit("FEHLER: Akkordtrainer-Taktanker fehlt.")
s = s.replace(needle, repl, 1)
s = s.replace('''        try {
            tone.stopTone()
        } catch (_: Exception) {}
''', '''        GuitarAudioEngine.stopAll()
''', 1)
s = s.replace('''        try {
            tone.release()
        } catch (_: Exception) {}
''', '''        GuitarAudioEngine.stopAll()
''', 1)

# Rhythm and strumming training use real plucked strings/chord strokes.
s = s.replace('    private var rhythmTone: ToneGenerator? = null\n', '')
s = s.replace('    private var strumTone: ToneGenerator? = null\n', '')
s = s.replace('rhythmTone = ToneGenerator(AudioManager.STREAM_MUSIC, 65); ', '')
s = s.replace('''                            rhythmTone?.startTone(if (strong) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP, if (strong) 80 else 55)
''', '''                            GuitarAudioEngine.playTick(a, strong)
''', 1)
s = s.replace('strumTone = ToneGenerator(AudioManager.STREAM_MUSIC, 60); ', '')

# Add a persistent chord choice to the strumming trainer.
needle = '''            var selectedName = prefs.getString("learn_strum_pattern", patterns.keys.first()) ?: patterns.keys.first()
            var selected = patterns[selectedName] ?: patterns.values.first()
'''
repl = needle + '''            var selectedChordName = prefs.getString("learn_strum_chord", "G") ?: "G"
            var selectedChord = ChordLibrary.all.firstOrNull { it.name == selectedChordName } ?: ChordLibrary.all.first()
'''
if needle not in s: raise SystemExit("FEHLER: Schlagmuster-Auswahlanker fehlt.")
s = s.replace(needle, repl, 1)
needle = '''            val patternButton = a.button(selectedName)
            val patternHint = TextView(a).apply'''
repl = '''            val patternButton = a.button(selectedName)
            val chordButton = a.button("Gitarrenklang · $selectedChordName")
            val patternHint = TextView(a).apply'''
if needle not in s: raise SystemExit("FEHLER: Schlagmuster-Buttonanker fehlt.")
s = s.replace(needle, repl, 1)
needle = '''            box.addView(patternButton, LinearLayout.LayoutParams(-1, a.dp(46)))
            box.addView(patternHint)
'''
repl = '''            box.addView(chordButton, LinearLayout.LayoutParams(-1, a.dp(44)).apply { bottomMargin = a.dp(5) })
            box.addView(patternButton, LinearLayout.LayoutParams(-1, a.dp(46)))
            box.addView(patternHint)
            chordButton.setOnClickListener {
                val names = ChordLibrary.all.map { it.name }.toTypedArray()
                androidx.appcompat.app.AlertDialog.Builder(a)
                    .setTitle("Akkord für das Schlagmuster")
                    .setSingleChoiceItems(names, names.indexOf(selectedChordName).coerceAtLeast(0)) { dialog, which ->
                        selectedChordName = names[which]
                        selectedChord = ChordLibrary.all.first { it.name == selectedChordName }
                        prefs.edit().putString("learn_strum_chord", selectedChordName).apply()
                        chordButton.text = "Gitarrenklang · $selectedChordName"
                        dialog.dismiss()
                    }
                    .setNegativeButton("Abbrechen", null)
                    .show()
            }
'''
if needle not in s: raise SystemExit("FEHLER: Schlagmuster-Layoutanker fehlt.")
s = s.replace(needle, repl, 1)
needle = '''                            val strong = step == 0
                            strumTone?.startTone(if (strong) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_BEEP, if (strong) 75 else 45)
                            markBeat(); strumStep++
'''
repl = '''                            val strong = step == 0
                            GuitarAudioEngine.playChord(
                                a, selectedChord, downstroke = selected[step] == "↓",
                                volume = if (strong) 0.78f else 0.56f
                            )
                            markBeat(); strumStep++
'''
if needle not in s: raise SystemExit("FEHLER: Schlagmuster-Audiotaktanker fehlt.")
s = s.replace(needle, repl, 1)
s = s.replace('''            down.setOnClickListener { userHit("↓") }
            up.setOnClickListener { userHit("↑") }
''', '''            down.setOnClickListener {
                GuitarAudioEngine.playChord(a, selectedChord, downstroke = true, volume = 0.84f)
                userHit("↓")
            }
            up.setOnClickListener {
                GuitarAudioEngine.playChord(a, selectedChord, downstroke = false, volume = 0.84f)
                userHit("↑")
            }
''', 1)

# Song practice can now audition the selected progression with real guitar chords.
needle = '''            box.addView(selected)
            val progressions = listOf("G – D – Em – C", "C – Am – F – G", "Am – F – C – G", "Em – C – G – D")
'''
repl = '''            box.addView(selected)
            val playProgression = a.button("▶ Akkordfolge anhören")
            val stopProgression = a.button("■ Wiedergabe stoppen")
            box.addView(playProgression, LinearLayout.LayoutParams(-1, a.dp(46)).apply { topMargin = a.dp(6) })
            box.addView(stopProgression, LinearLayout.LayoutParams(-1, a.dp(42)).apply { topMargin = a.dp(5) })
            playProgression.setOnClickListener {
                val names = selected.text.toString().substringAfter(":").split("–").map { it.trim() }
                if (names.any { name -> ChordLibrary.all.none { it.name == name } }) {
                    Toast.makeText(a, "Für diese Folge fehlt ein Akkordgriff.", Toast.LENGTH_SHORT).show()
                } else {
                    playProgression.text = "♫ Akkordfolge läuft · 80 BPM"
                    GuitarAudioEngine.playProgression(a, names, 80) {
                        playProgression.text = "▶ Akkordfolge anhören"
                    }
                }
            }
            stopProgression.setOnClickListener {
                GuitarAudioEngine.stopAll()
                playProgression.text = "▶ Akkordfolge anhören"
            }
            val progressions = listOf("G – D – Em – C", "C – Am – F – G", "Am – F – C – G", "Em – C – G – D")
'''
if needle not in s: raise SystemExit("FEHLER: Song-Praxis-Audioanker fehlt.")
s = s.replace(needle, repl, 1)
s = s.replace('''                        prefs.edit().putString("learn_song_progression", progression).apply()
                        selected.text = "Aktuelle Folge: $progression"
''', '''                        GuitarAudioEngine.stopAll()
                        playProgression.text = "▶ Akkordfolge anhören"
                        prefs.edit().putString("learn_song_progression", progression).apply()
                        selected.text = "Aktuelle Folge: $progression"
''', 1)

# Stop shared sample playback when practice sessions are left or destroyed.
s = s.replace('''        try { strumTone?.stopTone(); strumTone?.release() } catch (_: Exception) {}
        strumTone = null
''', '''        GuitarAudioEngine.stopAll()
''', 1)
s = s.replace('''        try { rhythmTone?.stopTone(); rhythmTone?.release() } catch (_: Exception) {}
        rhythmTone = null
''', '''        GuitarAudioEngine.stopAll()
''', 1)

# Drop now-unused tone imports and fail if any artificial training beeps remain.
s = s.replace("import android.media.ToneGenerator\n", "")
s = s.replace("import android.media.AudioManager\n", "")
for forbidden in ["ToneGenerator", "rhythmTone", "strumTone", "private val tone ="]:
    if forbidden in s:
        raise SystemExit("FEHLER: Künstliche Tonquelle/alte Audio-Referenz bleibt übrig: " + forbidden)
checks = [
    "object GuitarAudioEngine {",
    "GuitarAudioEngine.playTunedString",
    "GuitarAudioEngine.playChord",
    "GuitarAudioEngine.playTick",
    "GuitarAudioEngine.playProgression",
    "Gitarrenklang · $selectedChordName",
    "▶ Akkordfolge anhören",
    "private fun playReferenceTone",
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("FEHLER: Gemeinsame Audio-Integration unvollständig: " + ", ".join(missing))

main.write_text(s, encoding="utf-8")
print("PREMIUM-GITARRENKLANG: PASS")
print("Gemeinsame Sample-Engine, Stimmgerät, Akkordvorschau, Akkordwechsel, Schlagmuster, Metronom und Song-Praxis integriert.")
