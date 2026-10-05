# CI RELEASE STAMP: V10.0.0
import tkinter as tk
from pathlib import Path
import tempfile
import sys

APP = "Trader Planner Pro"
VERSION = "10.0.0"

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
    root.after(1850, root.destroy)
    root.mainloop()

def _write_startup_error(exc):
    try:
        log_dir=Path.home()/ "TraderPlannerPro"
        log_dir.mkdir(parents=True,exist_ok=True)
        (log_dir/"startup.log").write_text(
            f"Trader Planner Pro {VERSION} startup failure\n\n{type(exc).__name__}: {exc}\n",
            encoding="utf-8"
        )
    except Exception:
        pass


def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
            # Headless CI validation for Windows service runners.
            import importlib
            required = [
                "TraderPlannerPro_v7_0_3", "market_data", "news_data",
                "ai_assistant", "academy_visuals", "academy_diagrams",
                "glass_theme", "google_oauth", "statement_report", "webview_runner", "native_trading_desk"
            ]
            for module_name in required:
                importlib.import_module(module_name)
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
            required_assets = [base / "education_sources"]
            missing = [str(p) for p in required_assets if not p.exists()]
            if missing:
                raise RuntimeError("Missing bundled assets: " + ", ".join(missing))
            print(f"{APP} {VERSION} self-test: OK")
            return
        if len(sys.argv) > 1 and sys.argv[1] == "--webview":
            from webview_runner import main as webview_main
            webview_main()
            return
        show_splash()
        from TraderPlannerPro_v7_0_3 import App
        app=App()
        try: app.state("zoomed")
        except Exception: pass
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
    except Exception as exc:
        _write_startup_error(exc)
        try:
            root=tk.Tk(); root.withdraw()
            from tkinter import messagebox
            messagebox.showerror(
                f"{APP} — Startup error",
                f"{exc}\n\nA diagnostic log was saved to:\n{Path.home()/ 'TraderPlannerPro' / 'startup.log'}"
            )
            root.destroy()
        except Exception:
            pass
        raise



if __name__=="__main__":
    main()
