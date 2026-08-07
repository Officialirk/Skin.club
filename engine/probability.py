"""
engine/probability.py
======================
Pure-math functions that turn a "case" definition (price + a list of
possible items, each with a probability and a market value) into the
statistics a player needs to make an informed decision:

    * Expected Value (EV)                — theoretical, NOT a promise
    * Return-to-Player (RTP) percentage
    * Variance / standard deviation       — how spread out outcomes are
    * Probability of profit / loss on a single open
    * Per-item contribution to EV         — full transparency

None of this predicts or influences any individual outcome. It describes
the *long-run average* behaviour of a random process whose odds you supply.

A "case" dict is expected to look like:
{
    "case_id": str,
    "name": str,
    "price": float,          # cost to open once, in `currency`
    "currency": str,
    "items": [
        {"name": str, "rarity": str, "probability": float, "market_value": float},
        ...
    ]
}
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

PROBABILITY_SUM_TOLERANCE = 0.002  # allow small rounding error in source odds


class InvalidCaseData(ValueError):
    """Raised when a case's item probabilities/values don't form a valid model."""


@dataclass
class ItemContribution:
    name: str
    rarity: str
    probability: float
    market_value: float
    ev_contribution: float          # probability * market_value
    is_profit: bool                 # market_value > case price


@dataclass
class CaseAnalysis:
    case_id: str
    name: str
    price: float
    currency: str
    expected_value_per_open: float      # Σ p_i * v_i  (expected item value received)
    net_ev: float                       # expected_value_per_open - price
    net_ev_pct: float                   # net_ev / price * 100
    rtp_pct: float                      # expected_value_per_open / price * 100 (Return To Player)
    variance: float                     # variance of the item VALUE received (not net EV, same shape)
    std_dev: float
    coefficient_of_variation: float     # std_dev / expected_value_per_open, a scale-free risk measure
    min_possible_value: float
    max_possible_value: float
    probability_of_profit: float        # P(market_value > price)
    probability_of_loss: float          # 1 - probability_of_profit (ties counted as loss)
    risk_level: str                     # "low" / "medium" / "high" / "extreme" — heuristic label
    items: List[ItemContribution] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = self.__dict__.copy()
        d["items"] = [i.__dict__ for i in self.items]
        return d


def validate_case(case: Dict[str, Any]) -> None:
    if "items" not in case or not case["items"]:
        raise InvalidCaseData(f"Case '{case.get('case_id')}' has no items.")
    if "price" not in case or case["price"] is None or case["price"] <= 0:
        raise InvalidCaseData(f"Case '{case.get('case_id')}' must have a positive price.")

    total_p = sum(i.get("probability", 0) for i in case["items"])
    if abs(total_p - 1.0) > PROBABILITY_SUM_TOLERANCE:
        raise InvalidCaseData(
            f"Case '{case.get('case_id')}' item probabilities sum to {total_p:.4f}, "
            f"expected 1.0 (+/- {PROBABILITY_SUM_TOLERANCE}). Fix the source odds data."
        )
    for i in case["items"]:
        if i.get("probability", 0) < 0:
            raise InvalidCaseData(f"Negative probability on item '{i.get('name')}'.")
        if i.get("market_value", 0) < 0:
            raise InvalidCaseData(f"Negative market value on item '{i.get('name')}'.")


def _risk_level(coefficient_of_variation: float) -> str:
    """Heuristic bucketing purely for display — not a scientific threshold."""
    if coefficient_of_variation < 2:
        return "low"
    if coefficient_of_variation < 6:
        return "medium"
    if coefficient_of_variation < 15:
        return "high"
    return "extreme"


def analyze_case(case: Dict[str, Any]) -> CaseAnalysis:
    """Compute the full statistical breakdown for a single case."""
    validate_case(case)

    price = float(case["price"])
    items_raw = case["items"]

    ev_per_open = sum(i["probability"] * i["market_value"] for i in items_raw)

    variance = sum(
        i["probability"] * (i["market_value"] - ev_per_open) ** 2 for i in items_raw
    )
    std_dev = variance ** 0.5
    coeff_var = (std_dev / ev_per_open) if ev_per_open > 0 else float("inf")

    net_ev = ev_per_open - price
    net_ev_pct = (net_ev / price) * 100 if price else 0.0
    rtp_pct = (ev_per_open / price) * 100 if price else 0.0

    prob_profit = sum(i["probability"] for i in items_raw if i["market_value"] > price)
    prob_loss = 1.0 - prob_profit

    items = [
        ItemContribution(
            name=i["name"],
            rarity=i.get("rarity", "unknown"),
            probability=i["probability"],
            market_value=i["market_value"],
            ev_contribution=i["probability"] * i["market_value"],
            is_profit=i["market_value"] > price,
        )
        for i in items_raw
    ]
    items.sort(key=lambda x: x.market_value, reverse=True)

    warnings: List[str] = []
    if net_ev < 0:
        warnings.append(
            f"Negative expected value: on average you lose "
            f"{abs(net_ev_pct):.2f}% of your stake per open over the long run "
            f"({case['currency']} {abs(net_ev):.4f} per {case['currency']} {price:.2f} spent)."
        )
    if rtp_pct < 100:
        warnings.append(
            f"Return-to-player is {rtp_pct:.2f}% — this case is not designed to profit players "
            f"on average, regardless of short-term results."
        )
    if coeff_var >= 15:
        warnings.append(
            "Extremely high variance: the average outcome is almost entirely driven by a tiny-"
            "probability jackpot item. Most individual opens will lose relative to price."
        )
    if prob_profit < 0.01:
        warnings.append(
            f"Only a {prob_profit*100:.2f}% chance any single open returns an item worth more "
            f"than the case price."
        )

    return CaseAnalysis(
        case_id=case["case_id"],
        name=case["name"],
        price=price,
        currency=case.get("currency", "USD"),
        expected_value_per_open=ev_per_open,
        net_ev=net_ev,
        net_ev_pct=net_ev_pct,
        rtp_pct=rtp_pct,
        variance=variance,
        std_dev=std_dev,
        coefficient_of_variation=coeff_var,
        min_possible_value=min(i["market_value"] for i in items_raw),
        max_possible_value=max(i["market_value"] for i in items_raw),
        probability_of_profit=prob_profit,
        probability_of_loss=prob_loss,
        risk_level=_risk_level(coeff_var),
        items=items,
        warnings=warnings,
    )


def analyze_all(cases: List[Dict[str, Any]]) -> List[CaseAnalysis]:
    return [analyze_case(c) for c in cases]
