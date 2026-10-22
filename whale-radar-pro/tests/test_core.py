import unittest
from unittest.mock import patch
import requests

from radar.bitunix import explain_api_error, make_signature
from radar.copytrade import (
    BitunixClient, CopyTradeError, calculate_order_plan, calculate_risk_headroom, check_loss_circuit_breaker,
    futures_symbol, interpret_fill, process_copy_fill, validate_settings,
)
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

    def test_read_only_api_key_error_explains_futures_trade_permission(self):
        message = explain_api_error(403)
        self.assertIn("Futures trading permission", message)
        self.assertIn("withdrawals", message.casefold())

    def test_account_trade_restriction_has_actionable_guidance(self):
        message = explain_api_error("20011")
        self.assertIn("not allowed to trade", message.casefold())
        self.assertIn("Bitunix", message)

    def test_verify_futures_account_reads_balance_positions_and_orders_without_ordering(self):
        client = BitunixClient("unit-test-key", "unit-test-secret")
        with patch.object(client, "account", return_value={"available": "12.50"}) as account:
            with patch.object(client, "positions", return_value=[{"positionId": "p1"}]) as positions:
                with patch.object(client, "pending_orders", return_value=[{"orderId": "o1"}, {"orderId": "o2"}]) as orders:
                    result = client.verify_futures_account()
        self.assertEqual(result, {"available_usdt": 12.5, "open_positions": 1, "pending_orders": 2})
        account.assert_called_once_with()
        positions.assert_called_once_with()
        orders.assert_called_once_with()


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




class IsolatedCopyRiskTests(unittest.TestCase):
    def test_long_stop_risks_half_of_actual_allocated_margin(self):
        plan = calculate_order_plan(4.0, 5, 100.0, "LONG", 4, 2, 0.0001)
        self.assertAlmostEqual(float(plan["margin"]), 4.0, places=4)
        self.assertAlmostEqual(float(plan["risk_usdt"]), 2.0, places=4)
        self.assertAlmostEqual(float(plan["stop_price"]), 90.0, places=2)
        self.assertAlmostEqual(float(plan["notional"]), 20.0, places=4)

    def test_short_stop_is_above_entry_with_same_risk(self):
        plan = calculate_order_plan(4.0, 5, 100.0, "SHORT", 4, 2, 0.0001)
        self.assertAlmostEqual(float(plan["risk_usdt"]), 2.0, places=4)
        self.assertAlmostEqual(float(plan["stop_price"]), 110.0, places=2)

    def test_rounding_never_exceeds_authorized_margin(self):
        plan = calculate_order_plan(4.0, 5, 333.33, "LONG", 2, 2, 0.01)
        self.assertLessEqual(float(plan["margin"]), 4.0)
        self.assertLessEqual(float(plan["risk_usdt"]), 2.0)

    def test_minimum_contract_size_rejects_small_margin(self):
        with self.assertRaises(ValueError):
            calculate_order_plan(0.01, 2, 1000.0, "LONG", 3, 2, 0.01)

    def test_only_unambiguous_open_close_directions_are_accepted(self):
        self.assertEqual(interpret_fill({"dir": "Open Long"}), ("OPEN", "LONG"))
        self.assertEqual(interpret_fill({"dir": "Close Short"}), ("CLOSE", "SHORT"))
        self.assertIsNone(interpret_fill({"dir": "Add Long"}))

    def test_coin_mapping_is_simple_and_usdt_only(self):
        self.assertEqual(futures_symbol("BTC"), "BTCUSDT")
        with self.assertRaises(Exception):
            futures_symbol("BTC/USDT")

    def test_invalid_leverage_cap_rejected(self):
        with self.assertRaises(ValueError):
            validate_settings({
                "authorized_capital_usdt": 20,
                "margin_per_trade_pct": 20,
                "max_total_loss_pct": 10,
                "max_leverage": 10,
            })

    def test_aggregate_stop_risk_budget_respects_existing_positions(self):
        settings = {"authorized_capital_usdt": 20, "max_total_loss_pct": 10}
        state = {"active_trades": {"one": {"risk_usdt": 1.5}}}
        self.assertAlmostEqual(calculate_risk_headroom(settings, state, 0), 0.5)
        self.assertAlmostEqual(calculate_risk_headroom(settings, {"active_trades": {}}, -1.9), 0.1)
        self.assertAlmostEqual(calculate_risk_headroom(settings, {"active_trades": {}}, -2.0), 0.0)

    def test_profitable_active_position_releases_only_remaining_stop_budget(self):
        settings = {"authorized_capital_usdt": 20, "max_total_loss_pct": 10}
        state = {"active_trades": {"one": {"risk_usdt": 2.0}}}
        # Realized profit may add headroom; floating profit must not, because it can disappear before a stop fills.
        self.assertAlmostEqual(calculate_risk_headroom(settings, state, 1.0), 1.0)
        self.assertAlmostEqual(calculate_risk_headroom(settings, state, 1.0, active_unrealized_pnl=1.0), 0.0)

    def test_loss_halt_keeps_position_tracked_if_close_request_fails(self):
        class FakeClient:
            close_calls = 0
            def positions(self, symbol=None):
                return [{
                    "positionId": "pos1", "symbol": "BTCUSDT", "side": "LONG",
                    "marginMode": "ISOLATION", "unrealizedPNL": "-2",
                    "realizedPNL": "0", "fee": "0", "funding": "0",
                }]
            def close_position(self, position_id):
                self.close_calls += 1
                raise CopyTradeError("temporary close failure")
        client = FakeClient()
        settings = {"authorized_capital_usdt": 20, "max_total_loss_pct": 10}
        state = {
            "halted": False, "halt_reason": "", "started_at": 0,
            "active_trades": {"copy1": {
                "position_id": "pos1", "symbol": "BTCUSDT", "side": "LONG",
                "margin": 4, "risk_usdt": 2, "created_at": 1,
            }},
            "closed_trades": [],
        }
        result = check_loss_circuit_breaker(client, settings, state)
        self.assertIn("Loss limit reached", result)
        self.assertTrue(state["halted"])
        self.assertIn("copy1", state["active_trades"])
        check_loss_circuit_breaker(client, settings, state)
        self.assertGreaterEqual(client.close_calls, 2)
        self.assertIn("copy1", state["active_trades"])

    def test_halted_bot_never_places_new_orders(self):
        class ForbiddenClient:
            def __getattr__(self, name):
                raise AssertionError("API must not be touched when the circuit breaker is active: " + name)
        message = process_copy_fill(
            ForbiddenClient(),
            {"hash": "fill-1", "coin": "BTC", "dir": "Open Long", "px": "60000", "sz": "1"},
            "0x" + "1" * 40,
            {"live_copy_enabled": True},
            {"halted": True, "halt_reason": "loss limit reached", "seen_fills": [],
             "active_trades": {}, "closed_trades": []},
        )
        self.assertIn("loss limit", message)


if __name__ == "__main__":
    unittest.main()
