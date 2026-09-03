from __future__ import annotations


def test_session_widget_imports_and_session_rules():
    import run_session_widget as widget

    assert callable(widget.main)
    assert len(widget.SESSIONS) == 4
    assert widget._is_open(8, 8, 17)
    assert not widget._is_open(17, 8, 17)


def test_session_widget_is_desktop_friendly():
    import inspect
    import run_session_widget as widget

    source = inspect.getsource(widget.SessionClockWidget)
    assert "overrideredirect" in source
    assert "-topmost" in source
    assert "<Double-Button-1>" in source
