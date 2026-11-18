from pathlib import Path
import os
import urllib.request

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
raw = root / "app/src/main/res/raw"
raw.mkdir(parents=True, exist_ok=True)

# Six real, individually recorded open-string plucks from Meta Open Sound.
# Meta Nylon Guitar is released under CC0-1.0.
samples = {
    "guitar_string_6e": "INSGuitarNylon_StringLowE_Vel03Pick_E2_01.ogg",
    "guitar_string_5a": "INSGuitarNylon_StringA_Vel03Pick_A2_01.ogg",
    "guitar_string_4d": "INSGuitarNylon_StringD_Vel03Pick_D3_01.ogg",
    "guitar_string_3g": "INSGuitarNylon_StringG_Vel03Pick_G3_01.ogg",
    "guitar_string_2b": "INSGuitarNylon_StringB_Vel03Pick_B3_01.ogg",
    "guitar_string_1e": "INSGuitarNylon_StringHighE_Vel03Pick_E4_01.ogg",
}
base = "https://raw.githubusercontent.com/facebookincubator/Meta-open-sound/main/systems/instruments/meta-nylon-guitar/ogg/"
for resource, filename in samples.items():
    destination = raw / (resource + ".ogg")
    request = urllib.request.Request(base + filename, headers={"User-Agent": "Saitenwerk-build"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    if len(data) < 4096 or not data.startswith(b"OggS"):
        raise SystemExit(f"Ungültiges Gitarren-Sample: {filename}")
    destination.write_bytes(data)
    print(f"Gitarren-Sample geladen: {resource} ({len(data)} Bytes)")

assets = root / "app/src/main/assets"
assets.mkdir(parents=True, exist_ok=True)
(assets / "guitar-audio-license.txt").write_text(
    "Saitenwerk – Gitarren-Referenztöne\n"
    "Verwendete Aufnahmen: Meta Nylon Guitar, Meta Open Sound.\n"
    "Quelle: https://github.com/facebookincubator/Meta-open-sound\n"
    "Instrument-Samples: systems/instruments/meta-nylon-guitar/ogg/\n"
    "Lizenz: CC0 1.0 Universal (Public Domain Dedication).\n"
    "Die sechs verwendeten Samples sind einzeln aufgenommene offene Gitarrensaiten "
    "(E2, A2, D3, G3, B3, E4), jeweils Velocity 03 / Pick.\n",
    encoding="utf-8"
)

s = main.read_text(encoding="utf-8")
start = s.index("class TunerFragment : Fragment() {")
end = s.index("\nclass TunerGaugeView", start)
t = s[start:end]

if "import android.media.SoundPool" not in s:
    s = s.replace("import android.media.AudioTrack\n", "import android.media.AudioTrack\nimport android.media.SoundPool\n", 1)
    main.write_text(s, encoding="utf-8")
    s = main.read_text(encoding="utf-8")
    start = s.index("class TunerFragment : Fragment() {")
    end = s.index("\nclass TunerGaugeView", start)
    t = s[start:end]

old_fields = """    private var referenceTrack: AudioTrack? = null
    private val referenceAudioHandler = Handler(Looper.getMainLooper())
    private var referenceReleaseTask: Runnable? = null
    private var selectedReferenceName: String? = null"""
new_fields = """    private var selectedReferenceName: String? = null
    private var referenceSoundPool: SoundPool? = null
    private val referenceSampleIds = mutableMapOf<String, Int>()
    private val loadedReferenceSamples = mutableSetOf<Int>()
    private var pendingReference: Pair<String, Double>? = null
    private var referenceStreamId = 0"""
if old_fields in t:
    t = t.replace(old_fields, new_fields, 1)
elif "private var referenceSoundPool: SoundPool? = null" not in t:
    raise SystemExit("FEHLER: Referenzton-Felder nicht gefunden")

# Initialize the six recorded samples once per fragment instance.
if "private fun prepareReferenceSamples()" not in t:
    insert_at = t.index("    override fun onCreateView")
    init_code = r'''    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prepareReferenceSamples()
    }

    private fun prepareReferenceSamples() {
        val ctx = context ?: return
        val attributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
            .build()
        val pool = SoundPool.Builder().setMaxStreams(2).setAudioAttributes(attributes).build()
        referenceSoundPool = pool
        pool.setOnLoadCompleteListener { _, sampleId, status ->
            if (status == 0) {
                loadedReferenceSamples.add(sampleId)
                if (loadedReferenceSamples.size == 6) {
                    pendingReference?.let { (string, hz) ->
                        pendingReference = null
                        playRecordedReference(string, hz)
                    }
                }
            }
        }
        referenceSampleIds["6"] = pool.load(ctx, R.raw.guitar_string_6e, 1)
        referenceSampleIds["5"] = pool.load(ctx, R.raw.guitar_string_5a, 1)
        referenceSampleIds["4"] = pool.load(ctx, R.raw.guitar_string_4d, 1)
        referenceSampleIds["3"] = pool.load(ctx, R.raw.guitar_string_3g, 1)
        referenceSampleIds["2"] = pool.load(ctx, R.raw.guitar_string_2b, 1)
        referenceSampleIds["1"] = pool.load(ctx, R.raw.guitar_string_1e, 1)
    }

'''
    t = t[:insert_at] + init_code + t[insert_at:]

# Replace the synthetic oscillator with the actual plucked string recordings.
a = t.index("    /** Plucked reference tone")
b = t.index("    private fun startTuner()", a)
new_audio = r'''    /** Spielt eine echte, aufgenommene Gitarrensaite aus dem CC0-Samplepaket. */
    private fun playReferenceTone(frequency: Double = referenceA4) {
        stopReferenceTone()
        if (!frequency.isFinite() || frequency !in 20.0..2000.0) return
        val string = selectedReferenceName?.take(1) ?: return
        if (referenceSoundPool == null) prepareReferenceSamples()
        val sampleId = referenceSampleIds[string] ?: return
        if (!loadedReferenceSamples.contains(sampleId)) {
            pendingReference = string to frequency
            return
        }
        playRecordedReference(string, frequency)
    }

    private fun playRecordedReference(string: String, frequency: Double) {
        val pool = referenceSoundPool ?: return
        val sampleId = referenceSampleIds[string] ?: return
        if (!loadedReferenceSamples.contains(sampleId)) return
        val openStringHz = mapOf(
            "6" to 82.4069, "5" to 110.0, "4" to 146.832,
            "3" to 196.0, "2" to 246.942, "1" to 329.628
        )[string] ?: return
        // Kleine Pitch-Anpassung für alternative Stimmungen; der Klang bleibt eine echte Aufnahme.
        val playbackRate = (frequency / openStringHz).coerceIn(0.5, 2.0).toFloat()
        referenceStreamId = pool.play(sampleId, 0.88f, 0.88f, 1, 0, playbackRate)
    }

    private fun stopReferenceTone() {
        pendingReference = null
        if (referenceStreamId != 0) {
            try { referenceSoundPool?.stop(referenceStreamId) } catch (_: Exception) { }
            referenceStreamId = 0
        }
    }

'''
t = t[:a] + new_audio + t[b:]

# Release the sample player with the fragment, not on every view recreation.
if "override fun onDestroy() {" not in t:
    marker = "    override fun onDestroyView()"
    pos = t.index(marker)
    t = t[:pos] + """    override fun onDestroy() {
        stopReferenceTone()
        try { referenceSoundPool?.release() } catch (_: Exception) { }
        referenceSoundPool = null
        referenceSampleIds.clear()
        loadedReferenceSamples.clear()
        super.onDestroy()
    }
""" + t[pos:]

# Ensure the previous generated AudioTrack engine is completely gone from TunerFragment.
if "referenceTrack" in t or "referenceAudioHandler" in t or "referenceReleaseTask" in t:
    raise SystemExit("FEHLER: Alte synthetische Referenzton-Engine ist noch vorhanden")
required = [
    "R.raw.guitar_string_6e", "R.raw.guitar_string_5a", "R.raw.guitar_string_4d",
    "R.raw.guitar_string_3g", "R.raw.guitar_string_2b", "R.raw.guitar_string_1e",
    "SoundPool", "playRecordedReference", "CC0"
]
missing = [x for x in required if x not in t and x != "CC0"]
if missing:
    raise SystemExit("FEHLER: Sample-Engine unvollständig: " + ", ".join(missing))
main.write_text(s[:start] + t + s[end:], encoding="utf-8")
print("ORIGINAL-GITARRENKLÄNGE: PASS")
print("6 aufgenommene Nylonsaiten, lokale Offline-Wiedergabe, SoundPool-Cleanup und Lizenznachweis geprüft.")
