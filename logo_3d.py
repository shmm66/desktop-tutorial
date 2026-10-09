from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BG=(0,0,0,0); TEAL=(46,230,198,255); GOLD=(246,211,120,255)
NAVY=(7,16,27,255); NAVY2=(13,29,44,255); WHITE=(244,249,252,255)
RED=(255,103,118,255)

def _font(size:int,bold=False):
    candidates=[r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        if Path(p).exists():
            try: return ImageFont.truetype(p,size)
            except OSError: pass
    return ImageFont.load_default()

def _candle(d,x,y,w,h,up=True):
    c=TEAL if up else RED
    d.line((x+w//2,y,x+w//2,y+h),fill=c,width=max(2,w//7))
    d.rounded_rectangle((x,y+int(h*.24),x+w,y+int(h*.76)),radius=max(2,w//4),fill=c)

def create_logo_image(path:Path,size=520):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    img=Image.new("RGBA",(size,size),BG)
    shadow=Image.new("RGBA",(size,size),BG); sd=ImageDraw.Draw(shadow)
    pad=int(size*.095)
    sd.rounded_rectangle((pad+18,pad+24,size-pad+18,size-pad+24),radius=int(size*.18),fill=(0,0,0,175))
    shadow=shadow.filter(ImageFilter.GaussianBlur(int(size*.035))); img.alpha_composite(shadow)
    d=ImageDraw.Draw(img)
    for i in range(30,0,-2):
        off=i; k=max(10,30-i//3)
        d.rounded_rectangle((pad-off,pad+off,size-pad+off,size-pad+off),radius=int(size*.18),fill=(k,42+k//2,58+k//2,255))
    d.rounded_rectangle((pad,pad,size-pad,size-pad),radius=int(size*.18),fill=NAVY,outline=TEAL,width=max(4,size//72))
    d.rounded_rectangle((pad+16,pad+16,size-pad-16,size-pad-16),radius=int(size*.145),outline=GOLD,width=max(3,size//120))
    d.rounded_rectangle((pad+20,pad+20,size-pad-20,int(size*.38)),radius=int(size*.13),fill=(255,255,255,18))
    # TP monogram with depth
    f=_font(int(size*.26),True); bb=d.textbbox((0,0),"TP",font=f)
    tw,th=bb[2]-bb[0],bb[3]-bb[1]; x=(size-tw)//2; y=int(size*.19)
    for ox,oy in [(10,12),(8,10),(6,8),(4,6),(2,4)]:
        d.text((x+ox,y+oy),"TP",font=f,fill=(84,52,12,190))
    d.text((x,y),"TP",font=f,fill=WHITE)
    # compact market candles
    base=int(size*.62)
    for j,(h,up) in enumerate([(76,True),(118,True),(82,False),(154,True),(194,True)]):
        xx=int(size*.22)+j*int(size*.09)
        _candle(d,xx,base-h, max(10,size//42),h,up)
    # directional gold path
    pts=[(size*.18,size*.79),(size*.35,size*.69),(size*.49,size*.74),(size*.63,size*.59),(size*.76,size*.64),(size*.87,size*.48)]
    d.line(pts,fill=GOLD,width=max(4,size//72),joint="curve")
    ex,ey=pts[-1]; a=size*.055
    d.polygon([(ex,ey),(ex-a,ey+a*1.2),(ex-a*.2,ey+a*.15)],fill=GOLD)
    # dual market badge
    cx,cy,r=size*.73,size*.39,size*.105
    d.ellipse((cx-r,cy-r,cx,cy+r),fill=(16,29,41,255),outline=GOLD,width=max(2,size//130))
    d.ellipse((cx,cy-r,cx+r,cy+r),fill=(24,44,52,255),outline=TEAL,width=max(2,size//130))
    fm=_font(int(size*.07),True)
    d.text((cx-r/2,cy),"B",font=fm,anchor="mm",fill=GOLD)
    d.text((cx+r/2,cy),"P",font=fm,anchor="mm",fill=TEAL)
    led=size*.885
    d.ellipse((led-14,led-14,led+14,led+14),fill=TEAL,outline=GOLD,width=max(2,size//220))
    img.save(path,"PNG"); return path
