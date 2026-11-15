#!/usr/bin/env python3
"""Fetch the CC0 Meta steel-string guitar multisamples and prepare compact PCM assets."""
from pathlib import Path
import json
import os
import re
import subprocess
import tempfile
import urllib.request
import zipfile

root = Path(os.environ["PROJECT_DIR"])
assets = root / "app/src/main/assets/guitar_samples"
assets.mkdir(parents=True, exist_ok=True)
url = "https://github.com/facebookincubator/Meta-open-sound/releases/download/meta-steel-guitar-v1.0.0/meta-open-sound-meta-steel-guitar-ogg.zip"
archive = Path(tempfile.gettempdir()) / "meta-steel-guitar-ogg.zip"
print("Downloading CC0 steel-string guitar multisamples...")
urllib.request.urlretrieve(url, archive)

with zipfile.ZipFile(archive) as zf:
    names = zf.namelist()
    sfz_name = next((n for n in names if n.endswith("meta-steel-guitar.sfz")), None)
    if not sfz_name:
        raise SystemExit("ERROR: SFZ map missing from guitar sample archive.")
    sfz = zf.read(sfz_name).decode("utf-8", errors="replace")
    mapping = {}
    for line in sfz.splitlines():
        if "Vel02" not in line:
            continue
        match = re.search(r"<region>\s+key=(\d+).*?sample=([^\s]+)", line)
        if match:
            midi = int(match.group(1))
            if 40 <= midi <= 84:
                mapping.setdefault(midi, Path(match.group(2)).name)
    missing = sorted(set(range(40, 85)) - set(mapping))
    if missing:
        raise SystemExit("ERROR: Guitar sample map lacks MIDI notes: " + ", ".join(map(str, missing)))

    for midi, filename in sorted(mapping.items()):
        if (assets / f"note_{midi}.pcm").exists():
            continue
        entry = next((n for n in names if n.endswith("/" + filename)), None)
        if entry is None:
            raise SystemExit(f"ERROR: OGG sample not found in archive: {filename}")
        source = Path(tempfile.gettempdir()) / filename
        source.write_bytes(zf.read(entry))
        output = assets / f"note_{midi}.pcm"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(source), "-ac", "1", "-ar", "22050",
            "-f", "s16le", str(output)
        ], check=True)
        source.unlink(missing_ok=True)
        if output.stat().st_size < 4096:
            raise SystemExit(f"ERROR: Converted sample is unexpectedly short: {output.name}")

    license_name = next((n for n in names if n.endswith("/LICENSE")), None)
    if license_name:
        (assets / "LICENSE.txt").write_bytes(zf.read(license_name))

manifest = {
    "instrument": "Meta Steel Guitar",
    "source": "https://github.com/facebookincubator/Meta-open-sound",
    "release": "meta-steel-guitar-v1.0.0",
    "license": "CC0-1.0",
    "format": "signed 16-bit little-endian PCM, mono, 22050 Hz",
    "midi_range": [40, 84],
    "velocity_layer": 2,
}
(assets / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
count = len(list(assets.glob("note_*.pcm")))
if count != 45:
    raise SystemExit(f"ERROR: Expected 45 real guitar note samples, found {count}.")
print(f"REAL GUITAR SAMPLE PACK: PASS ({count} notes, CC0, 22.05 kHz PCM)")
