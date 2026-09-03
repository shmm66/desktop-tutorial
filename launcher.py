import os, sys, time, tempfile, threading
from pathlib import Path
import tkinter as tk

APP = 'Trader Planner Pro'
VERSION = '7.0.2'


def resource_root():
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))


def show_splash():
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg='#061019')
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    width, height = min(1100, sw - 80), min(735, sh - 100)
    root.geometry(f'{width}x{height}+{(sw-width)//2}+{(sh-height)//2}')

    try:
        from PIL import Image, ImageTk
        from branding_assets import materialize_assets
        temp = Path(tempfile.gettempdir()) / 'TraderPlannerPro_branding'
        logo_path, splash_path = materialize_assets(temp)
        image = Image.open(splash_path).convert('RGB')
        image.thumbnail((width - 30, height - 125), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        tk.Label(root, image=photo, bg='#061019').pack(padx=15, pady=(12, 0))
        root._photo = photo
    except Exception:
        # Safe fallback: startup must never crash because of branding assets.
        tk.Canvas(root, bg='#061019', highlightthickness=0).pack(fill='both', expand=True)
        tk.Label(root, text='🐂   TRADER   🐻', fg='#E7B85B', bg='#061019', font=('Segoe UI', 34, 'bold')).place(relx=.5, rely=.43, anchor='center')
        tk.Label(root, text='PLANNER PRO', fg='white', bg='#061019', font=('Segoe UI', 24, 'bold')).place(relx=.5, rely=.51, anchor='center')

    status = tk.Label(root, text='Loading Trader Planner Pro...', fg='white', bg='#061019', font=('Segoe UI', 13))
    status.pack(pady=(7, 5))
    bar = tk.Canvas(root, width=max(300, width//2), height=14, bg='#061019', highlightthickness=0)
    bar.pack()
    percent = tk.Label(root, text='0%', fg='#E7B85B', bg='#061019', font=('Segoe UI', 11, 'bold'))
    percent.pack(pady=(4, 0))
    tk.Label(root, text=f'Version {VERSION}', fg='#9CA7AF', bg='#061019', font=('Segoe UI', 10)).pack(pady=(5, 8))

    bar_w = max(300, width//2)
    def tick(p=0):
        if p > 100:
            root.destroy()
            return
        bar.delete('all')
        bar.create_rectangle(0, 0, bar_w, 14, outline='#33404A', fill='#0D1821')
        bar.create_rectangle(0, 0, int(bar_w*p/100), 14, outline='', fill='#E7B85B')
        percent.config(text=f'{p}%')
        status.config(text='Loading Trader Planner Pro...' if p < 100 else 'Ready')
        root.after(22, lambda: tick(p + 2))

    root.after(80, tick)
    root.mainloop()


def main():
    show_splash()
    from TraderPlannerPro_v7 import App
    app = App()
    try:
        from PIL import Image, ImageTk
        from branding_assets import materialize_assets
        temp = Path(tempfile.gettempdir()) / 'TraderPlannerPro_branding'
        logo_path, _ = materialize_assets(temp)
        logo = ImageTk.PhotoImage(Image.open(logo_path).convert('RGB').resize((64,64)))
        app.iconphoto(True, logo)
        app._app_icon = logo
    except Exception:
        pass
    app.mainloop()


if __name__ == '__main__':
    main()
