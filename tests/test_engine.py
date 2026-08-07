"""
tests/test_engine.py
======================
Unit tests for the analysis engine. Run with:  python -m pytest tests/
(or python -m unittest discover tests, no extra dependency needed).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.probability import analyze_case, validate_case, InvalidCaseData
from engine.risk import simulate_opens
from engine.bankroll import compute_bankroll_plan


SIMPLE_CASE = {
    "case_id": "unit-test-case",
    "name": "Unit Test Case",
    "price": 2.0,
    "currency": "USD",
    "items": [
        {"name": "Common", "rarity": "common", "probability": 0.9, "market_value": 1.0},
        {"name": "Rare", "rarity": "rare", "probability": 0.1, "market_value": 12.0},
    ],
}
# EV = 0.9*1.0 + 0.1*12.0 = 0.9 + 1.2 = 2.1 ; net EV = 2.1 - 2.0 = 0.1 (positive, 5%)

NEGATIVE_EV_CASE = {
    "case_id": "unit-test-negative",
    "name": "Unit Test Negative Case",
    "price": 5.0,
    "currency": "USD",
    "items": [
        {"name": "Common", "rarity": "common", "probability": 0.95, "market_value": 1.0},
        {"name": "Rare", "rarity": "rare", "probability": 0.05, "market_value": 20.0},
    ],
}
# EV = 0.95*1.0 + 0.05*20.0 = 0.95 + 1.0 = 1.95 ; net EV = 1.95 - 5.0 = -3.05 (negative)


class TestProbabilityEngine(unittest.TestCase):
    def test_ev_calculation(self):
        a = analyze_case(SIMPLE_CASE)
        self.assertAlmostEqual(a.expected_value_per_open, 2.1, places=6)
        self.assertAlmostEqual(a.net_ev, 0.1, places=6)
        self.assertAlmostEqual(a.net_ev_pct, 5.0, places=4)
        self.assertAlmostEqual(a.rtp_pct, 105.0, places=4)

    def test_negative_ev_flagged(self):
        a = analyze_case(NEGATIVE_EV_CASE)
        self.assertLess(a.net_ev, 0)
        self.assertTrue(any("Negative expected value" in w for w in a.warnings))

    def test_probability_of_profit(self):
        a = analyze_case(SIMPLE_CASE)
        # Only "Rare" (12.0) beats price 2.0 -> probability 0.1
        self.assertAlmostEqual(a.probability_of_profit, 0.1, places=6)
        self.assertAlmostEqual(a.probability_of_loss, 0.9, places=6)

    def test_invalid_probabilities_rejected(self):
        bad_case = {
            "case_id": "bad",
            "name": "Bad",
            "price": 1.0,
            "currency": "USD",
            "items": [
                {"name": "A", "rarity": "x", "probability": 0.5, "market_value": 1.0},
                {"name": "B", "rarity": "x", "probability": 0.2, "market_value": 1.0},
            ],
        }
        with self.assertRaises(InvalidCaseData):
            validate_case(bad_case)

    def test_variance_nonnegative(self):
        a = analyze_case(SIMPLE_CASE)
        self.assertGreaterEqual(a.variance, 0)
        self.assertGreaterEqual(a.std_dev, 0)


class TestRiskEngine(unittest.TestCase):
    def test_simulation_converges_near_ev(self):
        sim = simulate_opens(SIMPLE_CASE, n_opens=200, n_trials=4000, seed=42)
        analysis = analyze_case(SIMPLE_CASE)
        expected_net_total = analysis.net_ev * 200
        # Simulated mean should be in the right ballpark of the theoretical value
        # (loose tolerance since this is a stochastic test).
        self.assertAlmostEqual(sim.mean_net, expected_net_total, delta=abs(expected_net_total) + 3.0)

    def test_percentiles_ordered(self):
        sim = simulate_opens(SIMPLE_CASE, n_opens=50, n_trials=2000, seed=1)
        self.assertLessEqual(sim.percentile_5, sim.percentile_25)
        self.assertLessEqual(sim.percentile_25, sim.percentile_75)
        self.assertLessEqual(sim.percentile_75, sim.percentile_95)


class TestBankrollEngine(unittest.TestCase):
    def test_budget_too_small_for_one_open(self):
        analysis = analyze_case(SIMPLE_CASE)
        plan = compute_bankroll_plan(SIMPLE_CASE, analysis, budget=1.0, max_acceptable_loss=1.0, seed=1)
        self.assertEqual(plan.max_opens_affordable, 0)
        self.assertTrue(any("cannot cover even a single open" in w for w in plan.warnings))

    def test_negative_ev_warns_regardless_of_bankroll(self):
        analysis = analyze_case(NEGATIVE_EV_CASE)
        plan = compute_bankroll_plan(
            NEGATIVE_EV_CASE, analysis, budget=100.0, max_acceptable_loss=30.0, seed=1
        )
        self.assertTrue(any("negative expected value" in w for w in plan.warnings))

    def test_max_loss_cannot_exceed_budget(self):
        analysis = analyze_case(SIMPLE_CASE)
        with self.assertRaises(ValueError):
            compute_bankroll_plan(SIMPLE_CASE, analysis, budget=10.0, max_acceptable_loss=20.0)


if __name__ == "__main__":
    unittest.main()
