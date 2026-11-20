"""Contact sheet of PNG stills: python sheet.py <out.png> <cols> <width> <files...>"""
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
ims = []
font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 18)
for f in files:
    im = Image.open(f).convert("RGB")
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    label = f.rsplit("/", 1)[-1].replace("still-", "").replace(".png", "")
    d.rectangle((0, 0, 10 + d.textlength(label, font=font), 26), fill=(0, 0, 0))
    d.text((5, 2), label, font=font, fill=(255, 210, 90))
    ims.append(im)
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, h * rows), "white")
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
print(out)
