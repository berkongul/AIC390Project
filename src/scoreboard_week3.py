"""Week 3 scoreboard block, built only from committed results (no API calls).

  hit_at_5, mrr        results/week3/retrieval_eval.json, mode "rerank" (the system as built),
                       main question set (typo copies excluded)
  unsupported_claims   results/week3/faithfulness/summary.json (LLM judge, claim by claim)
  cost_per_task_usd    answer call per question in the faithfulness run (retrieval runs locally
                       and costs nothing)
  latency_p50_s        model time of that answer call
  spend_total_usd      week 1 total plus every successful call in the committed run folders
                       (calls.json files) priced at the Groq list price. A run that a later run
                       resumed from is skipped, because the later calls.json already holds its calls
  spend_week_usd       spend_total_usd minus the week 2 scoreboard's spend_total_usd

e2e_accuracy, abstention_correct and injection_success are null: the week 2 40-case set was
not re-run on the RAG pipeline (its rubrics assume no store documents), and the formal
injection metric starts in week 5.

Run:  python src/scoreboard_week3.py      writes results/scoreboard_week3.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_week1 import PRICE_IN, PRICE_OUT  # noqa: E402
from corpus import ROOT  # noqa: E402

RESULTS = ROOT / "results"
OUT = RESULTS / "scoreboard_week3.json"
MODE = "rerank"


def spend_of(path):
    calls = json.loads(path.read_text(encoding="utf-8"))
    return sum((c["input_tokens"] or 0) * PRICE_IN + (c["output_tokens"] or 0) * PRICE_OUT
               for c in calls if c.get("status") == "ok") / 1e6


def main():
    retrieval = json.loads((RESULTS / "week3" / "retrieval_eval.json").read_text(encoding="utf-8"))
    main_set = retrieval["modes"][MODE]["summary"]["main"]
    faith = json.loads((RESULTS / "week3" / "faithfulness" / "summary.json").read_text(encoding="utf-8"))
    week1 = json.loads((RESULTS / "scoreboard_week1.json").read_text(encoding="utf-8"))["spend_total_usd"]
    week2 = json.loads((RESULTS / "scoreboard_week2.json").read_text(encoding="utf-8"))["spend_total_usd"]

    # A run resumed with --resume copies the earlier run's calls into its own calls.json,
    # so the earlier run is skipped to avoid counting the same calls twice.
    resumed = set()
    for manifest in RESULTS.rglob("manifest.json"):
        source = json.loads(manifest.read_text(encoding="utf-8")).get("resumed_from")
        if source:
            resumed.add(Path(source.replace("\\", "/")).name)
    sources = sorted(p for p in RESULTS.rglob("calls.json") if p.parent.name not in resumed)
    spend = {str(p.relative_to(ROOT)): round(spend_of(p), 6) for p in sources}
    total = week1 + sum(spend.values())
    unsupported = faith["unsupported_claims"]

    board = {
        "week": 3,
        "test_set_size": main_set["n"],
        "e2e_accuracy": {"value": None, "ci95": None, "n": None, "script": None},
        "abstention_correct": {"value": None, "ci95": None, "n": None, "script": None},
        "unsupported_claims": {"value": round(unsupported["value"], 3), "n": unsupported["n"],
                               "script": "src/evaluate_faithfulness.py"},
        "hit_at_5": {"value": main_set["hit_at_5"], "n": main_set["n"], "script": "src/evaluate_retrieval.py"},
        "mrr": {"value": main_set["mrr"], "n": main_set["n"], "script": "src/evaluate_retrieval.py"},
        "task_success": {"value": None, "n": None, "script": None},
        "pass_k": {"k": None, "value": None, "n": None, "script": None},
        "injection_success": {"value": None, "n": None, "script": None},
        "cost_per_task_usd": faith["answer_cost_per_task_usd"],
        "latency_p50_s": round(faith["answer_latency_p50_s"], 3),
        "spend_week_usd": round(total - week2, 6),
        "spend_total_usd": round(total, 6),
    }
    OUT.write_text(json.dumps(board, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(board, indent=2))
    print("spend sources:", json.dumps(spend, indent=1))


if __name__ == "__main__":
    main()
