from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BG = (0, 0, 0, 0)
TEAL = (46, 230, 198, 255)
GOLD = (246, 211, 120, 255)
NAVY = (7, 16, 27, 255)
NAVY2 = (13, 29, 44, 255)
WHITE = (244, 249, 252, 255)
RED = (255, 103, 118, 255)


def _font(size: int, bold=False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _draw_candle(d, x, y, w, h, up=True):
    c = TEAL if up else RED
    wick = max(2, w // 10)
    d.rounded_rectangle((x + w//2 - wick//2, y, x + w//2 + wick//2, y + h), radius=wick, fill=c)
    body_y1 = y + int(h * .24)
    body_y2 = y + int(h * .76)
    d.rounded_rectangle((x, body_y1, x+w, body_y2), radius=max(2, w//5), fill=c)


def create_logo_image(path: Path, size=520):
    """Premium 3D glass trading mark used by launcher, app icon preview and splash."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (size, size), BG)

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    pad = int(size * 0.095)
    sd.rounded_rectangle(
        (pad + 18, pad + 24, size - pad + 18, size - pad + 24),
        radius=int(size * .18),
        fill=(0, 0, 0, 170),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(size * .035)))
    img.alpha_composite(shadow)

    d = ImageDraw.Draw(img)
    # 3D extrusion/depth
    for i in range(30, 0, -2):
        off = i
        shade = max(10, 30 - i // 3)
        d.rounded_rectangle(
            (pad-off, pad+off, size-pad+off, size-pad+off),
            radius=int(size*.18),
            fill=(shade, 42 + shade//2, 58 + shade//2, 255)
        )

    d.rounded_rectangle(
        (pad, pad, size-pad, size-pad),
        radius=int(size*.18),
        fill=NAVY,
        outline=TEAL,
        width=max(4, size//72)
    )

    # Glass highlight
    hi = (pad+12, pad+12, size-pad-12, int(size*.42))
    d.rounded_rectangle(hi, radius=int(size*.13), fill=(255,255,255,16))
    d.line(
        (pad+34, pad+74, size-pad-40, pad+74),
        fill=(255,255,255,45),
        width=max(2, size//180)
    )

    # Inner gold bezel
    d.rounded_rectangle(
        (pad+22, pad+22, size-pad-22, size-pad-22),
        radius=int(size*.145),
        outline=GOLD,
        width=max(3, size//120)
    )

    # Market pulse / candles
    base_y = int(size*.62)
    for j,(yy,hh,up) in enumerate([(base_y+22, 70, True),(base_y-2, 112, True),(base_y-30, 152, False),(base_y-60, 192, True)]):
        _draw_candle(d, int(size*.25)+j*int(size*.09), yy, int(size*.048), hh, up)

    # Twin-market emblem: bull/bear circles with directional chevrons
    cx, cy = size*.68, size*.42
    r = size*.13
    d.ellipse((cx-r, cy-r, cx, cy+r), fill=(17, 31, 44, 255), outline=GOLD, width=max(2,size//120))
    d.ellipse((cx, cy-r, cx+r, cy+r), fill=(28, 45, 53, 255), outline=TEAL, width=max(2,size//120))
    fmark=_font(int(size*.085), True)
    d.text((cx-r/2, cy), "B", font=fmark, anchor="mm", fill=GOLD)
    d.text((cx+r/2, cy), "P", font=fmark, anchor="mm", fill=TEAL)

    # Central TP monogram with extrusion
    f = _font(int(size*.27), True)
    text = "TP"
    bb = d.textbbox((0,0), text, font=f)
    tw,th = bb[2]-bb[0], bb[3]-bb[1]
    x=(size-tw)//2
    y=int(size*.23)
    for ox,oy in [(10,12),(8,10),(6,8),(4,6),(2,4)]:
        d.text((x+ox,y+oy), text, font=f, fill=(77, 51, 11, 185))
    d.text((x,y), text, font=f, fill=WHITE)
    d.text((x+2,y+2), text, font=f, fill=(255,255,255,26))

    # Uptrend arrow + node
    pts=[
        (size*.24,size*.79),
        (size*.42,size*.68),
        (size*.56,size*.73),
        (size*.72,size*.56),
        (size*.83,size*.61),
        (size*.88,size*.49),
    ]
    d.line(pts, fill=GOLD, width=max(4,size//72), joint="curve")
    ah=size*.055
    ex,ey=pts[-1]
    d.polygon([(ex,ey),(ex-ah,ey+ah*1.2),(ex-ah*.2,ey+ah*.15)], fill=GOLD)

    # tiny status LED
    led=size*.885
    d.ellipse((led-14,led-14,led+14,led+14), fill=TEAL, outline=GOLD, width=max(2,size//220))

    img.save(path, "PNG")
    return path
