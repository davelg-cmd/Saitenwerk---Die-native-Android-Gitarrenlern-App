#!/usr/bin/env python3
"""Apply the deterministic SongTimeline migration to the Alpha 7 source archive."""
from pathlib import Path
import os

root = Path(os.environ.get("PROJECT_DIR", ""))
source_path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
if not source_path.is_file():
    raise SystemExit(f"ERROR: MainActivity.kt not found: {source_path}")
s = source_path.read_text(encoding="utf-8")

if "private data class SongTimeline(" in s:
    required = [
        "timeline: SongTimeline,",
        "fun buildPlayerTimeline(raw: String): SongTimeline",
        "currentTimeline?.chordIndexAt(position.toLong())",
        "currentTimeline?.progressAt(position.toLong())",
    ]
    missing = [item for item in required if item not in s]
    if missing:
        raise SystemExit("ERROR: Partial SongTimeline migration detected: " + ", ".join(missing))
    print("SongTimeline migration already present and validated; no changes needed.")
    raise SystemExit(0)

replacements = [
("""    private data class PlayerNote(val midi: Int, val startMs: Long, val durationMs: Long, val velocity: Float = 0.72f)

    private class GuitarPlayerEngine""",
"""    private data class PlayerNote(val midi: Int, val startMs: Long, val durationMs: Long, val velocity: Float = 0.72f)

    /** One immutable timing model for audio, chord highlighting, progress and reader sync. */
    private data class SongTimeline(
        val tempoBpm: Int,
        val chords: List<ChordEvent>,
        val melody: List<PlayerNote>,
        val durationMs: Long
    ) {
        data class ChordEvent(val chord: String, val startMs: Long, val endMs: Long)

        fun chordIndexAt(positionMs: Long): Int =
            chords.indexOfFirst { positionMs >= it.startMs && positionMs < it.endMs }

        fun progressAt(positionMs: Long): Int =
            ((positionMs.coerceIn(0L, durationMs.coerceAtLeast(1L)) * 100L) / durationMs.coerceAtLeast(1L)).toInt().coerceIn(0, 100)
    }

    private class GuitarPlayerEngine"""),
("""        fun play(
            chords: List<Pair<String, Long>>,
            melody: List<PlayerNote>,
            tempoBpm: Int,
            onReady: (Int) -> Unit,
            onCompleted: () -> Unit,
            onError: (Throwable) -> Unit
        ) {
            stop()
            cancelled = false
            val beatMs = 60_000.0 / tempoBpm.coerceIn(40, 180)
            val lastChordEnd = chords.maxOfOrNull { it.second } ?: 0L
            val lastNoteEnd = melody.maxOfOrNull { it.startMs + it.durationMs } ?: 0L
            totalDurationMs = maxOf(lastChordEnd + (beatMs * 2.0).toLong(), lastNoteEnd + 450L).toInt().coerceAtLeast(1000)""",
"""        fun play(
            timeline: SongTimeline,
            onReady: (Int) -> Unit,
            onCompleted: () -> Unit,
            onError: (Throwable) -> Unit
        ) {
            stop()
            cancelled = false
            val beatMs = 60_000.0 / timeline.tempoBpm.coerceIn(40, 180)
            totalDurationMs = timeline.durationMs.toInt().coerceAtLeast(1000)"""),
("""                val chordEvents = chords.mapIndexed { index, pair ->
                    val end = chords.getOrNull(index + 1)?.second ?: totalDurationMs.toLong()
                    Triple(pair.first, pair.second, end)
                }""",
"""                val chordEvents = timeline.chords.map { Triple(it.chord, it.startMs, it.endMs) }
                val melody = timeline.melody"""),
("""        var chordEvents = emptyList<PlayerChordEvent>()
        var activeChordIndex = -1""",
"""        var chordEvents = emptyList<PlayerChordEvent>()
        var currentTimeline: SongTimeline? = null
        var activeChordIndex = -1"""),
("""        fun buildPlayerTimeline(raw: String): Pair<List<Pair<String, Long>>, List<PlayerNote>> {
            val beat = 60_000L / playerTempo
            var cursor = 0L
            val timeline = mutableListOf<Pair<String, Long>>()
            parseLines(raw).forEach { line ->
                val chords = line.parts.map { it.first }.filter { it.isNotBlank() }
                if (chords.isEmpty()) cursor += beat * 2
                else {
                    val perChord = (beat * 2).coerceAtLeast(beat)
                    chords.forEach { chord -> timeline.add(chord to cursor); cursor += perChord }
                }
            }
            return timeline to melodyForSong(song.title, timeline, playerTempo)
        }""",
"""        fun buildPlayerTimeline(raw: String): SongTimeline {
            val beat = 60_000L / playerTempo
            var cursor = 0L
            val chordStarts = mutableListOf<Pair<String, Long>>()
            parseLines(raw).forEach { line ->
                val lineChords = line.parts.map { it.first }.filter { it.isNotBlank() }
                if (lineChords.isEmpty()) cursor += beat * 2
                else {
                    val perChord = (beat * 2).coerceAtLeast(beat)
                    lineChords.forEach { chord -> chordStarts.add(chord to cursor); cursor += perChord }
                }
            }
            val chordEvents = chordStarts.mapIndexed { index, item ->
                SongTimeline.ChordEvent(item.first, item.second, chordStarts.getOrNull(index + 1)?.second ?: cursor)
            }
            val melody = melodyForSong(song.title, chordStarts, playerTempo)
            val lastNoteEnd = melody.maxOfOrNull { it.startMs + it.durationMs } ?: 0L
            val duration = maxOf(cursor + beat * 2, lastNoteEnd + 450L, 1000L)
            return SongTimeline(playerTempo, chordEvents, melody, duration)
        }"""),
("""            val (timeline, melody) = buildPlayerTimeline(raw)
            val bpm = playerTempo""",
"""            val timeline = buildPlayerTimeline(raw)
            currentTimeline = timeline
            val bpm = timeline.tempoBpm"""),
("""            playerEngine.play(
                chords = timeline,
                melody = melody,
                tempoBpm = bpm,
                onReady = { duration ->""",
"""            playerEngine.play(
                timeline = timeline,
                onReady = { duration ->"""),
("""            val events = mutableListOf<PlayerChordEvent>()
            var fakeTime = 0L
            parseLines(raw).forEach { line ->""",
"""            val events = mutableListOf<PlayerChordEvent>()
            val timeline = buildPlayerTimeline(raw)
            currentTimeline = timeline
            var timelineChordIndex = 0
            parseLines(raw).forEach { line ->"""),
("""                    readerContent.addView(TextView(a).apply { text = " "; textSize = 8f }); fakeTime += (60_000L / playerTempo) * 2L""",
"""                    readerContent.addView(TextView(a).apply { text = " "; textSize = 8f })"""),
("""                            events.add(PlayerChordEvent(chord, fakeTime, fakeTime + durationPerChord, chordView))
                            fakeTime += durationPerChord""",
"""                            val timing = timeline.chords.getOrNull(timelineChordIndex++)
                            if (timing != null) events.add(PlayerChordEvent(chord, timing.startMs, timing.endMs, chordView))"""),
("""                    if (chordCount == 0) fakeTime += durationPerChord
                    readerContent.addView(row)""",
"""                    readerContent.addView(row)"""),
("""                                val active = chordEvents.indexOfFirst { position >= it.startMs && position < it.endMs }
                                highlightChord(active)""",
"""                                val active = currentTimeline?.chordIndexAt(position.toLong()) ?: -1
                                highlightChord(active)"""),
("""                                progress.setProgress((position * 100 / durationMs).coerceIn(0, 100))""",
"""                                progress.setProgress(currentTimeline?.progressAt(position.toLong()) ?: (position * 100 / durationMs).coerceIn(0, 100))""")
]

for old, new in replacements:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"ERROR: Expected exactly one patch anchor, found {count}: {old[:100]!r}")
    s = s.replace(old, new, 1)

source_path.write_text(s, encoding="utf-8")
checks = [
    "private data class SongTimeline(",
    "timeline: SongTimeline,",
    "fun buildPlayerTimeline(raw: String): SongTimeline",
    "currentTimeline = timeline",
    "currentTimeline?.chordIndexAt(position.toLong())",
    "currentTimeline?.progressAt(position.toLong())",
]
missing = [check for check in checks if check not in s]
if missing:
    raise SystemExit("ERROR: SongTimeline post-validation failed: " + ", ".join(missing))
print("SongTimeline migration applied and validated.")
print("Audio engine, chord highlighting and progress now consume one immutable timing model.")
