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
    try:
        root.wm_attributes("-topmost", True)
    except Exception:
        pass
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    width, height = min(1040, sw - 90), min(680, sh - 120)
    root.geometry(f"{width}x{height}+{(sw-width)//2}+{(sh-height)//2}")

    canvas = tk.Canvas(root, bg="#061019", highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)

    # Soft native-looking background glows.
    canvas.create_oval(width*0.58, -height*0.35, width*1.10, height*0.45,
                       fill="#0B2735", outline="")
    canvas.create_oval(-width*0.15, height*0.70, width*0.46, height*1.25,
                       fill="#0A202A", outline="")

    logo_photo = None
    try:
        from PIL import Image, ImageTk
        from logo_3d import create_logo_image
        p = Path(tempfile.gettempdir()) / "TraderPlannerPro_3D" / "logo.png"
        create_logo_image(p, 420)
        image = Image.open(p).convert("RGBA")
        image.thumbnail((330, 330), Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(image)
        canvas.create_image(width//2, height//2-55, image=logo_photo)
        root._photo = logo_photo
    except Exception:
        canvas.create_text(width//2, height//2-55, text="TP", fill="#F2C46D",
                           font=("Segoe UI", 58, "bold"))

    canvas.create_text(width//2, height-132, text="TRADER PLANNER PRO",
                       fill="#EAF2F7", font=("Segoe UI", 24, "bold"))
    canvas.create_text(width//2, height-102,
                       text=f"PROFESSIONAL TRADING WORKSPACE  •  V{VERSION}",
                       fill="#36E0C0", font=("Segoe UI", 9, "bold"))

    bar_w = min(520, width-180)
    x0 = (width-bar_w)//2
    y0 = height-68
    canvas.create_rectangle(x0, y0, x0+bar_w, y0+5, fill="#203444", outline="")
    progress = canvas.create_rectangle(x0, y0, x0+2, y0+5, fill="#36E0C0", outline="")
    status = canvas.create_text(width//2, y0+30, text="Initializing workspace…",
                                fill="#8EA5B4", font=("Segoe UI", 8))

    start_time = root.after_idle(lambda: None)
    phases = [
        (12, "Loading visual workspace…"),
        (34, "Preparing market engine…"),
        (57, "Loading Academy & Journal…"),
        (78, "Starting AI Command Center…"),
        (92, "Finalizing glass interface…"),
        (100, "Ready"),
    ]
    idx = 0
    tick = 0

    def animate():
        nonlocal idx, tick
        tick += 1
        target, label = phases[min(idx, len(phases)-1)]
        current = x0 + (bar_w * target / 100.0)
        canvas.coords(progress, x0, y0, current, y0+5)
        canvas.itemconfigure(status, text=label)
        # Small pulse on the accent edge.
        pulse = 0.55 + 0.45 * ((tick % 20) / 20.0)
        canvas.itemconfigure(progress, fill="#36E0C0" if pulse > 0.72 else "#27B89E")
        if idx < len(phases)-1:
            idx += 1
            root.after(190, animate)
        else:
            root.after(260, root.destroy)

    root.after(90, animate)
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


def _run_ui_smoke_test():
    """Render every primary page on the real Tk toolkit without network calls."""
    # Keep the smoke test deterministic and avoid network waits. Patch before
    # importing the main module so its imported callback also uses the stub.
    import news_data
    import market_data
    news_data.fetch_market_news = lambda callback, include_forex=False: callback([])
    market_data.MarketDataService.start = lambda self, market: None

    from TraderPlannerPro_v7_0_3 import App

    pages = (
        "home", "daily", "weekly", "plan", "check", "journal",
        "academy", "ai", "news", "calculators", "chart", "settings",
    )
    app = App()
    failures = []
    try:
        app.withdraw()
        startup_job = getattr(app, "_finish_startup_job", None)
        if startup_job:
            try:
                app.after_cancel(startup_job)
            except Exception:
                pass
            app._finish_startup_job = None

        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        for page in pages:
            try:
                app.show(page)
                app.update_idletasks()
                children = app.content.winfo_children()
                if not children:
                    failures.append(f"{page}: page rendered no widgets")
                    continue
                texts = []
                for widget in descendants(app.content):
                    try:
                        value = str(widget.cget("text"))
                        if value:
                            texts.append(value)
                    except Exception:
                        pass
                recovery = next((value for value in texts if "SAFE RECOVERY" in value), None)
                if recovery:
                    detail = next((value for value in texts if "SAFE RECOVERY" not in value and value not in {"Trader Planner Pro"}), "unknown page error")
                    failures.append(f"{page}: recovered after render error ({detail})")
                else:
                    print(f"UI page OK: {page}")
            except Exception as exc:
                failures.append(f"{page}: {type(exc).__name__}: {exc}")

        if failures:
            raise RuntimeError("Tk UI section smoke test failed:\\n- " + "\\n- ".join(failures))
        print(f"{APP} {VERSION} UI smoke-test: {len(pages)} pages rendered OK")
    finally:
        try:
            app.close_app()
        except Exception:
            try:
                app.destroy()
            except Exception:
                pass


def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--ui-smoke-test":
            _run_ui_smoke_test()
            return
        if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
            # Headless CI validation for Windows service runners.
            import importlib
            required = [
                "TraderPlannerPro_v7_0_3", "market_data", "news_data",
                "ai_assistant", "academy_visuals", "academy_diagrams",
                "glass_theme", "google_oauth", "statement_report", "webview_runner",
                "native_trading_desk", "tradingview_runner"
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
        if len(sys.argv) > 1 and sys.argv[1] == "--tradingview":
            from tradingview_runner import main as tradingview_main
            raise SystemExit(tradingview_main(sys.argv[2:]))
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
