"""Week 3 reranker (W3.3): re-score the hybrid search candidates with a cross-encoder.

Owner: Orhun Cerit (data and retrieval lead).

Hybrid search (src/retrieval.py) is fast because it compares vectors that were computed
separately for the question and for each chunk (a bi-encoder). A cross-encoder reads the
question and one chunk together and outputs a relevance score, which is slower but more
precise (Module 3, slides 37-38). So we use it only on the top CANDIDATES chunks from
hybrid search and re-order them: retrieve, then rerank.

Model: Xenova/ms-marco-MiniLM-L-6-v2 through fastembed (runs locally, no API key, about
80 MB on first use). It was trained on MS MARCO, web search questions with relevant passages.

Run:  python src/rerank.py "Does the TR-220 run small?"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieval import Hit, Index  # noqa: E402

MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
CANDIDATES = 20


class Reranker:
    def __init__(self, model=MODEL):
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        self.name = model
        try:
            self.model = TextCrossEncoder(model_name=model)
        except ValueError as exc:
            names = [m["model"] for m in TextCrossEncoder.list_supported_models()]
            raise SystemExit(f"Reranker model {model!r} not available. Supported: {names}") from exc

    def scores(self, query, texts):
        return [float(s) for s in self.model.rerank(query, list(texts))]


def search_reranked(index, reranker, query, k=5, candidates=CANDIDATES):
    """Hybrid search for `candidates` chunks, then keep the k with the highest cross-encoder score."""
    hits = index.search(query, candidates, "hybrid")
    scores = reranker.scores(query, (h.chunk.text for h in hits))
    order = sorted(range(len(hits)), key=lambda i: -scores[i])
    return [Hit(hits[i].chunk, scores[i], hits[i].bm25_rank, hits[i].dense_rank,
                hits[i].bm25_score, hits[i].dense_score) for i in order[:k]]


def main():
    parser = argparse.ArgumentParser(description="Hybrid search, then cross-encoder reranking.")
    parser.add_argument("query")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    index, reranker = Index(), Reranker()
    before = [h.chunk.id for h in index.search(args.query, args.k, "hybrid")]
    for n, h in enumerate(search_reranked(index, reranker, args.query, args.k), 1):
        was = before.index(h.chunk.id) + 1 if h.chunk.id in before else "-"
        print(f"{n}. {h.chunk.id:<34} rerank {h.score:7.3f}  (hybrid rank {was})  | {h.chunk.label}")


if __name__ == "__main__":
    main()
