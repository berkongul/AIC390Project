"""Retrieval evaluation: week 3 (W3.5, W3.7) and the week 4 scale test at about 10,000 chunks.

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
  rerank  hybrid, then the top 20 re-scored by a cross-encoder -> what the reranker adds

Questions tagged "typo" are misspelled copies of main questions. They are reported
separately so they do not change the main numbers.

Week 4: the corpus grows to about 10,000 chunks with the generated product catalogue
(src/catalogue.py). Two question sets are scored separately:
  week3      the 32 week 3 questions, unchanged (tests/retrieval_questions.json)
  catalogue  22 questions about generated products whose codes differ by one digit from
             other products, asked by code or by product name
             (tests/retrieval_questions_catalogue.json)

Run:  python src/evaluate_retrieval.py                  full corpus (~10,000 chunks), all four modes
      python src/evaluate_retrieval.py --corpus small   week 3 corpus (109 chunks), week 3 questions
      python src/evaluate_retrieval.py --mode bm25      one mode (bm25 needs no model download)
Writes results/week4/retrieval_eval_<corpus>.json (week 3 results in results/week3/ stay as they are).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import ROOT, load_chunks  # noqa: E402
from retrieval import Index  # noqa: E402

QUESTIONS = ROOT / "tests" / "retrieval_questions.json"
CATALOGUE_QUESTIONS = ROOT / "tests" / "retrieval_questions_catalogue.json"
OUTPUT_DIR = ROOT / "results" / "week4"
KS = (1, 3, 5, 10)
DEPTH = 10


def load_questions(path, chunk_ids, set_name):
    questions = json.loads(Path(path).read_text(encoding="utf-8"))
    for q in questions:
        q["set"] = set_name
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


def evaluate(index, questions, mode):
    rows = []
    for q in questions:
        results = [h.chunk.id for h in index.search(q["question"], DEPTH, mode)]
        rows.append({"id": q["id"], "set": q["set"], "type": q["type"], "question": q["question"],
                     "gold": q["gold"], "rank": first_gold_rank(results, set(q["gold"])),
                     "top3": results[:3]})
    summary = {}
    for set_name in dict.fromkeys(r["set"] for r in rows):
        in_set = [r for r in rows if r["set"] == set_name and r["type"] != "typo"]
        summary[set_name] = score([r["rank"] for r in in_set])
    for t in sorted({r["type"] for r in rows}):
        summary[t] = score([r["rank"] for r in rows if r["type"] == t])
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--mode", choices=["hybrid", "dense", "bm25", "rerank"], action="append",
                        help="search mode(s) to evaluate; default: all four")
    parser.add_argument("--corpus", choices=["full", "small"], default="full",
                        help="full: with the generated catalogue (~10,000 chunks); small: week 3 corpus")
    args = parser.parse_args()
    modes = args.mode or ["hybrid", "dense", "bm25", "rerank"]

    chunks = load_chunks(catalogue=args.corpus == "full")
    chunk_ids = {c.id for c in chunks}
    sets = [("week3", QUESTIONS)] + ([("catalogue", CATALOGUE_QUESTIONS)] if args.corpus == "full" else [])
    questions = [q for name, path in sets for q in load_questions(path, chunk_ids, name)]
    print(f"Indexing {len(chunks)} public chunks (the first full run embeds them all, a few minutes)...")
    index = Index(chunks=chunks, dense=any(m != "bm25" for m in modes))
    report = {"corpus": args.corpus,
              "questions": {name: str(path.relative_to(ROOT)) for name, path in sets}, "depth": DEPTH,
              "public_chunks": len(index.chunks),
              "embedding_model": index.embedder.name if index.embedder else None,
              "modes": {}}
    for mode in modes:
        summary, rows = evaluate(index, questions, mode)
        report["modes"][mode] = {"summary": summary, "per_question": rows}

    output = OUTPUT_DIR / f"retrieval_eval_{args.corpus}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    for set_name, _ in sets:
        n = report["modes"][modes[0]]["summary"][set_name]["n"]
        print(f"\n{set_name} questions: {n}, corpus: {report['public_chunks']} public chunks\n")
        print(f"{'mode':<8}" + "".join(f"{'hit@' + str(k):>9}" for k in KS) + f"{'MRR':>8}")
        for mode in modes:
            s = report["modes"][mode]["summary"][set_name]
            print(f"{mode:<8}" + "".join(f"{s[f'hit_at_{k}']:>9.3f}" for k in KS) + f"{s['mrr']:>8.3f}")
    print("\nhit@5 by question type:")
    for mode in modes:
        s = report["modes"][mode]["summary"]
        types = sorted({r["type"] for r in report["modes"][mode]["per_question"]})
        print(f"  {mode:<7} " + ", ".join(f"{t} {s[t]['hits_at_5']}/{s[t]['n']}" for t in types))
    print("\nMissed at hit@5 (rank of first gold chunk, '-' = not in top 10):")
    for mode in modes:
        for r in report["modes"][mode]["per_question"]:
            if r["rank"] is None or r["rank"] > 5:
                print(f"  {mode:<7} {r['id']:<5} rank {r['rank'] or '-':<3} {r['question'][:55]}"
                      f"  -> got {r['top3'][0]}")
    print(f"\nSaved {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
