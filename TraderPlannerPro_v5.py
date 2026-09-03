# Trader Planner Pro V5 release entrypoint
# Copyright (c) 2026 Seyed Hadi Mir Mohammad (سید هادی میر محمد), Gorgan, Iran.
# Free to use and fork; original project copyright and attribution must remain intact.
"""Release wrapper: keeps the proven V5 application logic and applies the final visual theme.
Persian: B Titr when installed. English: Times New Roman.
"""
import runpy
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

PALETTE = {
    "#070d19": "#F5F1E8",  # warm pastel cream background
    "#0e182a": "#EAF1F2",  # pastel blue panel
    "#14223a": "#DCE9EE",  # pastel blue secondary panel
    "#eef5ff": "#243447",  # readable dark text
    "#91a5c6": "#6F7F8C",  # muted text
    "#42d9b5": "#79D8C0",  # mint accent
    "#243754": "#C5D6DC",  # soft border
    "#1e476b": "#B8D5DE",  # selected row
}
PERSIAN_FONT = "B Titr"
ENGLISH_FONT = "Times New Roman"


def has_persian(text):
    return any("\u0600" <= ch <= "\u06ff" for ch in str(text or ""))


def choose_font(text, requested):
    size = 10
    weight = "normal"
    if isinstance(requested, (tuple, list)):
        if len(requested) > 1 and isinstance(requested[1], int):
            size = requested[1]
        if len(requested) > 2:
            weight = requested[2]
    elif isinstance(requested, str):
        return requested
    family = PERSIAN_FONT if has_persian(text) else ENGLISH_FONT
    # B Titr is a Windows font; if it is absent, use a safe Persian fallback.
    if family == PERSIAN_FONT:
        try:
            if PERSIAN_FONT not in tkfont.families():
                family = "Tahoma"
        except tk.TclError:
            family = "Tahoma"
    return (family, size, weight)


def map_color(value):
    if isinstance(value, str):
        return PALETTE.get(value.lower(), value)
    return value


def patch_kwargs(kwargs):
    for key in ("bg", "background", "fg", "foreground", "activebackground", "activeforeground",
                "highlightbackground", "highlightcolor", "insertbackground", "selectbackground",
                "selectforeground"):
        if key in kwargs:
            kwargs[key] = map_color(kwargs[key])
    if "font" in kwargs:
        kwargs["font"] = choose_font(kwargs.get("text", ""), kwargs["font"])
    return kwargs


def wrap_widget(cls):
    def factory(*args, **kwargs):
        return cls(*args, **patch_kwargs(kwargs))
    return factory


for _name in ("Frame", "Label", "Button", "Entry", "Text", "Canvas", "Checkbutton", "Radiobutton", "Listbox", "Scale"):
    if hasattr(tk, _name):
        setattr(tk, _name, wrap_widget(getattr(tk, _name)))

# Keep canvas drawing consistent with the pastel palette.
_original_canvas_line = tk.Canvas.create_line
_original_canvas_text = tk.Canvas.create_text
_original_canvas_rectangle = tk.Canvas.create_rectangle


def _canvas_line(self, *args, **kwargs):
    if "fill" in kwargs:
        kwargs["fill"] = map_color(kwargs["fill"])
    return _original_canvas_line(self, *args, **kwargs)


def _canvas_text(self, *args, **kwargs):
    if "fill" in kwargs:
        kwargs["fill"] = map_color(kwargs["fill"])
    if "font" in kwargs:
        kwargs["font"] = choose_font(kwargs.get("text", ""), kwargs["font"])
    return _original_canvas_text(self, *args, **kwargs)


def _canvas_rectangle(self, *args, **kwargs):
    if "fill" in kwargs:
        kwargs["fill"] = map_color(kwargs["fill"])
    if "outline" in kwargs:
        kwargs["outline"] = map_color(kwargs["outline"])
    return _original_canvas_rectangle(self, *args, **kwargs)


tk.Canvas.create_line = _canvas_line
tk.Canvas.create_text = _canvas_text
tk.Canvas.create_rectangle = _canvas_rectangle

# Patch ttk styling values used by the proven application.
_original_style_configure = ttk.Style.configure
_original_style_map = ttk.Style.map


def _style_configure(self, tag, *args, **kwargs):
    patch_kwargs(kwargs)
    return _original_style_configure(self, tag, *args, **kwargs)


def _style_map(self, tag, *args, **kwargs):
    for state in ("background", "foreground", "fieldbackground"):
        if state in kwargs:
            value = kwargs[state]
            if isinstance(value, list):
                kwargs[state] = [(s, map_color(v)) for s, v in value]
    return _original_style_map(self, tag, *args, **kwargs)


ttk.Style.configure = _style_configure
ttk.Style.map = _style_map

# Execute the tested application exactly as a normal script.
runpy.run_path("TraderPlannerPro_v4.py", run_name="__main__")
