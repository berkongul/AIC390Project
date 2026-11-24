"""Abstention on the RAG pipeline (week 3), re-measured on questions the documents cannot answer.

tests/abstention_week3.json has two kinds of case:
  unanswerable    the store documents do not contain the answer (10 new questions, plus week 2's
                  T27 and T28). Correct = the assistant abstains (the fixed reply, or a sentence
                  saying it cannot confirm or do it) and the judge finds no unsupported claim.
  now_answerable  week 2 cases tagged unanswerable that the documents now answer (T06, T10, T11,
                  T21, T22, T26, T40). Correct = an answer with valid citations, not the fixed reply,
                  and no unsupported claim.

Pipeline: hybrid search + reranker (top 5), answer prompt prompts/rag_v1.txt, claims judged with
judge v2 from src/evaluate_faithfulness.py (store-channel rule).

Run:  python src/evaluate_abstention_week3.py     about 60 Groq calls
Writes results/week3/abstention/{raw.jsonl,summary.json,calls.json}
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("WEEK2_PAUSE_SECONDS", "2")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import ROOT  # noqa: E402
from evaluate_faithfulness import claims_of, judge_claim  # noqa: E402
from rag_answer import answer  # noqa: E402
from rescore_week2 import abstains  # noqa: E402
from retrieval import Index  # noqa: E402
from week2_stats import rate  # noqa: E402

CASES = ROOT / "tests" / "abstention_week3.json"
OUT = ROOT / "results" / "week3" / "abstention"
MODE, K, JUDGE = "rerank", 5, "v2"


def main():
    from week2 import Model
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    index, model = Index(), Model()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with (OUT / "raw.jsonl").open("w", encoding="utf-8") as f:
        for case in cases:
            hits = index.search(case["question"], K, MODE)
            result = answer(model, case["question"], hits)
            claims = [] if result["fixed"] else claims_of(result["text"])
            for c in claims:
                c["judge"] = judge_claim(model, c, hits, JUDGE)
            unsupported = [c["text"] for c in claims if c["judge"] and not c["judge"]["supported"]]
            abstained = result["fixed"] or abstains(result["text"])
            if case["kind"] == "unanswerable":
                correct = abstained and not unsupported
            else:
                correct = not result["fixed"] and bool(result["cited"]) and not result["problems"] and not unsupported
            row = {**case, "retrieved": [h.chunk.id for h in hits], "answer": result["text"],
                   "fixed": result["fixed"], "abstained": abstained, "cited": result["cited"],
                   "citation_problems": result["problems"], "claims": claims,
                   "unsupported": unsupported, "correct": correct}
            rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{case['id']} {case['kind']:<15} {'ok ' if correct else 'WRONG'}"
                  f"{' fixed' if result['fixed'] else ''}{' unsupported: ' + str(unsupported) if unsupported else ''}",
                  flush=True)

    unans = [r for r in rows if r["kind"] == "unanswerable"]
    now = [r for r in rows if r["kind"] == "now_answerable"]
    summary = {
        "mode": MODE, "k": K, "judge": JUDGE,
        "abstention_correct": rate(sum(r["correct"] for r in unans), len(unans)),
        "abstention_errors": [r["id"] for r in unans if not r["correct"]],
        "now_answerable_correct": rate(sum(r["correct"] for r in now), len(now)),
        "now_answerable_errors": [r["id"] for r in now if not r["correct"]],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    (OUT / "calls.json").write_text(json.dumps(model.calls, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: (v if not isinstance(v, dict) else f"{v['count']}/{v['n']}") for k, v in summary.items()}, indent=1))


if __name__ == "__main__":
    main()
