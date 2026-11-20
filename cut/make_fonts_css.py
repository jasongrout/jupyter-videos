"""Write fonts.css: the typefaces of the cards as data URLs, because a page from setContent cannot load local files.

Usage: python make_fonts_css.py

render_overlays.js reads fonts.css next to style.css. The fonts are Source Sans 3 and Source Code Pro (SIL OFL),
the typefaces of the mini summit deck that the opening card follows.
"""

import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
FACES = [("SourceSansDeck", "SourceSans3-Variable.woff2"), ("SourceCodeDeck", "SourceCodePro-Variable.woff2")]

css = ["/* The typefaces of the mini summit deck (SIL OFL), from fonts/ as data URLs. */"]
for family, file in FACES:
    data = base64.b64encode((HERE / "fonts" / file).read_bytes()).decode()
    css.append(f"@font-face {{ font-family: '{family}'; src: url(data:font/woff2;base64,{data}) format('woff2'); "
               "font-weight: 200 900; font-style: normal; font-display: block; }")
(HERE / "fonts.css").write_text("\n".join(css) + "\n")
print(HERE / "fonts.css")
