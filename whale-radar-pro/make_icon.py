"""Generate the app icon used by the EXE, installer, and shortcuts."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
SIZES = [16, 24, 32, 48, 64, 128, 256]

def draw_icon(size: int) -> Image.Image:
    im = Image.new("RGBA", (size, size), (16, 21, 31, 255))
    d = ImageDraw.Draw(im)
    pad = max(1, size // 24)
    d.rounded_rectangle((pad, pad, size-pad-1, size-pad-1),
                        radius=max(3, size//5), fill=(25, 34, 49, 255),
                        outline=(70, 214, 178, 255), width=max(1, size//32))
    d.ellipse((size*.20, size*.34, size*.78, size*.69), fill=(70, 214, 178, 255))
    d.polygon([(size*.23,size*.51),(size*.10,size*.39),(size*.12,size*.56),(size*.21,size*.61)],
              fill=(70,214,178,255))
    d.polygon([(size*.68,size*.48),(size*.86,size*.52),(size*.69,size*.59)],
              fill=(70,214,178,255))
    d.ellipse((size*.68,size*.43,size*.73,size*.48), fill=(8,18,26,255))
    d.arc((size*.43,size*.13,size*.62,size*.40), 205, 320,
          fill=(70,214,178,255), width=max(1,size//22))
    return im

if __name__ == "__main__":
    images = [draw_icon(s) for s in SIZES]
    images[-1].save(ASSETS / "whaleradar.ico", format="ICO", sizes=[(s,s) for s in SIZES])
    print("Generated assets/whaleradar.ico")
