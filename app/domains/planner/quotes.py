from __future__ import annotations

QUOTES: tuple[tuple[str, str], ...] = (
    ("The goal of a successful trader is to make the best trades. Money is secondary.", "Alexander Elder"),
    ("Plan your trade and trade your plan.", "Unknown / commonly attributed trading maxim"),
    ("The market is a device for transferring money from the impatient to the patient.", "Warren Buffett"),
    ("Risk comes from not knowing what you're doing.", "Warren Buffett"),
    ("The most important thing in trading is not to lose money.", "Paul Tudor Jones"),
    ("Amateurs think about how much money they can make. Professionals think about how much money they could lose.", "Jack Schwager"),
)


def daily_quote(day_index: int) -> tuple[str, str]:
    return QUOTES[day_index % len(QUOTES)]
