"""Transcribe voiced lines back to text with Moonshine, to catch words that the voice reads wrongly.

Usage: python stt.py <wav>...

It needs the moonshine_voice package and the medium streaming English model: MOONSHINE_MODEL is the model's folder.
Compare each transcript with the line's text, and reword a line whose words come back wrong.
"""
import array
import os
import sys
import wave
from pathlib import Path

from moonshine_voice import ModelArch, Transcriber

if not os.environ.get("MOONSHINE_MODEL"):
    sys.exit("Set MOONSHINE_MODEL to the folder of the Moonshine medium streaming English model.")
t = Transcriber(model_path=os.environ["MOONSHINE_MODEL"], model_arch=ModelArch["MEDIUM_STREAMING"])
for f in sys.argv[1:]:
    with wave.open(f) as w:
        rate, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        data = array.array("h", w.readframes(n))
    samples = [s / 32768 for s in data[::ch]]
    out = t.transcribe_without_streaming(samples, sample_rate=rate, flags=0)
    text = " ".join(getattr(line, "text", str(line)) for line in getattr(out, "lines", [out]))
    print(f"{Path(f).name}: {text}")
