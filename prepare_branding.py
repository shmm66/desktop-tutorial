from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from logo_3d import create_logo_image
OUT=Path("assets");OUT.mkdir(exist_ok=True)
logo=OUT/"trader_planner_logo.png";ico=OUT/"trader_planner_logo.ico";wiz=OUT/"installer_wizard.bmp";small=OUT/"installer_small.bmp"
create_logo_image(logo,1024)
im=Image.open(logo).convert("RGB")
im.resize((256,256),Image.Resampling.LANCZOS).save(ico,"ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
bg=Image.new("RGB",(164,314),(7,16,27));d=ImageDraw.Draw(bg)
for y in range(314):
    t=y/313;d.line((0,y,164,y),fill=(7+int(10*t),16+int(15*t),27+int(24*t)))
thumb=im.copy();thumb.thumbnail((132,132),Image.Resampling.LANCZOS);bg.paste(thumb,((164-thumb.width)//2,30))
try:f=ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf",12)
except Exception:f=ImageFont.load_default()
d.text((82,185),"TRADER PLANNER",font=f,anchor="mm",fill=(244,249,252));d.text((82,207),"PRO • V10",font=f,anchor="mm",fill=(246,211,120))
d.rounded_rectangle((24,250,140,258),radius=4,fill=(46,230,198));d.rounded_rectangle((24,267,128,275),radius=4,fill=(246,211,120))
bg.save(wiz,"BMP");im.resize((55,55),Image.Resampling.LANCZOS).save(small,"BMP");bg.save(OUT/"trader_planner_splash.bmp","BMP")
print("Premium branding prepared")
