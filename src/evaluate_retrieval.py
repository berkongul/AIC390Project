"""Week 3 retrieval evaluation (W3.5) and the search ablations (W3.7).

Owner: Orhun Cerit (data and retrieval lead).

For every question in tests/retrieval_questions.json we know the gold chunk(s): the store
passage(s) that contain the answer. We run the search and look at the rank of the first
gold chunk in the top 10 results.

  hit@k   share of questions with a gold chunk among the top k results (k = 1, 3, 5, 10)
  MRR     mean reciprocal rank: 1/rank of the first gold chunk, 0 if it is not in the top 10
          (so this is MRR@10)

Ablations, one change each (W3.7): the same questions with
  hybrid  BM25 + embeddings fused with reciprocal rank fusion (the system as built)
  dense   embeddings only            -> what BM25 adds
  bm25    BM25 (keywords) only       -> what embeddings add
  hybrid+rerank  hybrid top 20 re-ordered by a cross-encoder (src/rerank.py) -> what the reranker adds

Questions tagged "typo" are misspelled copies of main questions. They are reported
separately so they do not change the main numbers.

Run:  python src/evaluate_retrieval.py              all four modes
      python src/evaluate_retrieval.py --mode bm25  one mode (bm25 needs no model download)
Writes results/week3/retrieval_eval.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import ROOT, load_chunks  # noqa: E402
from retrieval import Index  # noqa: E402

MODES = ["hybrid", "dense", "bm25", "hybrid+rerank"]

QUESTIONS = ROOT / "tests" / "retrieval_questions.json"
OUTPUT = ROOT / "results" / "week3" / "retrieval_eval.json"
KS = (1, 3, 5, 10)
DEPTH = 10


def load_questions(path=QUESTIONS):
    questions = json.loads(Path(path).read_text(encoding="utf-8"))
    chunk_ids = {c.id for c in load_chunks()}
    for q in questions:
        missing = [g for g in q["gold"] if g not in chunk_ids]
        if missing:
            raise SystemExit(f"{q['id']}: gold chunk(s) not in the public corpus: {missing}")
    return questions


def first_gold_rank(results, gold):
    """1-based rank of the first gold chunk in the result list, or None."""
    for rank, chunk_id in enumerate(results, start=1):
        if chunk_id in gold:
            return rank
    return None


def score(ranks):
    n = len(ranks)
    out = {"n": n}
    for k in KS:
        hits = sum(1 for r in ranks if r is not None and r <= k)
        out[f"hit_at_{k}"] = round(hits / n, 3)
        out[f"hits_at_{k}"] = hits
    out["mrr"] = round(sum(1 / r for r in ranks if r is not None) / n, 3)
    return out


def run_search(index, reranker, query, mode):
    if mode == "hybrid+rerank":
        from rerank import search_reranked
        return search_reranked(index, reranker, query, DEPTH)
    return index.search(query, DEPTH, mode)


def evaluate(index, questions, mode, reranker=None):
    rows = []
    for q in questions:
        results = [h.chunk.id for h in run_search(index, reranker, q["question"], mode)]
        rows.append({"id": q["id"], "type": q["type"], "question": q["question"],
                     "gold": q["gold"], "rank": first_gold_rank(results, set(q["gold"])),
                     "top3": results[:3]})
    main = [r for r in rows if r["type"] != "typo"]
    typo = [r for r in rows if r["type"] == "typo"]
    summary = {"main": score([r["rank"] for r in main])}
    for t in sorted({r["type"] for r in main}):
        summary[t] = score([r["rank"] for r in main if r["type"] == t])
    if typo:
        summary["typo"] = score([r["rank"] for r in typo])
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--mode", choices=MODES, action="append",
                        help="search mode(s) to evaluate; default: all four")
    args = parser.parse_args()
    modes = args.mode or MODES

    questions = load_questions()
    index = Index(dense=any(m != "bm25" for m in modes))
    reranker = None
    if "hybrid+rerank" in modes:
        from rerank import Reranker
        reranker = Reranker()
    report = {"questions": str(QUESTIONS.relative_to(ROOT)), "depth": DEPTH,
              "public_chunks": len(index.chunks),
              "embedding_model": index.embedder.name if index.embedder else None,
              "reranker_model": reranker.name if reranker else None,
              "modes": {}}
    for mode in modes:
        summary, rows = evaluate(index, questions, mode, reranker)
        report["modes"][mode] = {"summary": summary, "per_question": rows}

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    n = report["modes"][modes[0]]["summary"]["main"]["n"]
    print(f"\nMain set: {n} questions, {report['public_chunks']} public chunks\n")
    print(f"{'mode':<14}" + "".join(f"{'hit@' + str(k):>9}" for k in KS) + f"{'MRR':>8}")
    for mode in modes:
        s = report["modes"][mode]["summary"]["main"]
        print(f"{mode:<14}" + "".join(f"{s[f'hit_at_{k}']:>9.3f}" for k in KS) + f"{s['mrr']:>8.3f}")
    for mode in modes:
        s = report["modes"][mode]["summary"]
        parts = [f"{t} hit@5 {s[t]['hits_at_5']}/{s[t]['n']}" for t in s if t != "main"]
        print(f"  {mode}: " + ", ".join(parts))
    print("\nMissed at hit@5 (rank of first gold chunk, '-' = not in top 10):")
    for mode in modes:
        for r in report["modes"][mode]["per_question"]:
            if r["rank"] is None or r["rank"] > 5:
                print(f"  {mode:<13} {r['id']:<5} rank {r['rank'] or '-':<3} {r['question'][:60]}"
                      f"  -> got {r['top3'][0]}")
    print(f"\nSaved {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
