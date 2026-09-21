from __future__ import annotations

import sys
import webbrowser

try:
    import webview
except Exception:
    webview = None


def main():
    url = sys.argv[2] if len(sys.argv) > 2 else "https://www.forexfactory.com/calendar"
    title = sys.argv[3] if len(sys.argv) > 3 else "Trader Planner Pro — Web View"
    if webview is None:
        webbrowser.open(url)
        return
    try:
        webview.create_window(title, url, width=1400, height=900, min_size=(1000, 700))
        webview.start(gui="edgechromium")
    except Exception:
        webbrowser.open(url)


if __name__ == "__main__":
    main()
