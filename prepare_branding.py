from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from logo_3d import create_logo_image

OUT=Path("assets")
OUT.mkdir(exist_ok=True)

logo_png=OUT/"trader_planner_logo.png"
logo_ico=OUT/"trader_planner_logo.ico"
splash_bmp=OUT/"installer_wizard.bmp"
splash_small=OUT/"installer_small.bmp"

# Generate the same premium mark used by the running application and the installer.
create_logo_image(logo_png, 1024)
img=Image.open(logo_png).convert("RGB")
img.resize((256,256),Image.Resampling.LANCZOS).save(
    logo_ico,"ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]
)

# Inno Setup wizard image: 164x314, with a clean premium glass presentation.
canvas=Image.new("RGB",(164,314),(7,16,27))
d=ImageDraw.Draw(canvas)
for y in range(314):
    t=y/313
    c=(7+int(10*t),16+int(15*t),27+int(24*t))
    d.line((0,y,164,y),fill=c)
logo_thumb=img.copy()
logo_thumb.thumbnail((136,136),Image.Resampling.LANCZOS)
canvas.paste(logo_thumb,((164-logo_thumb.width)//2,34),logo_thumb.convert("RGBA") if logo_thumb.mode=="RGBA" else None)
f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",13)
d.text((82,188),"TRADER PLANNER",font=f,anchor="mm",fill=(244,249,252))
d.text((82,211),"PRO • v10",font=f,anchor="mm",fill=(246,211,120))
d.rounded_rectangle((24,250,140,257),radius=4,fill=(46,230,198))
d.rounded_rectangle((24,266,124,273),radius=4,fill=(246,211,120))
canvas.save(splash_bmp,"BMP")

small=img.resize((55,55),Image.Resampling.LANCZOS)
small.save(splash_small,"BMP")

# Keep legacy names for older installer configs.
canvas.save(OUT/"trader_planner_splash.bmp","BMP")
print("Branding prepared:", [str(p) for p in OUT.iterdir()])
