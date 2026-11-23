"""Week 3 corpus: load the store documents and split them into chunks (W3.1, W3.2).

Documents live in data/docs/<id>.md with front matter: id, title, type, access, version,
updated, store, source. access is "public" (customers may see it) or "staff" (internal only).

Chunking is structure-aware: one chunk per "## " section, with the document title and the
section heading at the top of the chunk. A section that has no heading becomes "Overview".
Sections are short (one topic each), so a chunk is one self-contained rule, which makes a
citation point to exactly the rule it relies on.

The customer-facing assistant loads only public chunks (load_chunks() default), so staff-only
rules can never reach a customer through retrieval.

Run:  python src/corpus.py     prints documents and chunk statistics
"""
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data" / "docs"
REQUIRED = ("id", "title", "type", "access", "version", "updated", "source")
ACCESS = ("public", "staff")


@dataclass(frozen=True)
class Document:
    id: str
    meta: dict
    body: str

    @property
    def title(self):
        return self.meta["title"]


@dataclass(frozen=True)
class Chunk:
    id: str          # "<doc id>#<section number>", e.g. "returns-policy#1"
    doc_id: str
    title: str
    section: str
    text: str        # what is indexed and shown to the model
    access: str
    type: str
    version: str

    @property
    def label(self):
        return f"{self.title} > {self.section}"


def parse(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: missing front matter")
    end = text.index("\n---\n", 4)
    meta = {}
    for line in text[4:end].splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        raise ValueError(f"{path.name}: front matter misses {missing}")
    if meta["access"] not in ACCESS:
        raise ValueError(f"{path.name}: access must be one of {ACCESS}")
    if meta["id"] != path.stem:
        raise ValueError(f"{path.name}: id '{meta['id']}' does not match the file name")
    return Document(meta["id"], meta, text[end + 5:])


def load_documents():
    return [parse(p) for p in sorted(DOCS.glob("*.md"))]


def chunk(doc):
    chunks, section, lines = [], "Overview", []

    def flush():
        body = "\n".join(lines).strip()
        if body:
            n = len(chunks) + 1
            chunks.append(Chunk(
                id=f"{doc.id}#{n}", doc_id=doc.id, title=doc.title, section=section,
                text=f"{doc.title} > {section}\n{body}", access=doc.meta["access"],
                type=doc.meta["type"], version=doc.meta["version"]))

    for line in doc.body.splitlines():
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            flush()
            section, lines = line[3:].strip(), []
        else:
            lines.append(line)
    flush()
    return chunks


def load_chunks(access=("public",)):
    return [c for d in load_documents() for c in chunk(d) if c.access in access]


def main():
    docs = load_documents()
    every = [c for d in docs for c in chunk(d)]
    words = [len(c.text.split()) for c in every]
    print(f"{len(docs)} documents: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(d.meta['type'] for d in docs).items())))
    print("access: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(d.meta['access'] for d in docs).items())))
    print(f"{len(every)} chunks ({len(load_chunks())} public), words per chunk: "
          f"min {min(words)}, median {statistics.median(words):.0f}, max {max(words)}")
    if len(sys.argv) > 1:
        for c in every:
            if c.doc_id == sys.argv[1]:
                print(f"\n[{c.id}] ({c.access})\n{c.text}")


if __name__ == "__main__":
    main()
