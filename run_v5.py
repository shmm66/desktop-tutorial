"""PyInstaller-safe V5 launcher from repository root."""
from app.ui import views as _views


class DashboardHomeView(_views.HomeView):
    """Home dashboard without Journal-only trade-entry controls."""

    def __init__(self, master, config, open_view):
        super().__init__(master, config, open_view)
        self._remove_journal_controls(self)

    def _remove_journal_controls(self, widget):
        for child in widget.winfo_children():
            try:
                text = child.cget("text")
            except Exception:
                text = ""
            if text in ("+ ثبت معامله", "ثبت معامله"):
                child.destroy()
                continue
            self._remove_journal_controls(child)


# Shell imports HomeView from app.ui.views, so replace only the presentation class.
_views.HomeView = DashboardHomeView

from app.main import main


if __name__ == "__main__":
    main()
