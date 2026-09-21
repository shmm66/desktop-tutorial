from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

WINDOW_BACKDROP = 38
BACKDROP_AUTO = 0
BACKDROP_MICA = 2
BACKDROP_ACRYLIC = 3
DARK_MODE_ATTRIBUTES = (20, 19)

def is_windows() -> bool:
    return sys.platform.startswith("win")

def _hwnd(window):
    try:
        return wintypes.HWND(window.winfo_id())
    except Exception:
        return None

def _dwm_set(hwnd, attribute, value, size):
    try:
        dwmapi = ctypes.windll.dwmapi
        return dwmapi.DwmSetWindowAttribute(
            hwnd,
            wintypes.DWORD(attribute),
            ctypes.byref(value),
            size,
        ) == 0
    except Exception:
        return False

def _apply_native_backdrop(window, dark=True, acrylic=True):
    if not is_windows():
        return False
    hwnd = _hwnd(window)
    if not hwnd:
        return False

    backdrop = wintypes.DWORD(BACKDROP_ACRYLIC if acrylic else BACKDROP_MICA)
    ok = _dwm_set(hwnd, WINDOW_BACKDROP, backdrop, ctypes.sizeof(backdrop))

    for attr in DARK_MODE_ATTRIBUTES:
        flag = wintypes.BOOL(bool(dark))
        if _dwm_set(hwnd, attr, flag, ctypes.sizeof(flag)):
            ok = True
            break

    try:
        margin = wintypes.INT(-1)
        dwmapi = ctypes.windll.dwmapi
        margins = type("MARGINS", (ctypes.Structure,), {
            "_fields_": [("cxLeftWidth", ctypes.c_int), ("cxRightWidth", ctypes.c_int),
                         ("cyTopHeight", ctypes.c_int), ("cyBottomHeight", ctypes.c_int)]
        })()
        margins.cxLeftWidth = margins.cxRightWidth = margins.cyTopHeight = margins.cyBottomHeight = -1
        dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
        ok = True
    except Exception:
        pass

    return ok

def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Apply Windows 11 native acrylic/mica plus a glass-friendly surface.

    Tk itself does not expose per-pixel alpha for child widgets. The reliable
    glass effect therefore combines DWM acrylic on the top-level with
    translucent native widget surfaces where pywinstyles supports them.
    """
    if not is_windows():
        return False

    style = style if style in {"acrylic", "mica", "transparent"} else "acrylic"
    try:
        window.configure(bg="#061019" if dark else "#EEF5F8")
    except Exception:
        pass

    native_ok = False
    try:
        import pywinstyles
        if style == "mica":
            pywinstyles.apply_style(window, "mica")
        elif style == "transparent":
            pywinstyles.apply_style(window, "transparent")
        else:
            pywinstyles.apply_style(window, "acrylic")
        if hasattr(pywinstyles, "change_header_color"):
            pywinstyles.change_header_color(window, "#08131F" if dark else "#E8F2F7")
        if hasattr(pywinstyles, "change_title_color"):
            pywinstyles.change_title_color(window, "#F4FBFF" if dark else "#13202A")
        if hasattr(pywinstyles, "change_border_color"):
            pywinstyles.change_border_color(window, "#4BE8C8" if dark else "#0E987E")
        native_ok = True
    except Exception:
        native_ok = _apply_native_backdrop(window, dark=dark, acrylic=(style != "mica"))

    # Keep the window itself visually solid enough for legibility while the
    # DWM backdrop gives the surface its real acrylic behavior.
    try:
        window.attributes("-alpha", 0.985)
    except Exception:
        pass
    return native_ok

def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic") -> bool:
    try:
        window.after(60, lambda: apply_glass(window, dark=dark, style=style))
        return True
    except Exception:
        return False

def set_widget_glass(widget, opacity: float = 0.90) -> bool:
    """Make supported Tk child surfaces translucent without touching text alpha."""
    if not is_windows():
        return False
    try:
        import pywinstyles
        value = max(0.62, min(float(opacity), 0.985))
        try:
            pywinstyles.set_opacity(widget, value=value)
            return True
        except Exception:
            return False
    except Exception:
        return False

def apply_glass_surface(widget, opacity: float = 0.90, border_color: str = "") -> bool:
    ok = set_widget_glass(widget, opacity)
    if border_color:
        try:
            widget.configure(highlightbackground=border_color, highlightcolor=border_color)
        except Exception:
            pass
    return ok
