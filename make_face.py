"""
Turn a photo into the ASCII portrait used on the card (writes face.txt).

  pip install pillow "rembg[cpu]"
  python make_face.py photo.jpg

rembg cuts out the background; the face is then shaded with block characters.
Works best with a square, centred head-and-shoulders photo.
"""
import sys
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops

src = sys.argv[1]
out = "face.txt"
cols, rows = 72, 38

from rembg import remove, new_session
_photo = Image.open(src).convert("RGB").resize((400, 400))
_photo.save("_face_src.png")
remove(_photo, session=new_session("u2net_human_seg"), only_mask=True).save("_face_mask.png")
src, mask_path = "_face_src.png", "_face_mask.png"

box = (30, 10, 370, 375)
im = Image.open(src).convert("L").crop(box)
mask = Image.open(mask_path).convert("L").crop(box)

# stretch contrast using only subject pixels
hist = [0] * 256
for p, m in zip(im.getdata(), mask.getdata()):
    if m > 127:
        hist[p] += 1
tot = sum(hist); acc = 0; lo = hi = None
for i, h in enumerate(hist):
    acc += h
    if lo is None and acc > tot * 0.02: lo = i
    if hi is None and acc > tot * 0.995: hi = i
im = im.point(lambda p: max(0, min(255, int((p - lo) * 255 / max(1, hi - lo)))))
im = im.point(lambda p: int(255 * (p / 255) ** 1.1))
im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=120))

im = im.resize((cols, rows), Image.LANCZOS)
mask = mask.resize((cols, rows), Image.LANCZOS)

ramp = " ·░░▒▒▓▓██"
lines = []
for y in range(rows):
    line = ""
    for x in range(cols):
        if mask.getpixel((x, y)) < 110:
            line += " "
            continue
        v = im.getpixel((x, y)) / 255
        line += ramp[max(1, min(len(ramp) - 1, int(v * len(ramp))))]
    lines.append(line.ljust(cols))
open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
import os; os.remove("_face_src.png"); os.remove("_face_mask.png")
