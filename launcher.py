import tkinter as tk
from pathlib import Path
import tempfile
import sys

APP = "Trader Planner Pro"
VERSION = "7.6.1"

def show_splash():
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg="#061019")
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    width, height = min(1100, sw - 80), min(720, sh - 100)
    root.geometry(f"{width}x{height}+{(sw-width)//2}+{(sh-height)//2}")
    try:
        from PIL import Image, ImageTk
        from logo_3d import create_logo_image
        p=Path(tempfile.gettempdir())/"TraderPlannerPro_3D"/"logo.png"
        create_logo_image(p, 620)
        image=Image.open(p).convert("RGBA")
        image.thumbnail((360,360), Image.Resampling.LANCZOS)
        photo=ImageTk.PhotoImage(image)
        tk.Label(root,image=photo,bg="#061019").pack(pady=(36,6))
        root._photo=photo
    except Exception:
        c=tk.Canvas(root,bg="#061019",highlightthickness=0); c.pack(fill="both",expand=True)
        c.create_text(width//2, height//2-30, text="TP", fill="#F2C46D", font=("Segoe UI",54,"bold"))
    tk.Label(root,text="TRADER PLANNER PRO",fg="#EAF2F7",bg="#061019",font=("Segoe UI",24,"bold")).pack()
    tk.Label(root,text=f"Professional trading workspace  •  V{VERSION}",fg="#27D3B0",bg="#061019",font=("Segoe UI",10,"bold")).pack(pady=(4,14))
    root.update()
    root.after(850, root.destroy)
    root.mainloop()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--webview":
        from webview_runner import main as webview_main
        webview_main()
        return
    show_splash()
    from TraderPlannerPro_v7_0_3 import App
    app=App()
    try:
        from PIL import Image,ImageTk
        from logo_3d import create_logo_image
        p=Path(tempfile.gettempdir())/"TraderPlannerPro_3D"/"app_icon.png"
        create_logo_image(p,256)
        icon=ImageTk.PhotoImage(Image.open(p).convert("RGBA").resize((64,64)))
        app.iconphoto(True,icon); app._app_icon=icon
    except Exception:
        pass
    app.mainloop()

if __name__=="__main__":
    main()
