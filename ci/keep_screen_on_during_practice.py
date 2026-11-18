from pathlib import Path
import os
import re

main = Path(os.environ["PROJECT_DIR"]) / "app/src/main/java/de/saitenwerk/app/MainActivity.kt"
source = main.read_text(encoding="utf-8")

def keep_awake_in_fragment(source: str, class_name: str, end_marker: str) -> str:
    start_token = f"class {class_name} : Fragment() {{"
    start = source.find(start_token)
    if start < 0:
        raise SystemExit(f"FEHLER: Fragment {class_name} nicht gefunden")
    end = source.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"FEHLER: Ende von {class_name} nicht gefunden")
    fragment = source[start:end]

    resume_call = "requireActivity().window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)"
    pause_call = "requireActivity().window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)"

    def inject(method: str, super_call: str, call: str, before_super: bool) -> None:
        nonlocal fragment
        pattern = rf"(    override fun {method}\(\)\s*\{{\s*)"
        match = re.search(pattern, fragment)
        if match:
            body_start = match.end()
            if call in fragment[body_start:]:
                return
            super_pattern = re.compile(rf"super\.{method}\(\)")
            super_match = super_pattern.search(fragment, body_start)
            if not super_match:
                raise SystemExit(f"FEHLER: super.{method}() in {class_name} fehlt")
            position = super_match.start() if before_super else super_match.end()
            fragment = fragment[:position] + call + "\n        " + fragment[position:]
        else:
            block = (
                f"    override fun {method}() {{\n"
                + (f"        {call}\n        {super_call}\n" if before_super
                   else f"        {super_call}\n        {call}\n")
                + "    }\n\n"
            )
            marker = "    override fun onCreateView"
            if fragment.count(marker) != 1:
                raise SystemExit(f"FEHLER: onCreateView-Einfügepunkt in {class_name} nicht eindeutig")
            fragment = fragment.replace(marker, block + marker, 1)

    inject("onResume", "super.onResume()", resume_call, False)
    inject("onPause", "super.onPause()", pause_call, True)

    if resume_call not in fragment or pause_call not in fragment:
        raise SystemExit(f"FEHLER: Display-Wachhalten in {class_name} unvollständig")
    return source[:start] + fragment + source[end:]

source = keep_awake_in_fragment(source, "TunerFragment", "\nclass TunerGaugeView")
source = keep_awake_in_fragment(source, "LearnFragment", "\nclass PathFragment")

# Keep the tuner audio engine free of a hard attack; protect against regressions.
tuner_start = source.index("class TunerFragment : Fragment() {")
tuner_end = source.index("\nclass TunerGaugeView", tuner_start)
tuner = source[tuner_start:tuner_end]
if "FLAG_KEEP_SCREEN_ON" not in tuner:
    raise SystemExit("FEHLER: Display-Flag im Stimmgerät fehlt")
learn_start = source.index("class LearnFragment : Fragment() {")
learn_end = source.index("\nclass PathFragment", learn_start)
learn = source[learn_start:learn_end]
if "FLAG_KEEP_SCREEN_ON" not in learn:
    raise SystemExit("FEHLER: Display-Flag im Lernstudio fehlt")

main.write_text(source, encoding="utf-8")
print("DISPLAY WÄHREND ÜBUNGEN UND STIMMEN AN: PASS")
