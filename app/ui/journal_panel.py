from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from tkinter import filedialog, messagebox, StringVar
from tkinter import ttk

from app.core.database import connect
from app.core.config import AppConfig
from app.domains.journal.models import AssetClass, JournalEntry, TradeDirection, TradeOutcome
from app.repositories.sqlite_journal_repository import SQLiteJournalRepository
from app.services.journal import JournalService


class JournalPanel(ttk.Frame):
    """Production-oriented journal UI. Forex and Crypto expose different fields."""

    FOREX_FIELDS = ("Symbol", "Direction", "Lot", "Entry", "Stop Loss", "Take Profit", "Exit", "Fees", "Funding", "Setup", "Thesis", "Emotion", "Notes")
    CRYPTO_FIELDS = ("Symbol", "Direction", "Quantity", "Entry", "Stop Loss", "Take Profit", "Exit", "Leverage", "Margin", "Fees", "Funding", "Liquidation", "Exchange", "Setup", "Thesis", "Emotion", "Notes")

    def __init__(self, master, config: AppConfig):
        super().__init__(master)
        self.config = config
        self.market = StringVar(value="forex")
        self.vars: dict[str, ttk.Entry] = {}
        self.image_refs: list[str] = []
        self._build()
        self._render_fields()
        self.refresh()

    def _build(self):
        head = ttk.Frame(self)
        head.pack(fill="x", pady=(0, 12))
        ttk.Label(head, text="Trading Journal", style="Title.TLabel").pack(side="right")
        ttk.Label(head, text="ثبت دقیق معاملات؛ داده‌ها محلی و قابل خروجی هستند", style="Muted.TLabel").pack(side="right", padx=16)
        ttk.Radiobutton(head, text="Forex", value="forex", variable=self.market, command=self._render_fields).pack(side="left", padx=4)
        ttk.Radiobutton(head, text="Crypto", value="crypto", variable=self.market, command=self._render_fields).pack(side="left", padx=4)

        self.form = ttk.Frame(self, style="Card.TFrame", padding=14)
        self.form.pack(fill="x")
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="افزودن تصویر", command=self.add_image).pack(side="right", padx=4)
        ttk.Button(actions, text="ثبت معامله", style="Accent.TButton", command=self.save).pack(side="right", padx=4)
        ttk.Button(actions, text="پاک‌کردن فرم", command=self.clear).pack(side="right", padx=4)
        self.image_label = ttk.Label(actions, text="تصویری انتخاب نشده", style="Muted.TLabel")
        self.image_label.pack(side="right", padx=12)

        self.table = ttk.Treeview(self, columns=("market", "symbol", "direction", "entry", "exit", "pnl", "outcome"), show="headings", height=12)
        for col, title in zip(self.table["columns"], ("Market", "Symbol", "Direction", "Entry", "Exit", "Net P&L", "Outcome")):
            self.table.heading(col, text=title)
            self.table.column(col, width=120, anchor="center")
        self.table.pack(fill="both", expand=True, pady=(6, 0))
        self.table.bind("<Double-1>", self._load_selected)

    def _render_fields(self):
        for child in self.form.winfo_children(): child.destroy()
        self.vars.clear(); self.image_refs = []
        fields = self.FOREX_FIELDS if self.market.get() == "forex" else self.CRYPTO_FIELDS
        for i, name in enumerate(fields):
            row, col = divmod(i, 4)
            ttk.Label(self.form, text=name).grid(row=row, column=col * 2 + 1, sticky="e", padx=6, pady=5)
            if name == "Direction":
                v = ttk.Combobox(self.form, values=("long", "short"), state="readonly", width=18)
                v.set("long")
            elif name == "Emotion":
                v = ttk.Combobox(self.form, values=("calm", "confident", "fear", "greed", "FOMO", "revenge", "uncertain"), width=18)
            else:
                v = ttk.Entry(self.form, width=20)
            v.grid(row=row, column=col * 2, sticky="ew", padx=6, pady=5)
            self.vars[name] = v
        for col in range(0, 8, 2): self.form.columnconfigure(col, weight=1)
        self.image_label.configure(text="تصویری انتخاب نشده")

    def _decimal(self, name: str, required: bool = False) -> Decimal | None:
        value = self.vars[name].get().strip()
        if not value:
            if required: raise ValueError(f"{name} is required")
            return None
        try: return Decimal(value)
        except InvalidOperation as exc: raise ValueError(f"{name} must be numeric") from exc

    def _entry(self, editing_id: str | None = None) -> JournalEntry:
        market = AssetClass(self.market.get())
        quantity = self._decimal("Lot" if market is AssetClass.FOREX else "Quantity", True)
        notes = self.vars["Notes"].get().strip()
        extras = []
        if market is AssetClass.CRYPTO:
            extras.append(f"Leverage={self.vars['Leverage'].get().strip()}; Margin={self.vars['Margin'].get().strip()}; Liquidation={self.vars['Liquidation'].get().strip()}; Exchange={self.vars['Exchange'].get().strip()}")
        else:
            extras.append(f"Lot={self.vars['Lot'].get().strip()}")
        return JournalEntry(
            id=editing_id, asset_class=market, symbol=self.vars["Symbol"].get().strip(),
            direction=TradeDirection(self.vars["Direction"].get()), entry_price=self._decimal("Entry", True), quantity=quantity,
            stop_loss=self._decimal("Stop Loss"), take_profit=self._decimal("Take Profit"), exit_price=self._decimal("Exit"),
            fees=self._decimal("Fees") or Decimal("0"), funding=self._decimal("Funding") or Decimal("0"),
            outcome=TradeOutcome.OPEN, setup=self.vars["Setup"].get().strip(), thesis=self.vars["Thesis"].get().strip(),
            emotion=self.vars["Emotion"].get().strip(), notes=(notes + " | " + " | ".join(extras)).strip(" |"), image_refs=list(self.image_refs),
        )

    def _service(self):
        conn = connect(self.config.db_path)
        return conn, JournalService(SQLiteJournalRepository(conn))

    def save(self):
        conn = None
        try:
            entry = self._entry()
            conn, service = self._service(); service.record(entry)
            self.clear(); self.refresh(); messagebox.showinfo("Journal", "معامله با موفقیت ثبت شد.")
        except Exception as exc:
            messagebox.showerror("Journal", str(exc))
        finally:
            if conn: conn.close()

    def refresh(self):
        for item in self.table.get_children(): self.table.delete(item)
        conn = None
        try:
            conn, service = self._service()
            for e in service.entries(AssetClass(self.market.get())):
                self.table.insert("", "end", iid=e.id or "", values=(e.asset_class.value, e.symbol, e.direction.value, str(e.entry_price), str(e.exit_price or ""), str(e.net_pnl or ""), e.outcome.value))
        finally:
            if conn: conn.close()

    def clear(self):
        for v in self.vars.values():
            try: v.delete(0, "end")
            except Exception: v.set("")
        if "Direction" in self.vars: self.vars["Direction"].set("long")
        self.image_refs = []; self.image_label.configure(text="تصویری انتخاب نشده")

    def add_image(self):
        path = filedialog.askopenfilename(title="انتخاب تصویر معامله", filetypes=(("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")))
        if path:
            self.image_refs.append(str(Path(path).resolve()))
            self.image_label.configure(text=f"{len(self.image_refs)} تصویر انتخاب شد")

    def _load_selected(self, _event=None):
        selected = self.table.selection()
        if not selected: return
        conn = None
        try:
            conn, service = self._service(); entry = service.get(selected[0])
            if not entry: return
            self.market.set(entry.asset_class.value); self._render_fields()
            values = {"Symbol": entry.symbol, "Direction": entry.direction.value, "Entry": str(entry.entry_price), "Stop Loss": str(entry.stop_loss or ""), "Take Profit": str(entry.take_profit or ""), "Exit": str(entry.exit_price or ""), "Fees": str(entry.fees), "Funding": str(entry.funding), "Setup": entry.setup, "Thesis": entry.thesis, "Emotion": entry.emotion, "Notes": entry.notes}
            qname = "Lot" if entry.asset_class is AssetClass.FOREX else "Quantity"; values[qname] = str(entry.quantity)
            for key, value in values.items():
                if key in self.vars: self.vars[key].insert(0, value)
            self.image_refs = list(entry.image_refs); self.image_label.configure(text=f"{len(self.image_refs)} تصویر ذخیره شده" if self.image_refs else "تصویری انتخاب نشده")
        finally:
            if conn: conn.close()
