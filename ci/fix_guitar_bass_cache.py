#!/usr/bin/env python3
"""Fix bass-note cache coverage and start the audio clock after synthesis preparation."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

old_start = """                // Start playback immediately. The audio is rendered in small chunks while it plays,
                // so there is no multi-second WAV generation delay before the first note.
                track.play()
                running = true
                onReady(totalDurationMs)

                val chordEvents = timeline.chords.map { Triple(it.chord, it.startMs, it.endMs) }
                val melody = timeline.melody
                // Precompute plucked-string waveforms before playback. This avoids expensive
                // synthesis in the real-time render loop and keeps the first attack immediate.
                val requiredMidi = (melody.map { it.midi } + chordEvents.flatMap { chordToMidi(it.first) }).distinct()
                val pluckSamples = requiredMidi.associateWith { buildPluckSample(it) }
                renderThread = Thread {"""
new_start = """                val chordEvents = timeline.chords.map { Triple(it.chord, it.startMs, it.endMs) }
                val melody = timeline.melody
                // Include bass fundamentals as well as chord tones and melody notes.
                val chordNotes = chordEvents.flatMap { chordToMidi(it.first) }
                val bassNotes = chordEvents.mapNotNull { chordToMidi(it.first).firstOrNull()?.minus(12) }
                val requiredMidi = (melody.map { it.midi } + chordNotes + bassNotes).distinct()
                // Prepare short pluck tables before starting AudioTrack: its playback-head clock
                // must not run ahead while the renderer is still synthesizing its lookup tables.
                val pluckSamples = requiredMidi.associateWith { buildPluckSample(it) }

                // Start the master audio clock only after all required string samples are ready.
                track.play()
                running = true
                onReady(totalDurationMs)

                renderThread = Thread {"""
if old_start in s:
    s = s.replace(old_start, new_start, 1)
elif new_start not in s:
    raise SystemExit("ERROR: audio preparation/start sequence anchor not found.")

checks = [
    "val bassNotes = chordEvents.mapNotNull",
    "val requiredMidi = (melody.map { it.midi } + chordNotes + bassNotes).distinct()",
    "track.play()\n                running = true\n                onReady(totalDurationMs)",
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("ERROR: audio preparation validation failed: " + ", ".join(missing))
path.write_text(s, encoding="utf-8")
print("AUDIO PREPARATION CHECK: PASS")
print("Bass plucks are included in the sample cache.")
print("AudioTrack master clock starts only after all pluck tables are prepared.")
