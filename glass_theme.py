from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _hwnd(window):
    try:
        return wintypes.HWND(int(window.winfo_id()))
    except Exception:
        return None


def _dwm_attr(hwnd, attribute: int, value, value_type):
    if not hwnd or not is_windows():
        return False
    try:
        dwmapi = ctypes.windll.dwmapi
        c_value = value_type(value)
        return dwmapi.DwmSetWindowAttribute(
            hwnd,
            wintypes.DWORD(attribute),
            ctypes.byref(c_value),
            ctypes.sizeof(c_value),
        ) == 0
    except Exception:
        return False


def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Apply a Windows 11 native acrylic/mica backdrop to a top-level window.

    Tk widgets remain normal controls, while the window behind them receives
    the native DWM blur/backdrop. This is the most reliable glass treatment
    available to a desktop Tk application without replacing the entire UI
    toolkit.
    """
    if not is_windows():
        return False

    try:
        window.configure(bg="#09111B" if dark else "#F2F6F8")
    except Exception:
        pass

    # pywinstyles provides a robust Windows implementation when available.
    try:
        import pywinstyles

        native_style = style if style in {"acrylic", "mica", "transparent"} else "acrylic"
        pywinstyles.apply_style(window, native_style)
        if hasattr(pywinstyles, "change_header_color"):
            pywinstyles.change_header_color(window, "#0A1320" if dark else "#EAF1F5")
        if hasattr(pywinstyles, "change_title_color"):
            pywinstyles.change_title_color(window, "#F5FBFF" if dark else "#16232D")
        if hasattr(pywinstyles, "change_border_color"):
            pywinstyles.change_border_color(window, "#42E1C0" if dark else "#128A74")
        return True
    except Exception:
        pass

    hwnd = _hwnd(window)
    if hwnd is None:
        return False

    ok = False
    # DWMWA_SYSTEMBACKDROP_TYPE: 2=Mica, 3=Desktop Acrylic, 4=Tabbed.
    backdrop = 3 if style == "acrylic" else (2 if style == "mica" else 1)
    ok = _dwm_attr(hwnd, 38, backdrop, wintypes.DWORD) or ok

    # DWMWA_USE_IMMERSIVE_DARK_MODE.
    for attr in (20, 19):
        if _dwm_attr(hwnd, attr, bool(dark), wintypes.BOOL):
            ok = True
            break

    # DWMWA_WINDOW_CORNER_PREFERENCE: 2=round.
    ok = _dwm_attr(hwnd, 33, 2, wintypes.DWORD) or ok
    return ok


def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic") -> bool:
    try:
        window.after(60, lambda: apply_glass(window, dark=dark, style=style))
        return True
    except Exception:
        return False


def set_widget_glass(widget, opacity: float = 0.88) -> bool:
    """Best-effort translucent surface treatment for native/top-level widgets.

    Tk child frames do not expose separate DWM surfaces on Windows. We therefore
    never pretend that they are independently blurred windows. When a platform
    implementation can set opacity safely, use it; otherwise the parent native
    acrylic backdrop remains the real glass layer.
    """
    if not is_windows():
        return False

    try:
        import pywinstyles

        value = max(0.62, min(float(opacity), 0.98))
        setter = getattr(pywinstyles, "set_opacity", None)
        if setter is None:
            return False
        try:
            setter(widget, value=value)
            return True
        except Exception:
            return False
    except Exception:
        return False
