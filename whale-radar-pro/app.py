"""Whale Radar Pro — responsive Windows desktop interface."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from radar.bitunix import test_connection
from radar.copytrade import (
    BitunixClient, CopyTradeError, check_loss_circuit_breaker, load_copy_settings,
    load_copy_state, process_copy_fill, reset_loss_halt, save_copy_settings,
)
from radar.credentials import delete_profile, get_profile_secrets, list_profiles, save_profile
from radar.hyperliquid import fetch_leaderboard
from radar.models import Trader, rank_traders
from radar.monitor import fetch_recent_fills, fill_identity
from radar.risk import calculate_position_size

BG = "#10151f"
PANEL = "#192231"
TEXT = "#edf3ff"
ACCENT = "#46d6b2"


class RadarApp(tk.Tk):
    """Three-section, scroll-safe UI; profile editing is done in one persistent form."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Whale Radar Pro")
        self.geometry("1180x850")
        self.minsize(900, 640)
        self.configure(bg=BG)
        self.traders: list[Trader] = []
        self._test_in_progress = False
        self._scan_in_progress = False
        self._monitor_stop: threading.Event | None = None
        self._watched_address: str | None = None
        self._loading_profile = False
        self.copy_settings = load_copy_settings()
        self.copy_state = load_copy_state()
        self._style()
        self._build()
        self.refresh_profiles()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        style.configure("Section.TLabelframe", background=BG, foreground=ACCENT, bordercolor="#33435a")
        style.configure("Section.TLabelframe.Label", background=BG, foreground=ACCENT,
                        font=("Segoe UI Semibold", 10))
        style.configure("TButton", padding=(10, 7), font=("Segoe UI Semibold", 9))
        style.configure("Accent.TButton", background=ACCENT, foreground="#08121a")
        style.map("Accent.TButton", background=[("active", "#6de7c8")])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=29)
        style.configure("Treeview.Heading", background="#263348", foreground=TEXT,
                        font=("Segoe UI Semibold", 9))
        style.map("Treeview", background=[("selected", "#245b57")], foreground=[("selected", "#ffffff")])

    def _build(self) -> None:
        # Scrollable outer surface prevents the bottom risk panel disappearing on scaled displays.
        shell = ttk.Frame(self)
        shell.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(shell, bg=BG, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        root = ttk.Frame(self.canvas, padding=18)
        self._canvas_window = self.canvas.create_window((0, 0), window=root, anchor="nw")
        root.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.bind_all("<MouseWheel>", self._mousewheel)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="WHALE RADAR", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="PRO 2.2  •  HYPERLIQUID × BITUNIX",
                   style="Muted.TLabel").pack(side="right", pady=10)

        # 01 — Bitunix credentials and connection test.
        p1 = ttk.LabelFrame(root, text="  01  EXCHANGE CONNECTION · BITUNIX  ", padding=12,
                            style="Section.TLabelframe")
        p1.pack(fill="x", pady=(0, 12))
        p1.columnconfigure(1, weight=1)
        self.profile_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.api_secret_var = tk.StringVar()
        self.show_secret_var = tk.BooleanVar(value=False)

        ttk.Label(p1, text="Saved profile").grid(row=0, column=0, sticky="w", padx=(0, 9), pady=5)
        self.profile_combo = ttk.Combobox(p1, textvariable=self.profile_var, state="readonly", width=28)
        self.profile_combo.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=5)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        ttk.Button(p1, text="New profile", command=self.new_profile).grid(row=0, column=2, padx=4, pady=5)
        ttk.Button(p1, text="Reload list", command=self.refresh_profiles).grid(row=0, column=3, padx=4, pady=5)

        ttk.Label(p1, text="API Key").grid(row=1, column=0, sticky="w", padx=(0, 9), pady=5)
        self.api_key_entry = ttk.Entry(p1, textvariable=self.api_key_var)
        self.api_key_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=5)
        ttk.Button(p1, text="Paste key", command=lambda: self._paste_to(self.api_key_var)).grid(
            row=1, column=2, padx=4, pady=5)

        ttk.Label(p1, text="API Secret").grid(row=2, column=0, sticky="w", padx=(0, 9), pady=5)
        self.api_secret_entry = ttk.Entry(p1, textvariable=self.api_secret_var, show="•")
        self.api_secret_entry.grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=5)
        ttk.Button(p1, text="Paste secret", command=lambda: self._paste_to(self.api_secret_var)).grid(
            row=2, column=2, padx=4, pady=5)
        ttk.Checkbutton(p1, text="Show secret", variable=self.show_secret_var,
                        command=self._toggle_secret).grid(row=2, column=3, sticky="w", padx=8, pady=5)

        self.profile_status = tk.StringVar(value="Select a profile or paste new credentials, then save.")
        action_row = ttk.Frame(p1)
        action_row.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(7, 2))
        ttk.Button(action_row, text="Save / update profile", style="Accent.TButton",
                   command=self.save_current_profile).pack(side="left")
        ttk.Button(action_row, text="Delete selected", command=self.remove_profile).pack(side="left", padx=7)
        self.test_button = ttk.Button(action_row, text="Test Bitunix connection",
                                      command=self.test_profile, style="Accent.TButton")
        self.test_button.pack(side="left", padx=(0, 10))
        ttk.Label(p1, textvariable=self.profile_status, style="Muted.TLabel",
                  wraplength=760).grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 0))
        ttk.Label(p1, text="Keys are stored in Windows Credential Manager. Live copy needs Futures trading permission; never enable withdrawals.",
                  style="Muted.TLabel", wraplength=950).grid(row=5, column=0, columnspan=4, sticky="w", pady=(7, 0))

        # 02 — Hyperliquid discovery and one-wallet opt-in alerts.
        p2 = ttk.LabelFrame(root, text="  02  SUCCESSFUL TRADERS · MAX 10  ", padding=12,
                            style="Section.TLabelframe")
        p2.pack(fill="x", pady=(0, 12))
        filters = ttk.Frame(p2)
        filters.pack(fill="x", pady=(0, 8))
        self.min_return = tk.StringVar(value="10")
        self.min_win = tk.StringVar(value="55")
        ttk.Label(filters, text="Min return %").pack(side="left")
        ttk.Entry(filters, textvariable=self.min_return, width=8).pack(side="left", padx=(5, 14))
        ttk.Label(filters, text="Min win rate %").pack(side="left")
        ttk.Entry(filters, textvariable=self.min_win, width=8).pack(side="left", padx=(5, 14))
        self.scan_button = ttk.Button(filters, text="Scan Hyperliquid", style="Accent.TButton", command=self.scan)
        self.scan_button.pack(side="left")
        self.status = tk.StringVar(value="Ready. Scan uses public Hyperliquid data; no simulated traders.")
        ttk.Label(filters, textvariable=self.status, style="Muted.TLabel",
                  wraplength=900).pack(side="left", padx=12, fill="x", expand=True)

        cols = ("name", "address", "return", "win", "trades")
        self.table = ttk.Treeview(p2, columns=cols, show="headings", height=6, selectmode="browse")
        for col, label, width in [
            ("name", "Trader", 155), ("address", "Wallet / Address", 300),
            ("return", "Return %", 88), ("win", "Closed-fill win % · 7d proxy", 185),
            ("trades", "Sample size", 100)
        ]:
            self.table.heading(col, text=label)
            self.table.column(col, width=width, anchor="w" if col in ("name", "address") else "center",
                              stretch=(col == "address"))
        self.table.pack(fill="x", expand=False)
        controls = ttk.Frame(p2)
        controls.pack(fill="x", pady=(8, 0))
        self.watch_button = ttk.Button(controls, text="Start auto-copy", command=self.start_monitor)
        self.watch_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="Stop auto-copy", command=self.stop_monitor, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        ttk.Button(controls, text="Review selected", command=self.review_alert).pack(side="right")
        ttk.Label(p2, text="Win-rate data is a 7-day closed-fill estimate, not verified position-level win rate. Unknown stays Unknown.",
                  style="Muted.TLabel", wraplength=980).pack(anchor="w", pady=(7, 0))

        # 03 — saved capital guardrails, editable once and reused on every trade.
        p3 = ttk.LabelFrame(root, text="  03  AUTO-COPY CAPITAL & RISK  ", padding=12,
                            style="Section.TLabelframe")
        p3.pack(fill="x", pady=(0, 10))
        p3.columnconfigure(0, weight=1)
        self.copy_summary = tk.StringVar()
        ttk.Label(p3, textvariable=self.copy_summary, style="Muted.TLabel",
                  wraplength=960).grid(row=0, column=0, sticky="w", pady=(0, 7))
        action_row3 = ttk.Frame(p3)
        action_row3.grid(row=1, column=0, sticky="w")
        ttk.Button(action_row3, text="Edit copy settings", style="Accent.TButton",
                   command=self.edit_copy_settings).pack(side="left")
        ttk.Button(action_row3, text="Reset loss stop",
                   command=self.reset_copy_loss_stop).pack(side="left", padx=8)
        self.sizing_result = tk.StringVar(value="")
        ttk.Button(action_row3, text="Preview risk per trade",
                   command=self.calculate).pack(side="left")
        ttk.Label(p3, textvariable=self.sizing_result, style="Muted.TLabel",
                  wraplength=960).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Label(root, text="New fills from the selected wallet are copied automatically after the one-time setup. No per-trade confirmation is shown. The built-in stop targets 50% of each trade's allocated margin; execution gaps, fees and slippage may change the result.",
                  style="Muted.TLabel", wraplength=980).pack(anchor="w", pady=(0, 8))
        self._refresh_copy_summary()

    def _update_scrollregion(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event) -> None:
        self.canvas.itemconfigure(self._canvas_window, width=event.width)

    def _mousewheel(self, event) -> None:
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _paste_to(self, variable: tk.StringVar) -> None:
        try:
            value = self.clipboard_get()
            if not value:
                raise ValueError("Clipboard is empty.")
            variable.set(value.strip())
            self.profile_status.set("Clipboard text pasted into the selected field. Save the profile when ready.")
        except (tk.TclError, ValueError) as exc:
            messagebox.showwarning("Paste failed", str(exc) or "There is no text in the clipboard.", parent=self)

    def _toggle_secret(self) -> None:
        self.api_secret_entry.configure(show="" if self.show_secret_var.get() else "•")

    def refresh_profiles(self) -> None:
        try:
            profiles = list_profiles()
            names = [p["name"] for p in profiles]
            selected = self.profile_var.get().strip()
            self.profile_combo.configure(values=names)
            if selected in names:
                self.profile_var.set(selected)
            elif names:
                self.profile_var.set(names[0])
            else:
                self.profile_var.set("")
                self.api_key_var.set("")
                self.api_secret_var.set("")
                self.profile_status.set("No saved profiles yet. Paste your API key and secret, then save.")
                return
            self._load_profile(self.profile_var.get())
        except Exception as exc:
            self.profile_status.set(f"Could not load profile list: {exc}")

    def _on_profile_selected(self, _event=None) -> None:
        self._load_profile(self.profile_var.get())

    def _load_profile(self, name: str) -> None:
        if not name:
            return
        self._loading_profile = True
        try:
            key, secret = get_profile_secrets(name)
            self.api_key_var.set(key)
            self.api_secret_var.set(secret)
            self.profile_status.set(f"Loaded '{name}'. Edit fields and save to update, or test the connection.")
        except Exception as exc:
            self.api_key_var.set("")
            self.api_secret_var.set("")
            self.profile_status.set(f"Profile '{name}' has no readable saved credentials: {exc}")
        finally:
            self._loading_profile = False

    def new_profile(self) -> None:
        self.profile_var.set("")
        self.api_key_var.set("")
        self.api_secret_var.set("")
        self.api_key_entry.focus_set()
        self.profile_status.set("New profile: enter a name in the Profile field, paste credentials, then save.")

    def save_current_profile(self) -> None:
        name = self.profile_var.get().strip()
        key = self.api_key_var.get().strip()
        secret = self.api_secret_var.get().strip()
        if not name:
            # Re-use the editable combobox as the profile-name input for creating a new profile.
            from tkinter import simpledialog
            name = simpledialog.askstring("New Bitunix profile", "Give this API profile a name:", parent=self)
            if not name:
                return
        try:
            save_profile(name, key, secret, "Bitunix")
            self.profile_var.set(name.strip())
            self.refresh_profiles()
            self.profile_var.set(name.strip())
            self.profile_status.set(f"Profile '{name.strip()}' saved securely on this computer.")
        except Exception as exc:
            messagebox.showerror("Could not save profile", str(exc), parent=self)

    def remove_profile(self) -> None:
        name = self.profile_var.get().strip()
        if not name:
            messagebox.showinfo("No profile selected", "Choose the saved Bitunix profile you want to delete.", parent=self)
            return
        if not messagebox.askyesno("Delete profile", f"Delete '{name}' and its stored credentials from this computer?",
                                   parent=self):
            return
        try:
            delete_profile(name)
            self.profile_var.set("")
            self.api_key_var.set("")
            self.api_secret_var.set("")
            self.refresh_profiles()
            self.profile_status.set(f"Profile '{name}' deleted.")
        except Exception as exc:
            messagebox.showerror("Delete failed", str(exc), parent=self)

    def test_profile(self) -> None:
        key, secret = self.api_key_var.get().strip(), self.api_secret_var.get().strip()
        if not key or not secret:
            messagebox.showwarning("Credentials required", "Select a saved profile or paste both API Key and API Secret first.",
                                   parent=self)
            return
        if self._test_in_progress:
            return
        self._test_in_progress = True
        self.test_button.configure(state="disabled", text="Testing connection…")
        self.profile_status.set("Testing signed read-only request to Bitunix…")
        threading.Thread(target=self._test_profile_worker, args=(key, secret), daemon=True).start()

    def _test_profile_worker(self, key: str, secret: str) -> None:
        ok, detail = test_connection(key, secret)
        self.after(0, lambda: self._finish_profile_test(ok, detail))

    def _finish_profile_test(self, ok: bool, detail: str) -> None:
        self._test_in_progress = False
        self.test_button.configure(state="normal", text="Test Bitunix connection")
        self.profile_status.set(detail)
        (messagebox.showinfo if ok else messagebox.showerror)("Bitunix connection status", detail, parent=self)

    def scan(self) -> None:
        if self._scan_in_progress:
            return
        try:
            low_ret, low_win = float(self.min_return.get()), float(self.min_win.get())
            if not 0 <= low_win <= 100:
                raise ValueError("Win-rate filter must be between 0 and 100.")
        except ValueError as exc:
            messagebox.showerror("Invalid filters", str(exc) or "Return and win-rate filters must be numbers.", parent=self)
            return
        self._scan_in_progress = True
        self.scan_button.configure(state="disabled", text="Scanning…")
        self.status.set("Fetching public leaderboard and recent closed fills (7 days)…")
        threading.Thread(target=self._scan_worker, args=(low_ret, low_win), daemon=True).start()

    def _scan_worker(self, low_ret: float, low_win: float) -> None:
        try:
            data = fetch_leaderboard()
            ranked = rank_traders(data, low_ret, low_win, 10)
            self.after(0, lambda: self._show_traders(ranked, len(data)))
        except Exception as exc:
            detail = str(exc)
            self.after(0, lambda detail=detail: self._finish_scan_error(detail))

    def _finish_scan_error(self, detail: str) -> None:
        self._scan_in_progress = False
        self.scan_button.configure(state="normal", text="Scan Hyperliquid")
        self.status.set(f"Scan failed: {detail}")

    def _show_traders(self, traders: list[Trader], total: int) -> None:
        self._scan_in_progress = False
        self.scan_button.configure(state="normal", text="Scan Hyperliquid")
        self.traders = traders
        for item in self.table.get_children():
            self.table.delete(item)
        for trader in traders:
            fmt = lambda value: "Unknown" if value is None else f"{value:.2f}"
            sample = "Unknown" if trader.trades is None else (
                f"7d n={trader.trades}" if "closed-fill proxy" in trader.source else str(trader.trades))
            self.table.insert("", "end", values=(
                trader.display_name, trader.address, fmt(trader.return_pct), fmt(trader.win_rate_pct), sample))
        self.status.set(f"Received {total} traders; {len(traders)} match your filters. Select one and start auto-copy.")

    def start_monitor(self) -> None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("Select a trader", "Scan Hyperliquid and select one trader first.", parent=self)
            return
        profile = self.profile_var.get().strip()
        if not profile:
            messagebox.showwarning("Save Bitunix profile first",
                "Save the Bitunix API profile in section 01 before enabling copy trading.", parent=self)
            return
        try:
            key, secret = get_profile_secrets(profile)
        except Exception as exc:
            messagebox.showerror("Bitunix profile unavailable", str(exc), parent=self)
            return
        if not self.copy_settings.get("live_copy_enabled", False):
            self.edit_copy_settings(require_enable=True)
        if not self.copy_settings.get("live_copy_enabled", False):
            self.status.set("Auto-copy was not enabled; no order will be sent.")
            return
        values = self.table.item(selected[0], "values")
        name, address = str(values[0]), str(values[1])
        if self._monitor_stop is not None:
            self.stop_monitor()
        stop_event = threading.Event()
        self._monitor_stop = stop_event
        self._watched_address = address
        self.watch_button.configure(state="disabled", text="Auto-copy running…")
        self.stop_button.configure(state="normal")
        self.status.set("Starting automatic copy for {0}. Existing fills will be ignored; new fills are copied.".format(name))
        settings = dict(self.copy_settings)
        threading.Thread(target=self._monitor_worker,
            args=(name, address, stop_event, key, secret, settings), daemon=True).start()

    def _monitor_worker(self, name: str, address: str, stop_event: threading.Event,
                        api_key: str, api_secret: str, settings: dict) -> None:
        seen: set[str] = set()
        try:
            initial = fetch_recent_fills(address, lookback_seconds=600)
            seen.update(fill_identity(fill) for fill in initial)
            client = BitunixClient(api_key, api_secret)
            self.after(0, lambda: self.status.set(
                "Auto-copy active for {0}; watching fresh Hyperliquid fills every 20 seconds.".format(name)))
        except Exception as exc:
            detail = str(exc)
            self.after(0, lambda detail=detail: self._monitor_error(detail))
            return
        while not stop_event.wait(20):
            try:
                fills = fetch_recent_fills(address, lookback_seconds=120)
                fresh = []
                for fill in fills:
                    identity = fill_identity(fill)
                    if identity not in seen:
                        seen.add(identity)
                        fresh.append(fill)
                if len(seen) > 2500:
                    seen = {fill_identity(fill) for fill in fills}
                if fresh:
                    fresh.sort(key=lambda fill: int(fill.get("time", 0) or 0))
                    for fill in fresh:
                        if stop_event.is_set():
                            break
                        try:
                            state = load_copy_state()
                            result = process_copy_fill(client, fill, address, settings, state)
                            detail = "{0} · {1} · {2}".format(name, fill.get("coin", "?"), result)
                        except Exception as exc:
                            detail = "Copy skipped / guarded: {0}".format(str(exc))
                        self.after(0, lambda detail=detail: self.status.set(detail))
                try:
                    state = load_copy_state()
                    loss_status = check_loss_circuit_breaker(client, settings, state)
                    if loss_status:
                        self.after(0, lambda msg=loss_status: self.status.set(msg))
                except Exception as exc:
                    detail = "Risk monitor could not verify positions: {0}. No additional copy orders are sent while checks fail.".format(exc)
                    self.after(0, lambda detail=detail: self.status.set(detail))
            except Exception as exc:
                detail = "Hyperliquid monitor temporarily failed: {0}".format(exc)
                self.after(0, lambda detail=detail: self.status.set(detail))

    def _monitor_error(self, detail: str) -> None:
        self.stop_monitor()
        self.status.set("Auto-copy could not start: {0}".format(detail))

    def _on_new_fills(self, name: str, address: str, fills: list[dict]) -> None:
        # Legacy-safe status callback; intentionally no per-trade confirmation prompt.
        if fills:
            self.status.set("{0}: {1} new fill(s) detected.".format(name, len(fills)))

    def stop_monitor(self) -> None:
        if self._monitor_stop is not None:
            self._monitor_stop.set()
        self._monitor_stop = None
        self._watched_address = None
        self.watch_button.configure(state="normal", text="Start auto-copy")
        self.stop_button.configure(state="disabled")
        self.status.set("Auto-copy monitor stopped. Any already-open isolated position and its exchange-side stop remain active.")

    def _refresh_copy_summary(self) -> None:
        settings = self.copy_settings
        state = load_copy_state()
        reserved = sum(float(r.get("margin", 0) or 0) for r in state.get("active_trades", {}).values())
        mode = "LIVE COPY ENABLED" if settings.get("live_copy_enabled") else "LIVE COPY DISABLED"
        halted = " · LOSS STOP ACTIVE" if state.get("halted") else ""
        self.copy_summary.set(
            "{0}{1}   |   Authorized capital: {2:.2f} USDT   |   Per-trade margin: {3:.1f}% ({4:.2f} USDT max)   |   Per-trade stop-risk: 50% of allocated margin   |   Max cumulative loss: {5:.1f}% ({6:.2f} USDT)   |   Leverage cap: {7}x   |   Tracked open margin: {8:.2f} USDT".format(
                mode, halted, settings["authorized_capital_usdt"], settings["margin_per_trade_pct"],
                settings["authorized_capital_usdt"] * settings["margin_per_trade_pct"] / 100.0,
                settings["max_total_loss_pct"],
                settings["authorized_capital_usdt"] * settings["max_total_loss_pct"] / 100.0,
                settings["max_leverage"], reserved))

    def edit_copy_settings(self, require_enable: bool = False) -> None:
        current = dict(self.copy_settings)
        win = tk.Toplevel(self)
        win.title("Auto-copy risk settings")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        outer = ttk.Frame(win, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="AUTO-COPY RISK SETTINGS", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(outer,
            text="These values are saved locally and reused automatically. You are not asked to approve every trade.",
            style="Muted.TLabel", wraplength=460
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))
        fields = [
            ("Authorized futures capital (USDT)", "authorized_capital_usdt", str(current["authorized_capital_usdt"])),
            ("Margin per trade (% of authorized capital)", "margin_per_trade_pct", str(current["margin_per_trade_pct"])),
            ("Maximum cumulative loss (% of authorized capital)", "max_total_loss_pct", str(current["max_total_loss_pct"])),
            ("Maximum leverage (1x–5x)", "max_leverage", str(current["max_leverage"])),
        ]
        variables = {}
        for row, (label, key, value) in enumerate(fields, start=2):
            ttk.Label(outer, text=label).grid(row=row, column=0, sticky="w", padx=(0, 14), pady=5)
            variable = tk.StringVar(value=value)
            variables[key] = variable
            ttk.Entry(outer, textvariable=variable, width=16).grid(row=row, column=1, sticky="e", pady=5)
        enabled_var = tk.BooleanVar(value=bool(current.get("live_copy_enabled")))
        ttk.Checkbutton(outer, text="Enable unattended real-money copy trades", variable=enabled_var).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(9, 3))
        ttk.Label(outer,
            text="For each position, requested margin is capped by these settings and the free futures balance. "
                 "The app switches the symbol to ISOLATED, verifies it, and attaches a market stop at a loss "
                 "target of 50% of the actual allocated margin. Gaps, fees, funding, exchange rejection and "
                 "liquidation can still make the realized loss differ. No funds are transferred.",
            style="Muted.TLabel", wraplength=500
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(5, 12))

        def save_settings() -> None:
            try:
                updated = save_copy_settings({
                    "authorized_capital_usdt": float(variables["authorized_capital_usdt"].get()),
                    "margin_per_trade_pct": float(variables["margin_per_trade_pct"].get()),
                    "max_total_loss_pct": float(variables["max_total_loss_pct"].get()),
                    "max_leverage": int(variables["max_leverage"].get()),
                    "live_copy_enabled": enabled_var.get(),
                })
            except (ValueError, TypeError) as exc:
                messagebox.showerror("Invalid settings", str(exc), parent=win)
                return
            if require_enable and not updated["live_copy_enabled"]:
                messagebox.showwarning("Live copy is disabled",
                    "Enable unattended copy trading to start the monitor.", parent=win)
                return
            if updated["live_copy_enabled"] and not current.get("live_copy_enabled"):
                approved = messagebox.askyesno(
                    "Confirm automatic futures trading",
                    "This enables real-money Bitunix futures orders from newly detected Hyperliquid fills without "
                    "asking you per trade. Orders use ISOLATED margin and saved size/loss caps, but execution and "
                    "exchange risk mean losses are not guaranteed to stay within a precise amount. Continue?",
                    parent=win)
                if not approved:
                    updated["live_copy_enabled"] = False
                    self.copy_settings = save_copy_settings(updated)
                    self._refresh_copy_summary()
                    return
            self.copy_settings = updated
            self._refresh_copy_summary()
            self.sizing_result.set("Settings saved. New trades use these limits; no per-trade prompt will appear.")
            win.destroy()

        buttons = ttk.Frame(outer)
        buttons.grid(row=8, column=0, columnspan=2, sticky="e", pady=(5, 0))
        ttk.Button(buttons, text="Cancel", command=win.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Save settings", style="Accent.TButton", command=save_settings).pack(side="right")
        win.update_idletasks()
        win.geometry("+%d+%d" % (self.winfo_rootx() + 100, self.winfo_rooty() + 80))
        self.wait_window(win)

    def reset_copy_loss_stop(self) -> None:
        if not messagebox.askyesno(
            "Reset cumulative loss stop",
            "Reset the saved cumulative-loss circuit breaker? This does not close positions and should only be used after reviewing the account.",
            parent=self):
            return
        try:
            reset_loss_halt()
            self.copy_state = load_copy_state()
            self._refresh_copy_summary()
            self.sizing_result.set("Loss stop reset. Current risk settings remain unchanged.")
        except Exception as exc:
            messagebox.showerror("Could not reset loss stop", str(exc), parent=self)

    def calculate(self) -> None:
        settings = self.copy_settings
        margin = settings["authorized_capital_usdt"] * settings["margin_per_trade_pct"] / 100.0
        risk = margin * 0.50
        leverage = settings["max_leverage"]
        move_pct = 50.0 / leverage
        notional = margin * leverage
        self.sizing_result.set(
            "Preview only: max margin {0:.2f} USDT · planned stop-risk {1:.2f} USDT · approximate stop distance {2:.2f}% at {3}x · notional {4:.2f} USDT. Actual execution can differ.".format(
                margin, risk, move_pct, leverage, notional))

    def review_alert(self) -> None:
        selected = self.table.selection()
        if not selected:
            messagebox.showinfo("No trader selected", "Select a trader row first.", parent=self)
            return
        values = self.table.item(selected[0], "values")
        messagebox.showinfo(
            "Trade alert review",
            f"Selected trader: {values[0]}\nWallet: {values[1]}\n\n"
            "Use Start auto-copy to automatically submit market orders for new fills from this wallet according to the saved isolated-margin risk settings.",
            parent=self)

    def _on_close(self) -> None:
        if self._monitor_stop is not None:
            self._monitor_stop.set()
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        self.destroy()


if __name__ == "__main__":
    RadarApp().mainloop()
