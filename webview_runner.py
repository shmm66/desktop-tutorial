from __future__ import annotations

import sys
import webview


def main():
    url = sys.argv[2] if len(sys.argv) > 2 else "https://www.forexfactory.com/calendar"
    title = sys.argv[3] if len(sys.argv) > 3 else "Trader Planner Pro — Web View"
    webview.create_window(title, url, width=1400, height=900, min_size=(1000, 700))
    webview.start(gui="edgechromium")


if __name__ == "__main__":
    main()
