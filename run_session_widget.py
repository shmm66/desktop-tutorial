"""Windows desktop Session Clock widget for Trader Planner Pro V5."""
from __future__ import annotations

import math
import tkinter as tk
from datetime import datetime
from zoneinfo import ZoneInfo

SESSIONS = (
    ("Sydney", "Australia/Sydney", 7, 16),
    ("Tokyo", "Asia/Tokyo", 9, 18),
    ("London", "Europe/London", 8, 17),
    ("New York", "America/New_York", 8, 17),
)


def _is_open(local_hour: int, start: int, end: int) -> bool:
    return start <= local_hour < end


class SessionClockWidget(tk.Tk):
    """Small borderless, always-on-top clock designed for trader desktops."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Trader Planner Pro — Session Clock")
        self.geometry("230x230+30+80")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#101820")

        self.canvas = tk.Canvas(self, width=230, height=230, bg="#101820", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._drag = (0, 0)
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag_window)
        self.canvas.bind("<Double-Button-1>", lambda _e: self.destroy())
        self.after(100, self._tick)

    def _start_drag(self, event: tk.Event) -> None:
        self._drag = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _drag_window(self, event: tk.Event) -> None:
        x = event.x_root - self._drag[0]
        y = event.y_root - self._drag[1]
        self.geometry(f"+{x}+{y}")

    def _tick(self) -> None:
        self.canvas.delete("all")
        now = datetime.now().astimezone()
        cx = cy = 115
        radius = 82
        self.canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="#334756", width=2)

        # 12-hour analog face.
        hour_angle = ((now.hour % 12) + now.minute / 60) * math.pi / 6
        minute_angle = (now.minute + now.second / 60) * math.pi / 30
        second_angle = now.second * math.pi / 30
        for i in range(12):
            a = i * math.pi / 6
            x1 = cx + math.sin(a) * (radius - 8)
            y1 = cy - math.cos(a) * (radius - 8)
            x2 = cx + math.sin(a) * (radius - 15)
            y2 = cy - math.cos(a) * (radius - 15)
            self.canvas.create_line(x1, y1, x2, y2, fill="#9fb3c8", width=2)

        for angle, length, width in ((hour_angle, 42, 5), (minute_angle, 60, 3), (second_angle, 67, 1)):
            x = cx + math.sin(angle) * length
            y = cy - math.cos(angle) * length
            self.canvas.create_line(cx, cy, x, y, fill="#e7eef5", width=width)
        self.canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill="#e7eef5", outline="")

        local_lines = []
        for name, zone, start, end in SESSIONS:
            dt = now.astimezone(ZoneInfo(zone))
            state = "OPEN" if _is_open(dt.hour, start, end) else "closed"
            local_lines.append(f"{name}: {state}  {dt:%H:%M}")

        self.canvas.create_text(cx, 16, text=f"{now:%H:%M:%S}", fill="#ffffff", font=("Segoe UI", 13, "bold"))
        self.canvas.create_text(cx, 206, text="  •  ".join(line.split(": ")[0] + " " + line.split(": ")[1].split()[0] for line in local_lines), fill="#9fb3c8", font=("Segoe UI", 7))
        self.after(1000, self._tick)


def main() -> None:
    SessionClockWidget().mainloop()


if __name__ == "__main__":
    main()
