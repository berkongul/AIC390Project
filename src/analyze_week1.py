"""UC1 Week 1 - analysis of the baseline run (W1.5, W1.6).

Reads results/baseline_results.csv and writes results/week1_analysis.json with:
  - tokens, cost and latency per temperature and in total (W1.6, scoreboard)
  - two heuristic failure checks per temperature (W1.5):
      invented_contact: the answer contains an e-mail address or phone number.
          The system prompt says the store is fictional, so any contact detail is invented.
      invented_policy_number: an answer to a policy/product question states a specific
          number of days, although the model has no store policy.
These are keyword heuristics, not a correctness score. Every flagged answer was also
read by hand (see docs/baseline_analysis.md).

Run:  python src/analyze_week1.py
"""
import csv
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "baseline_results.csv"
OUTPUT = ROOT / "results" / "week1_analysis.json"

# Groq price for openai/gpt-oss-20b, USD per 1M tokens.
# Check https://groq.com/pricing on the day you submit and update if it changed.
PRICE_IN = 0.075
PRICE_OUT = 0.30

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.\w+")
PHONE = re.compile(r"1[-‑]800|\d{3}[-‑]\d{3,4}")
DAYS = re.compile(r"\b\d+\s*(?:[–-]\s*\d+\s*)?(?:business\s+)?days?\b", re.I)
POLICY_CATEGORIES = {"returns", "product", "multi_step"}


def cost(rows):
    tin = sum(int(r["input_tokens"]) for r in rows)
    tout = sum(int(r["output_tokens"]) for r in rows)
    return tin, tout, (tin * PRICE_IN + tout * PRICE_OUT) / 1e6


def describe(rows):
    tin, tout, usd = cost(rows)
    contact = sorted(r["test_id"] for r in rows if EMAIL.search(r["answer"]) or PHONE.search(r["answer"]))
    policy = sorted(r["test_id"] for r in rows
                    if r["category"] in POLICY_CATEGORIES and DAYS.search(r["answer"]))
    return {
        "requests": len(rows),
        "successful": sum(r["status"] == "ok" for r in rows),
        "input_tokens": tin,
        "output_tokens": tout,
        "mean_output_tokens": round(tout / len(rows), 1),
        "cost_usd": round(usd, 6),
        "latency_p50_s": round(statistics.median(float(r["latency_seconds"]) for r in rows), 3),
        "invented_contact": {"count": len(contact), "cases": contact},
        "invented_policy_number": {"count": len(policy), "cases": policy},
    }


def main():
    rows = list(csv.DictReader(SOURCE.open(encoding="utf-8")))
    ok = [r for r in rows if r["status"] == "ok"]
    temps = sorted({r["temperature"] for r in ok}, key=float)
    total = describe(ok)
    total["cost_per_request_usd"] = round(total["cost_usd"] / len(ok), 8)
    total["cost_per_1000_requests_usd"] = round(1000 * total["cost_usd"] / len(ok), 4)
    result = {
        "model": ok[0]["model"],
        "price_usd_per_million": {"input": PRICE_IN, "output": PRICE_OUT},
        "total": total,
        "by_temperature": {t: describe([r for r in ok if r["temperature"] == t]) for t in temps},
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
