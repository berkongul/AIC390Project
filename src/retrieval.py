"""Week 3 hybrid search (W3.3): BM25 and embeddings, combined with reciprocal rank fusion.

  BM25     rank_bm25 over a tokenizer that keeps product and order codes whole ("tr-220",
           "sku-778") and also as parts, because exact identifiers are what embeddings
           handle badly (handbook ingredient 7).
  Dense    fastembed with BAAI/bge-small-en-v1.5 (384 dimensions, runs locally, no API key).
           Chunk vectors are cached in results/week3/index/ and rebuilt when the corpus
           or the model changes.
  Fusion   reciprocal rank fusion, score = sum over both lists of 1 / (RRF_K + rank).

  Rerank   mode "rerank": the top CANDIDATES of the hybrid ranking are scored again by a
           cross-encoder (Xenova/ms-marco-MiniLM-L-6-v2), which reads the question and the
           passage together instead of comparing two separate vectors.

Run:  python src/retrieval.py "Does the TR-220 run small?"
      python src/retrieval.py --mode bm25 "sku-778 warranty"
      python src/retrieval.py --mode rerank "Can I get my money back?"
"""
import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import ROOT, load_chunks  # noqa: E402

MODEL = "BAAI/bge-small-en-v1.5"
RERANKER = "Xenova/ms-marco-MiniLM-L-6-v2"
MODES = ("hybrid", "dense", "bm25", "rerank")
CACHE = ROOT / "results" / "week3" / "index"
RRF_K = 60
CANDIDATES = 20
TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def tokenize(text):
    out = []
    for token in TOKEN.findall(text.lower()):
        out.append(token)
        if "-" in token:
            parts = token.split("-")
            out.extend(parts)
            out.append("".join(parts))
    return out


@dataclass
class Hit:
    chunk: object
    score: float               # RRF score in hybrid mode, the raw score otherwise
    bm25_rank: int | None
    dense_rank: int | None
    bm25_score: float | None
    dense_score: float | None  # cosine similarity


def rrf(rankings, k=RRF_K):
    """rankings: list of lists of ids, best first. Returns {id: score}."""
    scores = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return scores


class Embedder:
    def __init__(self, model=MODEL):
        from fastembed import TextEmbedding
        self.name = model
        self.model = TextEmbedding(model)

    def passages(self, texts):
        return _unit(np.array(list(self.model.passage_embed(list(texts)))))

    def query(self, text):
        return _unit(np.array(list(self.model.query_embed(text))))[0]


class Reranker:
    def __init__(self, model=RERANKER):
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        self.name = model
        self.model = TextCrossEncoder(model)

    def scores(self, query, texts):
        return [float(s) for s in self.model.rerank(query, list(texts))]


def _unit(m):
    return m / np.linalg.norm(m, axis=-1, keepdims=True)


class Index:
    def __init__(self, chunks=None, embedder=None, dense=True):
        self.chunks = chunks if chunks is not None else load_chunks()
        self.bm25 = BM25Okapi([tokenize(c.text) for c in self.chunks])
        self.embedder = embedder or (Embedder() if dense else None)
        self.vectors = self._vectors() if self.embedder else None

    def _vectors(self):
        key = hashlib.sha256((self.embedder.name + "\n" + "\n".join(c.id + c.text for c in self.chunks))
                             .encode("utf-8")).hexdigest()[:16]
        path = CACHE / f"{key}.npz"
        if path.exists():
            return np.load(path)["vectors"]
        vectors = self.embedder.passages(c.text for c in self.chunks)
        CACHE.mkdir(parents=True, exist_ok=True)
        np.savez(path, vectors=vectors)
        (CACHE / f"{key}.json").write_text(json.dumps({"model": self.embedder.name,
                                                       "chunks": [c.id for c in self.chunks]}, indent=1))
        return vectors

    def bm25_ranking(self, query):
        scores = self.bm25.get_scores(tokenize(query))
        order = np.argsort(-scores)
        return [int(i) for i in order if scores[i] > 0][:CANDIDATES], scores

    def dense_ranking(self, query):
        sims = self.vectors @ self.embedder.query(query)
        return [int(i) for i in np.argsort(-sims)[:CANDIDATES]], sims

    def search(self, query, k=5, mode="hybrid"):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        b_rank, b_scores = self.bm25_ranking(query) if mode in ("hybrid", "bm25", "rerank") else ([], None)
        d_rank, d_scores = self.dense_ranking(query) if mode in ("hybrid", "dense", "rerank") else ([], None)
        if mode == "bm25":
            ranked = [(i, float(b_scores[i])) for i in b_rank]
        elif mode == "dense":
            ranked = [(i, float(d_scores[i])) for i in d_rank]
        else:
            fused = rrf([b_rank, d_rank])
            ranked = sorted(fused.items(), key=lambda kv: -kv[1])
            if mode == "rerank":
                if getattr(self, "reranker", None) is None:
                    self.reranker = Reranker()
                pool = [i for i, _ in ranked[:CANDIDATES]]
                scores = self.reranker.scores(query, [self.chunks[i].text for i in pool])
                ranked = sorted(zip(pool, scores), key=lambda kv: -kv[1])
        b_pos = {i: r for r, i in enumerate(b_rank, 1)}
        d_pos = {i: r for r, i in enumerate(d_rank, 1)}
        return [Hit(self.chunks[i], score, b_pos.get(i), d_pos.get(i),
                    float(b_scores[i]) if b_scores is not None else None,
                    float(d_scores[i]) if d_scores is not None else None)
                for i, score in ranked[:k]]


def main():
    parser = argparse.ArgumentParser(description="Search the public store documents.")
    parser.add_argument("query")
    parser.add_argument("--mode", choices=list(MODES), default="hybrid")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    index = Index(dense=args.mode != "bm25")
    for n, h in enumerate(index.search(args.query, args.k, args.mode), 1):
        print(f"{n}. {h.chunk.id:<34} score {h.score:.4f}  bm25 #{h.bm25_rank}  dense #{h.dense_rank}"
              f"  | {h.chunk.label}")


if __name__ == "__main__":
    main()
