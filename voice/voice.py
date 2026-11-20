"""Voice the narration of an edit file with Piper, the local text-to-speech model.

Usage: python voice.py <edit.json> <out folder> [--length-scale 1.05]

Every item of the edit file may carry "say": a list of {"id", "text", "at"}.
One WAV per line goes to the out folder, with durations.json. A line whose
text and settings did not change is not voiced again. The lexicon changes only
what the voice reads; the captions keep the text as written.

For a final cut, el_voice.py voices the same lines with ElevenLabs through
OpenRouter, into a folder of the same format.

PIPER is the piper command (default: piper on the PATH), and PIPER_VOICE the
.onnx file of a Piper voice: the 4.7 drafts used en_GB-alba-medium.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

PIPER = os.environ.get("PIPER", "piper")
VOICE = os.environ.get("PIPER_VOICE", "")

# What the voice should read instead of the written text.
LEXICON = [
    (r"\bJupyterLab\b", "Jupiter Lab"),
    (r"\bJupyterLite\b", "Jupiter Lite"),
    (r"\bJupyter\b", "Jupiter"),
    (r"\b4\.7\b", "four point seven"),
    (r"\b4\.6\b", "four point six"),
    (r"\b4\.1\b", "four point one"),
    (r"\b3\.11\b", "three point eleven"),
    (r"\b3\.15\b", "three point fifteen"),
    (r"\b7\.7\b", "seven point seven"),
    (r"\bCSV\b", "C S V"),
    (r"\bMathJax\b", "Math Jax"),
    (r"\bview-only\b", "view only"),
    (r"\bR\b", "Ar"),
    (r"\bpip\b", "pip"),
]
UNSPOKEN = re.compile(r"[_`=\[\]{}<>\\|%]")


def spoken(text):
    for pattern, replacement in LEXICON:
        text = re.sub(pattern, replacement, text)
    return text


def lines_of(edit):
    out = []
    for item in edit["sequence"]:
        for line in item.get("say", []):
            out.append({"id": line["id"], "text": line["text"]})
    return out


def main():
    if not VOICE:
        sys.exit("Set PIPER_VOICE to the .onnx file of a Piper voice.")
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("out")
    ap.add_argument("--length-scale", type=float, default=1.05)
    args = ap.parse_args()
    edit = json.loads(Path(args.edit).read_text())
    lines = lines_of(edit)
    bad = [l for l in lines if UNSPOKEN.search(l["text"])]
    if bad:
        raise SystemExit("lines with characters a voice reads as symbols: " + ", ".join(l["id"] for l in bad))
    ids = [l["id"] for l in lines]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise SystemExit(f"duplicate line ids: {sorted(dupes)}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "lines.json").write_text(json.dumps(lines, indent=1))
    index_file = out / "durations.json"
    index = json.loads(index_file.read_text()) if index_file.exists() else {}
    settings = {"engine": "piper", "voice": Path(VOICE).name, "length_scale": args.length_scale, "noise_scale": 0.6, "noise_w": 0.75,
                "lexicon": [list(x) for x in LEXICON]}
    for line in lines:
        digest = hashlib.sha256(json.dumps([line["text"], settings]).encode()).hexdigest()[:16]
        wav = out / f"{line['id']}.wav"
        if index.get(line["id"], {}).get("hash") == digest and wav.exists():
            continue
        subprocess.run(
            [PIPER, "-m", VOICE, "-f", str(wav), "--length-scale", str(args.length_scale),
             "--noise-scale", str(settings["noise_scale"]), "--noise-w-scale", str(settings["noise_w"]),
             "--sentence-silence", "0.3"],
            input=spoken(line["text"]).encode(), check=True, capture_output=True)
        with wave.open(str(wav)) as w:
            seconds = w.getnframes() / w.getframerate()
        index[line["id"]] = {"hash": digest, "seconds": round(seconds, 3), "text": line["text"]}
        index_file.write_text(json.dumps(index, indent=1))
        print(f"{line['id']}: {seconds:.2f} s")
    total = sum(index[i]["seconds"] for i in ids if i in index)
    words = sum(len(l["text"].split()) for l in lines)
    print(f"{len(lines)} lines, {words} words, {total:.1f} s of speech")


if __name__ == "__main__":
    main()
