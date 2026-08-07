"""
engine/bankroll.py
====================
Bankroll / risk-management calculator.

Given a budget, a maximum acceptable loss, and a case's statistics, this
module answers practical "how much / how long" questions:

    * How many opens can the budget afford at most?
    * At what point does the simulated chance of having lost more than the
      max acceptable loss cross a risk threshold (e.g. 75%)?
    * What is a reasonable "stop-loss" session size given the user's own
      risk tolerance?

This is decision SUPPORT, not a betting system. It never claims a
recommended session size prevents losses — it only estimates probabilities
under the odds the user supplied, using the Monte Carlo engine in risk.py.
Nothing here places bets, opens cases, or interacts with any live service.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .probability import CaseAnalysis
from .risk import simulate_opens, _bounded_trials


@dataclass
class BankrollRecommendation:
    budget: float
    max_acceptable_loss: float
    case_price: float
    max_opens_affordable: int
    recommended_session_opens: int
    recommended_session_reasoning: str
    probability_session_exceeds_max_loss: float
    probability_full_budget_lost: float
    expected_net_at_recommended_session: float
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def compute_bankroll_plan(
    case: Dict[str, Any],
    analysis: CaseAnalysis,
    budget: float,
    max_acceptable_loss: float,
    risk_tolerance_pct: float = 25.0,
    n_trials: int = 3000,
    seed: Optional[int] = None,
) -> BankrollRecommendation:
    """
    risk_tolerance_pct: the maximum probability (0-100) the user is willing
    to accept of a session's losses exceeding `max_acceptable_loss`. Lower
    = more conservative recommendation.
    """
    if budget <= 0:
        raise ValueError("budget must be positive")
    if max_acceptable_loss <= 0:
        raise ValueError("max_acceptable_loss must be positive")
    if max_acceptable_loss > budget:
        raise ValueError("max_acceptable_loss cannot exceed budget")

    price = analysis.price
    max_opens_affordable = int(budget // price)
    # Sanity cap so a tiny case price + huge budget can't request an
    # unreasonably long simulated session from the server.
    SIMULATION_OPENS_CAP = 50_000
    sim_opens_ceiling = min(max_opens_affordable, SIMULATION_OPENS_CAP)

    warnings: List[str] = []
    if max_opens_affordable == 0:
        warnings.append(
            f"Your budget ({budget:.2f}) cannot cover even a single open of this case "
            f"({price:.2f}). No session is possible."
        )
        return BankrollRecommendation(
            budget=budget,
            max_acceptable_loss=max_acceptable_loss,
            case_price=price,
            max_opens_affordable=0,
            recommended_session_opens=0,
            recommended_session_reasoning="Budget too small to open this case even once.",
            probability_session_exceeds_max_loss=1.0,
            probability_full_budget_lost=0.0,
            expected_net_at_recommended_session=0.0,
            warnings=warnings,
        )

    if max_acceptable_loss < price:
        warnings.append(
            f"Your maximum acceptable loss ({max_acceptable_loss:.2f}) is smaller than the "
            f"price of a single open ({price:.2f}). Realistically you cannot open this case "
            f"even once without risking more than your stated limit."
        )

    if analysis.net_ev < 0:
        warnings.append(
            f"This case has a negative expected value ({analysis.net_ev_pct:.2f}% per open). "
            f"No session length or bankroll strategy changes that — on average, more opens "
            f"means a larger expected loss, not a better chance of ending up ahead."
        )

    # Search increasing session lengths (in opens) up to max_opens_affordable,
    # tracking the simulated probability of exceeding the user's max acceptable loss.
    # We find the largest session length for which that probability stays at or
    # below the user's risk_tolerance_pct, using a coarse-to-fine scan to keep
    # simulation cost bounded.
    candidates = sorted(set(
        max(1, int(sim_opens_ceiling * f))
        for f in (0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.85, 1.0)
    ))

    best_n = candidates[0]
    best_prob_exceed = None
    best_expected_net = None
    results_by_n = {}

    threshold = risk_tolerance_pct / 100.0

    for n in candidates:
        sim = simulate_opens(case, n_opens=n, n_trials=n_trials, seed=seed)
        # Probability that the loss (negative net) magnitude exceeds max_acceptable_loss.
        # Approximate using the simulated distribution's percentiles/mean+std via a
        # normal approximation on the underlying samples is unnecessary here — instead
        # we re-derive it directly from the same simulation by rerunning a light check.
        prob_exceed = _prob_loss_exceeds(case, n, max_acceptable_loss, n_trials=n_trials, seed=seed)
        results_by_n[n] = (sim, prob_exceed)
        if prob_exceed <= threshold:
            best_n = n
            best_prob_exceed = prob_exceed
            best_expected_net = sim.mean_net

    if best_prob_exceed is None:
        # Even the smallest candidate session exceeds the user's risk tolerance.
        n = candidates[0]
        sim, prob_exceed = results_by_n[n]
        best_n = n
        best_prob_exceed = prob_exceed
        best_expected_net = sim.mean_net
        warnings.append(
            f"Even a small session of {n} open(s) has an estimated "
            f"{prob_exceed*100:.1f}% chance of losing more than your stated maximum "
            f"acceptable loss. Consider a smaller max loss threshold, a cheaper case, "
            f"or not opening at all."
        )

    prob_full_budget_lost = _prob_loss_exceeds(case, sim_opens_ceiling, budget, n_trials=n_trials, seed=seed)

    reasoning = (
        f"Simulated {n_trials} sessions at several session lengths (up to the "
        f"{max_opens_affordable} opens your budget affords). Recommended "
        f"{best_n} open(s) as the largest session length where the estimated chance of "
        f"losing more than your stated max ({max_acceptable_loss:.2f}) stays at or below "
        f"your risk tolerance ({risk_tolerance_pct:.0f}%)."
    )

    return BankrollRecommendation(
        budget=budget,
        max_acceptable_loss=max_acceptable_loss,
        case_price=price,
        max_opens_affordable=max_opens_affordable,
        recommended_session_opens=best_n,
        recommended_session_reasoning=reasoning,
        probability_session_exceeds_max_loss=best_prob_exceed,
        probability_full_budget_lost=prob_full_budget_lost,
        expected_net_at_recommended_session=best_expected_net,
        warnings=warnings,
    )


def _prob_loss_exceeds(
    case: Dict[str, Any],
    n_opens: int,
    loss_threshold: float,
    n_trials: int = 3000,
    seed: Optional[int] = None,
) -> float:
    """Fraction of simulated sessions of `n_opens` where net loss > loss_threshold."""
    if n_opens <= 0:
        return 0.0
    import random
    n_trials = _bounded_trials(n_opens, n_trials)
    rng = random.Random(seed)
    items = case["items"]
    weights = [i["probability"] for i in items]
    values = [i["market_value"] for i in items]
    price = float(case["price"])
    total_cost = price * n_opens

    exceed_count = 0
    for _ in range(n_trials):
        picks = rng.choices(values, weights=weights, k=n_opens)
        net = sum(picks) - total_cost
        if -net > loss_threshold:
            exceed_count += 1
    return exceed_count / n_trials
