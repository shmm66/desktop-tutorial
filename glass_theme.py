from __future__ import annotations

import sys


def is_windows() -> bool:
    return sys.platform.startswith("win")


def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Apply a Windows-native acrylic backdrop plus a light translucent surface."""
    if not is_windows():
        return False

    try:
        # Keep a translucent, cool glass-tinted base behind Tk widgets.
        window.configure(bg="#08111B")
        try:
            # Tk's alpha works at the top-level and makes the DWM backdrop
            # perceptible even when child widgets are opaque.
            window.attributes("-alpha", 0.965)
        except Exception:
            pass
    except Exception:
        pass

    try:
        import pywinstyles

        native_style = style if style in {"acrylic", "mica", "transparent"} else "acrylic"
        pywinstyles.apply_style(window, native_style)
        if hasattr(pywinstyles, "change_header_color"):
            pywinstyles.change_header_color(window, "#0B1220" if dark else "#EAF1F6")
        if hasattr(pywinstyles, "change_title_color"):
            pywinstyles.change_title_color(window, "#F2F7FA" if dark else "#15212C")
        if hasattr(pywinstyles, "change_border_color"):
            pywinstyles.change_border_color(window, "#42E1C0" if dark else "#148F78")
        return True
    except Exception:
        pass

    # Dependency-free Windows 11 fallback using DWM system backdrop.
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = wintypes.HWND(window.winfo_id())
        dwmapi = ctypes.windll.dwmapi

        # DWMWA_SYSTEMBACKDROP_TYPE = 38; 3 = transient/acrylic-like.
        attribute = wintypes.DWORD(38)
        value = wintypes.DWORD(3 if dark else 3)
        dwmapi.DwmSetWindowAttribute(
            hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
        )

        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (19 on older Windows builds).
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


def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic") -> bool:
    try:
        window.after(80, lambda: apply_glass(window, dark=dark, style=style))
        return True
    except Exception:
        return False


def set_widget_glass(widget, opacity: float = 0.88) -> bool:
    """Apply native translucency to a surface; fall back cleanly on Tk widgets."""
    if not is_windows():
        return False

    try:
        import pywinstyles
        value = max(0.55, min(float(opacity), 0.98))

        # Whole-surface opacity is preferable to color-key transparency for
        # glassmorphism because it preserves the backdrop and avoids haloing.
        try:
            pywinstyles.set_opacity(widget, value=value)
            return True
        except Exception:
            pass

        # Some versions expose only the color-key form. Keep it as a fallback.
        try:
            bg = str(widget.cget("bg"))
            pywinstyles.set_opacity(widget, color=bg)
            return True
        except Exception:
            return False
    except Exception:
        return False
