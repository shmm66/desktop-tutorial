from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _native_backdrop(window, dark: bool, acrylic: bool = True) -> bool:
    """Apply the real Windows 11 DWM material to a native HWND."""
    if not is_windows():
        return False
    try:
        hwnd = wintypes.HWND(window.winfo_id())
        dwm = ctypes.windll.dwmapi

        # DWMWA_SYSTEMBACKDROP_TYPE = 38
        # 3 = Desktop Acrylic, 2 = Mica.
        attr = wintypes.DWORD(38)
        material = wintypes.DWORD(3 if acrylic else 2)
        hr = dwm.DwmSetWindowAttribute(
            hwnd, attr, ctypes.byref(material), ctypes.sizeof(material)
        )
        if hr != 0 and acrylic:
            material = wintypes.DWORD(2)
            hr = dwm.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(material), ctypes.sizeof(material)
            )

        # Rounded corners.
        corner = wintypes.DWORD(33)
        corner_value = wintypes.DWORD(2)
        dwm.DwmSetWindowAttribute(
            hwnd, corner, ctypes.byref(corner_value), ctypes.sizeof(corner_value)
        )

        # Dark title-bar support.
        for dark_attr in (20, 19):
            try:
                flag = wintypes.BOOL(bool(dark))
                dwm.DwmSetWindowAttribute(
                    hwnd,
                    wintypes.DWORD(dark_attr),
                    ctypes.byref(flag),
                    ctypes.sizeof(flag),
                )
                break
            except Exception:
                continue

        # Light, crisp border around the glass surface.
        try:
            border = wintypes.DWORD(0x0038E6C3 if dark else 0x006C9DA8)
            dwm.DwmSetWindowAttribute(
                hwnd, wintypes.DWORD(34),
                ctypes.byref(border), ctypes.sizeof(border)
            )
        except Exception:
            pass
        return hr == 0
    except Exception:
        return False


def _pywinstyles_fallback(window, dark: bool, style: str) -> bool:
    try:
        import pywinstyles
        native = style if style in {"acrylic", "mica", "transparent"} else "acrylic"
        pywinstyles.apply_style(window, native)
        if hasattr(pywinstyles, "change_header_color"):
            pywinstyles.change_header_color(window, "#06111D" if dark else "#EAF4F7")
        if hasattr(pywinstyles, "change_title_color"):
            pywinstyles.change_title_color(window, "#F4FBFF" if dark else "#17232D")
        if hasattr(pywinstyles, "change_border_color"):
            pywinstyles.change_border_color(window, "#38E6C3" if dark else "#6C9DA8")
        return True
    except Exception:
        return False


def _try_alpha(window, value: float = 0.975):
    try:
        window.attributes("-alpha", max(0.90, min(1.0, float(value))))
    except Exception:
        pass


def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Apply a real system glass backdrop, then use Tk surfaces as glass layers.
    
    Tk cannot blur individual child frames, so the actual blur/material is applied
    to the native window by DWM; child widgets use carefully tuned translucent-look
    surfaces and borders for the glassmorphism composition.
    """
    if not is_windows():
        return False

    def _apply():
        try:
            window.configure(bg="#06111D" if dark else "#EAF4F7")
        except Exception:
            pass
        _try_alpha(window, 0.98)
        native = _native_backdrop(window, dark=dark, acrylic=(style != "mica"))
        fallback = _pywinstyles_fallback(window, dark=dark, style=style)
        try:
            window.update_idletasks()
        except Exception:
            pass
        return native or fallback

    try:
        window.after(40, _apply)
        return True
    except Exception:
        return _apply()


def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic") -> bool:
    return apply_glass(window, dark=dark, style=style)


def set_widget_glass(widget, opacity: float = 0.86) -> bool:
    """Give a Tk widget the visual treatment that sits on top of native Acrylic."""
    try:
        opacity = max(0.55, min(1.0, float(opacity)))
        widget.configure(
            highlightthickness=max(1, int(round((1.0 - opacity) * 4))),
            bd=0,
        )
        return True
    except Exception:
        return False


def apply_glass_after_map(window, dark: bool = True, style: str = "acrylic") -> bool:
    try:
        window.update_idletasks()
        window.after(60, lambda: apply_glass(window, dark=dark, style=style))
        return True
    except Exception:
        return apply_glass(window, dark=dark, style=style)
