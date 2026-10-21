"""Whale Radar Pro — compact Windows desktop interface."""
from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from radar.bitunix import test_connection
from radar.credentials import delete_profile, get_profile_secrets, list_profiles, save_profile
from radar.hyperliquid import fetch_leaderboard
from radar.models import Trader, rank_traders
from radar.risk import calculate_position_size

BG = "#10151f"
PANEL = "#192231"
TEXT = "#edf3ff"
ACCENT = "#46d6b2"


class RadarApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Whale Radar Pro")
        self.geometry("1040x720")
        self.minsize(900, 620)
        self.configure(bg=BG)
        self.traders: list[Trader] = []
        self._style()
        self._build()
        self.refresh_profiles()

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 22), foreground=TEXT)
        style.configure("Muted.TLabel", foreground="#9aabc2")
        style.configure("TButton", padding=(10, 7), font=("Segoe UI Semibold", 9))
        style.configure("Accent.TButton", background=ACCENT, foreground="#08121a")
        style.map("Accent.TButton", background=[("active", "#6de7c8")])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=28)
        style.configure("Treeview.Heading", background="#263348", foreground=TEXT, font=("Segoe UI Semibold", 9))

    def _build(self) -> None:
        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(header, text="WHALE RADAR", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="PRO 2.0  •  HYPERLIQUID × BITUNIX", style="Muted.TLabel").pack(side="right", pady=10)

        p1 = ttk.LabelFrame(root, text="  01  EXCHANGE CONNECTION  ", padding=12)
        p1.pack(fill="x", pady=(0, 12))
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(p1, textvariable=self.profile_var, state="readonly", width=25)
        self.profile_combo.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        ttk.Button(p1, text="Add / Edit", command=self.edit_profile).grid(row=0, column=1, padx=4)
        ttk.Button(p1, text="Delete", command=self.remove_profile).grid(row=0, column=2, padx=4)
        ttk.Button(p1, text="Test selected", command=self.test_profile).grid(row=0, column=3, padx=4)
        ttk.Label(p1, text="Secrets are stored in Windows Credential Manager; paste into the editor.", style="Muted.TLabel").grid(row=1, column=0, columnspan=4, sticky="w", pady=(5, 0))

        p2 = ttk.LabelFrame(root, text="  02  SUCCESSFUL TRADERS  •  MAX 10  ", padding=12)
        p2.pack(fill="both", expand=True, pady=(0, 12))
        filters = ttk.Frame(p2)
        filters.pack(fill="x", pady=(0, 8))
        self.min_return = tk.StringVar(value="10")
        self.min_win = tk.StringVar(value="55")
        ttk.Label(filters, text="Min return %").pack(side="left")
        ttk.Entry(filters, textvariable=self.min_return, width=8).pack(side="left", padx=(5, 14))
        ttk.Label(filters, text="Min win rate %").pack(side="left")
        ttk.Entry(filters, textvariable=self.min_win, width=8).pack(side="left", padx=(5, 14))
        ttk.Button(filters, text="Scan Hyperliquid", style="Accent.TButton", command=self.scan).pack(side="left")
        self.status = tk.StringVar(value="Not scanned yet — live results are never simulated.")
        ttk.Label(filters, textvariable=self.status, style="Muted.TLabel").pack(side="right", padx=8)
        cols = ("name", "address", "return", "win", "trades")
        self.table = ttk.Treeview(p2, columns=cols, show="headings", height=7)
        for col, label, width in [("name", "Trader", 180), ("address", "Wallet / Address", 300), ("return", "Return %", 100), ("win", "Win rate %", 100), ("trades", "Trades", 80)]:
            self.table.heading(col, text=label)
            self.table.column(col, width=width, anchor="w" if col in ("name", "address") else "center")
        self.table.pack(fill="both", expand=True)
        ttk.Button(p2, text="Review selected trade alert", command=self.review_alert).pack(anchor="e", pady=(8, 0))

        p3 = ttk.LabelFrame(root, text="  03  MARGIN & RISK  ", padding=12)
        p3.pack(fill="x")
        self.margin = tk.StringVar(value="100")
        self.risk = tk.StringVar(value="10")
        self.stop = tk.StringVar(value="1")
        for i, (label, var) in enumerate([("Margin (USDT)", self.margin), ("Risk amount (USDT)", self.risk), ("Entry-to-stop %", self.stop)]):
            ttk.Label(p3, text=label).grid(row=0, column=i * 2, sticky="w", padx=(0, 6))
            ttk.Entry(p3, textvariable=var, width=12).grid(row=0, column=i * 2 + 1, padx=(0, 18), sticky="w")
        ttk.Button(p3, text="Calculate leverage", style="Accent.TButton", command=self.calculate).grid(row=0, column=6, padx=6)
        self.sizing_result = tk.StringVar(value="Enter margin, risk, and stop distance.")
        ttk.Label(p3, textvariable=self.sizing_result, style="Muted.TLabel").grid(row=1, column=0, columnspan=7, sticky="w", pady=(10, 0))
        ttk.Label(root, text="Monitoring only • Copying is never automatic • Risk estimate excludes fees, slippage and funding", style="Muted.TLabel").pack(anchor="w", pady=(12, 0))

    def refresh_profiles(self) -> None:
        names = [p["name"] for p in list_profiles()]
        self.profile_combo["values"] = names
        if names and self.profile_var.get() not in names:
            self.profile_var.set(names[0])

    def edit_profile(self) -> None:
        name = simpledialog.askstring("API profile", "Profile name (e.g. Bitunix Main):", parent=self)
        if not name:
            return
        key = simpledialog.askstring("API profile", "Paste API key:", parent=self)
        if key is None:
            return
        secret = simpledialog.askstring("API profile", "Paste API secret:", show="•", parent=self)
        if secret is None:
            return
        try:
            save_profile(name, key, secret, "Bitunix")
            self.refresh_profiles()
            self.profile_var.set(name.strip())
            messagebox.showinfo("Saved", "Profile saved to the operating system credential store.", parent=self)
        except Exception as exc:
            messagebox.showerror("Could not save profile", str(exc), parent=self)

    def remove_profile(self) -> None:
        name = self.profile_var.get()
        if not name:
            return
        if messagebox.askyesno("Delete profile", f"Delete API profile '{name}' from this computer?", parent=self):
            try:
                delete_profile(name)
                self.refresh_profiles()
            except Exception as exc:
                messagebox.showerror("Delete failed", str(exc), parent=self)

    def test_profile(self) -> None:
        name = self.profile_var.get()
        if not name:
            messagebox.showwarning("Select profile", "Add or select a Bitunix profile first.", parent=self)
            return
        try:
            key, secret = get_profile_secrets(name)
            ok, detail = test_connection(key, secret)
            messagebox.showinfo("Bitunix connection status", detail, parent=self)
        except Exception as exc:
            messagebox.showerror("Profile error", str(exc), parent=self)

    def scan(self) -> None:
        try:
            low_ret, low_win = float(self.min_return.get()), float(self.min_win.get())
            if not 0 <= low_win <= 100:
                raise ValueError("Win-rate filter must be between 0 and 100.")
        except ValueError as exc:
            messagebox.showerror("Invalid filters", str(exc) or "Return and win-rate filters must be numbers.", parent=self)
            return
        self.status.set("Fetching public leaderboard…")
        threading.Thread(target=self._scan_worker, args=(low_ret, low_win), daemon=True).start()

    def _scan_worker(self, low_ret: float, low_win: float) -> None:
        try:
            data = fetch_leaderboard()
            ranked = rank_traders(data, low_ret, low_win, 10)
            self.after(0, lambda: self._show_traders(ranked, len(data)))
        except Exception as exc:
            detail = str(exc)
            self.after(0, lambda detail=detail: self.status.set(f"Scan failed: {detail}"))

    def _show_traders(self, traders: list[Trader], total: int) -> None:
        self.traders = traders
        for item in self.table.get_children():
            self.table.delete(item)
        for t in traders:
            fmt = lambda value: "Unknown" if value is None else f"{value:.2f}"
            self.table.insert("", "end", values=(
                t.display_name, t.address, fmt(t.return_pct), fmt(t.win_rate_pct),
                "Unknown" if t.trades is None else t.trades,
            ))
        self.status.set(f"Received {total}; {len(traders)} matched filters. Unknown metrics are excluded.")

    def calculate(self) -> None:
        try:
            result = calculate_position_size(float(self.margin.get()), float(self.risk.get()), float(self.stop.get()))
            self.sizing_result.set(f"Estimated notional: {result.notional:,.2f} USDT   •   Estimated leverage: {result.leverage:.2f}×")
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Invalid risk inputs", str(exc), parent=self)

    def review_alert(self) -> None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("No trader selected", "Select a trader row first. This build does not have verified live trade-event detection yet.", parent=self)
            return
        values = self.table.item(selected[0], "values")
        messagebox.showinfo("Trade alert review", f"Selected trader: {values[0]}\nWallet: {values[1]}\n\nLive trade-event detection and copy execution are not enabled in this build. No order was sent.", parent=self)


if __name__ == "__main__":
    RadarApp().mainloop()
