from __future__ import annotations

import sys


def _win_dwm_backdrop(window, dark=True):
    """Request a real Windows 11 acrylic backdrop when DWM is available."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = wintypes.HWND(window.winfo_id())
        dwmapi = ctypes.windll.dwmapi

        # DWMWA_SYSTEMBACKDROP_TYPE = 38
        # 3 = Acrylic, 2 = Mica. Prefer Acrylic for true translucency.
        attr = wintypes.DWORD(38)
        value = wintypes.DWORD(3)
        dwmapi.DwmSetWindowAttribute(
            hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
        )

        # DWMWA_WINDOW_CORNER_PREFERENCE = 33, 2 = round.
        corner_attr = wintypes.DWORD(33)
        corner = wintypes.DWORD(2)
        try:
            dwmapi.DwmSetWindowAttribute(
                hwnd, corner_attr, ctypes.byref(corner), ctypes.sizeof(corner)
            )
        except Exception:
            pass

        # DWMWA_USE_IMMERSIVE_DARK_MODE.
        for dark_attr in (20, 19):
            try:
                flag = wintypes.BOOL(bool(dark))
                dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    wintypes.DWORD(dark_attr),
                    ctypes.byref(flag),
                    ctypes.sizeof(flag),
                )
                break
            except Exception:
                continue
        return True
    except Exception:
        return False


def apply_glass(window, dark=True, style="acrylic"):
    """Apply a real Windows glass backdrop with safe fallbacks.

    On Windows 11, pywinstyles provides the acrylic/mica treatment and DWM is
    used as a second path. On unsupported systems the app simply keeps its
    normal Tk widgets; no feature depends on transparency being available.
    """
    if not sys.platform.startswith("win"):
        return False

    applied = False
    try:
        import pywinstyles

        # Prefer the requested style, then fall back to mica.
        for candidate in (style, "acrylic", "mica"):
            try:
                pywinstyles.apply_style(window, candidate)
                applied = True
                break
            except Exception:
                continue

        try:
            pywinstyles.change_header_color(window, "#0B1420" if dark else "#EAF1F6")
            pywinstyles.change_title_color(window, "#F2F7FA" if dark else "#12202A")
            pywinstyles.change_border_color(window, "#37E0C1" if dark else "#0C9F85")
        except Exception:
            pass
    except Exception:
        pass

    # Give the DWM backdrop visible room to breathe. The acrylic blur remains
    # underneath the Tk surface while this alpha softens the surface itself.
    try:
        window.attributes("-alpha", 0.965 if dark else 0.985)
    except Exception:
        pass
    return _win_dwm_backdrop(window, dark=dark) or applied


def apply_glass_to_toplevel(window, dark=True):
    try:
        window.after(80, lambda: apply_glass(window, dark=dark, style="acrylic"))
    except Exception:
        return False
    return True


def set_widget_glass(widget, opacity=0.82, color=None):
    """Make a Tk widget visually translucent where Windows supports it."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import pywinstyles

        if color:
            try:
                pywinstyles.set_opacity(widget, value=float(opacity), color=color)
                return True
            except Exception:
                pass
        pywinstyles.set_opacity(widget, value=float(opacity))
        return True
    except Exception:
        return False
