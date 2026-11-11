"""UC1 Week 1 - scoreboard block and failure rates with 95% intervals.

Uses the same data and checks as analyze_week1.py and writes:
  results/scoreboard_week1.json  the scoreboard block for section 3 of reports/week-1.md
  results/week1_rates.json       the two heuristic failure rates per temperature, each with
                                 its count, n and a 95% interval

Intervals: "ci95" is the normal approximation from handbook section 5,
p +/- 1.96 * sqrt(p * (1 - p) / n), clipped to [0, 1]. With n = 12 or 25 and counts of
0 to 3 it is unreliable, so "ci95_wilson" (Wilson score interval) is reported as well.

Spend is the Groq list price of the tokens used (prices in analyze_week1.py), not an invoice.

Run:  python src/scoreboard.py
"""
import csv
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_week1 as aw  # noqa: E402

WEEK = 1
TEST_SET_SIZE = 25
SCOREBOARD = aw.ROOT / "results" / "scoreboard_week1.json"
RATES = aw.ROOT / "results" / "week1_rates.json"
Z = 1.96


def wald(k, n):
    p = k / n
    half = Z * math.sqrt(p * (1 - p) / n)
    return [round(max(0.0, p - half), 3), round(min(1.0, p + half), 3)]


def wilson(k, n):
    p = k / n
    centre = (p + Z**2 / (2 * n)) / (1 + Z**2 / n)
    half = Z * math.sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / (1 + Z**2 / n)
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def rate(flagged, eligible):
    k, n = len(flagged), len(eligible)
    return {
        "count": k,
        "n": n,
        "value": round(k / n, 3),
        "ci95": wald(k, n),
        "ci95_wilson": wilson(k, n),
        "cases": sorted(r["test_id"] for r in flagged),
    }


def failure_rates(rows):
    contact = [r for r in rows if aw.EMAIL.search(r["answer"]) or aw.PHONE.search(r["answer"])]
    eligible = [r for r in rows if r["category"] in aw.POLICY_CATEGORIES]
    policy = [r for r in eligible if aw.DAYS.search(r["answer"])]
    return {
        "invented_contact": rate(contact, rows),
        "invented_policy_number": rate(policy, eligible),
    }


def empty(with_ci=True, with_k=False):
    block = {"value": None}
    if with_k:
        block = {"k": None, "value": None}
    if with_ci:
        block["ci95"] = None
    block.update({"n": None, "script": None})
    return block


def main():
    rows = list(csv.DictReader(aw.SOURCE.open(encoding="utf-8")))
    ok = [r for r in rows if r["status"] == "ok"]
    _, _, usd = aw.cost(ok)
    latency = statistics.median(float(r["latency_seconds"]) for r in ok)

    scoreboard = {
        "week": WEEK,
        "test_set_size": TEST_SET_SIZE,
        "e2e_accuracy": empty(),
        "abstention_correct": empty(),
        "unsupported_claims": empty(with_ci=False),
        "hit_at_5": empty(with_ci=False),
        "mrr": empty(with_ci=False),
        "task_success": empty(with_ci=False),
        "pass_k": empty(with_ci=False, with_k=True),
        "injection_success": empty(with_ci=False),
        "cost_per_task_usd": round(usd / len(ok), 8),
        "latency_p50_s": round(latency, 3),
        "spend_week_usd": round(usd, 6),
        "spend_total_usd": round(usd, 6),
    }

    temps = sorted({r["temperature"] for r in ok}, key=float)
    rates = {
        "source": "results/baseline_results.csv",
        "checks": "keyword heuristics from src/analyze_week1.py, flagged answers read by hand",
        "invented_policy_number_applies_to": sorted(aw.POLICY_CATEGORIES),
        "total": failure_rates(ok),
        "by_temperature": {t: failure_rates([r for r in ok if r["temperature"] == t]) for t in temps},
    }

    SCOREBOARD.write_text(json.dumps(scoreboard, indent=2) + "\n", encoding="utf-8")
    RATES.write_text(json.dumps(rates, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scoreboard, indent=2))
    print(f"Wrote {SCOREBOARD.relative_to(aw.ROOT)} and {RATES.relative_to(aw.ROOT)}")


if __name__ == "__main__":
    main()
