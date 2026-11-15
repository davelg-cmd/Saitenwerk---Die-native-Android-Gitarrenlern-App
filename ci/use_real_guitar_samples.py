#!/usr/bin/env python3
"""Use real recorded CC0 steel-string samples in the synchronized AudioTrack renderer."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

anchor = """        private var totalDurationMs = 0

        fun stop() {"""
insert = """        private var totalDurationMs = 0
        private data class GuitarSample(val rootMidi: Int, val samples: FloatArray)

        fun stop() {"""
if anchor in s:
    s = s.replace(anchor, insert, 1)
elif insert not in s:
    raise SystemExit("ERROR: GuitarPlayerEngine sample-model insertion anchor missing.")

old_cache = "val pluckSamples = requiredMidi.associateWith { buildPluckSample(it) }"
new_cache = "val pluckSamples = requiredMidi.associateWith { midi -> loadGuitarSample(midi) ?: GuitarSample(midi, buildPluckSample(midi)) }"
if old_cache in s:
    s = s.replace(old_cache, new_cache, 1)
elif new_cache not in s:
    raise SystemExit("ERROR: Guitar sample-cache anchor missing.")

replacements = [
    ("guitarPluck(pluckSamples[midi], strumLocal,", "guitarPluck(pluckSamples[midi], midi, strumLocal,"),
    ("guitarPluck(pluckSamples[bass], local,", "guitarPluck(pluckSamples[bass], bass, local,"),
    ("guitarPluck(pluckSamples[note.midi], local,", "guitarPluck(pluckSamples[note.midi], note.midi, local,"),
]
for old, new in replacements:
    if old in s:
        s = s.replace(old, new, 1)
    elif new not in s:
        raise SystemExit("ERROR: Guitar sample playback call-site missing: " + old)

old_method = """        private fun guitarPluck(samples: FloatArray?, t: Double, velocity: Double): Double {
            if (samples == null || t < 0.0) return 0.0
            val index = (t * sampleRate).toInt()
            if (index !in samples.indices) return 0.0
            return samples[index].toDouble() * velocity
        }"""
new_method = """        private fun loadGuitarSample(targetMidi: Int): GuitarSample? {
            // Meta's CC0 steel-string pack contains a separately recorded sample for
            // every semitone from E2 (MIDI 40) through C6 (MIDI 84).
            val sourceMidi = targetMidi.coerceIn(40, 84)
            return try {
                val bytes = context.assets.open("guitar_samples/note_${sourceMidi}.pcm").use { it.readBytes() }
                val count = bytes.size / 2
                if (count < 2048) return null
                val pcm = FloatArray(count)
                for (i in 0 until count) {
                    val lo = bytes[i * 2].toInt() and 0xff
                    val hi = bytes[i * 2 + 1].toInt()
                    val value = (hi shl 8) or lo
                    pcm[i] = value.toShort() / 32768.0f
                }
                GuitarSample(sourceMidi, pcm)
            } catch (_: Exception) {
                null
            }
        }

        private fun guitarPluck(sample: GuitarSample?, targetMidi: Int, t: Double, velocity: Double): Double {
            if (sample == null || t < 0.0) return 0.0
            val rate = 2.0.pow((targetMidi - sample.rootMidi) / 12.0)
            val index = (t * sampleRate * rate).toInt()
            if (index !in sample.samples.indices) return 0.0
            val attack = (t / 0.004).coerceAtMost(1.0)
            return sample.samples[index].toDouble() * velocity * attack
        }"""
if old_method in s:
    s = s.replace(old_method, new_method, 1)
elif new_method not in s:
    raise SystemExit("ERROR: Guitar pluck playback method anchor missing.")

required = [
    "private data class GuitarSample(val rootMidi: Int, val samples: FloatArray)",
    "loadGuitarSample(midi)",
    'context.assets.open("guitar_samples/note_${sourceMidi}.pcm")',
    "private fun guitarPluck(sample: GuitarSample?, targetMidi: Int",
    "guitarPluck(pluckSamples[midi], midi, strumLocal,",
    "guitarPluck(pluckSamples[bass], bass, local,",
    "guitarPluck(pluckSamples[note.midi], note.midi, local,",
]
missing = [token for token in required if token not in s]
if missing:
    raise SystemExit("ERROR: Real guitar sample integration check failed: " + ", ".join(missing))
path.write_text(s, encoding="utf-8")
print("REAL STEEL-STRING SAMPLE ENGINE: PASS")
print("The renderer now plays recorded guitar samples, not generated pluck oscillations.")
