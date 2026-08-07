"""
engine/history.py
===================
Storage and analysis of the user's OWN historical opening log.

This log is entered manually by the user (or imported from a CSV they
export themselves from their own account activity — data they are legally
entitled to access). This module never fetches, scrapes, or infers data
from Skin.Club or any other live service; it only reads/writes a local
CSV file and compares it against the theoretical EV computed by
engine.probability.

Log row schema (CSV columns):
    date, case_id, case_price, item_name, item_value
"""

from __future__ import annotations
import csv
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

HISTORY_FIELDS = ["date", "case_id", "case_price", "item_name", "item_value"]


@dataclass
class HistoryEntry:
    date: str
    case_id: str
    case_price: float
    item_name: str
    item_value: float


@dataclass
class HistorySummary:
    n_opens: int
    total_spent: float
    total_received: float
    net_actual: float
    actual_roi_pct: float
    theoretical_ev_over_n_opens: Optional[float]
    variance_vs_theory: Optional[float]
    entries: List[HistoryEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = self.__dict__.copy()
        d["entries"] = [e.__dict__ for e in self.entries]
        return d


def ensure_history_file(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
            writer.writeheader()


def append_entry(path: str, entry: HistoryEntry) -> None:
    ensure_history_file(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        writer.writerow(entry.__dict__)


def load_history(path: str, case_id: Optional[str] = None) -> List[HistoryEntry]:
    ensure_history_file(path)
    entries = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if case_id and row["case_id"] != case_id:
                continue
            entries.append(HistoryEntry(
                date=row["date"],
                case_id=row["case_id"],
                case_price=float(row["case_price"]),
                item_name=row["item_name"],
                item_value=float(row["item_value"]),
            ))
    return entries


def summarize_history(
    path: str,
    case_id: Optional[str] = None,
    theoretical_net_ev_per_open: Optional[float] = None,
) -> HistorySummary:
    entries = load_history(path, case_id=case_id)
    n = len(entries)
    total_spent = sum(e.case_price for e in entries)
    total_received = sum(e.item_value for e in entries)
    net_actual = total_received - total_spent
    roi_pct = (net_actual / total_spent * 100) if total_spent else 0.0

    theoretical_total = (
        theoretical_net_ev_per_open * n if theoretical_net_ev_per_open is not None else None
    )
    variance_vs_theory = (
        net_actual - theoretical_total if theoretical_total is not None else None
    )

    return HistorySummary(
        n_opens=n,
        total_spent=total_spent,
        total_received=total_received,
        net_actual=net_actual,
        actual_roi_pct=roi_pct,
        theoretical_ev_over_n_opens=theoretical_total,
        variance_vs_theory=variance_vs_theory,
        entries=entries,
    )
