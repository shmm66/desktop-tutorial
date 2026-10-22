from __future__ import annotations

import json
import time
import unittest

from radar.hyperliquid_stream import HyperliquidFillStream


class HyperliquidFillStreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.address = "0x" + "1" * 40
        self.stream = HyperliquidFillStream([("Trader One", self.address)])

    def make_message(self, fill_time: int, is_snapshot: bool) -> str:
        return json.dumps({
            "channel": "userFills",
            "data": {
                "user": self.address,
                "isSnapshot": is_snapshot,
                "fills": [{
                    "coin": "BTC",
                    "dir": "Open Long",
                    "px": "65000",
                    "sz": "0.01",
                    "time": fill_time,
                    "hash": "0xtrade",
                }],
            },
        })

    def test_live_fill_is_queued(self) -> None:
        now_ms = int(time.time() * 1000)
        self.stream._on_message(None, self.make_message(now_ms, False))
        event = self.stream.get_fill(timeout=0)
        self.assertIsNotNone(event)
        name, address, fill = event
        self.assertEqual(name, "Trader One")
        self.assertEqual(address, self.address.lower())
        self.assertEqual(fill["coin"], "BTC")

    def test_old_snapshot_history_is_ignored(self) -> None:
        old_time = int(time.time() * 1000) - 120_000
        self.stream._on_message(None, self.make_message(old_time, True))
        self.assertIsNone(self.stream.get_fill(timeout=0))

    def test_recent_snapshot_fill_is_queued(self) -> None:
        recent_time = int(time.time() * 1000) - 5_000
        self.stream._on_message(None, self.make_message(recent_time, True))
        self.assertIsNotNone(self.stream.get_fill(timeout=0))

    def test_unknown_wallet_is_ignored(self) -> None:
        payload = json.loads(self.make_message(int(time.time() * 1000), False))
        payload["data"]["user"] = "0x" + "2" * 40
        self.stream._on_message(None, json.dumps(payload))
        self.assertIsNone(self.stream.get_fill(timeout=0))


if __name__ == "__main__":
    unittest.main()
