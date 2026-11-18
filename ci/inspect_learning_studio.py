from pathlib import Path
import os
p=Path(os.environ["PROJECT_DIR"])/"app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s=p.read_text(encoding="utf-8")
anchor=s.find('root.addView(a.title("Lernstudio"))')
if anchor<0: raise SystemExit("Lernstudio anchor fehlt")
start=s.rfind("\nclass ",0,anchor)+1
end=s.find("\ndata class Song(",anchor)
if end<0: end=len(s)
print("=== LEARNING STUDIO SOURCE BOUNDS ===")
print("START:",start)
print("DECL:",s[start:s.find("\n",start)])
print("END:",end)
print("SOURCE_START:\n"+s[start:start+1200])
print("SOURCE_END:\n"+s[max(start,end-1600):end])
print("=== END BOUNDS ===")
