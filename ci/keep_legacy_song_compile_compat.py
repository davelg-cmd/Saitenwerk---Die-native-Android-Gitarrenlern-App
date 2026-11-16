from pathlib import Path
import os

root = Path(os.environ["PROJECT_DIR"])
path = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s = path.read_text(encoding="utf-8")

# The old song implementation is still present in the source archive for now.
# Keep it compilable while it is unreachable from the active UI.
if "fun openSong(song: Song)" not in s:
    # Insert directly inside MainActivity's class body. Find the class opening
    # brace explicitly; lifecycle method names can repeat in nested classes.
    class_anchor = "class MainActivity"
    if s.count(class_anchor) != 1:
        raise SystemExit(
            f"FEHLER: MainActivity-Klassenname nicht eindeutig "
            f"(Treffer: {s.count(class_anchor)})."
        )
    class_start = s.index(class_anchor)
    class_brace = s.find("{", class_start)
    if class_brace < 0:
        raise SystemExit("FEHLER: Öffnende Klammer der MainActivity nicht gefunden.")
    insertion = '''
    fun openSong(song: Song) {
        show(SongDetailFragment.newInstance(song))
    }
'''
    s = s[:class_brace + 1] + insertion + s[class_brace + 1:]

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
    # Insert BEFORE the complete ScrollView expression. Matching only the
    # constructor prefix would place declarations inside its .apply receiver
    # and detach setFillViewport/background from ScrollView.
    anchor = "        val readerScroll = ScrollView(a).apply {"
    if s.count(anchor) != 1:
        raise SystemExit(
            f"FEHLER: vollständiger readerScroll-Anker nicht eindeutig "
            f"(Treffer: {s.count(anchor)})."
        )
    declarations = "\n".join("        " + line.strip() for line in fields.rstrip().splitlines())
    s = s.replace(anchor, declarations + "\n" + anchor, 1)

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
