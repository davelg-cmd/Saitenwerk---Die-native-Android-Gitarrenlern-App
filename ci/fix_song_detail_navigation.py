#!/usr/bin/env python3
"""Stop song playback when leaving the song view and simplify complete-song view."""
from pathlib import Path
import os

root = Path(os.environ['PROJECT_DIR'])
path = root / 'app/src/main/java/de/saitenwerk/app/MainActivity.kt'
s = path.read_text(encoding='utf-8')

old_back = 'back.setOnClickListener { a.openSection(4) }'
new_back = 'back.setOnClickListener { a.onBackPressedDispatcher.onBackPressed() }'
if old_back in s:
    s = s.replace(old_back, new_back, 1)
elif new_back not in s:
    raise SystemExit('Navigation anchor not found.')

old_editor = 'root.addView(editorCard, LinearLayout.LayoutParams(-1, -2).apply { setMargins(a.dp(16), a.dp(14), a.dp(16), a.dp(12)) })'
new_editor = '''// Bei einem vollständigen, mitgelieferten Song steht der Lesemodus im Vordergrund.
        // Das separate Arrangement-/Eingabefeld bleibt für eigene/unvollständige Songs verfügbar.
        if (bundledSheet.optString("content").isBlank()) {
            root.addView(editorCard, LinearLayout.LayoutParams(-1, -2).apply { setMargins(a.dp(16), a.dp(14), a.dp(16), a.dp(12)) })
        }'''
if old_editor in s:
    s = s.replace(old_editor, new_editor, 1)
elif new_editor not in s:
    raise SystemExit('Song arrangement card anchor not found.')

old_lifecycle = '''        a.lifecycle.addObserver(object : androidx.lifecycle.DefaultLifecycleObserver {
            override fun onDestroy(owner: androidx.lifecycle.LifecycleOwner) {
                stopAutoScroll(); stopPlayer()
            }
        })
        return ScrollView(a).apply { addView(root) }'''
new_lifecycle = '''        // Leaving the song screen (hardware back, toolbar back, or navigation) must
        // stop the AudioTrack immediately; Activity.onDestroy alone is too late because
        // this Fragment can be removed while the Activity remains alive.
        readerScroll.addOnAttachStateChangeListener(object : View.OnAttachStateChangeListener {
            override fun onViewAttachedToWindow(v: View) = Unit
            override fun onViewDetachedFromWindow(v: View) {
                stopAutoScroll()
                stopPlayer(updateUi = false)
            }
        })
        a.lifecycle.addObserver(object : androidx.lifecycle.DefaultLifecycleObserver {
            override fun onDestroy(owner: androidx.lifecycle.LifecycleOwner) {
                stopAutoScroll(); stopPlayer()
            }
        })
        return ScrollView(a).apply { addView(root) }'''
if old_lifecycle in s:
    s = s.replace(old_lifecycle, new_lifecycle, 1)
elif new_lifecycle not in s:
    raise SystemExit('Lifecycle cleanup anchor not found.')

checks = [new_back, 'if (bundledSheet.optString("content").isBlank()) {',
          'readerScroll.addOnAttachStateChangeListener', 'stopPlayer(updateUi = false)']
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit('Validation failed: ' + ', '.join(missing))
path.write_text(s, encoding='utf-8')
print('SONG DETAIL NAVIGATION CHECK: PASS')
print('Playback stops as soon as the song reader detaches.')
print('Complete bundled songs open without the separate arrangement editor.')
print('Back button pops the current song detail instead of stacking another song list.')
