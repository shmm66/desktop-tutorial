from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.core.config import AppConfig, APP_NAME, APP_VERSION
from .theme import ACCENT, BG, MUTED, SURFACE, SURFACE_2, TEXT, apply

if not hasattr(ttk, "BooleanVar"):
    ttk.BooleanVar = tk.BooleanVar  # type: ignore[attr-defined]

from .journal_panel import JournalPanel
from .views import CalculatorView, ChecklistView, HomeView, MarketView, PlannerView, ReportsView, SessionsView, SettingsView


class AppShell(tk.Tk):
    """Thin UI shell; business logic remains in domains/services/repositories."""

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config_obj = config
        self.title(f"{APP_NAME} • V5")
        self.geometry("1440x900")
        self.minsize(1180, 760)
        apply(self)
        self.active = None
        self.views = {}
        self._build_shell()
        self.show("home")

    def _build_shell(self):
        header = tk.Frame(self, bg=BG, height=72)
        header.pack(fill="x", side="top")
        tk.Label(header, text="TRADER PLANNER PRO", bg=BG, fg=ACCENT, font=("Segoe UI", 20, "bold")).pack(side="left", padx=22, pady=16)
        tk.Label(header, text="V5 • Professional Trading Workspace", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left", padx=4)
        ttk.Button(header, text="☰  Menu", command=self.toggle_menu).pack(side="right", padx=16, pady=14)

        self.menu = tk.Frame(self, bg=SURFACE, width=250, highlightthickness=1, highlightbackground="#263858")
        self.menu.pack(side="left", fill="y")
        self.menu.pack_propagate(False)
        tk.Label(self.menu, text="WORKSPACE", bg=SURFACE, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="e", padx=18, pady=(22, 10))
        items=[("⌂  Home","home"),("▣  Trading Plan","planner"),("☑  Checklist","checklist"),("▤  Journal","journal"),("◈  Forex Calculator","calculator"),("◉  Market / Forex Factory","market"),("◷  Sessions","sessions"),("▥  Reports","reports"),("⚙  Settings","settings")]
        for label,key in items:
            b=tk.Button(self.menu,text=label,command=lambda k=key:self.show(k),anchor="e",bg=SURFACE,fg=TEXT,activebackground=SURFACE_2,activeforeground=ACCENT,relief="flat",bd=0,font=("Segoe UI",10),padx=18,pady=10)
            b.pack(fill="x",pady=1)
        tk.Label(self.menu,text="\nFree • Local-first • Exportable\nSeyed Hadi Mir Mohammad",bg=SURFACE,fg=MUTED,font=("Segoe UI",8),justify="right").pack(side="bottom",anchor="e",padx=18,pady=18)

        self.content=tk.Frame(self,bg=BG);self.content.pack(side="left",fill="both",expand=True,padx=18,pady=8)

    def toggle_menu(self):
        if self.menu.winfo_ismapped(): self.menu.pack_forget()
        else:self.menu.pack(side="left",fill="y",before=self.content);self.menu.pack_propagate(False)

    def show(self,key):
        if self.active: self.active.pack_forget()
        if key not in self.views:
            factory={
                "home":lambda:HomeView(self.content,self.config_obj,self.show),
                "planner":lambda:PlannerView(self.content,self.config_obj),
                "checklist":lambda:ChecklistView(self.content),
                "journal":lambda:JournalPanel(self.content,self.config_obj),
                "calculator":lambda:CalculatorView(self.content),
                "market":lambda:MarketView(self.content),
                "sessions":lambda:SessionsView(self.content),
                "reports":lambda:ReportsView(self.content,self.config_obj),
                "settings":lambda:SettingsView(self.content,self.config_obj),
            }
            self.views[key]=factory[key]()
        self.active=self.views[key];self.active.pack(fill="both",expand=True)
        if key=="home" and hasattr(self.active,"refresh"):self.active.refresh()


def run(config: AppConfig)->None:
    AppShell(config).mainloop()
