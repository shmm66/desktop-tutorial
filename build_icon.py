from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TEAL = (39, 211, 176, 255)
GOLD = (242, 196, 109, 255)
NAVY = (9, 20, 31, 255)
NAVY2 = (17, 34, 49, 255)
WHITE = (245, 249, 252, 255)

def font(size):
    for p in (r"C:\Windows\Fonts\segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_icon(path="app.ico"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    base = Image.new("RGBA", (512, 512), (0,0,0,0))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((22,22,490,490), radius=96, fill=NAVY, outline=TEAL, width=18)
    d.rounded_rectangle((52,52,460,460), radius=78, fill=NAVY2, outline=GOLD, width=7)
    d.ellipse((115,115,397,397), fill=(8,16,24,255), outline=TEAL, width=7)
    d.ellipse((135,135,377,377), outline=(242,196,109,220), width=4)
    f=font(170)
    text="TP"
    bb=d.textbbox((0,0),text,font=f)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    x=(512-tw)//2; y=(512-th)//2-18
    d.text((x+5,y+7),text,font=f,fill=(0,0,0,200))
    d.text((x,y),text,font=f,fill=WHITE)
    d.ellipse((398,398,450,450),fill=TEAL,outline=GOLD,width=3)
    ico_sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
    base.save(path,format="ICO",sizes=ico_sizes)
    return path

if __name__ == "__main__":
    create_icon()
