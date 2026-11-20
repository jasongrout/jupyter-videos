"""Voice some narration lines of an edit with ElevenLabs through OpenRouter.

Usage: python el_voice.py <edit.json> <out folder> --voice george [--model elevenlabs/eleven-v4] [--parts 0,1,2,3]

Writes one WAV per line and durations.json in the format of voice.py, so the cut can use the folder.
The OpenRouter key comes from OPENROUTER_API_KEY and is never printed. The script prints what the key has
spent before and after. A line whose text, model and voice did not change is not voiced again.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

SPEECH_URL = "https://openrouter.ai/api/v1/audio/speech"


def key():
    if not os.environ.get("OPENROUTER_API_KEY"):
        sys.exit("Set OPENROUTER_API_KEY to an OpenRouter key.")
    return os.environ["OPENROUTER_API_KEY"]


def usage(k):
    """What the key has spent so far, in US dollars."""
    request = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {k}"})
    return json.loads(urllib.request.urlopen(request, timeout=30).read())["data"]["usage"]


def speak(text, wav, model, voice, k):
    body = json.dumps({"model": model, "input": text, "voice": voice, "response_format": "pcm"}).encode()
    request = urllib.request.Request(SPEECH_URL, data=body, method="POST",
                                     headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                kind = response.headers.get("Content-Type", "")
                audio = response.read()
            break
        except urllib.error.HTTPError as error:
            detail = error.read()[:300].decode(errors="replace")
            if error.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            sys.exit(f"speech request failed: HTTP {error.code}: {detail}")
    if not kind.startswith("audio/pcm"):
        sys.exit(f"expected PCM audio, got {kind!r}")
    rate = int(re.search(r"rate=(\d+)", kind).group(1)) if "rate=" in kind else 24000
    with wave.open(str(wav), "w") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(audio)
    return len(audio) / 2 / rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("out")
    ap.add_argument("--voice", required=True)
    ap.add_argument("--model", default="elevenlabs/eleven-v4")
    ap.add_argument("--parts", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    seq = json.loads(Path(args.edit).read_text())["sequence"]
    keep = {int(i) for i in args.parts.split(",") if i.strip()} or set(range(len(seq)))
    lines = [l for i, item in enumerate(seq) if i in keep for l in item.get("say", [])]
    chars = sum(len(l["text"]) for l in lines)
    print(f"{len(lines)} lines, {chars} characters")
    if args.dry_run:
        return
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    index_file = out / "durations.json"
    index = json.loads(index_file.read_text()) if index_file.exists() else {}
    k = key()
    spent = usage(k)
    print(f"spent before: ${spent:.4f}")
    for line in lines:
        digest = hashlib.sha256(json.dumps([line["text"], args.model, args.voice]).encode()).hexdigest()[:16]
        wav = out / f"{line['id']}.wav"
        if index.get(line["id"], {}).get("hash") == digest and wav.exists():
            continue
        seconds = speak(line["text"], wav, args.model, args.voice, k)
        index[line["id"]] = {"hash": digest, "seconds": round(seconds, 3), "text": line["text"],
                             "settings": {"engine": "openrouter", "model": args.model, "voice": args.voice}}
        index_file.write_text(json.dumps(index, indent=1))
        print(f"{line['id']}: {seconds:.2f} s")
    print(f"spent after: ${usage(k):.4f}")


if __name__ == "__main__":
    main()
