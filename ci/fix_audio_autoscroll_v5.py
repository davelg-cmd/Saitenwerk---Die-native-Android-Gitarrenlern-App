#!/usr/bin/env python3
"""Harden Songsterr-style playback and auto-scroll after the V4 regression."""
from pathlib import Path
import os
import re

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

# 3) Replace auto-scroll methods robustly. The previous implementation assumed
#    every matching function was a class member; in this generated source one
#    match can be a local function, which makes "private fun" illegal Kotlin.
#    Remove every existing definition, then insert exactly one definition at the
#    same indentation level as stopPlayer().
def remove_all_methods(src, name):
    pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]+)(?:private\s+)?fun "
        + re.escape(name)
        + r"\([^\n]*\)\s*\{"
    )
    while True:
        m = pattern.search(src)
        if not m:
            return src
        brace = src.find("{", m.start())
        depth = 0
        j = brace
        while j < len(src):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    src = src[:m.start()] + src[j + 1:]
                    break
            j += 1
        else:
            raise SystemExit(f"ERROR: Could not parse {name}()")

s = remove_all_methods(s, "startAutoScroll")
s = remove_all_methods(s, "stopAutoScroll")

stop_player = re.search(
    r"(?m)^(?P<indent>[ \t]+)(?:private\s+)?fun stopPlayer\([^\n]*\)\s*\{",
    s,
)
if not stop_player:
    raise SystemExit("ERROR: No class-level insertion point for auto-scroll methods.")

indent = stop_player.group("indent")
child = indent + "    "

start_body = (
    f"{indent}private fun startAutoScroll() {{\n"
    f"{child}if (autoScroll) return\n"
    f"{child}autoScroll = true\n"
    f"{child}resumeAfterTouch = false\n"
    f"{child}lastScrollTime = android.os.SystemClock.uptimeMillis()\n"
    f"{child}scrollRemainder = 0f\n"
    f"{child}scrollRunnable?.let {{ scrollHandler.removeCallbacks(it) }}\n\n"
    f"{child}val runnable = object : Runnable {{\n"
    f"{child}    override fun run() {{\n"
    f"{child}        if (!autoScroll || !isAdded || view == null) return\n"
    f"{child}        val total = playerEngine.duration().coerceAtLeast(1)\n"
    f"{child}        val position = playerEngine.position().coerceIn(0, total)\n"
    f"{child}        val maxY = (readerScroll.getChildAt(0)?.height ?: 0) - readerScroll.height\n"
    f"{child}        if (maxY > 0) {{\n"
    f"{child}            val target = (maxY.toDouble() * position.toDouble() / total.toDouble()).toInt()\n"
    f"{child}            val delta = target - readerScroll.scrollY\n"
    f"{child}            if (kotlin.math.abs(delta) > 1) {{\n"
    f"{child}                readerScroll.smoothScrollBy(0, (delta * 0.18f).toInt().coerceAtLeast(1))\n"
    f"{child}            }}\n"
    f"{child}        }}\n"
    f"{child}        scrollRunnable = this\n"
    f"{child}        scrollHandler.postDelayed(this, 120L)\n"
    f"{child}    }}\n"
    f"{child}}}\n"
    f"{child}scrollRunnable = runnable\n"
    f"{child}scrollHandler.post(runnable)\n"
    f"{indent}}}\n"
)

stop_body = (
    f"{indent}private fun stopAutoScroll() {{\n"
    f"{child}autoScroll = false\n"
    f"{child}scrollRunnable?.let {{ scrollHandler.removeCallbacks(it) }}\n"
    f"{child}scrollRunnable = null\n"
    f"{child}lastScrollTime = 0L\n"
    f"{child}scrollRemainder = 0f\n"
    f"{child}resumeAfterTouch = false\n"
    f"{indent}}}\n"
)

pos = stop_player.start()
s = s[:pos] + start_body + "\n" + stop_body + "\n" + s[pos:]

required = [
    "track.setVolume(1.0f)",
    "if (events.isEmpty())",
    "private fun startAutoScroll()",
    "private fun stopAutoScroll()",
    "scrollHandler.postDelayed(this, 120L)",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit(
        "ERROR: Audio/autoscroll hardening validation failed: " + ", ".join(missing)
    )

path.write_text(s, encoding="utf-8")
print("AUDIO + AUTOSCROLL HARDENING V5.1: PASS")
print("AudioTrack initialization/volume is verified.")
print("Empty timelines receive a restrained audible guitar fallback.")
print("Auto-scroll methods are inserted at the same class level as stopPlayer().")
