"""
config.py
==========
Small collection of constants and the standing legal/ethical disclaimer
text shown throughout the dashboard. Centralized here so the same wording
appears everywhere the tool talks about odds, EV, or money.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SAMPLE_CASES_PATH = os.path.join(DATA_DIR, "sample_cases.json")
CUSTOM_CASES_PATH = os.path.join(DATA_DIR, "custom_cases.json")
HISTORY_PATH = os.path.join(DATA_DIR, "history_log.csv")

APP_NAME = "Skin.Club Stats & Decision-Support Tool"

STANDING_DISCLAIMER = (
    "This tool performs arithmetic and simulation on odds/price data you provide. "
    "It does not connect to, scrape, automate, or place any action on Skin.Club or any "
    "other service. All figures are theoretical, long-run averages derived from the data "
    "you entered — they are NOT a guarantee of any individual outcome, and past or "
    "simulated results do not predict future results. Case opening and similar mechanics "
    "are gambling-like activities that, on almost all commercial platforms, are designed "
    "with a built-in house edge (RTP under 100%). No calculation here can turn a "
    "negative-EV product into a winning strategy. If you choose to spend money on these "
    "products, only spend what you can fully afford to lose, and stop if it stops being fun."
)

DATA_SOURCING_NOTE = (
    "Case/item data is never scraped automatically. Import your own data (JSON/CSV) from "
    "information a platform has itself published publicly (e.g. an odds/rarity table it "
    "discloses), or from your own account history, which you are legally entitled to "
    "access. The bundled sample_cases.json is illustrative demo data only."
)
