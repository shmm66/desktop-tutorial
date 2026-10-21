import unittest
from unittest.mock import patch
import requests

from radar.bitunix import explain_api_error, make_signature
from radar.hyperliquid import closed_fill_stats, enrich_missing_win_rates
from radar.models import Trader, rank_traders
from radar.monitor import fetch_recent_fills, fill_identity
from radar.risk import calculate_position_size


class BitunixSigningTests(unittest.TestCase):
    def test_double_sha256_signature_matches_reference_vector(self):
        signature = make_signature("123456", "20241120123045", "yourApiKey", "yourSecretKey", "id1uid200", '{"uid":"2899","arr":[{"id":1,"name":"maple"},{"id":2,"name":"lily"}]}')
        self.assertEqual(signature, "00397cd1e52c7dce3258067324363b6361fabc9178a0912b330c138db8745655")

    def test_error_10004_explains_ip_whitelist_fix(self):
        message = explain_api_error(10004, "generic rejection")
        self.assertIn("IP address", message)
        self.assertIn("IP whitelist", message)
        self.assertIn("read-only", message)

    def test_error_10007_is_reported_as_signature_error(self):
        message = explain_api_error("10007")
        self.assertIn("signature", message.casefold())
        self.assertNotIn("whitelist", message.casefold())


class RiskTests(unittest.TestCase):
    def test_position_size(self):
        size = calculate_position_size(100, 10, 2)
        self.assertAlmostEqual(size.notional, 500)
        self.assertAlmostEqual(size.leverage, 5)

    def test_invalid_risk_rejected(self):
        with self.assertRaises(ValueError):
            calculate_position_size(100, 120, 1)

    def test_stop_must_be_positive(self):
        with self.assertRaises(ValueError):
            calculate_position_size(100, 10, 0)


class RankingTests(unittest.TestCase):
    def test_filters_and_caps_at_ten(self):
        traders = [Trader(f"0x{i}", f"T{i}", 20, 60, i) for i in range(15)]
        self.assertEqual(len(rank_traders(traders, 10, 55, 10)), 10)
        self.assertEqual(len(rank_traders(traders, 30, 55, 10)), 0)

    def test_unknown_win_rate_is_not_fabricated(self):
        traders = [Trader("0xknown", "Known", 20, 60, 12), Trader("0xunknown", "Unknown", 500, None, 1000), Trader("0xno-return", "No return", None, 99, 10)]
        self.assertEqual([trader.address for trader in rank_traders(traders, 10, 55)], ["0xknown"])

    def test_limit_over_ten_rejected(self):
        with self.assertRaises(ValueError):
            rank_traders([], 0, 0, 11)


class HyperliquidClosedFillTests(unittest.TestCase):
    def test_closed_fill_proxy_counts_only_nonzero_realized_close_fills(self):
        fills = [{"dir": "Close Long", "closedPnl": "12.5"}, {"dir": "Close Short", "closedPnl": "-4"}, {"dir": "Open Long", "closedPnl": "100"}, {"dir": "Close Long", "closedPnl": "0"}, {"dir": "Liquidated Isolated Position", "closedPnl": "-1"}, "bad-row"]
        win_rate, sample = closed_fill_stats(fills)
        self.assertEqual(sample, 3)
        self.assertAlmostEqual(win_rate, 100 / 3)

    def test_no_closed_fills_means_unknown_not_zero(self):
        self.assertEqual(closed_fill_stats([{"dir": "Open Long", "closedPnl": "9"}]), (None, 0))

    @patch("radar.hyperliquid._fetch_closed_fill_stats")
    def test_enrichment_labels_proxy_and_preserves_unknown_on_failure(self, fetch_stats):
        def stats_for(address, *_args):
            if address == "0x1":
                return 75.0, 4
            raise requests.RequestException("network failed")
        fetch_stats.side_effect = stats_for
        traders = [Trader("0x1", "A", 20, None, None), Trader("0x2", "B", 15, None, None)]
        result = enrich_missing_win_rates(traders, max_wallets=2)
        self.assertEqual(result[0].win_rate_pct, 75.0)
        self.assertEqual(result[0].trades, 4)
        self.assertIn("closed-fill proxy", result[0].source)
        self.assertIsNone(result[1].win_rate_pct)
        self.assertIsNone(result[1].trades)


class HyperliquidMonitorTests(unittest.TestCase):
    def test_fill_identity_prefers_exchange_hash(self):
        self.assertEqual(fill_identity({"hash": "0xabc", "coin": "BTC"}), "0xabc")

    @patch("radar.monitor.requests.post")
    def test_fetch_recent_fills_parses_public_response(self, post):
        response = post.return_value
        response.json.return_value = [{"hash": "0xabc", "coin": "BTC", "dir": "Open Long"}, None, "bad"]
        response.raise_for_status.return_value = None
        result = fetch_recent_fills("0x" + "1" * 40)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["coin"], "BTC")
        post.assert_called_once()

    def test_fetch_recent_fills_rejects_invalid_wallet_before_network(self):
        with self.assertRaises(ValueError):
            fetch_recent_fills("not-an-address")


if __name__ == "__main__":
    unittest.main()
