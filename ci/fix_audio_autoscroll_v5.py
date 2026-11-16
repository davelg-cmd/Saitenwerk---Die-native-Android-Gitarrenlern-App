#!/usr/bin/env python3
"""Harden Songsterr-style playback and auto-scroll after the V4 regression."""
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

# 1) Make AudioTrack initialization explicit and audible.
anchor = """                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .build()

                audioTrack = track
"""
replacement = """                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .build()

                if (track.state != AudioTrack.STATE_INITIALIZED) {
                    try { track.release() } catch (_: Exception) {}
                    throw IllegalStateException("AudioTrack konnte nicht initialisiert werden.")
                }
                track.setVolume(1.0f)
                audioTrack = track
"""
if anchor in s:
    s = s.replace(anchor, replacement, 1)
elif replacement not in s:
    raise SystemExit("ERROR: AudioTrack initialization anchor not found.")

# 2) Guarantee an audible event even for songs whose chord/melody data is sparse.
anchor = """                val events = buildEvents(timeline, chords, voicings, beatMs)

                track.play()
"""
replacement = """                var events = buildEvents(timeline, chords, voicings, beatMs)
                if (events.isEmpty()) {
                    val fallbackMidi = 52
                    val fallbackStep = beatMs.toLong().coerceAtLeast(250L)
                    val fallback = ArrayList<Event>()
                    var t = 0L
                    while (t < totalDurationMs) {
                        fallback.add(Event(t, fallbackMidi, 0.18, 0.0, (beatMs * 0.9).toLong()))
                        t += fallbackStep
                    }
                    events = fallback
                }

                track.play()
"""
if anchor in s:
    s = s.replace(anchor, replacement, 1)
elif replacement not in s:
    raise SystemExit("ERROR: Guitar event playback anchor not found.")

# 3) Replace broken auto-scroll implementations with a simple timeline-following
#    implementation. It uses only readerScroll + playerEngine, both already owned
#    by SongDetailFragment, and avoids recursive Handler callbacks.
def replace_method(src, name, body):
    pattern = re.compile(r"(?m)^        (?:private )?fun " + re.escape(name) + r"\([^\n]*\)\s*\{")
    m = pattern.search(src)
    if not m:
        return None
    i = m.start()
    brace = src.find("{", m.start())
    depth = 0
    j = brace
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[:i] + body + src[j+1:]
        j += 1
    raise SystemExit(f"ERROR: Could not parse {name}()")

start_body = """        private fun startAutoScroll() {
            if (autoScroll) return
            autoScroll = true
            resumeAfterTouch = false
            lastScrollTime = android.os.SystemClock.uptimeMillis()
            scrollRemainder = 0f
            scrollRunnable?.let { scrollHandler.removeCallbacks(it) }

            val runnable = object : Runnable {
                override fun run() {
                    if (!autoScroll || !isAdded || view == null) return
                    val total = playerEngine.duration().coerceAtLeast(1)
                    val position = playerEngine.position().coerceIn(0, total)
                    val maxY = (readerScroll.getChildAt(0)?.height ?: 0) - readerScroll.height
                    if (maxY > 0) {
                        val target = (maxY.toDouble() * position.toDouble() / total.toDouble()).toInt()
                        val delta = target - readerScroll.scrollY
                        if (kotlin.math.abs(delta) > 1) readerScroll.smoothScrollBy(0, (delta * 0.18f).toInt().coerceAtLeast(1))
                    }
                    scrollRunnable = this
                    scrollHandler.postDelayed(this, 120L)
                }
            }
            scrollRunnable = runnable
            scrollHandler.post(runnable)
        }
"""
stop_body = """        private fun stopAutoScroll() {
            autoScroll = false
            scrollRunnable?.let { scrollHandler.removeCallbacks(it) }
            scrollRunnable = null
            lastScrollTime = 0L
            scrollRemainder = 0f
            resumeAfterTouch = false
        }
"""
new_s = replace_method(s, "startAutoScroll", start_body)
if new_s is not None:
    s = new_s
else:
    # Insert before stopPlayer if the old method was missing.
    marker = "        fun stopPlayer("
    pos = s.find(marker)
    if pos < 0:
        raise SystemExit("ERROR: No insertion point for startAutoScroll().")
    s = s[:pos] + start_body + "\n" + s[pos:]

new_s = replace_method(s, "stopAutoScroll", stop_body)
if new_s is not None:
    s = new_s
else:
    marker = "        fun stopPlayer("
    pos = s.find(marker)
    if pos < 0:
        raise SystemExit("ERROR: No insertion point for stopAutoScroll().")
    s = s[:pos] + stop_body + "\n" + s[pos:]

required = [
    "track.setVolume(1.0f)",
    "if (events.isEmpty())",
    "private fun startAutoScroll()",
    "private fun stopAutoScroll()",
    "scrollHandler.postDelayed(this, 120L)",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("ERROR: Audio/autoscroll hardening validation failed: " + ", ".join(missing))

path.write_text(s, encoding="utf-8")
print("AUDIO + AUTOSCROLL HARDENING: PASS")
print("AudioTrack initialization/volume is verified.")
print("Empty timelines receive a restrained audible guitar fallback.")
print("Auto-scroll follows actual player position and uses one cancellable Runnable.")
