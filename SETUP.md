# Setup Instructions & File-by-File Explanation

## Requirements

- Python 3.10 or newer
- pip
- A modern web browser (Chart.js runs client-side; loaded from CDN, so an
  internet connection is needed for charts to render — everything else
  works fully offline)

## Install & run

### One-click launchers

- **macOS**: double-click `run.command`
- **Windows**: double-click `run.bat`
- **Linux**: double-click `run.sh` (if your file manager is set to run
  `.sh` files) or right-click → "Run in Terminal"; otherwise `./run.sh`
  from a terminal

These scripts create `.venv/` and install `requirements.txt` automatically
the first time they're run (subsequent runs skip straight to starting the
server, since `pip install` is a fast no-op when nothing changed), then
launch `app.py` and open your default browser to the dashboard. They set
`FLASK_DEBUG=0` by default. Override the port with an environment variable
before launching, e.g. `PORT=8080 ./run.sh`.

### Manual (any platform)

```bash
# 1. clone / cd into the project
cd Skin.club

# 2. create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 3. install dependencies (just Flask)
pip install -r requirements.txt

# 4. run the app
python app.py
```

By default the app listens on `http://127.0.0.1:5000/`. Override with
environment variables:

```bash
PORT=8080 FLASK_DEBUG=0 python app.py
```

`FLASK_DEBUG=0` disables Flask's debug/auto-reload mode — use this for
anything other than local development, since debug mode exposes a Python
console on errors.

The app binds to `127.0.0.1` (localhost only) by default, so it is not
reachable from other machines unless you change `app.run(...)` in
`app.py` — this is intentional for a personal/local decision-support tool.

## Running the tests

```bash
python -m unittest discover tests -v
```

10 unit tests cover the EV/RTP/variance math, the negative-EV warning
logic, the Monte Carlo simulator's statistical sanity (percentile
ordering, convergence near the theoretical mean), and the bankroll
calculator's edge cases (budget too small, max loss exceeding budget,
negative-EV cases still surfacing a warning regardless of bankroll size).

## File-by-file explanation

### Root

- **`app.py`** — The Flask application. Defines page routes (`/`,
  `/case/<id>`, `/bankroll`, `/history`, `/about`) that render the
  dashboard, and JSON API routes under `/api/*` that the dashboard's
  JavaScript calls (and that you can call directly, e.g. with `curl`, for
  scripting your own analysis). Loads case data from `data/` into memory
  at startup.
- **`config.py`** — Central constants: file paths, the app's display
  name, and the standing disclaimer / data-sourcing text shown on every
  page (`about.html` and the banner in `base.html`).
- **`requirements.txt`** — Just `Flask`. No database, ORM, or scraping
  library is used anywhere.
- **`.gitignore`** — Excludes Python bytecode caches, virtual
  environments, and your locally-generated data (`custom_cases.json`,
  `history_log.csv`) from version control, since that data is yours and
  may include your personal opening history.

### `engine/` — the analysis core (pure computation, no network I/O)

- **`probability.py`** — Given a "case" (price + list of possible items
  with probability and market value), computes: expected value per open,
  net EV, net EV %, return-to-player %, variance, standard deviation,
  coefficient of variation (a scale-free risk measure used to bucket a
  case as low/medium/high/extreme risk), probability of profit/loss on a
  single open, and a full per-item EV-contribution breakdown. Also
  validates that a case's probabilities are well-formed (sum to ~1,
  non-negative) before any of this is trusted, and generates warning
  strings (e.g. "negative expected value") consumed by the templates.
- **`risk.py`** — Monte Carlo simulator: given a case and a number of
  opens, runs many simulated sessions (random draws from your declared
  probabilities) and reports the distribution of net profit/loss —
  mean, median, standard deviation, 5th/25th/75th/95th percentiles,
  worst/best simulated outcome, and probability of an overall loss. This
  is what powers the "Simulate repeated opens" section on each case page.
  Includes a hard cap (`MAX_TOTAL_DRAWS`) so a request for a huge number
  of opens/trials can't turn into an unbounded computation.
- **`bankroll.py`** — The bankroll/risk-management calculator. Takes a
  case, a budget, a maximum acceptable loss, and a risk-tolerance
  percentage (how much chance of exceeding your loss limit you're willing
  to accept), and searches over candidate session lengths (using the
  Monte Carlo engine) to recommend the largest session length whose
  simulated probability of exceeding your loss limit stays at or below
  your risk tolerance. Always surfaces a warning if the case has negative
  EV, since no bankroll strategy changes a negative long-run average.
- **`history.py`** — Reads/writes `data/history_log.csv`, a plain CSV of
  opens you log yourself (date, case, price paid, item received, item
  value). Computes actual spend/return/ROI and compares it to the
  theoretical EV over the same number of opens, so you can see how far
  short-run variance can push actual results away from the long-run
  average.

### `data/`

- **`sample_cases.json`** — Bundled **demo** data so the dashboard has
  something to show out of the box. Clearly labeled as illustrative, not
  real data from any live platform. Replace it, or import additional
  cases via the dashboard's import box (writes to `custom_cases.json`),
  using odds/prices a platform has itself published publicly, or your own
  account history.
- **`custom_cases.json`** — Created automatically the first time you
  import case data through the dashboard. Gitignored by default.
- **`history_log.csv`** — Created automatically the first time you log an
  opening on the `/history` page. Gitignored by default (it's your data).

### `templates/` (Jinja2, server-rendered)

- **`base.html`** — Shared page shell: nav bar, the persistent disclaimer
  banner (shown on every page, not just `/about`), and footer.
- **`index.html`** — Dashboard home: a sortable-by-eye table of every
  loaded case's price/RTP/net EV/risk/probability-of-profit, inline
  warnings, and the JSON import box.
- **`case_detail.html`** — Full breakdown for one case: stat cards (EV,
  net EV, RTP, std dev, risk level, profit probability, value range), the
  complete odds table with every item's probability/value/EV contribution
  shown (so every calculation is checkable by hand), a bar chart of
  EV contribution per item, and the interactive Monte Carlo simulator
  (choose opens/trials, see percentile outcome bands).
- **`bankroll.html`** — The bankroll calculator form (case, budget, max
  acceptable loss, risk tolerance slider) and the resulting recommendation
  card, with explicit language that the output is a probability estimate,
  not a guarantee.
- **`history.html`** — Form to log an opening you've already made, plus a
  running summary (total spent/received/net/ROI) and a table of all
  logged entries.
- **`about.html`** — The full written disclaimer, the expected case-data
  JSON schema, and data-sourcing guidance.
- **`404.html`** — Minimal not-found page.

### `static/css/style.css`

Dashboard styling (dark theme, stat cards, tables, warning/success/error
banners, risk badges). No JS framework — plain CSS.

### `tests/test_engine.py`

Unit tests (standard library `unittest`, no extra test dependency) for
`engine/probability.py`, `engine/risk.py`, and `engine/bankroll.py`.

## Importing your own case data

POST JSON to `/api/cases/import`, or paste it into the import box on the
dashboard home page. Shape:

```json
{
  "cases": [
    {
      "case_id": "unique-id",
      "name": "Display name",
      "price": 2.50,
      "currency": "USD",
      "source": "where you got these odds",
      "last_updated": "2026-08-01",
      "items": [
        { "name": "Item name", "rarity": "Rarity label", "probability": 0.05, "market_value": 3.20 }
      ]
    }
  ]
}
```

Item `probability` values within a case must sum to ~1.0 (small rounding
tolerance is allowed); the import is rejected with a clear error otherwise.

## Deploying beyond your own machine

This tool was designed as a personal, local decision-support utility. If
you want to host it for others, you are responsible for adding your own
authentication, rate limiting, and HTTPS termination (e.g. behind nginx),
and for reviewing that your hosting complies with any applicable laws
around gambling-adjacent tools in your jurisdiction. None of that is
included here by design, to keep the tool's scope to "personal-use
calculator."
