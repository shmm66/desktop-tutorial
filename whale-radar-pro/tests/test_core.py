import unittest
from radar.models import Trader, rank_traders
from radar.risk import calculate_position_size


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

    def test_limit_over_ten_rejected(self):
        with self.assertRaises(ValueError):
            rank_traders([], 0, 0, 11)


if __name__ == "__main__":
    unittest.main()
