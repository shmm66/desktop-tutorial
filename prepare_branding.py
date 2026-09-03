from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path('assets')
OUT.mkdir(exist_ok=True)

try:
    from branding_assets import materialize_assets
    logo_path, splash_path = materialize_assets(OUT)
    logo = Image.open(logo_path).convert('RGB')
    logo.save(OUT/'trader_planner_logo.png', 'PNG')
    logo.resize((256,256), Image.Resampling.LANCZOS).save(OUT/'trader_planner_logo.ico', 'ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
except Exception as exc:
    print(f'Branding asset decode failed, generating safe fallback: {exc}')
    logo = Image.new('RGB',(512,512),'#061019')
    d = ImageDraw.Draw(logo)
    d.rounded_rectangle((18,18,494,494),radius=72,outline='#D9A441',width=10)
    d.text((256,190),'🐂  🐻',anchor='mm',fill='#E7B85B')
    d.text((256,285),'TRADER',anchor='mm',fill='white')
    d.text((256,345),'PLANNER PRO',anchor='mm',fill='#E7B85B')
    logo.save(OUT/'trader_planner_logo.png')
    logo.resize((256,256), Image.Resampling.LANCZOS).save(OUT/'trader_planner_logo.ico','ICO',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])

try:
    # Ensure splash exists; if the supplied asset was unavailable, use a clean fallback.
    splash = Image.open(OUT/'trader_planner_splash.jpg').convert('RGB')
except Exception:
    splash = Image.new('RGB',(960,640),'#061019')
    d = ImageDraw.Draw(splash)
    d.rounded_rectangle((120,40,840,590),radius=60,outline='#D9A441',width=8)
    d.text((480,220),'🐂       🐻',anchor='mm',fill='#E7B85B')
    d.text((480,320),'TRADER',anchor='mm',fill='white')
    d.text((480,370),'PLANNER PRO',anchor='mm',fill='#E7B85B')
    splash.save(OUT/'trader_planner_splash.jpg','JPEG',quality=90)
print('Branding prepared:', list(OUT.iterdir()))
