from pathlib import Path
import os
import re

root = Path(os.environ["PROJECT_DIR"])
main = root / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
source = main.read_text(encoding="utf-8")

replacements = {
    'ChordShape("C#7", "Septakkord", intArrayOf(-1,4,3,4,2,-1), note="Cis-Dominantseptakkord", fingers=intArrayOf(0,3,2,4,1,0))':
    'ChordShape("C#7", "Septakkord", intArrayOf(4,4,3,4,2,-1), note="Cis-Dominantseptakkord", fingers=intArrayOf(3,4,2,4,1,0))',
    'ChordShape("D#7", "Septakkord", intArrayOf(-1,6,5,6,4,-1), 4, note="Dis-Dominantseptakkord", fingers=intArrayOf(0,3,2,4,1,0))':
    'ChordShape("D#7", "Septakkord", intArrayOf(-1,6,5,6,4,6), 4, note="Dis-Dominantseptakkord", fingers=intArrayOf(0,3,2,4,1,4))',
    'ChordShape("C6", "Weitere Akkorde", intArrayOf(-1,3,2,2,1,0), note="C-Dur mit hinzugefügter Sexte", fingers=intArrayOf(0,3,2,4,1,0))':
    'ChordShape("C6", "Weitere Akkorde", intArrayOf(-1,3,2,2,1,3), note="C-Dur mit hinzugefügter Sexte", fingers=intArrayOf(0,3,2,4,1,4))',
}
for old, new in replacements.items():
    if old in source:
        if source.count(old) != 1:
            raise SystemExit("FEHLER: Griffbild mehrfach vorhanden: " + old.split('"')[1])
        source = source.replace(old, new, 1)
    elif source.count(new) != 1:
        raise SystemExit("FEHLER: Griffbild fehlt oder ist nicht eindeutig: " + new.split('"')[1])

tuning = [4, 9, 2, 7, 11, 4]
expected = {
    "C#7": {1, 5, 8, 11},
    "D#7": {1, 3, 7, 10},
    "C6": {0, 4, 7, 9},
}
for name, wanted in expected.items():
    line = next((line for line in source.splitlines() if f'ChordShape("{name}"' in line), None)
    if line is None:
        raise SystemExit("FEHLER: Akkordgriff nicht gefunden: " + name)
    fret_match = re.search(r'intArrayOf\(([^)]*)\)', line)
    finger_match = re.search(r'fingers=intArrayOf\(([^)]*)\)', line)
    if not fret_match or not finger_match:
        raise SystemExit("FEHLER: Griff-/Fingerarray fehlt: " + name)
    frets = [int(x.strip()) for x in fret_match.group(1).split(",")]
    fingers = [int(x.strip()) for x in finger_match.group(1).split(",")]
    if len(frets) != 6 or len(fingers) != 6:
        raise SystemExit("FEHLER: Kein vollständiges Sechs-Saiten-Griffbild: " + name)
    if any((fret <= 0 and finger != 0) or (fret > 0 and finger not in range(1, 5)) for fret, finger in zip(frets, fingers)):
        raise SystemExit("FEHLER: Ungültige Fingerposition: " + name)
    actual = {(pitch + fret) % 12 for pitch, fret in zip(tuning, frets) if fret >= 0}
    if not wanted.issubset(actual):
        raise SystemExit(f"FEHLER: {name} enthält nicht alle erwarteten Akkordtöne: {sorted(actual)}")
    print(f"{name}: PASS – Tonklassen {sorted(actual)} enthalten alle erwarteten Akkordtöne.")

main.write_text(source, encoding="utf-8")
print("AKKORD-BLITZTRAINER: Premium-Implementierung erhalten; drei Griffbilder musikalisch korrigiert.")
