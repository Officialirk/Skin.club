# Skin.Club Stats & Decision-Support Tool

A local, offline **statistics and decision-support tool** for case-opening /
loot-box style products (e.g. Skin.Club-style CS skin cases). It computes
expected value, return-to-player, variance/risk, and Monte-Carlo simulated
outcome ranges from odds data you supply, and includes a bankroll/risk
calculator so you can plan a budget before spending anything.

**It does not connect to, scrape, or automate Skin.Club or any other
service. It does not place bets, open cases, or perform any account
action. It cannot and does not guarantee any outcome.** See
[DISCLAIMER.md](DISCLAIMER.md) for the full statement, also shown in-app on
every page.

---

## What it does

| Feature | Where |
|---|---|
| Expected value (EV), net EV %, return-to-player (RTP) % per case | Dashboard (`/`), Case detail (`/case/<id>`) |
| Variance, standard deviation, coefficient-of-variation risk label | Case detail |
| Per-item probability, market value, and EV contribution (full transparency) | Case detail |
| Monte Carlo simulation of N repeated opens → percentile outcome ranges | Case detail |
| Bankroll calculator: budget + max acceptable loss → recommended session length & risk estimate | `/bankroll` |
| Personal opening history log vs. theoretical EV | `/history` |
| Import your own case/odds data (JSON) | Dashboard import box, or `data/custom_cases.json` |

Every number shown is explicitly labeled as a **theoretical, long-run
average or a simulated estimate** — never a promise. Negative-EV cases are
flagged with a warning wherever they appear.

## Tech stack

Python 3.10+ and [Flask](https://flask.palletsprojects.com/) for the web
server/API, server-rendered Jinja2 templates for the dashboard, vanilla
JS + [Chart.js](https://www.chartjs.org/) (via CDN) for interactivity and
charts. No database — case data lives in JSON files, history lives in a
local CSV. No build step required.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000/. See [SETUP.md](SETUP.md) for a
file-by-file explanation of the project and more detailed setup notes.

## Project structure

```
Skin.club/
├── app.py                 # Flask app: routes + JSON API
├── config.py               # Paths, app name, disclaimer text
├── requirements.txt
├── engine/                 # Pure-Python analysis engine (no I/O to any live service)
│   ├── probability.py      #   EV, RTP, variance, per-item breakdown
│   ├── risk.py              #   Monte Carlo simulation of repeated opens
│   ├── bankroll.py         #   Budget / max-loss → recommended session plan
│   └── history.py          #   Local CSV log of your own opens vs theoretical EV
├── data/
│   ├── sample_cases.json   # Illustrative demo case data (NOT real Skin.Club data)
│   ├── custom_cases.json   # Created when you import your own data (gitignored)
│   └── history_log.csv     # Created when you log opens (gitignored, your data only)
├── templates/               # Jinja2 HTML templates (dashboard pages)
├── static/css/style.css    # Dashboard styling
└── tests/test_engine.py    # Unit tests for the analysis engine
```

See [SETUP.md](SETUP.md) for what each file does in detail, and
[DISCLAIMER.md](DISCLAIMER.md) for the full legal/ethical disclaimer and
data-sourcing rules.

## Running tests

```bash
python -m unittest discover tests -v
```

## Compliance notes

- No web scraping, API automation, or bot interaction with Skin.Club (or
  any other platform) anywhere in this codebase.
- No functionality automates deposits, withdrawals, purchases, or betting.
- Case/item data is provided by you (the user), sourced from information a
  platform has itself published publicly, or from your own account history
  you're legally entitled to access — never fetched automatically by this
  tool.
- Nothing in this tool claims or implies a guaranteed win or a way to
  manipulate outcomes.

Use of case-opening / loot-box products may be regulated as gambling in
your jurisdiction. Confirm you're legally permitted to use such a service,
and that your use complies with that service's own terms, before you do so.
