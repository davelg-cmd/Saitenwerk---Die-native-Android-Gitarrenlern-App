from pathlib import Path
import os,re
p=Path(os.environ["PROJECT_DIR"])/"app/src/main/java/de/saitenwerk/app/MainActivity.kt"
s=p.read_text(encoding="utf-8")
print("=== LEARNING STUDIO DIAGNOSTIC ===")
for m in re.finditer(r"class\\s+([A-Za-z0-9_]*(?:Learn|Lern)[A-Za-z0-9_]*)",s):
    print("CLASS:",m.group(1))
for key in ["learn_quiz_correct","learn_quiz_total","learn_routine_day","learn_routine_done","learning_path_done","Lernstudio","Quiz","Routine","Lernpfad","Übung"]:
    pos=0
    found=0
    while True:
        i=s.find(key,pos)
        if i<0 or found>=5: break
        print(f"KEY {key} @ {i}: "+s[max(0,i-180):min(len(s),i+420)].replace("\\n"," "))
        pos=i+len(key); found+=1
print("=== END DIAGNOSTIC ===")
