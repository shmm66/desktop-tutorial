from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes


def is_windows() -> bool:
    return sys.platform.startswith("win")


def _set_dwm_backdrop(window, dark: bool) -> bool:
    """Use the Windows 11 DWM backdrop/corner APIs as a dependency-free fallback."""
    if not is_windows():
        return False
    try:
        hwnd = wintypes.HWND(window.winfo_id())
        dwmapi = ctypes.windll.dwmapi

        # DWMWA_SYSTEMBACKDROP_TYPE = 38
        # 3 = DWMSBT_TRANSIENTWINDOW (acrylic-like on modern Windows 11).
        backdrop_attr = wintypes.DWORD(38)
        backdrop_value = wintypes.DWORD(3)
        dwmapi.DwmSetWindowAttribute(
            hwnd, backdrop_attr, ctypes.byref(backdrop_value), ctypes.sizeof(backdrop_value)
        )

        # DWMWA_WINDOW_CORNER_PREFERENCE = 33
        # 2/3/4 are round/small-round depending on Windows build.
        corner_attr = wintypes.DWORD(33)
        corner_value = wintypes.DWORD(2)
        dwmapi.DwmSetWindowAttribute(
            hwnd, corner_attr, ctypes.byref(corner_value), ctypes.sizeof(corner_value)
        )

        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (19 on older builds).
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

        # DWMWA_BORDER_COLOR = 34
        border_attr = wintypes.DWORD(34)
        border = wintypes.COLORREF(0x00B0D6C6 if dark else 0x0079B6A6)
        try:
            dwmapi.DwmSetWindowAttribute(
                hwnd, border_attr, ctypes.byref(border), ctypes.sizeof(border)
            )
        except Exception:
            pass
        return True
    except Exception:
        return False


def apply_glass(window, dark: bool = True, style: str = "acrylic") -> bool:
    """Apply a real Windows acrylic/DWM backdrop to the top-level window.

    Tk child widgets cannot have independent alpha reliably, so the true glass
    effect is applied to the native window and the app layers translucent-looking
    surfaces/cards on top. This keeps the effect stable instead of making random
    controls disappear through color-key transparency.
    """
    if not is_windows():
        return False

    def _apply():
        try:
            # Keep the native surface slightly translucent so the acrylic/DWM
            # backdrop remains visible around glass cards and header gaps.
            try:
                window.attributes("-alpha", 0.94 if dark else 0.965)
            except Exception:
                pass

            try:
                window.configure(bg="#07131F" if dark else "#E8F0F5")
            except Exception:
                pass

            try:
                import pywinstyles

                native_style = style if style in {"acrylic", "mica", "transparent"} else "acrylic"
                pywinstyles.apply_style(window, native_style)
                if hasattr(pywinstyles, "change_header_color"):
                    pywinstyles.change_header_color(
                        window, "#0A1726" if dark else "#E8F0F5"
                    )
                if hasattr(pywinstyles, "change_title_color"):
                    pywinstyles.change_title_color(
                        window, "#F3FBFF" if dark else "#15212C"
                    )
                if hasattr(pywinstyles, "change_border_color"):
                    pywinstyles.change_border_color(
                        window, "#36E4C2" if dark else "#168F7B"
                    )
            except Exception:
                pass

            _set_dwm_backdrop(window, dark)
        except Exception:
            return

    try:
        window.after(120, _apply)
        return True
    except Exception:
        try:
            _apply()
            return True
        except Exception:
            return False


def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic") -> bool:
    return apply_glass(window, dark=dark, style=style)


def set_widget_glass(widget, opacity: float = 0.88) -> bool:
    """Best-effort child surface styling.

    Per-widget alpha is intentionally not used: on Tk/Win32 it can turn a child
    into a color-key transparent control and break hit testing. Cards instead
    use the app's translucent glass palette plus a subtle highlight border.
    """
    try:
        _ = float(opacity)
        widget.configure(highlightthickness=max(int(widget.cget("highlightthickness")), 1))
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
