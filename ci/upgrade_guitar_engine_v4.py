#!/usr/bin/env python3
"""Songsterr-inspired guitar performance renderer for Saitenwerk.

Keeps the real CC0 steel-string sample pack as the primary sound source,
but guarantees audible playback with a restrained pluck fallback if an
individual asset is unavailable. Playback is event based rather than
re-synthesizing a chord on every PCM frame.
"""
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
        // Songsterr-inspired playback model:
        // one continuous performance timeline, individual string attacks,
        // real recorded guitar samples, sustain overlap and small timing/level
        // variation. The tab remains the source of truth for timing.
        private val sampleRate = 22_050
        private val chunkFrames = 512
        private val tuning = intArrayOf(40, 45, 50, 55, 59, 64) // E A D G B E
        private var audioTrack: AudioTrack? = null
        private var renderThread: Thread? = null
        @Volatile private var cancelled = false
        @Volatile private var paused = false
        private var totalDurationMs = 0

        private data class Sample(val root: Int, val pcm: FloatArray)
        private data class Note(val midi: Int, val string: Int, val fret: Int)
        private data class Event(
            val at: Long,
            val midi: Int,
            val velocity: Double,
            val pan: Double,
            val durationMs: Long
        )
        private data class Voice(
            val sample: Sample,
            val midi: Int,
            val started: Long,
            val velocity: Double,
            val pan: Double,
            val maxAge: Double
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
            val track = audioTrack ?: return 0
            val frames = track.playbackHeadPosition.toLong() and 0xffffffffL
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
            paused = false

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

                val required = (
                    timeline.melody.map { it.midi } +
                    voicings.flatten().map { it.midi }
                ).distinct()

                val samples = required.associateWith { loadSample(it) }
                val events = buildEvents(timeline, chords, voicings, beatMs)

                track.play()
                onReady(totalDurationMs)

                renderThread = Thread {
                    try {
                        val buffer = ShortArray(chunkFrames * 2)
                        val active = ArrayList<Voice>(48)
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
                                    val sample = samples[e.midi] ?: loadSample(e.midi)
                                    val usable = sample ?: buildFallbackSample(e.midi)
                                    active.add(
                                        Voice(
                                            usable,
                                            e.midi,
                                            e.at,
                                            e.velocity,
                                            e.pan,
                                            e.durationMs / 1000.0
                                        )
                                    )
                                    nextEvent++
                                }

                                var left = 0.0
                                var right = 0.0
                                var i = active.lastIndex

                                while (i >= 0) {
                                    val v = active[i]
                                    val age = (now - v.started).toDouble() / 1000.0
                                    val value = renderVoice(v, age)

                                    if (value == 0.0 || age > v.maxAge + 0.25) {
                                        active.removeAt(i)
                                    } else {
                                        left += value * (1.0 - v.pan)
                                        right += value * (1.0 + v.pan)
                                    }
                                    i--
                                }

                                // Very small body bloom from the played guitar signal.
                                val body = (left + right) * 0.012
                                left += body
                                right += body

                                val l = softLimit(left * 0.86)
                                val r = softLimit(right * 0.86)
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

            // Rhythm guitar: four-beat bar feel, alternating down/up,
            // with a quieter off-beat. Individual strings are deliberately
            // staggered by a few milliseconds to preserve a human strum.
            for (c in chords.indices) {
                val range = chords[c]
                val notes = voicings[c]
                var beat = 0

                while (true) {
                    val beatStart = range.second + (beat * beatMs).toLong()
                    if (beatStart >= range.third) break

                    val down = beat % 2 == 0
                    val accent = when {
                        beat % 4 == 0 -> 1.0
                        beat % 2 == 0 -> 0.82
                        else -> 0.62
                    }

                    for (j in notes.indices) {
                        val order = if (down) j else notes.lastIndex - j
                        val note = notes[order]
                        val delay = if (down) j * 9L else j * 8L
                        val human = ((note.string * 13 + beat * 7) % 9 - 4) * 0.001
                        val velocity = 0.16 * accent * (0.92 + note.string * 0.014)

                        result.add(
                            Event(
                                at = beatStart + delay + human.toLong(),
                                midi = note.midi,
                                velocity = velocity,
                                pan = ((note.string - 2.5) / 3.5) * 0.22,
                                durationMs = (beatMs * 0.92).toLong().coerceAtLeast(90L)
                            )
                        )
                    }
                    beat++
                }
            }

            // Melody events are treated as played guitar notes rather than a
            // separate synthetic lead instrument.
            for (m in timeline.melody) {
                result.add(
                    Event(
                        at = m.startMs,
                        midi = m.midi,
                        velocity = m.velocity.toDouble().coerceIn(0.10, 1.0) * 0.50,
                        pan = 0.0,
                        durationMs = m.durationMs.toLong().coerceAtLeast(80L)
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
            val interpolated = a + (b - a) * frac

            val attack = (age / 0.002).coerceAtMost(1.0)
            val sustainFade = when {
                age < v.maxAge * 0.70 -> 1.0
                v.maxAge <= 0.0 -> 1.0
                else -> ((v.maxAge - age) / (v.maxAge * 0.30)).coerceIn(0.0, 1.0)
            }

            return interpolated * v.velocity * attack * sustainFade
        }

        private fun loadSample(target: Int): Sample? {
            val center = target.coerceIn(40, 84)

            // Prefer the exact recorded note. If unavailable, transpose the
            // closest recorded note; this mirrors a sampler's normal fallback.
            for (distance in 0..12) {
                val candidates =
                    if (distance == 0) intArrayOf(center)
                    else intArrayOf(center - distance, center + distance)

                for (midi in candidates) {
                    if (midi !in 40..84) continue
                    try {
                        val bytes = context.assets
                            .open("guitar_samples/note_" + midi + ".pcm")
                            .use { it.readBytes() }

                        if (bytes.size < 4096) continue

                        val pcm = FloatArray(bytes.size / 2)
                        for (i in pcm.indices) {
                            val lo = bytes[i * 2].toInt() and 0xff
                            val hi = bytes[i * 2 + 1].toInt()
                            pcm[i] = ((hi shl 8) or lo).toShort() / 32768.0f
                        }

                        return Sample(midi, pcm)
                    } catch (_: Exception) {
                        // Try the next mapped note.
                    }
                }
            }
            return null
        }

        private fun buildFallbackSample(midi: Int): Sample {
            val frequency = 440.0 * 2.0.pow((midi - 69) / 12.0)
            val delay = (sampleRate / frequency).roundToInt().coerceIn(2, sampleRate / 2)
            val line = FloatArray(delay)

            var seed = (midi.toLong() * 7919L + 104729L) and 0x7fffffffL
            for (i in line.indices) {
                seed = (seed * 1103515245L + 12345L) and 0x7fffffffL
                line[i] = (((seed.toDouble() / 1073741823.5) - 1.0) * 0.30).toFloat()
            }

            val pcm = FloatArray(sampleRate * 2)
            var cursor = 0

            for (i in pcm.indices) {
                val current = line[cursor]
                val next = line[(cursor + 1) % delay]
                line[cursor] = (current * 0.54f + next * 0.46f) * 0.9992f
                pcm[i] = current
                cursor = (cursor + 1) % delay
            }

            return Sample(midi, pcm)
        }

        private fun guitarVoicing(chord: String): List<Note> {
            val clean = chord.replace('♯', '#').replace('♭', 'b')
            val match = Regex("^([A-G](?:#|b)?)([^/]*)(?:/([A-G](?:#|b)?))?").find(clean)
                ?: return listOf(Note(52, 0, 12), Note(55, 1, 10), Note(59, 2, 9))

            val root = noteIndex(match.groupValues[1]) ?: 0
            val bass = match.groupValues[3].takeIf { it.isNotBlank() }?.let { noteIndex(it) }
            val suffix = match.groupValues[2].lowercase()

            val pcs = when {
                suffix.contains("dim") -> setOf(root, (root + 3) % 12, (root + 6) % 12)
                suffix.contains("sus4") -> setOf(root, (root + 5) % 12, (root + 7) % 12)
                suffix.contains("sus2") -> setOf(root, (root + 2) % 12, (root + 7) % 12)
                suffix.contains("maj7") -> setOf(root, (root + 4) % 12, (root + 7) % 12, (root + 11) % 12)
                suffix.contains("7") -> setOf(root, (root + 4) % 12, (root + 7) % 12, (root + 10) % 12)
                suffix.contains("m") && !suffix.contains("maj") -> setOf(root, (root + 3) % 12, (root + 7) % 12)
                else -> setOf(root, (root + 4) % 12, (root + 7) % 12)
            }

            val candidates = tuning.mapIndexed { string, open ->
                (0..7).mapNotNull { fret ->
                    val midi = open + fret
                    if (midi % 12 in pcs) Note(midi, string, fret) else null
                }.sortedWith(
                    compareBy<Note> {
                        if (bass != null && it.midi % 12 == bass) 0 else 1
                    }.thenBy { it.fret }
                )
            }

            val chosen = MutableList<Note?>(6) { null }
            val covered = mutableSetOf<Int>()

            for (string in 0..5) {
                val options = candidates[string]
                val best = options.firstOrNull {
                    it.midi % 12 == (bass ?: root) && string <= 1
                } ?: options.firstOrNull()

                if (best != null) {
                    chosen[string] = best
                    covered.add(best.midi % 12)
                }
            }

            for (pc in pcs) {
                if (covered.contains(pc)) continue
                val replacement = candidates.withIndex()
                    .flatMap { (string, opts) -> opts.map { string to it } }
                    .firstOrNull { (_, note) -> note.midi % 12 == pc }

                if (replacement != null) {
                    chosen[replacement.first] = replacement.second
                    covered.add(pc)
                }
            }

            val result = chosen.filterNotNull()
                .distinctBy { it.string }
                .sortedBy { it.string }

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

        private fun softLimit(value: Double): Double =
            value / (1.0 + kotlin.math.abs(value) * 0.30)

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

required = [
    "Songsterr-inspired playback model",
    "private fun buildEvents(",
    "private fun loadSample(target: Int)",
    "private fun buildFallbackSample(midi: Int)",
    "AudioTrack.WRITE_BLOCKING",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("ERROR: Guitar V4 validation failed: " + ", ".join(missing))

path.write_text(s, encoding="utf-8")
print("REALISTIC GUITAR ENGINE V4: PASS")
print("Songsterr-inspired event playback + real steel-string samples + audible fallback installed.")
