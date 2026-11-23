"""Live demo of the pipeline so far: understand -> retrieve -> answer with citations.

  1 Understand   the request classifier (week 2) returns intent, entities and urgency
  2 Retrieve     hybrid search over the public store documents: BM25 + embeddings + RRF
  3 Answer       Groq openai/gpt-oss-20b answers only from the passages, with [n] citations,
                 or gives the fixed "can't find it" reply. The citations are checked.

Run:  python src/demo.py                      type messages, empty line to quit
      python src/demo.py "Does the TR-220 run small? I'm usually a 42."
      python src/demo.py --no-llm "..."       retrieval only, no API key needed
"""
import argparse
import json
import os
import sys
import time
import textwrap
from pathlib import Path

os.environ.setdefault("WEEK2_PAUSE_SECONDS", "0")  # the harness paces calls, a live demo should not
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_week1 import PRICE_IN, PRICE_OUT  # noqa: E402
from rag_answer import answer  # noqa: E402
from retrieval import Index  # noqa: E402

BAR = "━" * 64


def header(n, title, seconds=None):
    t = f"  {seconds:.2f} s" if seconds is not None else ""
    print(f"\n{BAR}\n {n}  {title}{t}\n{BAR}")


def run(message, index, model, k):
    if model:
        from week2 import classify
        start = time.perf_counter()
        value, errors = classify(model, message)
        header(1, "Understand: request classifier (layer 1)", time.perf_counter() - start)
        print(json.dumps(value, ensure_ascii=False) if value else f"no valid classification, goes to a person {errors}")

    start = time.perf_counter()
    hits = index.search(message, k)
    header(2, "Retrieve: BM25 + embeddings, fused with RRF (layer 2)", time.perf_counter() - start)
    print(f" {'#':<3}{'passage':<44}{'bm25':>5}{'dense':>6}{'cosine':>8}{'rrf':>8}")
    for n, h in enumerate(hits, 1):
        print(f" [{n}] {h.chunk.label[:42]:<42}{h.bm25_rank or '-':>5}{h.dense_rank or '-':>6}"
              f"{h.dense_score:>8.3f}{h.score:>8.4f}")

    if not model:
        return
    start = time.perf_counter()
    calls_before = len(model.calls)
    result = answer(model, message, hits)
    header(3, "Answer with citations", time.perf_counter() - start)
    print(textwrap.fill(result["text"], 80))
    for n in result["cited"]:
        if 1 <= n <= len(hits):
            body = hits[n - 1].chunk.text.split("\n", 1)[1]
            print(textwrap.fill(f"[{n}] {hits[n - 1].chunk.label}: {body}", 80, subsequent_indent="    "))
    calls = model.calls[calls_before:]
    usd = sum((c["input_tokens"] or 0) * PRICE_IN + (c["output_tokens"] or 0) * PRICE_OUT for c in calls) / 1e6
    check = "fixed reply" if result["fixed"] else ("citations ok" if not result["problems"] else "; ".join(result["problems"]))
    print(f"\ncheck: {check} | answer cost ${usd:.6f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("message", nargs="?")
    parser.add_argument("--no-llm", action="store_true", help="retrieval only")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()

    print("Loading the index (BM25 + bge-small-en-v1.5 embeddings)...")
    index = Index()
    model = None
    if not args.no_llm:
        from week2 import Model
        model = Model()
    if args.message:
        run(args.message, index, model, args.k)
        return
    while True:
        try:
            message = input("\nCustomer> ").strip()
        except EOFError:
            break
        if not message:
            break
        run(message, index, model, args.k)


if __name__ == "__main__":
    main()
