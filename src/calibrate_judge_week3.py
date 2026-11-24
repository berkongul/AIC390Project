"""Judge calibration sample with real unsupported claims (week 3, evaluation and safety).

The week 3 faithfulness run had only 2 judge-unsupported claims, and the human check found
none, so Cohen's kappa could not say anything. This script builds a sample where both classes
occur:

  1. 24 questions (the 12 unanswerable ones in tests/abstention_week3.json and R01-R12 of the
     retrieval set) are answered with prompts/rag_loose_v0.txt, a deliberately loose prompt
     ("answer helpfully, the passages may help") that is not part of the system.
  2. Every sentence is a claim, judged by judge v2 against the 5 retrieved passages.
  3. Stratified sample: 10 claims judge v2 calls unsupported and 10 it calls supported (fixed
     seed). Judge v1 also scores these 20.
  4. sample.csv goes to the annotators WITHOUT the judge verdicts. Each annotator fills
     human_supported (0/1) and annotator in their own copy labels_<name>.csv.

Run:  python src/calibrate_judge_week3.py                   builds the sample (about 150 Groq calls)
      python src/calibrate_judge_week3.py --score           kappa of every labels_*.csv against
                                                            judge v1, judge v2 and each other
Writes results/week3/judge_calibration/
"""
import argparse
import csv
import json
import os
import random
import sys
from itertools import combinations
from pathlib import Path

os.environ.setdefault("WEEK2_PAUSE_SECONDS", "2")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import ROOT  # noqa: E402
from evaluate_faithfulness import claims_of, judge_claim  # noqa: E402
from rag_answer import user_message  # noqa: E402
from retrieval import Index  # noqa: E402
from week2_stats import kappa  # noqa: E402

OUT = ROOT / "results" / "week3" / "judge_calibration"
PROMPT = ROOT / "prompts" / "rag_loose_v0.txt"
PER_CLASS, SEED, K = 10, 24, 5


def questions():
    abst = json.loads((ROOT / "tests" / "abstention_week3.json").read_text(encoding="utf-8"))["cases"]
    retr = json.loads((ROOT / "tests" / "retrieval_questions.json").read_text(encoding="utf-8"))
    return ([(c["id"], c["question"]) for c in abst if c["kind"] == "unanswerable"]
            + [(q["id"], q["question"]) for q in retr[:12]])


def build():
    from week2 import Model
    index, model = Index(), Model()
    system = PROMPT.read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    pool = []
    with (OUT / "raw.jsonl").open("w", encoding="utf-8") as f:
        for qid, question in questions():
            hits = index.search(question, K, "rerank")
            text = model.call(system, user_message(question, hits)).strip()
            claims = claims_of(text)
            for i, c in enumerate(claims):
                c["cited"] = []  # judged against all 5 passages
                c["judge_v2"] = judge_claim(model, c, hits, "v2")
                if c["judge_v2"]:
                    pool.append({"key": f"{qid}#{i}", "qid": qid, "question": question, "claim": c["text"],
                                 "passages": [h.chunk.text for h in hits], "v2": int(c["judge_v2"]["supported"]),
                                 "hits": hits})
            f.write(json.dumps({"id": qid, "question": question, "answer": text,
                                "retrieved": [h.chunk.id for h in hits],
                                "claims": [{k: v for k, v in c.items()} for c in claims]}, ensure_ascii=False) + "\n")
            print(qid, len(claims), "claims", sum(1 for c in claims if c["judge_v2"] and not c["judge_v2"]["supported"]),
                  "unsupported", flush=True)

    rng = random.Random(SEED)
    unsup = [p for p in pool if p["v2"] == 0]
    sup = [p for p in pool if p["v2"] == 1]
    sample = rng.sample(unsup, min(PER_CLASS, len(unsup))) + rng.sample(sup, min(PER_CLASS, len(sup)))
    rng.shuffle(sample)
    for p in sample:
        v1 = judge_claim(model, {"text": p["claim"], "cited": []}, p["hits"], "v1")
        p["v1"] = int(v1["supported"]) if v1 else None

    with (OUT / "sample.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "question", "claim", "passages", "human_supported", "annotator"])
        w.writeheader()
        for p in sample:
            w.writerow({"key": p["key"], "question": p["question"], "claim": p["claim"],
                        "passages": "\n\n".join(f"[{n}] {t}" for n, t in enumerate(p["passages"], 1)),
                        "human_supported": "", "annotator": ""})
    (OUT / "judge_verdicts.json").write_text(json.dumps(
        {p["key"]: {"v1": p["v1"], "v2": p["v2"]} for p in sample}, indent=1) + "\n", encoding="utf-8")
    (OUT / "calls.json").write_text(json.dumps(model.calls, indent=1) + "\n", encoding="utf-8")
    print(f"pool {len(pool)} claims ({len(unsup)} unsupported by v2), sample {len(sample)} -> {OUT / 'sample.csv'}")


def score():
    verdicts = json.loads((OUT / "judge_verdicts.json").read_text(encoding="utf-8"))
    sheets = {}
    for path in sorted(OUT.glob("labels_*.csv")):
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        if rows and all(r["human_supported"] in ("0", "1") and r["annotator"].strip() for r in rows):
            sheets[path.stem[len("labels_"):]] = {r["key"]: int(r["human_supported"]) for r in rows}
    result = {"n": len(verdicts), "annotators": {}, "between_annotators": []}
    keys = sorted(verdicts)
    for name, labels in sheets.items():
        human = [labels[k] for k in keys]
        entry = {"unsupported": human.count(0)}
        for judge in ("v1", "v2"):
            scored = [k for k in keys if verdicts[k][judge] is not None]  # a judge can fail to answer
            entry[f"vs_judge_{judge}"] = kappa([labels[k] for k in scored], [verdicts[k][judge] for k in scored])
            entry[f"vs_judge_{judge}"]["missing_verdicts"] = len(keys) - len(scored)
            entry[f"disagree_{judge}"] = [k for k in scored if labels[k] != verdicts[k][judge]]
        result["annotators"][name] = entry
    for a, b in combinations(sheets, 2):
        result["between_annotators"].append({"pair": [a, b], **kappa([sheets[a][k] for k in keys],
                                                                       [sheets[b][k] for k in keys])})
    (OUT / "calibration.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--score", action="store_true")
    score() if parser.parse_args().score else build()
