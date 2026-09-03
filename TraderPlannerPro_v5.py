# Trader Planner Pro V5 — polished pastel release entrypoint
# Copyright (c) 2026 Seyed Hadi Mir Mohammad (سید هادی میر محمد), Gorgan, Iran.
"""V5 visual layer: modern pastel UI + bilingual typography over the tested V4 application.

The V4 application is bundled as data by the Windows build and resolved relative to
PyInstaller's extraction directory. This avoids relying on the installer's working
directory, which caused FileNotFoundError on installed builds.
"""

import os
import runpy
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

PALETTE = {
    "#070d19": "#F7F4EE",
    "#0e182a": "#EEF5F5",
    "#14223a": "#E4EEF1",
    "#eef5ff": "#203040",
    "#91a5c6": "#667784",
    "#42d9b5": "#76D7C3",
    "#243754": "#C9D9DE",
    "#1e476b": "#B9DCE0",
    "#06131c": "#173039",
}
PERSIAN_FONT = "B Titr"
ENGLISH_FONT = "Times New Roman"

_ORIGINAL_CLASSES = {
    name: getattr(tk, name)
    for name in (
        "Frame", "Label", "Button", "Entry", "Text", "Canvas",
        "Checkbutton", "Radiobutton", "Listbox", "Scale",
    )
    if hasattr(tk, name)
}
_ORIGINAL_CANVAS = _ORIGINAL_CLASSES["Canvas"]
_original_canvas_line = _ORIGINAL_CANVAS.create_line
_original_canvas_text = _ORIGINAL_CANVAS.create_text
_original_canvas_rectangle = _ORIGINAL_CANVAS.create_rectangle


def _has_persian(text):
    return any("\u0600" <= ch <= "\u06ff" for ch in str(text or ""))


def _font_exists(family):
    try:
        return family.lower() in {f.lower() for f in tkfont.families()}
    except tk.TclError:
        return False


def _choose_font(text, requested):
    size, weight = 10, "normal"
    if isinstance(requested, (tuple, list)):
        if len(requested) > 1 and isinstance(requested[1], (int, float)):
            size = int(requested[1])
        if len(requested) > 2:
            weight = requested[2]
    family = PERSIAN_FONT if _has_persian(text) else ENGLISH_FONT
    if family == PERSIAN_FONT and not _font_exists(PERSIAN_FONT):
        family = "Tahoma"
    if family == ENGLISH_FONT and not _font_exists(ENGLISH_FONT):
        family = "Georgia"
    return (family, size, weight)


def _map_color(value):
    if isinstance(value, str):
        return PALETTE.get(value.lower(), value)
    return value


def _patch_kwargs(kwargs):
    for key in (
        "bg", "background", "fg", "foreground", "activebackground",
        "activeforeground", "highlightbackground", "highlightcolor",
        "insertbackground", "selectbackground", "selectforeground",
    ):
        if key in kwargs:
            kwargs[key] = _map_color(kwargs[key])
    if "font" in kwargs:
        kwargs["font"] = _choose_font(kwargs.get("text", ""), kwargs["font"])
    if kwargs.get("_tpp_control") == "button":
        kwargs.pop("_tpp_control", None)
        kwargs.setdefault("relief", "flat")
        kwargs.setdefault("bd", 0)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("cursor", "hand2")
    return kwargs


def _wrap_widget(cls, name):
    def factory(*args, **kwargs):
        if name == "Button":
            kwargs["_tpp_control"] = "button"
        return cls(*args, **_patch_kwargs(kwargs))
    factory.__name__ = name
    return factory


def _canvas_line(self, *args, **kwargs):
    if "fill" in kwargs:
        kwargs["fill"] = _map_color(kwargs["fill"])
    return _original_canvas_line(self, *args, **kwargs)


def _canvas_text(self, *args, **kwargs):
    if "fill" in kwargs:
        kwargs["fill"] = _map_color(kwargs["fill"])
    if "font" in kwargs:
        kwargs["font"] = _choose_font(kwargs.get("text", ""), kwargs["font"])
    return _original_canvas_text(self, *args, **kwargs)


def _canvas_rectangle(self, *args, **kwargs):
    for key in ("fill", "outline"):
        if key in kwargs:
            kwargs[key] = _map_color(kwargs[key])
    return _original_canvas_rectangle(self, *args, **kwargs)

_ORIGINAL_CANVAS.create_line = _canvas_line
_ORIGINAL_CANVAS.create_text = _canvas_text
_ORIGINAL_CANVAS.create_rectangle = _canvas_rectangle

for _name, _cls in _ORIGINAL_CLASSES.items():
    setattr(tk, _name, _wrap_widget(_cls, _name))

_original_style_configure = ttk.Style.configure
_original_style_map = ttk.Style.map


def _style_configure(self, tag, *args, **kwargs):
    _patch_kwargs(kwargs)
    if tag == "Treeview":
        kwargs.setdefault("rowheight", 36)
        kwargs.setdefault("font", _choose_font("", (ENGLISH_FONT, 10)))
        kwargs.setdefault("headingfont", _choose_font("", (ENGLISH_FONT, 10, "bold")))
    return _original_style_configure(self, tag, *args, **kwargs)


def _style_map(self, tag, *args, **kwargs):
    for state in ("background", "foreground", "fieldbackground"):
        if state in kwargs and isinstance(kwargs[state], list):
            kwargs[state] = [(s, _map_color(v)) for s, v in kwargs[state]]
    return _original_style_map(self, tag, *args, **kwargs)


ttk.Style.configure = _style_configure
ttk.Style.map = _style_map

_base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
_v4_path = os.path.join(_base_dir, "TraderPlannerPro_v4.py")
if not os.path.isfile(_v4_path):
    raise FileNotFoundError(f"Bundled application component not found: {_v4_path}")

# V4 defines App.title(), which shadows Tk's window-title method. Loading it as
# __main__ therefore calls the page-title method before self.content exists.
# Load V4 without executing its main block, then instantiate a tiny compatibility
# subclass whose one-argument title call is the real window-title operation.
_v4 = runpy.run_path(_v4_path, run_name="TraderPlannerPro_v4")
_BaseApp = _v4["App"]
_V4_APP_NAME = _v4.get("APP", "Trader Planner Pro")


class App(_BaseApp):
    def title(self, a, b=""):
        if not b:
            return tk.Tk.title(self, a)
        return super().title(a, b)


if __name__ == "__main__":
    App().mainloop()
