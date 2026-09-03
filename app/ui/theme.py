from __future__ import annotations

BG = "#08101f"
SURFACE = "#101b31"
SURFACE_2 = "#14233e"
BORDER = "#263858"
TEXT = "#eef4ff"
MUTED = "#91a3c1"
ACCENT = "#21d4b2"
ACCENT_2 = "#58a6ff"
DANGER = "#ef476f"
WARNING = "#f6c85f"

FONT = "Segoe UI"
FA_FONT = "Segoe UI"


def apply(root) -> None:
    from tkinter import ttk

    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE)
    style.configure("TLabel", background=BG, foreground=TEXT, font=(FONT, 10))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=(FONT, 9))
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=(FONT, 20, "bold"))
    style.configure("Hero.TLabel", background=BG, foreground=ACCENT, font=(FONT, 28, "bold"))
    style.configure("CardTitle.TLabel", background=SURFACE, foreground=TEXT, font=(FONT, 11, "bold"))
    style.configure("CardValue.TLabel", background=SURFACE, foreground=TEXT, font=(FONT, 20, "bold"))
    style.configure("TButton", background=SURFACE_2, foreground=TEXT, bordercolor=BORDER, padding=(12, 8), font=(FONT, 9, "bold"))
    style.map("TButton", background=[("active", ACCENT_2)], foreground=[("active", "white")])
    style.configure("Accent.TButton", background=ACCENT, foreground="#041019")
    style.map("Accent.TButton", background=[("active", "#5be5cb")])
    style.configure("Danger.TButton", background=DANGER, foreground="white")
    style.configure("TEntry", fieldbackground=SURFACE_2, foreground=TEXT, insertcolor=TEXT, bordercolor=BORDER, padding=8)
    style.configure("TCombobox", fieldbackground=SURFACE_2, foreground=TEXT, arrowcolor=TEXT, padding=7)
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED, padding=(12, 8))
    style.map("TNotebook.Tab", background=[("selected", SURFACE_2)], foreground=[("selected", ACCENT)])
