"""Show what the embeddings do (instructor feedback, week 2: "show embeddings").

  1. A 2D map of every public chunk embedding (bge-small-en-v1.5, 384 dimensions), projected
     with PCA. Colour = document type. A query is projected into the same space and joined to
     its 5 nearest chunks by cosine similarity, which is what dense retrieval returns.
  2. A cosine-similarity table for short phrases: words with the same meaning ("refund",
     "money back") score high even without shared words, while BM25 would see no overlap.
     Exact codes ("TR-220" against "TR-310") score high although they are different products,
     which is why the search also uses BM25.

PCA keeps only the two directions with the most variance, so distances on the map are rough.
The nearest-neighbour lines and the printed cosine scores use the full 384 dimensions.

Run:  python src/embedding_map.py "Does the TR-220 run small?"
Writes results/week3/embedding_map.png and results/week3/embedding_similarity.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import ROOT  # noqa: E402
from retrieval import Index  # noqa: E402

OUT = ROOT / "results" / "week3"
PHRASES = ["refund", "money back", "return an item", "delivery time", "shipping",
           "waterproof", "rain jacket", "TR-220", "TR-310", "password"]
COLOURS = {"policy": "#2a6fdb", "product": "#e07b1a", "guide": "#2e9e5b", "faq": "#8e44ad", "procedure": "#888888"}


def pca_2d(matrix):
    centre = matrix.mean(axis=0)
    _, s, vt = np.linalg.svd(matrix - centre, full_matrices=False)
    explained = (s ** 2) / (s ** 2).sum()
    return (lambda m: (m - centre) @ vt[:2].T), explained[:2]


def draw(index, query, path, k=5):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    project, explained = pca_2d(index.vectors)
    points = project(index.vectors)
    q_vec = index.embedder.query(query)
    q_point = project(q_vec[None, :])[0]
    sims = index.vectors @ q_vec
    nearest = np.argsort(-sims)[:k]

    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=150)
    for kind, colour in COLOURS.items():
        idx = [i for i, c in enumerate(index.chunks) if c.type == kind]
        if idx:
            ax.scatter(points[idx, 0], points[idx, 1], s=28, c=colour, alpha=0.75, label=f"{kind} ({len(idx)})")
    offsets = [(8, 8), (-8, -16), (8, -14), (-8, 10), (8, 2)]
    for j, i in enumerate(nearest):
        ax.plot([q_point[0], points[i, 0]], [q_point[1], points[i, 1]], c="#d62728", lw=1, alpha=0.7)
        dx, dy = offsets[j % len(offsets)]
        ax.annotate(f"{index.chunks[i].id}  {sims[i]:.2f}", points[i], fontsize=8,
                    xytext=(dx, dy), textcoords="offset points", ha="left" if dx > 0 else "right",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
    ax.scatter(*q_point, marker="*", s=380, c="#d62728", edgecolors="black", zorder=5, label="query")
    ax.annotate(f'"{query}"', q_point, fontsize=9, weight="bold", xytext=(8, -14), textcoords="offset points")
    ax.set_title(f"{len(index.chunks)} store passages embedded with bge-small-en-v1.5 (384-d), PCA to 2D "
                 f"({100 * explained.sum():.0f}% of variance shown)", fontsize=10)
    ax.set_xlabel("PCA 1")
    ax.set_ylabel("PCA 2")
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path)
    return [(index.chunks[i].id, float(sims[i])) for i in nearest], explained


def similarity_table(embedder):
    vecs = np.array([embedder.query(p) for p in PHRASES])
    return (vecs @ vecs.T).round(3)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", nargs="?", default="Does the TR-220 run small?")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    index = Index()
    nearest, explained = draw(index, args.query, OUT / "embedding_map.png")
    table = similarity_table(index.embedder)

    print(f"Nearest passages to {args.query!r} (cosine, full 384 dimensions):")
    for chunk_id, sim in nearest:
        print(f"  {sim:.3f}  {chunk_id}")
    print(f"\nPCA keeps {100 * explained.sum():.1f}% of the variance in 2D.")
    width = max(len(p) for p in PHRASES)
    print("\nCosine similarity between phrases:\n" + " " * (width + 2) + " ".join(f"{p[:8]:>8}" for p in PHRASES))
    for p, row in zip(PHRASES, table):
        print(f"{p:<{width}}  " + " ".join(f"{v:>8.2f}" for v in row))
    (OUT / "embedding_similarity.json").write_text(json.dumps({
        "model": index.embedder.name, "query": args.query,
        "nearest": [{"chunk": c, "cosine": round(s, 4)} for c, s in nearest],
        "pca_variance_2d": round(float(explained.sum()), 4),
        "phrases": PHRASES, "cosine": table.tolist()}, indent=1) + "\n", encoding="utf-8")
    print(f"\nWrote {(OUT / 'embedding_map.png').relative_to(ROOT)} and {(OUT / 'embedding_similarity.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
