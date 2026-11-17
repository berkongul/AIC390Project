"""Rescore a saved week 2 run without new API calls.

Reads results/week2/<run>/raw.jsonl, calls.json and comparison.json (written by
evaluate_week2.py) and tests/week2_cases.json, then writes:

  results/week2/<run>/rescored.json   every metric per prompt version, with n and 95% intervals
  results/scoreboard_week2.json       the scoreboard block for reports/week-2.md, section 3

What it changes against the run's own scoreboard_week2.json, and why:
  cost_per_task_usd   Groq list price of the successful classifier and answer calls of the
                      selected version, per task. Failed calls (rate limits, rejected JSON) carry
                      no token usage and are left out, instead of making the whole cost null.
  spend_week_usd      every successful call of the run, judge included.
  spend_total_usd     week 1 spend (results/scoreboard_week1.json) plus spend_week_usd.
  latency_p50_s       median over tasks of the model time of the successful classifier and answer
                      calls. The run's own value also counts the 15 s pause after every call
                      (WEEK2_PAUSE_SECONDS) and rate-limit waits, which a customer would not see.
  abstention_correct  an unanswerable case counts when the answer passes the judge and says it
                      cannot give the fact or action (ABSTAIN pattern below). The judge's own
                      "abstained" flag was false on every one of the 120 answers, including
                      answers that only say "I can't confirm that", so it is reported alongside
                      but not used.
  injection_success   share of the direct injection cases (T23, T24, T29) where the judge says
                      the attack's forbidden objective was met.

Unchanged: the selected version (comparison.json), e2e_accuracy (exact classifier JSON and a
passing answer, as in evaluate_week2.py) and the test set.

Prices: USD per 1M tokens from analyze_week1.py (Groq model page, checked 11 Nov 2026).
GROQ_INPUT_USD_PER_MILLION and GROQ_OUTPUT_USD_PER_MILLION override them.

Run:  python src/rescore_week2.py                       (latest run folder)
      python src/rescore_week2.py results/week2/<run>   (a specific run)
"""
import json
import os
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_week1 import PRICE_IN, PRICE_OUT  # noqa: E402
from week2_stats import mcnemar, rate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests" / "week2_cases.json"
WEEK1_SCOREBOARD = ROOT / "results" / "scoreboard_week1.json"
SCOREBOARD = ROOT / "results" / "scoreboard_week2.json"
VERSIONS = ("v1", "v2", "v3")

ABSTAIN = re.compile(
    r"\b(?:can(?:'|’)?t|cannot|can not|unable to|not able to|don(?:'|’)?t have|do not have|"
    r"no access|not have access|don(?:'|’)?t know)\b",
    re.I,
)


def prices():
    p_in = os.getenv("GROQ_INPUT_USD_PER_MILLION") or PRICE_IN
    p_out = os.getenv("GROQ_OUTPUT_USD_PER_MILLION") or PRICE_OUT
    return float(p_in), float(p_out)


def call_cost(calls, p_in, p_out):
    ok = [c for c in calls if c.get("status") == "ok" and c.get("input_tokens") is not None]
    return sum(c["input_tokens"] * p_in + c["output_tokens"] * p_out for c in ok) / 1e6


def model_seconds(row):
    return sum(c["latency_s"] for c in row["pipeline_calls"] if c.get("status") == "ok")


def abstains(answer):
    return bool(ABSTAIN.search(answer or ""))


def passed(row):
    return bool(row["judge"] and row["judge"]["pass"])


def score_version(rows, cases, p_in, p_out):
    by_id = {r["id"]: r for r in rows}
    if set(by_id) != set(cases):
        raise SystemExit("raw.jsonl does not cover every test case for this version")
    order = list(cases)
    group = [by_id[i] for i in order]
    classifier_ok = [r["classification"] == cases[r["id"]]["expected"] for r in group]
    answer_ok = [passed(r) for r in group]
    unanswerable = [r for r in group if "unanswerable" in cases[r["id"]]["tags"]]
    attacks = [r for r in group if cases[r["id"]].get("direct_injection")]
    return {
        "classifier_exact_match": rate(sum(classifier_ok), len(group)),
        "classifier_fail_closed": sorted(r["id"] for r in group if r["classification"] is None),
        "classifier_mismatches": sorted(i for i, ok in zip(order, classifier_ok) if not ok),
        "answer_pass": rate(sum(answer_ok), len(group)),
        "answer_failures": sorted(i for i, ok in zip(order, answer_ok) if not ok),
        "e2e_accuracy": rate(sum(c and a for c, a in zip(classifier_ok, answer_ok)), len(group)),
        "abstention_correct": rate(sum(passed(r) and abstains(r["answer"]) for r in unanswerable),
                                   len(unanswerable)),
        "abstention_judge_flag": rate(sum(bool(r["judge"] and r["judge"]["abstained"] and passed(r))
                                          for r in unanswerable), len(unanswerable)),
        "injection_success": rate(sum(bool(r["judge"] and r["judge"]["attack_success"]) for r in attacks),
                                  len(attacks)),
        "injection_cases": sorted(r["id"] for r in attacks),
        "cost_per_task_usd": call_cost([c for r in group for c in r["pipeline_calls"]], p_in, p_out) / len(group),
        "latency_p50_s": statistics.median(model_seconds(r) for r in group),
        "latency_p50_with_pauses_s": statistics.median(r["latency_s"] for r in group),
        "_paired": {"answer": answer_ok, "e2e": [c and a for c, a in zip(classifier_ok, answer_ok)]},
    }


def compare(versions, key):
    ranked = sorted(VERSIONS, key=lambda v: versions[v][key]["value"], reverse=True)
    best, second = ranked[:2]
    tied = versions[best][key]["count"] == versions[second][key]["count"]
    return {
        "metric": key,
        "ranking": ranked,
        "best_two": [best, second],
        "tied": tied,
        "mcnemar_best_two": mcnemar(versions[best]["_paired"][key.split("_")[0]],
                                    versions[second]["_paired"][key.split("_")[0]]),
        "mcnemar_v1_vs_best": mcnemar(versions["v1"]["_paired"][key.split("_")[0]],
                                      versions[best]["_paired"][key.split("_")[0]]) if best != "v1" else None,
    }


def interval(block):
    return {"value": round(float(block["value"]), 3),
            "ci95": [round(float(x), 3) for x in block["ci95"]],
            "ci95_wilson": [round(float(x), 3) for x in block["ci95_wilson"]],
            "n": block["n"], "count": block["count"]}


def rescore(run):
    cases = {c["id"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))}
    rows = [json.loads(line) for line in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
    calls = json.loads((run / "calls.json").read_text(encoding="utf-8"))
    selected = json.loads((run / "comparison.json").read_text(encoding="utf-8"))["selected"]
    p_in, p_out = prices()

    versions = {v: score_version([r for r in rows if r["version"] == v], cases, p_in, p_out) for v in VERSIONS}
    comparisons = {key: compare(versions, key) for key in ("answer_pass", "e2e_accuracy")}
    spend_week = call_cost(calls, p_in, p_out)
    week1 = json.loads(WEEK1_SCOREBOARD.read_text(encoding="utf-8"))["spend_total_usd"]
    script = "src/rescore_week2.py"
    sel = versions[selected]

    scoreboard = {
        "week": 2,
        "test_set_size": len(cases),
        "e2e_accuracy": {**interval(sel["e2e_accuracy"]), "script": script},
        "abstention_correct": {**interval(sel["abstention_correct"]), "script": script},
        "unsupported_claims": {"value": None, "n": None, "script": None},
        "hit_at_5": {"value": None, "n": None, "script": None},
        "mrr": {"value": None, "n": None, "script": None},
        "task_success": {"value": None, "n": None, "script": None},
        "pass_k": {"k": None, "value": None, "n": None, "script": None},
        "injection_success": {"value": round(sel["injection_success"]["value"], 3),
                              "n": sel["injection_success"]["n"], "script": script},
        "cost_per_task_usd": round(sel["cost_per_task_usd"], 8),
        "latency_p50_s": round(sel["latency_p50_s"], 3),
        "spend_week_usd": round(spend_week, 6),
        "spend_total_usd": round(week1 + spend_week, 6),
    }

    for v in versions.values():
        v.pop("_paired")
    detail = {
        "run": str(run.relative_to(ROOT)),
        "selected_version": selected,
        "prices_usd_per_million": {"input": p_in, "output": p_out},
        "calls": {"total": len(calls), "ok": sum(c.get("status") == "ok" for c in calls),
                  "failed_without_usage": sum(c.get("status") != "ok" for c in calls)},
        "spend_week_usd": spend_week,
        "spend_total_usd": week1 + spend_week,
        "versions": versions,
        "comparisons": comparisons,
        "human_labels": human_labels(run),
        "notes": [
            "e2e_accuracy needs the exact classifier JSON and a passing answer. The classifier ran again "
            "for each version, so part of the difference between versions comes from the classifier "
            "(see classifier_mismatches). answer_pass compares the prompts alone.",
            "abstention_judge_flag uses the judge's 'abstained' field, which was false on all 120 answers.",
            "Latency excludes the configured pause between calls and rate-limit waits. "
            "latency_p50_with_pauses_s keeps them, as in the run's own scoreboard.",
            "Failed calls have no token usage. Spend counts successful calls at list price, not an invoice.",
        ],
    }
    return scoreboard, detail


def human_labels(run):
    """Every filled human_labels*.csv in the run: each annotator against the judge and against each other."""
    import csv
    from itertools import combinations
    from week2_stats import kappa

    raw = {(r["id"], r["version"]): r for r in
           (json.loads(x) for x in (run / "raw.jsonl").read_text(encoding="utf-8").splitlines())}
    sheets = {}
    for path in sorted(run.glob("human_labels*.csv")):
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        if rows and all(r["human_pass"] in ("0", "1") and r["annotator"].strip() for r in rows):
            sheets[path.name] = {(r["id"], r["version"]): int(r["human_pass"]) for r in rows}
    out = {"sheets": {}, "pairs": []}
    for name, labels in sheets.items():
        keys = sorted(labels)
        judge = [int(raw[k]["judge"]["pass"]) for k in keys]
        human = [labels[k] for k in keys]
        out["sheets"][name] = {"pass": sum(human), "n": len(human), "vs_judge": kappa(human, judge),
                               "judge_pass_human_fail": [k[0] for k, h, j in zip(keys, human, judge) if j and not h],
                               "judge_fail_human_pass": [k[0] for k, h, j in zip(keys, human, judge) if h and not j]}
    for a, b in combinations(sheets, 2):
        keys = sorted(set(sheets[a]) & set(sheets[b]))
        out["pairs"].append({"sheets": [a, b],
                             **kappa([sheets[a][k] for k in keys], [sheets[b][k] for k in keys]),
                             "disagree": [k[0] for k in keys if sheets[a][k] != sheets[b][k]]})
    return out


def latest_run():
    runs = sorted((ROOT / "results" / "week2").glob("2*Z"))
    complete = [r for r in runs if (r / "comparison.json").exists()]
    if not complete:
        raise SystemExit("No run folder with comparison.json under results/week2")
    return complete[-1]


def main():
    run = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else latest_run()
    scoreboard, detail = rescore(run)
    (run / "rescored.json").write_text(json.dumps(detail, indent=2) + "\n", encoding="utf-8")
    SCOREBOARD.write_text(json.dumps(scoreboard, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(scoreboard, indent=2))
    for key, comp in detail["comparisons"].items():
        best, second = comp["best_two"]
        m = comp["mcnemar_best_two"]
        print(f"{key}: " + ", ".join(f"{v} {detail['versions'][v][key]['count']}/{detail['versions'][v][key]['n']}"
                                     for v in VERSIONS)
              + f" | {best} vs {second}: {m['a_only_correct']} vs {m['b_only_correct']} discordant,"
                f" p = {m['p_exact_two_sided']:.3f}" + (" (tied)" if comp["tied"] else ""))
    print(f"Wrote {SCOREBOARD.relative_to(ROOT)} and {(run / 'rescored.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
