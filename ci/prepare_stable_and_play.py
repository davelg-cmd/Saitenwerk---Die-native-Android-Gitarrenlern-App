from pathlib import Path
import os
r=Path(os.environ["PROJECT_DIR"])
mgr=r/"app/src/main/java/de/saitenwerk/app/AppUpdateManager.kt"
main=r/"app/src/main/java/de/saitenwerk/app/MainActivity.kt"
gp=r/"app/build.gradle.kts"
u=mgr.read_text()
u=u.replace("/** Checks the current Beta release and offers an Android-approved APK install. */","/** Checks the selected Stable or Development release and offers an Android-approved APK install. */")
old='''                val release = fetchBetaRelease()
                    ?: throw IllegalStateException("Kein veröffentlichter Beta-Release gefunden")
'''
new='''                val channel = selectedChannel()
                val tag = if (channel == CHANNEL_STABLE) STABLE_TAG else DEVELOPMENT_TAG
                val expectedApk = if (channel == CHANNEL_STABLE) STABLE_APK_NAME else DEVELOPMENT_APK_NAME
                val release = fetchRelease(tag)
                    ?: throw IllegalStateException("Kein veröffentlichter " + (if (channel == CHANNEL_STABLE) "Stable" else "Entwicklungs") + "-Release gefunden")
'''
if old in u: u=u.replace(old,new,1)
elif "val expectedApk" not in u: raise SystemExit("Update-Abfrage fehlt")
u=u.replace('if (name == APK_NAME || name.endsWith(".apk", ignoreCase = true))','if (name == expectedApk || name.endsWith(".apk", ignoreCase = true))').replace('if (name == APK_NAME) break','if (name == expectedApk) break').replace('download(url, apkName ?: APK_NAME)','download(url, apkName ?: expectedApk)')
a=u.find("    private fun fetchBetaRelease(): JSONObject? {")
if a>=0:
 b=u.find("    private fun showMessage",a)
 method='''    private fun selectedChannel(): String = prefs.getString(KEY_CHANNEL, CHANNEL_STABLE) ?: CHANNEL_STABLE

    private fun fetchRelease(tag: String): JSONObject? {
        val api = "https://api.github.com/repos/davelg-cmd/Saitenwerk---Die-native-Android-Gitarrenlern-App/releases/tags/$tag"
        val c = (URL(api).openConnection() as HttpURLConnection).apply {
            connectTimeout=15000; readTimeout=15000; instanceFollowRedirects=true; requestMethod="GET"
            setRequestProperty("Accept","application/vnd.github+json")
            setRequestProperty("X-GitHub-Api-Version","2022-11-28")
            setRequestProperty("User-Agent","Saitenwerk-Android-App")
            setRequestProperty("Cache-Control","no-cache")
        }
        return try {
            val code=c.responseCode
            if(code !in 200..299) throw IllegalStateException("GitHub antwortet mit HTTP $code")
            val release=JSONObject(c.inputStream.bufferedReader().use { it.readText() })
            if(release.optString("tag_name")!=tag || release.optBoolean("draft",false)) null else release
        } finally { c.disconnect() }
    }

'''
 u=u[:a]+method+u[b:]
elif "private fun fetchRelease(tag: String)" not in u: raise SystemExit("Release-Methode fehlt")
oldc='''    companion object {
        private const val RELEASES_API = "https://api.github.com/repos/davelg-cmd/Saitenwerk---Die-native-Android-Gitarrenlern-App/releases/tags/beta-latest"
        private const val RELEASE_TAG = "beta-latest"
        private const val APK_NAME = "saitenwerk-beta.apk"
'''
newc='''    companion object {
        const val CHANNEL_STABLE = "stable"
        const val CHANNEL_DEVELOPMENT = "development"
        private const val STABLE_TAG = "stable-latest"
        private const val DEVELOPMENT_TAG = "beta-latest"
        private const val STABLE_APK_NAME = "saitenwerk-stable.apk"
        private const val DEVELOPMENT_APK_NAME = "saitenwerk-beta.apk"
        private const val APK_NAME = STABLE_APK_NAME
        private const val KEY_CHANNEL = "update_channel"
'''
if oldc in u: u=u.replace(oldc,newc,1)
elif "STABLE_TAG" not in u: raise SystemExit("Kanal-Konstanten fehlen")
mgr.write_text(u)
s=main.read_text()
anchor='        section("App-Updates","Prüfe manuell, ob eine neue Saitenwerk-Version verfügbar ist. Deine installierte Version bleibt erhalten, bis du das Update bestätigst.","Nach Updates suchen") { a.checkForUpdatesManually() }'
if "Update-Kanal" not in s:
 ui='''        if (!BuildConfig.PLAY_STORE_BUILD) {
            val prefs=a.getSharedPreferences("saitenwerk_updates",android.content.Context.MODE_PRIVATE)
            val card=a.card().apply { radius=a.dp(18).toFloat(); strokeColor=a.getColor(R.color.sw_outline); strokeWidth=a.dp(1) }
            val box=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL; setPadding(a.dp(18),a.dp(17),a.dp(18),a.dp(17)) }
            box.addView(TextView(a).apply { text="Update-Kanal"; textSize=17f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_text)) })
            box.addView(TextView(a).apply { text="Stable erhält nur ausdrücklich freigegebene Versionen. Entwicklung erhält neue Zwischenstände."; textSize=13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0,a.dp(5),0,a.dp(12)) })
            val b=a.button("").apply { textSize=14f; minHeight=a.dp(48); background=android.graphics.drawable.GradientDrawable().apply { cornerRadius=a.dp(14).toFloat(); setColor(a.getColor(R.color.sw_surface2)); setStroke(a.dp(1),a.getColor(R.color.sw_copper)) } }
            fun refresh() { val v=prefs.getString("update_channel","stable") ?: "stable"; b.text=if(v=="development") "Aktiv: Entwicklung · Kanal ändern" else "Aktiv: Stable · Kanal ändern" }
            refresh()
            b.setOnClickListener {
                val v=prefs.getString("update_channel","stable") ?: "stable"
                androidx.appcompat.app.AlertDialog.Builder(a,R.style.ThemeOverlay_Saitenwerk_Dialog)
                    .setTitle("Update-Kanal wählen")
                    .setSingleChoiceItems(arrayOf("Stable – geprüfte Freigaben","Entwicklung – neue Zwischenstände"),if(v=="development") 1 else 0) { d,w ->
                        prefs.edit().putString("update_channel",if(w==1) "development" else "stable").apply(); refresh(); d.dismiss()
                        Toast.makeText(a,if(w==1) "Entwicklungskanal aktiviert" else "Stable-Kanal aktiviert",Toast.LENGTH_SHORT).show()
                    }.setNegativeButton("Abbrechen",null).show()
            }
            box.addView(b,LinearLayout.LayoutParams(-1,a.dp(48))); card.addView(box)
            page.addView(card,LinearLayout.LayoutParams(-1,-2).apply { bottomMargin=a.dp(13) })
            section("App-Updates","Prüfe manuell, ob eine neue Saitenwerk-Version verfügbar ist. Deine installierte Version bleibt erhalten, bis du das Update bestätigst.","Nach Updates suchen") { a.checkForUpdatesManually() }
        } else {
            val card=a.card().apply { radius=a.dp(18).toFloat(); strokeColor=a.getColor(R.color.sw_outline); strokeWidth=a.dp(1) }
            val box=LinearLayout(a).apply { orientation=LinearLayout.VERTICAL; setPadding(a.dp(18),a.dp(17),a.dp(18),a.dp(17)) }
            box.addView(TextView(a).apply { text="App-Updates"; textSize=17f; setTypeface(typeface,1); setTextColor(a.getColor(R.color.sw_text)) })
            box.addView(TextView(a).apply { text="Diese Play-Store-Version erhält Aktualisierungen über Google Play."; textSize=13f; setTextColor(a.getColor(R.color.sw_muted)); setPadding(0,a.dp(5),0,0) })
            card.addView(box); page.addView(card,LinearLayout.LayoutParams(-1,-2).apply { bottomMargin=a.dp(13) })
        }'''
 if anchor not in s: raise SystemExit("Einstellungsanker fehlt")
 s=s.replace(anchor,ui,1)
main.write_text(s)
g=gp.read_text().replace('namespace = "de.saitenwerk.app"; compileSdk = 35','namespace = "de.saitenwerk.app"; compileSdk = 36').replace('targetSdk = 35;','targetSdk = 36;')
if "buildFeatures { buildConfig = true }" not in g: g=g.replace("android {","android {\n    buildFeatures { buildConfig = true }",1)
g=g.replace('defaultConfig { applicationId = "de.saitenwerk.app";','defaultConfig { buildConfigField("boolean","PLAY_STORE_BUILD","false"); applicationId = "de.saitenwerk.app";',1)
debug='''        getByName("debug") {
            signingConfig = signingConfigs.getByName("saitenwerkUpload")
        }
'''
if 'create("directRelease")' not in g:
 if debug not in g: raise SystemExit("Signing-Config fehlt")
 g=g.replace(debug,debug+'''        getByName("release") {
            signingConfig=signingConfigs.getByName("saitenwerkUpload")
            isDebuggable=false; isMinifyEnabled=false
            buildConfigField("boolean","PLAY_STORE_BUILD","true")
        }
        create("directRelease") {
            initWith(getByName("debug")); signingConfig=signingConfigs.getByName("saitenwerkUpload")
            isDebuggable=false; isMinifyEnabled=false
            buildConfigField("boolean","PLAY_STORE_BUILD","false")
            matchingFallbacks += listOf("release")
        }
''',1)
if g.count('getByName("release")')>1: raise SystemExit("Doppelte release-Konfiguration")
gp.write_text(g)
(r/"app/src/release").mkdir(parents=True,exist_ok=True)
(r/"app/src/release/AndroidManifest.xml").write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools">
 <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" tools:node="remove" />
</manifest>
''')
rg=r/"build.gradle.kts"
if rg.exists(): rg.write_text(rg.read_text().replace('com.android.application") version "8.7.3"','com.android.application") version "8.10.1"'))
print("Stable/Entwicklung + Play-Build-Profil vorbereitet")
