"""
engine/risk.py
===============
Monte Carlo simulation of repeated case opens, used to show the *range* of
plausible outcomes (not a prediction of any specific outcome) for a given
number of opens. This is what lets the dashboard say things like:

    "If you open this case 100 times, 90% of simulated outcomes fall
     between a $-18.40 and a $+6.10 net result."

The simulation draws from the same probabilities you supplied for the case.
It does not read, infer, or influence anything about how Skin.Club (or any
other site) actually generates outcomes — it is a generic weighted random
draw over your own declared odds table, purely to visualize variance.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Dict, Any

# Upper bound on total random draws (n_opens * n_trials) per simulation call,
# so a large budget/session request from the web UI can't turn into an
# unbounded server-side computation. Trial count is scaled down automatically
# for long sessions instead of failing outright.
MAX_TOTAL_DRAWS = 2_000_000


def _bounded_trials(n_opens: int, n_trials: int) -> int:
    if n_opens <= 0:
        return n_trials
    capped = max(200, MAX_TOTAL_DRAWS // n_opens)
    return min(n_trials, capped)


@dataclass
class SimulationResult:
    n_opens: int
    n_trials: int
    total_cost: float
    mean_net: float
    median_net: float
    std_dev_net: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    prob_of_overall_loss: float
    worst_case_net: float
    best_case_net: float

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def _percentile(sorted_vals: List[float], pct: float) -> float:
    """Linear-interpolated percentile, no numpy dependency required."""
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def simulate_opens(
    case: Dict[str, Any],
    n_opens: int,
    n_trials: int = 5000,
    seed: int | None = None,
) -> SimulationResult:
    """
    Simulate `n_trials` independent sessions, each consisting of `n_opens`
    opens of `case`, and summarize the distribution of net profit/loss.
    """
    if n_opens <= 0:
        raise ValueError("n_opens must be positive")
    if n_trials <= 0:
        raise ValueError("n_trials must be positive")

    n_trials = _bounded_trials(n_opens, n_trials)
    rng = random.Random(seed)
    items = case["items"]
    weights = [i["probability"] for i in items]
    values = [i["market_value"] for i in items]
    price = float(case["price"])
    total_cost = price * n_opens

    net_results: List[float] = []
    for _ in range(n_trials):
        picks = rng.choices(values, weights=weights, k=n_opens)
        gross = sum(picks)
        net_results.append(gross - total_cost)

    net_results.sort()
    n = len(net_results)
    mean_net = sum(net_results) / n
    variance = sum((x - mean_net) ** 2 for x in net_results) / n
    std_dev = variance ** 0.5
    losses = sum(1 for x in net_results if x < 0)

    return SimulationResult(
        n_opens=n_opens,
        n_trials=n_trials,
        total_cost=total_cost,
        mean_net=mean_net,
        median_net=_percentile(net_results, 0.5),
        std_dev_net=std_dev,
        percentile_5=_percentile(net_results, 0.05),
        percentile_25=_percentile(net_results, 0.25),
        percentile_75=_percentile(net_results, 0.75),
        percentile_95=_percentile(net_results, 0.95),
        prob_of_overall_loss=losses / n,
        worst_case_net=net_results[0],
        best_case_net=net_results[-1],
    )
