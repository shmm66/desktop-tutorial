from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _set_dwm_backdrop(window, dark: bool, acrylic: bool = True) -> bool:
    """Apply the Windows 11 system material to the entire native window."""
    if not is_windows():
        return False
    try:
        hwnd = wintypes.HWND(window.winfo_id())
        dwmapi = ctypes.windll.dwmapi

        # DWMWA_SYSTEMBACKDROP_TYPE = 38.
        # DWMSBT_TRANSIENTWINDOW = 3 => Desktop Acrylic on Windows 11.
        attr = wintypes.DWORD(38)
        value = wintypes.DWORD(3 if acrylic else 2)
        result = dwmapi.DwmSetWindowAttribute(
            hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
        )
        if result != 0 and acrylic:
            # Fallback to Mica if the Acrylic material isn't available.
            value = wintypes.DWORD(2)
            dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
            )

        # Rounded corners.
        corner_attr = wintypes.DWORD(33)
        corner_value = wintypes.DWORD(2)
        dwmapi.DwmSetWindowAttribute(
            hwnd, corner_attr, ctypes.byref(corner_value), ctypes.sizeof(corner_value)
        )

        # Immersive dark mode. 20 is current; 19 is an older compatibility value.
        for dark_attr in (20, 19):
            try:
                flag = wintypes.BOOL(bool(dark))
                dwmapi.DwmSetWindowAttribute(
                    hwnd, wintypes.DWORD(dark_attr),
                    ctypes.byref(flag), ctypes.sizeof(flag)
                )
                break
            except Exception:
                continue

        # Keep a thin system border so the acrylic surface has a crisp edge.
        try:
            border_attr = wintypes.DWORD(34)
            border = wintypes.COLORREF(0x0038E6C3 if dark else 0x004F9E91)
            dwmapi.DwmSetWindowAttribute(
                hwnd, border_attr, ctypes.byref(border), ctypes.sizeof(border)
            )
        except Exception:
            pass
        return True
    except Exception:
        return False


def _apply_pywinstyles(window, dark: bool, style: str) -> bool:
    try:
        import pywinstyles
        native_style = style if style in {"acrylic", "mica", "transparent"} else "acrylic"
        pywinstyles.apply_style(window, native_style)
        if hasattr(pywinstyles, "change_header_color"):
            pywinstyles.change_header_color(window, "#071421" if dark else "#EEF5F8")
        if hasattr(pywinstyles, "change_title_color"):
            pywinstyles.change_title_color(window, "#F4FBFF" if dark else "#15212C")
        if hasattr(pywinstyles, "change_border_color"):
            pywinstyles.change_border_color(window, "#38E6C3" if dark else "#4F9E91")
        return True
    except Exception:
        return False


def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Use native Windows 11 Desktop Acrylic first, then a pywinstyles fallback.

    Microsoft documents DWMWA_SYSTEMBACKDROP_TYPE=38 with
    DWMSBT_TRANSIENTWINDOW=3 as Desktop Acrylic on Windows 11 22621+.
    """
    if not is_windows():
        return False

    def _apply():
        try:
            try:
                window.configure(bg="#071421" if dark else "#EEF5F8")
            except Exception:
                pass

            native_ok = _set_dwm_backdrop(window, dark=dark, acrylic=(style != "mica"))
            pywin_ok = _apply_pywinstyles(window, dark=dark, style=style)
            return native_ok or pywin_ok
        except Exception:
            return False

    try:
        window.after(80, _apply)
        return True
    except Exception:
        return _apply()


def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic") -> bool:
    return apply_glass(window, dark=dark, style=style)


def set_widget_glass(widget, opacity: float = 0.88) -> bool:
    """Apply real per-widget Windows translucency when pywinstyles exposes it.

    Tkinter itself has no widget-level alpha. On Windows 11, pywinstyles can
    apply opacity to individual Tk widgets, so the app uses that API and keeps
    a crisp border as a safe fallback when it is unavailable.
    """
    try:
        value = max(0.35, min(1.0, float(opacity)))
        widget.configure(
            highlightthickness=max(int(widget.cget("highlightthickness")), 1)
        )
        if is_windows():
            import pywinstyles
            setter = getattr(pywinstyles, "set_opacity", None)
            if setter is not None:
                try:
                    setter(widget, value=value)
                except TypeError:
                    setter(widget, value)
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
