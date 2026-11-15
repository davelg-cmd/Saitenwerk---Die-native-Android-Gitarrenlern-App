#!/usr/bin/env python3
"""Replace additive sine plucks with a precomputed Karplus-Strong string model."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

old = """                val chordEvents = timeline.chords.map { Triple(it.chord, it.startMs, it.endMs) }
                val melody = timeline.melody
                renderThread = Thread {"""
new = """                val chordEvents = timeline.chords.map { Triple(it.chord, it.startMs, it.endMs) }
                val melody = timeline.melody
                // Precompute plucked-string waveforms before playback. This avoids expensive
                // synthesis in the real-time render loop and keeps the first attack immediate.
                val requiredMidi = (melody.map { it.midi } + chordEvents.flatMap { chordToMidi(it.first) }).distinct()
                val pluckSamples = requiredMidi.associateWith { buildPluckSample(it) }
                renderThread = Thread {"""
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("ERROR: pluck cache insertion anchor not found.")

changes = [
("""                                            sample += guitarPluck(midi, local, if (idx == 0) 0.31 else 0.24, 0.95 - idx * 0.08)""",
 """                                            val strumLocal = local - idx * 0.012
                                            if (strumLocal >= 0.0) sample += guitarPluck(pluckSamples[midi], strumLocal, if (idx == 0) 0.31 else 0.24)"""),
("""                                            sample += guitarPluck(bass, local, 0.20, 0.78)""",
 """                                            sample += guitarPluck(pluckSamples[bass], local, 0.20)"""),
("""                                        sample += guitarPluck(note.midi, local, note.velocity.toDouble() * 0.64, 1.08)""",
 """                                        sample += guitarPluck(pluckSamples[note.midi], local, note.velocity.toDouble() * 0.64)"""),
]
for old, new in changes:
    if old in s:
        s = s.replace(old, new, 1)
    elif new not in s:
        raise SystemExit("ERROR: guitar pluck call-site anchor not found: " + old[:80])

old_method = """        private fun guitarPluck(midi: Int, t: Double, velocity: Double, brightness: Double): Double {
            if (t < 0.0) return 0.0
            val f = midiToHz(midi)
            // Inharmonische Teiltöne + kurzer Anschlag + schneller Verlust der hohen
            // Frequenzen. Das vermeidet den "Game-Sound" eines reinen Oszillators.
            val attack = (t / 0.0038).coerceAtMost(1.0)
            val fundamentalDecay = exp(-t * (2.35 + f / 2300.0))
            val phase = 2.0 * PI * f * t
            val p2 = 2.0 * PI * (f * 2.006) * t
            val p3 = 2.0 * PI * (f * 3.011) * t
            val p4 = 2.0 * PI * (f * 4.018) * t
            val p5 = 2.0 * PI * (f * 5.027) * t
            val body = sin(phase) * 0.56 +
                sin(p2 + 0.08) * (0.25 * brightness) * exp(-t * 4.7) +
                sin(p3 + 0.17) * (0.115 * brightness) * exp(-t * 7.2) +
                sin(p4 + 0.29) * (0.052 * brightness) * exp(-t * 10.0) +
                sin(p5 + 0.41) * (0.018 * brightness) * exp(-t * 13.5)
            val pickNoise = (sin(phase * 31.0 + 0.7) + sin(phase * 47.0 + 2.1)) * exp(-t * 150.0) * 0.010
            val wood = sin(2.0 * PI * (f * 0.497) * t + 0.9) * exp(-t * 18.0) * 0.010
            return (body * fundamentalDecay + pickNoise + wood) * attack * velocity
        }

        private fun midiToHz(midi: Int): Double = 440.0 * 2.0.pow((midi - 69) / 12.0)"""
new_method = """        /** Generate a naturally decaying plucked-string waveform using the Karplus-Strong
         * waveguide model. Unlike stacked sine oscillators, the delay-line feedback naturally
         * loses high-frequency energy and produces a softer, string-like decay. */
        private fun buildPluckSample(midi: Int): FloatArray {
            val frequency = midiToHz(midi)
            val delay = (sampleRate / frequency).roundToInt().coerceIn(2, sampleRate / 2)
            val line = FloatArray(delay)
            var random = (midi.toLong() * 7919L + 104729L) and 0x7fffffffL
            for (i in line.indices) {
                random = (random * 1103515245L + 12345L) and 0x7fffffffL
                line[i] = ((random.toDouble() / 1073741823.5) - 1.0).toFloat() * 0.72f
            }
            val output = FloatArray(sampleRate * 2)
            var cursor = 0
            for (i in output.indices) {
                val current = line[cursor]
                val next = line[(cursor + 1) % delay]
                // A slightly weighted averaging filter models string damping and warmth.
                line[cursor] = (current * 0.54f + next * 0.46f) * 0.99955f
                output[i] = current
                cursor = (cursor + 1) % delay
            }
            return output
        }

        private fun guitarPluck(samples: FloatArray?, t: Double, velocity: Double): Double {
            if (samples == null || t < 0.0) return 0.0
            val index = (t * sampleRate).toInt()
            if (index !in samples.indices) return 0.0
            return samples[index].toDouble() * velocity
        }

        private fun midiToHz(midi: Int): Double = 440.0 * 2.0.pow((midi - 69) / 12.0)"""
if old_method in s:
    s = s.replace(old_method, new_method, 1)
elif new_method not in s:
    raise SystemExit("ERROR: old guitarPluck synthesis function not found.")

required = [
    "val pluckSamples = requiredMidi.associateWith { buildPluckSample(it) }",
    "private fun buildPluckSample(midi: Int): FloatArray",
    "private fun guitarPluck(samples: FloatArray?",
    "val strumLocal = local - idx * 0.012",
]
missing = [token for token in required if token not in s]
if missing:
    raise SystemExit("ERROR: plucked-string model validation failed: " + ", ".join(missing))
path.write_text(s, encoding="utf-8")
print("KARPLUS-STRONG AUDIO MODEL: PASS")
print("Pluck samples are precomputed before playback; chord strings are lightly staggered.")
