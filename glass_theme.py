from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _set_attr(dwmapi, hwnd, attr, value, size):
    try:
        return dwmapi.DwmSetWindowAttribute(hwnd, wintypes.DWORD(attr), ctypes.byref(value), size) == 0
    except Exception:
        return False


def _set_dwm_backdrop(window, dark: bool, acrylic: bool = True) -> bool:
    """Apply Windows 11 native system backdrop with graceful fallbacks.

    DWMWA_SYSTEMBACKDROP_TYPE = 38:
      2 = Mica
      3 = Desktop Acrylic
    """
    if not is_windows():
        return False
    try:
        hwnd = wintypes.HWND(window.winfo_id())
        dwmapi = ctypes.windll.dwmapi

        # Prefer Desktop Acrylic, then Mica, then no backdrop.
        requested = wintypes.DWORD(3 if acrylic else 2)
        ok = _set_attr(dwmapi, hwnd, 38, requested, ctypes.sizeof(requested))
        if not ok and acrylic:
            mica = wintypes.DWORD(2)
            ok = _set_attr(dwmapi, hwnd, 38, mica, ctypes.sizeof(mica))

        # Rounded corners.
        corner = wintypes.DWORD(2)
        _set_attr(dwmapi, hwnd, 33, corner, ctypes.sizeof(corner))

        # Immersive dark mode (current + compatibility).
        for dark_attr in (20, 19):
            flag = wintypes.BOOL(bool(dark))
            if _set_attr(dwmapi, hwnd, dark_attr, flag, ctypes.sizeof(flag)):
                break

        # Prefer automatic system border rather than a heavy opaque frame.
        try:
            border_attr = wintypes.DWORD(34)
            # COLORREF is 0x00BBGGRR.
            border = wintypes.DWORD(0x00C0E637 if dark else 0x00918D4F)
            _set_attr(dwmapi, hwnd, border_attr, border, ctypes.sizeof(border))
        except Exception:
            pass
        return ok
    except Exception:
        return False


def _apply_pywinstyles(window, dark: bool, style: str) -> bool:
    try:
        import pywinstyles

        native_style = style if style in {"acrylic", "mica", "transparent"} else "acrylic"
        pywinstyles.apply_style(window, native_style)

        if hasattr(pywinstyles, "change_header_color"):
            pywinstyles.change_header_color(window, "#07121D" if dark else "#F1F7F9")
        if hasattr(pywinstyles, "change_title_color"):
            pywinstyles.change_title_color(window, "#F3FBFF" if dark else "#14232E")
        if hasattr(pywinstyles, "change_border_color"):
            pywinstyles.change_border_color(window, "#36DDBE" if dark else "#4F9E91")
        return True
    except Exception:
        return False


def _configure_window_transparency(window, dark: bool):
    """Tune the client/window alpha without relying on per-widget alpha.

    Tk child widgets are opaque by design, so the real glass effect comes from
    the Windows compositor backdrop + a lightly translucent top-level surface.
    """
    try:
        # Keep text/controls crisp while allowing the DWM material to breathe through.
        window.wm_attributes("-alpha", 0.94 if dark else 0.965)
    except Exception:
        pass
    try:
        window.configure(bg="#07121D" if dark else "#F1F7F9")
    except Exception:
        pass


def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Apply a production-safe native Windows 11 Acrylic surface."""
    if not is_windows():
        return False

    def _apply():
        try:
            _configure_window_transparency(window, dark)
            native_ok = _set_dwm_backdrop(window, dark=dark, acrylic=(style != "mica"))
            pywin_ok = _apply_pywinstyles(window, dark=dark, style=style)
            return native_ok or pywin_ok
        except Exception:
            return False

    try:
        result = _apply()
        # Re-apply after mapping because DWM can reset backdrop state on first show.
        window.after(80, _apply)
        window.bind("<Map>", lambda _e: window.after(45, _apply), add="+")
        return result
    except Exception:
        return _apply()


def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic") -> bool:
    return apply_glass(window, dark=dark, style=style)


def set_widget_glass(widget, opacity: float = 0.88) -> bool:
    """Give a Tk surface the visual language of a glass card.

    Tk cannot apply real per-widget alpha, so we use the compositor for the
    containing window and preserve a subtle 1px light/colored edge per card.
    """
    try:
        alpha = max(0.25, min(float(opacity), 1.0))
        thickness = 1 if alpha >= 0.70 else 0
        widget.configure(highlightthickness=thickness)
        return True
    except Exception:
        return False


def apply_glass_after_map(window, dark: bool = True, style: str = "acrylic") -> bool:
    try:
        window.update_idletasks()
        window.after(50, lambda: apply_glass(window, dark=dark, style=style))
        return True
    except Exception:
        return apply_glass(window, dark=dark, style=style)
