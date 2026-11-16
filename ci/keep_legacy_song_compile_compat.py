from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

# The old song implementation is still present in the source archive for now.
# Keep it compilable while it is unreachable from the active UI.
if "fun openSong(song: Song)" not in s:
    # MainActivity is a class. Insert the compatibility entry point immediately
    # before onCreate so it is always at class scope, independent of navigation
    # helper names in the archived source.
    anchor = 'override fun onCreate'
    if s.count(anchor) != 1:
        raise SystemExit(
            f"FEHLER: onCreate()-Anker für legacy openSong nicht eindeutig "
            f"(Treffer: {s.count(anchor)})."
        )
    s = s.replace(
        anchor,
        '''fun openSong(song: Song) {
            show(SongDetailFragment.newInstance(song))
        }

        ''' + anchor,
        1
    )

fields = '''private var autoScroll: Boolean = false
        private var scrollRunnable: Runnable? = null
        private val scrollHandler = Handler(Looper.getMainLooper())
        private var lastScrollTime: Long = 0L
        private var scrollRemainder: Float = 0f
        private var resumeAfterTouch: Boolean = false
'''
# In this archive SongDetail is implemented as a local-function scope. The fields
# therefore must be local vars, not class members.
fields = fields.replace("private var ", "var ").replace("private val ", "val ")

if "var autoScroll: Boolean = false" not in s:
    anchor = "val readerScroll = ScrollView(a)"
    if anchor not in s:
        raise SystemExit("FEHLER: readerScroll-Anker für Legacy-Songstatus nicht gefunden.")
    s = s.replace(anchor, anchor + "\n        " + fields.rstrip().replace("\n", "\n        "), 1)

checks = [
    "fun openSong(song: Song)",
    "var autoScroll: Boolean = false",
    "var scrollRunnable: Runnable? = null",
    "val scrollHandler = Handler(Looper.getMainLooper())",
    "var lastScrollTime: Long = 0L",
    "var scrollRemainder: Float = 0f",
    "var resumeAfterTouch: Boolean = false",
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("FEHLER: Legacy-Song-Kompatibilität unvollständig: " + ", ".join(missing))

path.write_text(s, encoding="utf-8")
print("LEGACY SONG COMPILE COMPATIBILITY: PASS")
print("Lieder bleiben aus der aktiven UI entfernt; alter Quellcode bleibt vorerst kompilierbar.")
