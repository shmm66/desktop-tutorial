from __future__ import annotations

import sys


def apply_glass(window, dark=True, style="acrylic"):
    """Apply a real Windows Acrylic backdrop when available.

    The UI keeps a Tkinter fallback so the application remains usable on
    Windows versions where the optional effect cannot be applied.
    """
    if not sys.platform.startswith("win"):
        return False

    try:
        import pywinstyles
        # Acrylic is the requested glass surface. pywinstyles applies the native Windows effect.
        pywinstyles.apply_style(window, style or "acrylic")
        pywinstyles.change_header_color(window, "#101B2A" if dark else "#EAF0F5")
        pywinstyles.change_title_color(window, "#EAF2F7" if dark else "#14202B")
        pywinstyles.change_border_color(window, "#2BD8BD" if dark else "#0C9F85")
        return True
    except Exception:
        pass

    # Small dependency-free fallback for Windows 11: request a native
    # system backdrop through DWM. It is harmless on unsupported builds.
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = wintypes.HWND(window.winfo_id())
        dwmapi = ctypes.windll.dwmapi
        # DWMWA_SYSTEMBACKDROP_TYPE = 38. 2 = Mica main window, 3 = Desktop Acrylic/transient.
        # Use Desktop Acrylic for the genuinely translucent glass look.
        attribute = wintypes.DWORD(38)
        value = wintypes.DWORD(3)
        dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value))
        # DWMWA_USE_IMMERSIVE_DARK_MODE.
        for dark_attr in (20, 19):
            try:
                flag = wintypes.BOOL(bool(dark))
                dwmapi.DwmSetWindowAttribute(hwnd, wintypes.DWORD(dark_attr),
                                             ctypes.byref(flag), ctypes.sizeof(flag))
                break
            except Exception:
                continue
        return True
    except Exception:
        return False


def apply_glass_to_toplevel(window, dark=True):
    try:
        window.after(80, lambda: apply_glass(window, dark=dark))
    except Exception:
        return False
    return True


def set_widget_glass(widget, opacity=0.86):
    """Apply controlled translucency to Tk widgets on Windows.

    The window itself supplies the native Acrylic backdrop; cards/buttons get
    slightly reduced opacity so the backdrop remains visible through the UI.
    """
    try:
        import pywinstyles
        if sys.platform.startswith("win"):
            pywinstyles.set_opacity(widget, value=max(0.35, min(1.0, float(opacity))))
            return True
    except Exception:
        pass
    return False
