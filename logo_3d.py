from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BG = (8, 16, 24, 0)
TEAL = (39, 211, 176, 255)
GOLD = (242, 196, 109, 255)
NAVY = (17, 28, 40, 255)
WHITE = (234, 242, 247, 255)

def _font(size: int, bold=False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except OSError: pass
    return ImageFont.load_default()

def create_logo_image(path: Path, size=520):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (size, size), BG)
    shadow = Image.new("RGBA", (size, size), (0,0,0,0)); sd = ImageDraw.Draw(shadow)
    pad = int(size*0.10)
    sd.rounded_rectangle((pad+18,pad+20,size-pad+18,size-pad+20), radius=int(size*.16), fill=(0,0,0,150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(size*.03))); img.alpha_composite(shadow)
    d = ImageDraw.Draw(img)
    # 3D extruded base
    for i in range(18, 0, -2):
        off = i
        d.rounded_rectangle((pad-off,pad+off,size-pad+off,size-pad+off), radius=int(size*.16), fill=(18,38,52,255))
    d.rounded_rectangle((pad,pad,size-pad,size-pad), radius=int(size*.16), fill=NAVY, outline=TEAL, width=max(3,size//90))
    # beveled rings
    d.rounded_rectangle((pad+16,pad+16,size-pad-16,size-pad-16), radius=int(size*.13), outline=(39,211,176,100), width=max(2,size//150))
    d.rounded_rectangle((pad+30,pad+30,size-pad-30,size-pad-30), radius=int(size*.10), outline=(242,196,109,80), width=max(2,size//170))
    f = _font(int(size*.29), True)
    text = "TP"
    box = d.textbbox((0,0),text,font=f)
    tw,th = box[2]-box[0],box[3]-box[1]
    x=(size-tw)//2; y=(size-th)//2-int(size*.04)
    for ox,oy in [(8,10),(6,8),(4,6),(2,4)]:
        d.text((x+ox,y+oy),text,font=f,fill=GOLD)
    d.text((x,y),text,font=f,fill=WHITE)
    d.ellipse((size*.76,size*.76,size*.88,size*.88),fill=TEAL)
    img.save(path, "PNG")
    return path
