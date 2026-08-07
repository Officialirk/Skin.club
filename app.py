"""
app.py
=======
Flask application entry point. Wires together the analysis engine
(engine/probability.py, engine/risk.py, engine/bankroll.py,
engine/history.py) with a small JSON API and a server-rendered dashboard
(templates/ + static/).

Run with:  python app.py
See SETUP.md for full setup instructions.

Scope reminder: every route below either (a) reads/writes local files the
user controls (case data imports, their own history log) or (b) performs
pure computation on that data. Nothing here makes outbound requests to
Skin.Club or any other gambling/case-opening service, and nothing here
submits any action (bet, deposit, withdrawal, purchase) anywhere.
"""

from __future__ import annotations
import json
import os
from datetime import date
from typing import Dict, Any, List

from flask import Flask, jsonify, request, render_template, abort

import config
from engine.probability import analyze_case, analyze_all, InvalidCaseData, validate_case
from engine.risk import simulate_opens
from engine.bankroll import compute_bankroll_plan
from engine.history import append_entry, summarize_history, HistoryEntry, ensure_history_file

app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory case registry, loaded from bundled sample data + any locally
# imported custom cases. This is intentionally simple (no database) — the
# tool is a local analysis utility, not a multi-user service.
# ---------------------------------------------------------------------------

_CASES: Dict[str, Dict[str, Any]] = {}


def _load_cases_file(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("cases", [])


def load_all_cases() -> None:
    _CASES.clear()
    for case in _load_cases_file(config.SAMPLE_CASES_PATH):
        _CASES[case["case_id"]] = case
    for case in _load_cases_file(config.CUSTOM_CASES_PATH):
        _CASES[case["case_id"]] = case


def get_case_or_404(case_id: str) -> Dict[str, Any]:
    case = _CASES.get(case_id)
    if not case:
        abort(404, description=f"Unknown case_id '{case_id}'.")
    return case


load_all_cases()
ensure_history_file(config.HISTORY_PATH)


# ---------------------------------------------------------------------------
# Page routes (server-rendered dashboard)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    analyses = analyze_all(list(_CASES.values()))
    analyses.sort(key=lambda a: a.net_ev_pct, reverse=True)
    return render_template(
        "index.html",
        app_name=config.APP_NAME,
        disclaimer=config.STANDING_DISCLAIMER,
        analyses=analyses,
    )


@app.route("/case/<case_id>")
def case_detail(case_id):
    case = get_case_or_404(case_id)
    analysis = analyze_case(case)
    return render_template(
        "case_detail.html",
        app_name=config.APP_NAME,
        disclaimer=config.STANDING_DISCLAIMER,
        case=case,
        analysis=analysis,
    )


@app.route("/bankroll")
def bankroll_page():
    analyses = analyze_all(list(_CASES.values()))
    return render_template(
        "bankroll.html",
        app_name=config.APP_NAME,
        disclaimer=config.STANDING_DISCLAIMER,
        analyses=analyses,
    )


@app.route("/history")
def history_page():
    summary = summarize_history(config.HISTORY_PATH)
    case_choices = list(_CASES.values())
    return render_template(
        "history.html",
        app_name=config.APP_NAME,
        disclaimer=config.STANDING_DISCLAIMER,
        summary=summary,
        cases=case_choices,
        today=date.today().isoformat(),
    )


@app.route("/about")
def about_page():
    return render_template(
        "about.html",
        app_name=config.APP_NAME,
        disclaimer=config.STANDING_DISCLAIMER,
        sourcing_note=config.DATA_SOURCING_NOTE,
    )


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

@app.route("/api/cases")
def api_list_cases():
    analyses = analyze_all(list(_CASES.values()))
    return jsonify([a.to_dict() for a in analyses])


@app.route("/api/cases/<case_id>")
def api_case_detail(case_id):
    case = get_case_or_404(case_id)
    return jsonify(analyze_case(case).to_dict())


@app.route("/api/cases/import", methods=["POST"])
def api_import_cases():
    """
    Import case/odds data supplied by the user (as JSON in the request body:
    {"cases": [ {case_id, name, price, currency, items:[...]}, ... ]}).

    This endpoint does NOT fetch anything itself — it only validates and
    stores whatever the client sends, which is expected to come from data
    the user copied from a publicly published odds page or exported from
    their own account.
    """
    payload = request.get_json(silent=True)
    if not payload or "cases" not in payload:
        return jsonify({"error": "Body must be JSON with a 'cases' array."}), 400

    validated = []
    errors = []
    for case in payload["cases"]:
        try:
            validate_case(case)
            validated.append(case)
        except InvalidCaseData as e:
            errors.append(str(e))

    if errors and not validated:
        return jsonify({"error": "No valid cases in payload.", "details": errors}), 400

    existing = _load_cases_file(config.CUSTOM_CASES_PATH)
    existing_ids = {c["case_id"] for c in existing}
    for case in validated:
        if case["case_id"] in existing_ids:
            existing = [c for c in existing if c["case_id"] != case["case_id"]]
        existing.append(case)

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.CUSTOM_CASES_PATH, "w") as f:
        json.dump({"cases": existing}, f, indent=2)

    load_all_cases()
    return jsonify({
        "imported": [c["case_id"] for c in validated],
        "errors": errors,
    })


@app.route("/api/cases/<case_id>/simulate", methods=["POST"])
def api_simulate(case_id):
    case = get_case_or_404(case_id)
    body = request.get_json(silent=True) or {}
    n_opens = int(body.get("n_opens", 100))
    n_trials = int(body.get("n_trials", 3000))

    if n_opens < 1 or n_opens > 1_000_000:
        return jsonify({"error": "n_opens must be between 1 and 1,000,000."}), 400
    if n_trials < 100 or n_trials > 20_000:
        return jsonify({"error": "n_trials must be between 100 and 20,000."}), 400

    result = simulate_opens(case, n_opens=n_opens, n_trials=n_trials)
    return jsonify(result.to_dict())


@app.route("/api/bankroll", methods=["POST"])
def api_bankroll():
    body = request.get_json(silent=True) or {}
    case_id = body.get("case_id")
    if not case_id:
        return jsonify({"error": "case_id is required."}), 400
    case = get_case_or_404(case_id)

    try:
        budget = float(body["budget"])
        max_acceptable_loss = float(body["max_acceptable_loss"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "budget and max_acceptable_loss are required numbers."}), 400

    risk_tolerance_pct = float(body.get("risk_tolerance_pct", 25.0))

    if budget <= 0 or max_acceptable_loss <= 0:
        return jsonify({"error": "budget and max_acceptable_loss must be positive."}), 400
    if max_acceptable_loss > budget:
        return jsonify({"error": "max_acceptable_loss cannot exceed budget."}), 400

    analysis = analyze_case(case)
    plan = compute_bankroll_plan(
        case, analysis, budget, max_acceptable_loss, risk_tolerance_pct=risk_tolerance_pct
    )
    return jsonify({
        "analysis": analysis.to_dict(),
        "plan": plan.to_dict(),
    })


@app.route("/api/history", methods=["GET"])
def api_get_history():
    case_id = request.args.get("case_id")
    theoretical_ev = None
    if case_id:
        case = get_case_or_404(case_id)
        theoretical_ev = analyze_case(case).net_ev
    summary = summarize_history(config.HISTORY_PATH, case_id=case_id, theoretical_net_ev_per_open=theoretical_ev)
    return jsonify(summary.to_dict())


@app.route("/api/history", methods=["POST"])
def api_add_history():
    body = request.get_json(silent=True) or {}
    required = ["date", "case_id", "item_name", "item_value"]
    if not all(k in body for k in required):
        return jsonify({"error": f"Body must include: {', '.join(required)}"}), 400

    case = get_case_or_404(body["case_id"])
    try:
        item_value = float(body["item_value"])
    except (TypeError, ValueError):
        return jsonify({"error": "item_value must be a number."}), 400

    entry = HistoryEntry(
        date=str(body["date"]),
        case_id=body["case_id"],
        case_price=float(case["price"]),
        item_name=str(body["item_name"]),
        item_value=item_value,
    )
    append_entry(config.HISTORY_PATH, entry)
    return jsonify({"status": "recorded", "entry": entry.__dict__})


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": str(e.description)}), 404
    return render_template("404.html", app_name=config.APP_NAME), 404


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", debug=debug, port=port)
