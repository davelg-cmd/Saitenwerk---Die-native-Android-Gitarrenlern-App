#!/usr/bin/env python3
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")
start = s.find("    private class GuitarPlayerEngine(")
end = s.find("    override fun onCreateView(", start)
if start < 0 or end < 0:
    raise SystemExit("ERROR: GuitarPlayerEngine anchors not found.")

new_class = '''    private class GuitarPlayerEngine(private val context: android.content.Context) {
        private val sampleRate = 22_050
        private val chunkFrames = 512
        private val tuning = intArrayOf(40, 45, 50, 55, 59, 64)
        private var audioTrack: AudioTrack? = null
        private var renderThread: Thread? = null
        @Volatile private var cancelled = false
        @Volatile private var paused = false
        private var totalDurationMs = 0

        private data class Sample(val root: Int, val pcm: FloatArray)
        private data class Note(val midi: Int, val string: Int, val fret: Int)
        private data class Event(val at: Long, val midi: Int, val velocity: Double, val pan: Double)
        private data class Voice(
            val sample: Sample,
            val midi: Int,
            val started: Long,
            val velocity: Double,
            val pan: Double
        )

        fun stop() {
            cancelled = true
            paused = false
            renderThread?.interrupt()
            renderThread = null
            audioTrack?.let {
                try { it.stop() } catch (_: Exception) {}
                try { it.release() } catch (_: Exception) {}
            }
            audioTrack = null
        }

        fun pause() {
            paused = true
            audioTrack?.pause()
        }

        fun resume() {
            paused = false
            audioTrack?.play()
        }

        fun position(): Int {
            val t = audioTrack ?: return 0
            val frames = t.playbackHeadPosition.toLong() and 0xffffffffL
            return ((frames * 1000L) / sampleRate).toInt().coerceIn(0, totalDurationMs)
        }

        fun duration(): Int = totalDurationMs

        fun play(
            timeline: SongTimeline,
            onReady: (Int) -> Unit,
            onCompleted: () -> Unit,
            onError: (Throwable) -> Unit
        ) {
            stop()
            cancelled = false
            val beatMs = 60_000.0 / timeline.tempoBpm.coerceIn(40, 180)
            totalDurationMs = timeline.durationMs.toInt().coerceAtLeast(1000)

            try {
                val minBuffer = AudioTrack.getMinBufferSize(
                    sampleRate,
                    AudioFormat.CHANNEL_OUT_STEREO,
                    AudioFormat.ENCODING_PCM_16BIT
                ).coerceAtLeast(chunkFrames * 4)

                val track = AudioTrack.Builder()
                    .setAudioAttributes(
                        AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_MEDIA)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                            .build()
                    )
                    .setAudioFormat(
                        AudioFormat.Builder()
                            .setSampleRate(sampleRate)
                            .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                            .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                            .build()
                    )
                    .setBufferSizeInBytes(minBuffer)
                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .build()

                audioTrack = track

                val chords = timeline.chords.map { Triple(it.chord, it.startMs, it.endMs) }
                val voicings = chords.map { guitarVoicing(it.first) }
                val needed = (
                    timeline.melody.map { it.midi } +
                    voicings.flatten().map { it.midi }
                ).distinct()
                val samples = needed.associateWith { loadSample(it) }
                val events = buildEvents(timeline, chords, voicings, beatMs)

                track.play()
                onReady(totalDurationMs)

                renderThread = Thread {
                    try {
                        val buffer = ShortArray(chunkFrames * 2)
                        val active = ArrayList<Voice>(32)
                        val totalFrames = totalDurationMs * sampleRate / 1000L
                        var frame = 0L
                        var nextEvent = 0

                        while (!cancelled && frame < totalFrames) {
                            while (paused && !cancelled) Thread.sleep(8L)
                            if (cancelled) break

                            var count = 0
                            while (count < chunkFrames && frame < totalFrames) {
                                val now = frame * 1000L / sampleRate

                                while (nextEvent < events.size && events[nextEvent].at <= now) {
                                    val e = events[nextEvent]
                                    samples[e.midi]?.let {
                                        active.add(Voice(it, e.midi, e.at, e.velocity, e.pan))
                                    }
                                    nextEvent++
                                }

                                var left = 0.0
                                var right = 0.0
                                var i = active.lastIndex

                                while (i >= 0) {
                                    val v = active[i]
                                    val age = (now - v.started).toDouble() / 1000.0
                                    val x = renderVoice(v, age)
                                    if (x == 0.0) {
                                        active.removeAt(i)
                                    } else {
                                        left += x * (1.0 - v.pan)
                                        right += x * (1.0 + v.pan)
                                    }
                                    i--
                                }

                                val body = (left + right) * 0.010
                                left += body
                                right += body

                                val l = softLimit(left * 0.80)
                                val r = softLimit(right * 0.80)
                                buffer[count * 2] =
                                    (l * 32767.0).roundToInt().coerceIn(-32768, 32767).toShort()
                                buffer[count * 2 + 1] =
                                    (r * 32767.0).roundToInt().coerceIn(-32768, 32767).toShort()

                                count++
                                frame++
                            }

                            var written = 0
                            while (written < count && !cancelled) {
                                val n = track.write(
                                    buffer,
                                    written * 2,
                                    (count - written) * 2,
                                    AudioTrack.WRITE_BLOCKING
                                )
                                if (n <= 0) break
                                written += n / 2
                            }
                        }

                        if (!cancelled) {
                            try { track.stop() } catch (_: Exception) {}
                            onCompleted()
                        }
                    } catch (t: Throwable) {
                        if (!cancelled) onError(t)
                    }
                }.also { it.start() }
            } catch (t: Throwable) {
                onError(t)
            }
        }

        private fun buildEvents(
            timeline: SongTimeline,
            chords: List<Triple<String, Long, Long>>,
            voicings: List<List<Note>>,
            beatMs: Double
        ): List<Event> {
            val result = ArrayList<Event>()

            for (c in chords.indices) {
                val range = chords[c]
                val notes = voicings[c]
                var beat = 0
                while (true) {
                    val start = range.second + (beat * beatMs).toLong()
                    if (start >= range.third) break
                    val reverse = beat % 2 == 1
                    val accent = if (beat % 4 == 0) 1.0 else 0.82

                    for (j in notes.indices) {
                        val n = notes[if (reverse) notes.lastIndex - j else j]
                        val delay = if (reverse) j * 9L else j * 10L
                        result.add(
                            Event(
                                start + delay,
                                n.midi,
                                0.145 * accent * (0.88 + n.string * 0.018),
                                ((n.string - 2.5) / 3.5) * 0.24
                            )
                        )
                    }
                    beat++
                }
            }

            for (m in timeline.melody) {
                result.add(
                    Event(
                        m.startMs,
                        m.midi,
                        m.velocity.toDouble() * 0.42,
                        0.0
                    )
                )
            }

            return result.sortedBy { it.at }
        }

        private fun renderVoice(v: Voice, age: Double): Double {
            if (age < 0.0) return 0.0
            val ratio = 2.0.pow((v.midi - v.sample.root) / 12.0)
            val position = age * sampleRate * ratio
            val index = position.toInt()
            if (index !in v.sample.pcm.indices) return 0.0
            val frac = position - index
            val a = v.sample.pcm[index].toDouble()
            val b = if (index + 1 < v.sample.pcm.size) v.sample.pcm[index + 1].toDouble() else a
            val attack = (age / 0.0022).coerceAtMost(1.0)
            return (a + (b - a) * frac) * v.velocity * attack
        }

        private fun loadSample(target: Int): Sample? {
            val center = target.coerceIn(40, 84)
            for (d in 0..12) {
                val candidates = if (d == 0) intArrayOf(center) else intArrayOf(center - d, center + d)
                for (midi in candidates) {
                    if (midi !in 40..84) continue
                    try {
                        val bytes = context.assets.open("guitar_samples/note_" + midi + ".pcm").use { it.readBytes() }
                        if (bytes.size < 4096) continue
                        val pcm = FloatArray(bytes.size / 2)
                        for (i in pcm.indices) {
                            val lo = bytes[i * 2].toInt() and 0xff
                            val hi = bytes[i * 2 + 1].toInt()
                            pcm[i] = ((hi shl 8) or lo).toShort() / 32768.0f
                        }
                        return Sample(midi, pcm)
                    } catch (_: Exception) {}
                }
            }
            return null
        }

        private fun guitarVoicing(chord: String): List<Note> {
            val clean = chord.replace('♯', '#').replace('♭', 'b')
            val m = Regex("^([A-G](?:#|b)?)([^/]*)(?:/([A-G](?:#|b)?))?").find(clean)
                ?: return listOf(Note(52, 0, 12), Note(55, 1, 10), Note(59, 2, 9))

            val root = noteIndex(m.groupValues[1]) ?: 0
            val bass = m.groupValues[3].takeIf { it.isNotBlank() }?.let { noteIndex(it) }
            val suffix = m.groupValues[2].lowercase()
            val pcs = when {
                suffix.contains("dim") -> setOf(root, (root + 3) % 12, (root + 6) % 12)
                suffix.contains("sus4") -> setOf(root, (root + 5) % 12, (root + 7) % 12)
                suffix.contains("sus2") -> setOf(root, (root + 2) % 12, (root + 7) % 12)
                suffix.contains("maj7") -> setOf(root, (root + 4) % 12, (root + 7) % 12, (root + 11) % 12)
                suffix.contains("7") -> setOf(root, (root + 4) % 12, (root + 7) % 12, (root + 10) % 12)
                suffix.contains("m") && !suffix.contains("maj") -> setOf(root, (root + 3) % 12, (root + 7) % 12)
                else -> setOf(root, (root + 4) % 12, (root + 7) % 12)
            }

            val choices = tuning.mapIndexed { string, open ->
                (0..7).mapNotNull { fret ->
                    val midi = open + fret
                    if (midi % 12 in pcs) Note(midi, string, fret) else null
                }.sortedBy { if (bass != null && it.midi % 12 == bass) 0 else it.fret }
            }

            val chosen = MutableList<Note?>(6) { null }
            val covered = mutableSetOf<Int>()

            for (string in 0..5) {
                val best = choices[string].firstOrNull {
                    bass != null && it.midi % 12 == bass && string <= 1
                } ?: choices[string].firstOrNull()
                if (best != null) {
                    chosen[string] = best
                    covered.add(best.midi % 12)
                }
            }

            for (pc in pcs) {
                if (covered.contains(pc)) continue
                val extra = choices.withIndex()
                    .flatMap { (string, list) -> list.map { string to it } }
                    .firstOrNull { it.second.midi % 12 == pc }
                if (extra != null) chosen[extra.first] = extra.second
            }

            val result = chosen.filterNotNull().distinctBy { it.string }.sortedBy { it.string }
            return if (result.size >= 3) result else fallbackTriad(root)
        }

        private fun fallbackTriad(root: Int): List<Note> {
            val base = 52 + root
            return listOf(
                Note(base, 0, (base - 40).coerceAtLeast(0)),
                Note(base + 4, 1, (base + 4 - 45).coerceAtLeast(0)),
                Note(base + 7, 2, (base + 7 - 50).coerceAtLeast(0))
            )
        }

        private fun softLimit(x: Double): Double =
            x / (1.0 + kotlin.math.abs(x) * 0.30)

        private fun noteIndex(note: String): Int? = when (note) {
            "C" -> 0
            "C#", "Db" -> 1
            "D" -> 2
            "D#", "Eb" -> 3
            "E" -> 4
            "F" -> 5
            "F#", "Gb" -> 6
            "G" -> 7
            "G#", "Ab" -> 8
            "A" -> 9
            "A#", "Bb" -> 10
            "B" -> 11
            else -> null
        }
    }

'''
s = s[:start] + new_class + s[end:]

for token in [
    "private data class Voice(",
    "private fun buildEvents(",
    "private fun loadSample(target: Int)",
    "private fun renderVoice(v: Voice",
    "AudioTrack.WRITE_BLOCKING"
]:
    if token not in s:
        raise SystemExit("ERROR: Guitar V3 validation failed: " + token)

path.write_text(s, encoding="utf-8")
print("REALISTIC GUITAR ENGINE V3: PASS")
print("Event-based six-string recorded-sample renderer installed.")
