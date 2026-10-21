import unittest
from radar.bitunix import make_signature
from radar.models import Trader, rank_traders
from radar.risk import calculate_position_size


class BitunixSigningTests(unittest.TestCase):
    def test_double_sha256_signature_matches_reference_vector(self):
        signature = make_signature(
            nonce="123456",
            timestamp="20241120123045",
            api_key="yourApiKey",
            secret_key="yourSecretKey",
            query_params="id1uid200",
            body='{"uid":"2899","arr":[{"id":1,"name":"maple"},{"id":2,"name":"lily"}]}',
        )
        self.assertEqual(
            signature,
            "00397cd1e52c7dce3258067324363b6361fabc9178a0912b330c138db8745655",
        )


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
        traders = [
            Trader("0xknown", "Known", 20, 60, 12),
            Trader("0xunknown", "Unknown", 500, None, 1000),
            Trader("0xno-return", "No return", None, 99, 10),
        ]
        result = rank_traders(traders, 10, 55)
        self.assertEqual([trader.address for trader in result], ["0xknown"])

    def test_limit_over_ten_rejected(self):
        with self.assertRaises(ValueError):
            rank_traders([], 0, 0, 11)


if __name__ == "__main__":
    unittest.main()
