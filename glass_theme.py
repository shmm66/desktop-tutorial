from __future__ import annotations

import sys


def is_windows() -> bool:
    return sys.platform.startswith("win")


def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Enable a real native Windows acrylic/mica backdrop when supported.

    Tk widgets remain the application surface, while the top-level window gets
    a native compositor backdrop. On unsupported Windows builds the app keeps
    its normal opaque rendering instead of failing.
    """
    if not is_windows():
        return False

    try:
        # pywinstyles uses the window background as the surface that reveals
        # the compositor. A black base is the documented acrylic fallback.
        window.configure(bg="#000000")
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
    """Make the widget surface translucent on Windows when possible."""
    if not is_windows():
        return False

    try:
        import pywinstyles

        background = None
        try:
            background = widget.cget("bg")
        except Exception:
            background = None

        # Prefer color-key transparency so text/children stay crisp.
        if background:
            try:
                pywinstyles.set_opacity(widget, color=str(background))
                return True
            except Exception:
                pass

        # Fallback to whole-widget opacity.
        try:
            pywinstyles.set_opacity(widget, value=max(0.2, min(float(opacity), 1.0)))
            return True
        except Exception:
            return False
    except Exception:
        return False
