#!/usr/bin/env python3
"""Stop active playback before rebuilding the reader's timeline after edits."""
from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

old_state = """        var chordEvents = emptyList<PlayerChordEvent>()
        var currentTimeline: SongTimeline? = null
        var activeChordIndex = -1"""
new_state = """        var chordEvents = emptyList<PlayerChordEvent>()
        var currentTimeline: SongTimeline? = null
        var playerStatusView: TextView? = null
        var playerButtonView: Button? = null
        var playerProgressView: ProgressBar? = null
        var activeChordIndex = -1"""

if old_state in s:
    s = s.replace(old_state, new_state, 1)
elif new_state not in s:
    raise SystemExit("ERROR: Player state insertion anchor not found.")

old_stop = """        fun stopPlayer() {
            playerEngine.stop()
            playerPlaying = false
            playerPrepared = false
            playerProgressRunnable?.let { scrollHandler.removeCallbacks(it) }
            playerProgressRunnable = null
            resetChordHighlight()
        }"""
new_stop = """        fun stopPlayer(updateUi: Boolean = false) {
            playerEngine.stop()
            playerPlaying = false
            playerPrepared = false
            playerProgressRunnable?.let { scrollHandler.removeCallbacks(it) }
            playerProgressRunnable = null
            resetChordHighlight()
            if (updateUi) {
                playerButtonView?.isEnabled = true
                playerButtonView?.text = "Start"
                playerProgressView?.setProgress(0)
                playerStatusView?.text = "Player gestoppt · Songblatt geändert"
                stopAutoScroll()
            }
        }"""

if old_stop in s:
    s = s.replace(old_stop, new_stop, 1)
elif new_stop not in s:
    raise SystemExit("ERROR: stopPlayer function anchor not found.")

old_render = """        fun renderReader() {
            readerContent.removeAllViews(); chordEvents = emptyList(); activeChordIndex = -1"""
new_render = """        fun renderReader() {
            // The audio thread owns the timeline captured at start. Never replace the
            // reader's timing model underneath it when lyrics/chords/settings change.
            if (playerPrepared || playerPlaying) stopPlayer(updateUi = true)
            readerContent.removeAllViews(); chordEvents = emptyList(); activeChordIndex = -1"""

if old_render in s:
    s = s.replace(old_render, new_render, 1)
elif new_render not in s:
    raise SystemExit("ERROR: renderReader guard anchor not found.")

old_status = """        val playerStatus = TextView(a).apply { text = "Bereit · Originaltempo ${playerTempo} BPM"; textSize = 13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(8), 0, a.dp(5)) }
        reader.addView(playerStatus)"""
new_status = """        val playerStatus = TextView(a).apply { text = "Bereit · Originaltempo ${playerTempo} BPM"; textSize = 13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0, a.dp(8), 0, a.dp(5)) }
        playerStatusView = playerStatus
        reader.addView(playerStatus)"""

if old_status in s:
    s = s.replace(old_status, new_status, 1)
elif new_status not in s:
    raise SystemExit("ERROR: player status reference anchor not found.")

old_progress = """        reader.addView(playerProgress, LinearLayout.LayoutParams(-1, a.dp(8)))"""
new_progress = """        playerProgressView = playerProgress
        reader.addView(playerProgress, LinearLayout.LayoutParams(-1, a.dp(8)))"""

if old_progress in s:
    s = s.replace(old_progress, new_progress, 1)
elif new_progress not in s:
    raise SystemExit("ERROR: player progress reference anchor not found.")

old_button = """        reader.addView(startButton, LinearLayout.LayoutParams(-1, a.dp(52)).apply { topMargin = a.dp(8) })"""
new_button = """        playerButtonView = startButton
        reader.addView(startButton, LinearLayout.LayoutParams(-1, a.dp(52)).apply { topMargin = a.dp(8) })"""

if old_button in s:
    s = s.replace(old_button, new_button, 1)
elif new_button not in s:
    raise SystemExit("ERROR: player button reference anchor not found.")

checks = [
    "var playerStatusView: TextView? = null",
    "var playerButtonView: Button? = null",
    "var playerProgressView: ProgressBar? = null",
    "fun stopPlayer(updateUi: Boolean = false)",
    "if (playerPrepared || playerPlaying) stopPlayer(updateUi = true)",
    "playerStatusView = playerStatus",
    "playerProgressView = playerProgress",
    "playerButtonView = startButton",
]
missing = [item for item in checks if item not in s]
if missing:
    raise SystemExit("ERROR: Timeline edit guard validation failed: " + ", ".join(missing))

path.write_text(s, encoding="utf-8")
print("TIMELINE EDIT GUARD: PASS")
print("Active playback stops before the reader timeline is rebuilt.")
print("The Start button, status and progress UI are reset consistently.")
