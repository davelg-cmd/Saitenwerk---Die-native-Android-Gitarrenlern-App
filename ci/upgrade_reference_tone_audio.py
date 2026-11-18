from pathlib import Path
import os
p=Path(os.environ["PROJECT_DIR"])/"app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s=p.read_text(encoding="utf-8")
a=s.index("class TunerFragment : Fragment() {"); b=s.index("\nclass TunerGaugeView",a); t=s[a:b]
needle="    private var referenceTrack: AudioTrack? = null"
fields="""    private var referenceTrack: AudioTrack? = null
    private val referenceAudioHandler = Handler(Looper.getMainLooper())
    private var referenceReleaseTask: Runnable? = null
    private var selectedReferenceName: String? = null"""
if "private val referenceAudioHandler" not in t:
    if needle in t:
        t=t.replace(needle,fields,1)
    else:
        raise SystemExit("Audio-State fehlt")
x=t.index("    private fun rebuildStringButtons() {"); y=t.index("\n    private fun startTuner()",x)
block=r'''    private fun rebuildStringButtons() {
        val panel = stringPanel ?: return
        panel.removeAllViews()
        val list = targets()
        if (list.isEmpty()) {
            panel.addView(TextView(requireContext()).apply {
                text = "Chromatisch · keine Zielsaiten"; textSize = 12f
                gravity = Gravity.CENTER; setTextColor(requireContext().getColor(R.color.sw_muted))
            })
            return
        }
        list.forEach { target ->
            val selected = selectedReferenceName == target.name
            val button = TextView(requireContext()).apply {
                text = target.name + "\n" + "%.1f".format(target.hz) + " Hz"
                textSize = 11.5f; gravity = Gravity.CENTER; includeFontPadding = false
                setLineSpacing(0f, 1.05f); setTypeface(typeface, android.graphics.Typeface.BOLD)
                setTextColor(if (selected) android.graphics.Color.WHITE else requireContext().getColor(R.color.sw_text))
                minHeight = (54 * resources.displayMetrics.density).toInt()
                isClickable = true; isFocusable = true
                contentDescription = "Referenzton Saite " + target.name + ", " + "%.1f".format(target.hz) + " Hertz abspielen"
                background = android.graphics.drawable.GradientDrawable().apply {
                    shape = android.graphics.drawable.GradientDrawable.RECTANGLE
                    cornerRadius = 11f * resources.displayMetrics.density
                    setColor(if (selected) requireContext().getColor(R.color.sw_copper) else requireContext().getColor(R.color.sw_surface2))
                    setStroke(((if (selected) 2f else 1f) * resources.displayMetrics.density).toInt(),
                        if (selected) requireContext().getColor(R.color.sw_copper) else requireContext().getColor(R.color.sw_outline))
                }
                setPadding(2, 5, 2, 5)
                setOnClickListener {
                    selectedReferenceName = target.name
                    targetView?.text = "Referenzton · " + target.name + " · " + "%.1f".format(target.hz) + " Hz"
                    rebuildStringButtons()
                    playReferenceTone(target.hz)
                }
            }
            panel.addView(button, LinearLayout.LayoutParams(0, -1, 1f).apply {
                val m = (3f * resources.displayMetrics.density).roundToInt()
                setMargins(m, 0, m, 0)
            })
        }
    }

    /** Plucked reference tone with natural harmonics and click-free envelope. */
    private fun playReferenceTone(frequency: Double = referenceA4) {
        stopReferenceTone()
        val ctx = context ?: return
        if (!frequency.isFinite() || frequency !in 20.0..2000.0) return
        try {
            val rate = 48000
            val seconds = 2.35
            val pcm = ShortArray((rate * seconds).toInt())
            val harmonics = doubleArrayOf(1.0, 0.48, 0.25, 0.13, 0.075, 0.035)
            val phases = DoubleArray(harmonics.size)
            for (i in pcm.indices) {
                val time = i.toDouble() / rate
                // 25 ms Vorlauf plus weiche Cosinus-Hüllkurve verhindert Einschaltknacken.
                val attackProgress = ((time - 0.025) / 0.055).coerceIn(0.0, 1.0)
                val attack = 0.5 - 0.5 * kotlin.math.cos(Math.PI * attackProgress)
                val decay = kotlin.math.exp(-1.55 * time)
                // Auch das Ende läuft mit einer glatten Kurve vollständig auf null.
                val tailProgress = ((seconds - time) / 0.12).coerceIn(0.0, 1.0)
                val tail = 0.5 - 0.5 * kotlin.math.cos(Math.PI * tailProgress)
                var sample = 0.0
                for (h in harmonics.indices) {
                    phases[h] += 2.0 * Math.PI * frequency * (h + 1) / rate
                    sample += harmonics[h] * kotlin.math.sin(phases[h])
                }
                pcm[i] = (sample * attack * decay * tail * 0.34 * Short.MAX_VALUE)
                    .toInt().coerceIn(Short.MIN_VALUE.toInt(), Short.MAX_VALUE.toInt()).toShort()
            }
            val track = AudioTrack.Builder()
                .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
                .setAudioFormat(AudioFormat.Builder().setSampleRate(rate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
                .setBufferSizeInBytes(pcm.size * 2)
                .setTransferMode(AudioTrack.MODE_STATIC).build()
            if (track.write(pcm, 0, pcm.size) != pcm.size) {
                track.release()
                throw IllegalStateException("Referenzton konnte nicht vollständig geladen werden")
            }
            referenceTrack = track
            track.play()
            val release = Runnable { if (referenceTrack === track) stopReferenceTone() }
            referenceReleaseTask = release
            referenceAudioHandler.postDelayed(release, (seconds * 1000).toLong() + 150L)
        } catch (_: Exception) {
            stopReferenceTone()
            Toast.makeText(ctx, "Referenzton konnte nicht abgespielt werden.", Toast.LENGTH_SHORT).show()
        }
    }

    private fun stopReferenceTone() {
        referenceReleaseTask?.let { referenceAudioHandler.removeCallbacks(it) }
        referenceReleaseTask = null
        val track = referenceTrack
        referenceTrack = null
        if (track != null) {
            try { track.pause() } catch (_: Exception) { }
            try { track.flush() } catch (_: Exception) { }
            try { track.stop() } catch (_: Exception) { }
            try { track.release() } catch (_: Exception) { }
        }
    }
'''
t=t[:x]+block+t[y:]
old="""        try { referenceTrack?.stop() } catch (_: Exception) { }
        try { referenceTrack?.release() } catch (_: Exception) { }
        referenceTrack = null"""
if old in t: t=t.replace(old,"        stopReferenceTone()",1)
elif "stopReferenceTone()" not in t[t.index("private fun stopTuner"):]: raise SystemExit("Tuner-Cleanup fehlt")
for q in ["private fun stopReferenceTone()","AudioTrack.MODE_STATIC","selectedReferenceName == target.name","referenceAudioHandler.postDelayed",'contentDescription = "Referenzton Saite']:
    if q not in t: raise SystemExit("Validierung fehlt: "+q)
t = t.replace('selector.addView(stringPanel, LinearLayout.LayoutParams(-1, a.dp(48)))',
              'selector.addView(stringPanel, LinearLayout.LayoutParams(-1, a.dp(60)))')
if "selector.addView(stringPanel, LinearLayout.LayoutParams(-1, a.dp(60)))" not in t:
    raise SystemExit("Saitenbutton-Zeilenhöhe konnte nicht angepasst werden")
if "exp(-3.8 * t)" in t: raise SystemExit("Alte Soundengine bleibt aktiv")
p.write_text(s[:a]+t+s[b:],encoding="utf-8")
print("SAITENBUTTONS UND REFERENZTON-ENGINE: PASS")
