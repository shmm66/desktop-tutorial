from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
TEAL=(46,230,198,255); GOLD=(246,211,120,255); NAVY=(7,16,27,255); NAVY2=(13,29,44,255); WHITE=(244,249,252,255); RED=(255,103,118,255)
def font(size):
    for p in (r"C:\Windows\Fonts\segoeuib.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(p).exists():
            try:return ImageFont.truetype(p,size)
            except OSError:pass
    return ImageFont.load_default()
def create_icon(path="app.ico"):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    base=Image.new("RGBA",(512,512),(0,0,0,0))
    sh=Image.new("RGBA",(512,512),(0,0,0,0));d=ImageDraw.Draw(sh)
    d.rounded_rectangle((38,48,488,492),radius=105,fill=(0,0,0,175));sh=sh.filter(ImageFilter.GaussianBlur(16));base.alpha_composite(sh)
    d=ImageDraw.Draw(base)
    for i in range(26,0,-2):
        d.rounded_rectangle((30-i,30+i,482+i,482+i),radius=100,fill=(10+i//2,30+i//2,44+i//3,255))
    d.rounded_rectangle((30,30,482,482),radius=100,fill=NAVY,outline=TEAL,width=16)
    d.rounded_rectangle((52,52,460,460),radius=82,outline=GOLD,width=7)
    d.rounded_rectangle((68,68,444,220),radius=60,fill=(255,255,255,18))
    f=font(158);bb=d.textbbox((0,0),"TP",font=f);tw=bb[2]-bb[0];th=bb[3]-bb[1];x=(512-tw)//2;y=102
    d.text((x+9,y+11),"TP",font=f,fill=(84,52,12,190));d.text((x,y),"TP",font=f,fill=WHITE)
    for j,(xx,yy,hh,up) in enumerate([(126,332,64,True),(176,294,104,True),(226,337,64,False),(276,272,130,True),(326,238,166,True)]):
        c=TEAL if up else RED;d.line((xx,yy,xx,yy+hh),fill=c,width=6);d.rounded_rectangle((xx-15,yy+hh//3,xx+15,yy+hh*2//3),radius=7,fill=c)
    pts=[(110,424),(188,392),(260,409),(334,350),(405,366),(435,321)];d.line(pts,fill=GOLD,width=8,joint="curve");d.polygon([(435,321),(410,331),(425,347)],fill=GOLD)
    d.ellipse((404,92,449,137),fill=TEAL,outline=GOLD,width=3)
    base.save(path,"ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]);return path
if __name__=="__main__":create_icon()
