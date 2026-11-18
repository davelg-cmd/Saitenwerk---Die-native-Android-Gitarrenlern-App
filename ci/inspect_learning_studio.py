from pathlib import Path
import os,re
p=Path(os.environ["PROJECT_DIR"])/"app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s=p.read_text(encoding="utf-8")
anchor=s.find('root.addView(a.title("Lernstudio"))')
start=s.rfind("\nclass ",0,anchor)+1
end=s.find("\ndata class Song(",anchor)
part=s[start:end]
print("=== LEARNING STUDIO METHODS ===")
for name in ["onCreateView","showQuiz","showChanges","showRhythm","showRoutine","stopRhythm"]:
    i=part.find("fun "+name)
    if i<0: i=part.find("private fun "+name)
    print("\n--- "+name+" ---")
    print(part[i:i+3200] if i>=0 else "MISSING")
print("=== END METHODS ===")
