from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes


DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMWCP_ROUND = 2
DWMSBT_MAINWINDOW = 2
DWMSBT_TRANSIENTWINDOW = 3
DWMSBT_TABBEDWINDOW = 4
DWMSBT_ACRYLIC = 3

WCA_ACCENT_POLICY = 19
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
ACCENT_ENABLE_BLURBEHIND = 3

# ARGB gradient colors used by the Win32 Acrylic fallback.
DARK_GRADIENT = 0xCC0A1422
LIGHT_GRADIENT = 0xCCF2F7FA


class _ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint32),
        ("AnimationId", ctypes.c_int),
    ]


class _WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attrib", ctypes.c_int),
        ("pvData", ctypes.c_void_p),
        ("cbData", ctypes.c_size_t),
    ]


def _hwnd(window):
    return wintypes.HWND(int(window.winfo_id()))


def _set_dwm(window, dark: bool, acrylic: bool = True):
    if not sys.platform.startswith("win"):
        return False

    hwnd = _hwnd(window)
    dwmapi = ctypes.windll.dwmapi
    ok = False

    # Windows 11 native system backdrop. Acrylic is preferred; if unsupported
    # use the main-window Mica backdrop.
    backdrop = DWMSBT_ACRYLIC if acrylic else DWMSBT_MAINWINDOW
    value = wintypes.DWORD(backdrop)
    hr = dwmapi.DwmSetWindowAttribute(
        hwnd,
        wintypes.DWORD(DWMWA_SYSTEMBACKDROP_TYPE),
        ctypes.byref(value),
        ctypes.sizeof(value),
    )
    ok = ok or hr == 0

    try:
        flag = wintypes.BOOL(bool(dark))
        for attr in (DWMWA_USE_IMMERSIVE_DARK_MODE, 19):
            try:
                dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    wintypes.DWORD(attr),
                    ctypes.byref(flag),
                    ctypes.sizeof(flag),
                )
                ok = True
                break
            except Exception:
                continue
    except Exception:
        pass

    try:
        corner = wintypes.DWORD(DWMWCP_ROUND)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            wintypes.DWORD(DWMWA_WINDOW_CORNER_PREFERENCE),
            ctypes.byref(corner),
            ctypes.sizeof(corner),
        )
        ok = True
    except Exception:
        pass

    return ok


def _set_accent_blur(window, dark: bool):
    if not sys.platform.startswith("win"):
        return False
    try:
        user32 = ctypes.windll.user32
        hwnd = _hwnd(window)
        policy = _ACCENT_POLICY()
        policy.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
        policy.AccentFlags = 2
        policy.GradientColor = DARK_GRADIENT if dark else LIGHT_GRADIENT
        policy.AnimationId = 0

        data = _WINDOWCOMPOSITIONATTRIBDATA()
        data.Attrib = WCA_ACCENT_POLICY
        data.pvData = ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p)
        data.cbData = ctypes.sizeof(policy)

        setter = getattr(user32, "SetWindowCompositionAttribute", None)
        if setter is None:
            return False
        setter.argtypes = [wintypes.HWND, ctypes.POINTER(_WINDOWCOMPOSITIONATTRIBDATA)]
        setter.restype = wintypes.BOOL
        return bool(setter(hwnd, ctypes.byref(data)))
    except Exception:
        # Try plain blur before giving up.
        try:
            user32 = ctypes.windll.user32
            hwnd = _hwnd(window)
            policy = _ACCENT_POLICY()
            policy.AccentState = ACCENT_ENABLE_BLURBEHIND
            policy.AccentFlags = 2
            policy.GradientColor = DARK_GRADIENT if dark else LIGHT_GRADIENT
            data = _WINDOWCOMPOSITIONATTRIBDATA()
            data.Attrib = WCA_ACCENT_POLICY
            data.pvData = ctypes.cast(ctypes.pointer(policy), ctypes.c_void_p)
            data.cbData = ctypes.sizeof(policy)
            setter = getattr(user32, "SetWindowCompositionAttribute", None)
            if setter is None:
                return False
            setter.argtypes = [wintypes.HWND, ctypes.POINTER(_WINDOWCOMPOSITIONATTRIBDATA)]
            setter.restype = wintypes.BOOL
            return bool(setter(hwnd, ctypes.byref(data)))
        except Exception:
            return False


def apply_glass(window, dark=True, style="acrylic"):
    """Apply a real native Windows glass/acrylic backdrop.

    Windows 11: pywinstyles first, then DWM system-backdrop.
    Windows 10/older builds: SetWindowCompositionAttribute Acrylic fallback.
    Tk widgets remain opaque glass panels over the blurred native surface.
    """
    if not sys.platform.startswith("win"):
        return False

    applied = False
    requested = str(style or "acrylic").lower()

    try:
        import pywinstyles

        pywinstyles.apply_style(window, "acrylic" if requested == "acrylic" else requested)
        try:
            pywinstyles.change_header_color(window, "#0B1420" if dark else "#F1F6FA")
            pywinstyles.change_title_color(window, "#EAF2F7" if dark else "#14202B")
            pywinstyles.change_border_color(window, "#39E6D0" if dark else "#0C9F85")
        except Exception:
            pass
        applied = True
    except Exception:
        pass

    # Explicit DWM system backdrop. Keep this even when pywinstyles succeeded:
    # it makes the effect resilient across package/runtime combinations.
    applied = _set_dwm(window, dark=dark, acrylic=True) or applied

    # Legacy Win32 acrylic fallback.
    applied = _set_accent_blur(window, dark=dark) or applied
    return applied


def apply_glass_to_toplevel(window, dark=True):
    try:
        window.after(50, lambda: apply_glass(window, dark=dark, style="acrylic"))
        return True
    except Exception:
        return False


def set_widget_glass(widget, opacity=0.88):
    """Give a child panel a translucent finish when the Windows API permits it."""
    try:
        if sys.platform.startswith("win"):
            import pywinstyles
            pywinstyles.set_opacity(widget, float(opacity))
            return True
    except Exception:
        pass
    return False
