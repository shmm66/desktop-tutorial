from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.config import APP_NAME, APP_VERSION, AppConfig


class AppShell(tk.Tk):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.title(f"{APP_NAME} • V5")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(bg="#0b1020")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#0b1020", borderwidth=0)
        style.configure("TFrame", background="#0b1020")
        style.configure("TLabel", background="#0b1020", foreground="#e8eefc")
        style.configure("TButton", padding=8)

        header = ttk.Frame(self, padding=(20, 16))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, font=("Segoe UI", 22, "bold")).pack(side="left")
        ttk.Label(header, text=APP_VERSION, font=("Segoe UI", 10)).pack(side="right")

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        for title in ("Home", "Planner", "Journal", "Risk", "Market", "Reports", "Settings"):
            frame = ttk.Frame(tabs, padding=24)
            ttk.Label(frame, text=title, font=("Segoe UI", 18, "bold")).pack(anchor="e")
            ttk.Label(frame, text="V5 migration scaffold — feature module will be connected here.").pack(anchor="e", pady=12)
            tabs.add(frame, text=title)


def run(config: AppConfig) -> None:
    AppShell(config).mainloop()
