package de.saitenwerk.app
import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import android.view.Gravity
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import java.io.File
object SongbookPdfViewer{
 fun show(a:MainActivity,start:Int,end:Int){
  val f=File(a.filesDir,"songbook.pdf");if(!f.isFile()){android.widget.Toast.makeText(a,"Das Original-PDF ist nicht mehr im privaten App-Speicher vorhanden.",android.widget.Toast.LENGTH_LONG).show();return}
  val first=(start-1).coerceAtLeast(0);val last=(end-1).coerceAtLeast(first);val d=AlertDialog.Builder(a,R.style.ThemeOverlay_Saitenwerk_Dialog).create()
  val root=LinearLayout(a).apply{orientation=LinearLayout.VERTICAL;setPadding(a.dp(8),a.dp(8),a.dp(8),a.dp(8))}
  val h=TextView(a).apply{textSize=15f;setTextColor(a.getColor(R.color.sw_copper));gravity=Gravity.CENTER}
  val img=ImageView(a).apply{adjustViewBounds=true;scaleType=ImageView.ScaleType.FIT_CENTER};val nav=LinearLayout(a).apply{gravity=Gravity.CENTER};val prev=a.button("‹");val next=a.button("›")
  nav.addView(prev,LinearLayout.LayoutParams(a.dp(64),a.dp(48)));nav.addView(next,LinearLayout.LayoutParams(a.dp(64),a.dp(48)));root.addView(h);root.addView(img,LinearLayout.LayoutParams(-1,0,1f));root.addView(nav);d.setView(root)
  val pfd=ParcelFileDescriptor.open(f,ParcelFileDescriptor.MODE_READ_ONLY);val r=PdfRenderer(pfd);var page=first
  fun render(){val p=r.openPage(page);val b=Bitmap.createBitmap(p.width*2,p.height*2,Bitmap.Config.ARGB_8888);p.render(b,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);p.close();img.setImageBitmap(b);h.text="Original-PDF · Seite \${page+1}";prev.isEnabled=page>first;next.isEnabled=page<last}
  prev.setOnClickListener{if(page>first){page--;render()}};next.setOnClickListener{if(page<last){page++;render()}};d.setOnDismissListener{r.close();pfd.close()};d.show();d.window?.setLayout(a.dp(380),a.dp(650));render()
 }
}
