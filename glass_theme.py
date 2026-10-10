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


def _configure_window_transparency(window, dark: bool, opacity: float = 0.94):
    """Tune the client/window alpha without relying on per-widget alpha.

    Tk child widgets are opaque by design, so the real glass effect comes from
    the Windows compositor backdrop + a lightly translucent top-level surface.
    """
    try:
        # Keep text/controls crisp while allowing the DWM material to breathe through.
        window.wm_attributes("-alpha", max(0.86, min(float(opacity), 0.995)))
    except Exception:
        pass

def apply_glass(window, dark: bool = True, style: str = "acrylic", opacity: float = 0.94) -> bool:
    """Apply the native Windows backdrop once, without recursive Tk scheduling.

    This function deliberately never calls after. Deferred application is
    owned exclusively by apply_glass_after_map, which debounces its single
    pending callback. This separation prevents repeated theme/map events from
    building an unbounded callback-registration chain.
    """
    if not is_windows():
        return False
    if getattr(window, "_tpp_glass_applying", False):
        return False
    try:
        if not window.winfo_exists():
            return False
    except Exception:
        return False

    # If a deferred map callback is pending, this immediate application wins.
    pending = getattr(window, "_tpp_glass_after_id", None)
    if pending:
        try:
            window.after_cancel(pending)
        except Exception:
            pass
        try:
            setattr(window, "_tpp_glass_after_id", None)
        except Exception:
            pass

    try:
        setattr(window, "_tpp_glass_applying", True)
    except Exception:
        pass
    try:
        native_ok = _set_dwm_backdrop(window, dark=dark, acrylic=(style != "mica"))
        pywin_ok = _apply_pywinstyles(window, dark=dark, style=style)
        # Apply alpha last because style helpers can reset attributes.
        # The selected skin background remains owned by apply_theme().
        _configure_window_transparency(window, dark, opacity)
        return native_ok or pywin_ok
    except Exception:
        return False
    finally:
        try:
            setattr(window, "_tpp_glass_applying", False)
        except Exception:
            pass


def apply_glass_to_toplevel(window, dark: bool = True, style: str = "acrylic", opacity: float = 0.94) -> bool:
    return apply_glass(window, dark=dark, style=style, opacity=opacity)


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


def apply_glass_after_map(window, dark: bool = True, style: str = "acrylic", opacity: float = 0.94) -> bool:
    """Apply the backdrop once after Tk has had a chance to map the native window.

    Only one timer is ever registered per window. The callback never reschedules
    itself, and this helper has no recursive fallback path.
    """
    if not is_windows():
        return False
    try:
        if not window.winfo_exists():
            return False
        if getattr(window, "_tpp_glass_after_id", None):
            return True

        def _apply_after_map() -> None:
            try:
                setattr(window, "_tpp_glass_after_id", None)
            except Exception:
                pass
            try:
                if not window.winfo_exists():
                    return
                if getattr(window, "_tpp_glass_after_map_done", False):
                    return
                # Mark before applying to prevent any nested/re-entrant map
                # event or theme callback from scheduling another attempt.
                setattr(window, "_tpp_glass_after_map_done", True)
                apply_glass(window, dark=dark, style=style, opacity=opacity)
            except BaseException:
                # DWM and window teardown failures must never interrupt Tk.
                return

        job = window.after(120, _apply_after_map)
        setattr(window, "_tpp_glass_after_id", job)
        return True
    except BaseException:
        return False

