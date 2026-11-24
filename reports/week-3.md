# Weekly report

| Field | Value |
|---|---|
| Team | Team 6 |
| Use case | UC1 Online store support agent |
| Week | 3 |
| Repository | https://github.com/berkongul/AIC390Project |
| Commit tag | week-3 |
| Presenter | Orhun Cerit |
| Members and roles | Orhun Cerit (data and retrieval lead), Nurettin Selim Özyılmaz (agent and tools lead), Yakup Berk Öngül (evaluation and safety lead) |

## 1. Summary

We added 37 synthetic store documents, section chunking, hybrid search (BM25 and embeddings with reciprocal rank fusion) with a cross-encoder reranker, and answers with numbered citations. On 32 retrieval questions the system finds a correct passage in the top 5 for **30 (hit@5 0.94, MRR 0.77)**. Embeddings alone did as well (31 of 32), BM25 alone much worse (20). 27 of 32 answers were fully supported. The judge flagged 2 of 44 claims, and the human check overruled both. Last week's feedback is answered with an architecture page, a live demo and an embeddings view.

## 2. Deliverables

| ID | Status | Evidence | Note |
|---|---|---|---|
| W3.1 | done | [`data/docs/`](../data/docs/) | 37 documents (17 policies, 4 guides, FAQ, 11 product pages, 4 staff-only procedures), each with id, title, type, access, version, updated and source. Synthetic, fictional store (R10). The instructor asked for about 10,000 chunks, which is not in this version (section 6) |
| W3.2 | done | [`src/corpus.py`](../src/corpus.py) | One chunk per section, with the document title and heading on top: 117 chunks, 109 public, median 29 words. Short sections hold one rule each, so a citation points to one rule |
| W3.3 | done | [`src/retrieval.py`](../src/retrieval.py) | BM25 with a tokenizer that keeps codes like `TR-220` whole, `BAAI/bge-small-en-v1.5` embeddings, reciprocal rank fusion, then `Xenova/ms-marco-MiniLM-L-6-v2` re-scores the top 20. Staff-only documents are never indexed for customers |
| W3.4 | done | [`src/rag_answer.py`](../src/rag_answer.py), [`prompts/rag_v1.txt`](../prompts/rag_v1.txt) | Every fact ends with [n]. A fixed reply when the passages do not answer. `check_citations()` flags missing or invalid citations |
| W3.5 | done | [`tests/retrieval_questions.json`](../tests/retrieval_questions.json), [`src/evaluate_retrieval.py`](../src/evaluate_retrieval.py), `results/week3/retrieval_eval.json` | 32 questions with gold passages: 25 paraphrases, 4 exact codes, 3 traps. hit@1, 3, 5, 10 and MRR@10 |
| W3.6 | done | [`src/evaluate_faithfulness.py`](../src/evaluate_faithfulness.py), `results/week3/faithfulness/` | 44 claims judged one by one against their cited passages. Judge checked against 20 human labels |
| W3.7 | done | `results/week3/retrieval_eval.json` | Two ablations, one change each: the retrieval method (hybrid, embeddings only, BM25 only) and the reranker (on or off) |
| W3.8 | done | `results/week3/faithfulness/raw.jsonl` (`failure`), section 5 | Each failed answer labelled retrieval or generation, then checked by hand |

## 3. Scoreboard

```json
{
  "week": 3,
  "test_set_size": 32,
  "e2e_accuracy":       {"value": null, "ci95": null, "n": null, "script": null},
  "abstention_correct": {"value": null, "ci95": null, "n": null, "script": null},
  "unsupported_claims": {"value": 0.045, "n": 44, "script": "src/evaluate_faithfulness.py"},
  "hit_at_5":           {"value": 0.938, "n": 32, "script": "src/evaluate_retrieval.py"},
  "mrr":                {"value": 0.77, "n": 32, "script": "src/evaluate_retrieval.py"},
  "task_success":       {"value": null, "n": null, "script": null},
  "pass_k":             {"k": null, "value": null, "n": null, "script": null},
  "injection_success":  {"value": null, "n": null, "script": null},
  "cost_per_task_usd":  0.00012414,
  "latency_p50_s":      0.548,
  "spend_week_usd":     0.016147,
  "spend_total_usd":    0.04563
}
```

Changes to any test set this week: a new 32-question retrieval set (W3.5). The week 2 set of 40 cases is unchanged and was not re-run.

`python src/scoreboard_week3.py` builds this block from the committed results (`results/scoreboard_week3.json`).

- `hit_at_5` and `mrr` are for the system as built (hybrid with reranker), main question set.
- `unsupported_claims` is the LLM judge's rate (Wilson 95% interval 0.01–0.15). Both flagged claims were judged supported by the human check, so it is an upper bound.
- `e2e_accuracy` and `abstention_correct` are null: the week 2 cases have rubrics written for an assistant without documents and were not re-run on the RAG pipeline. `injection_success` starts in week 5.
- Cost and latency are the answer call per question. Retrieval runs locally and costs nothing. Spend is list price of every committed call since the week 2 scoreboard.

## 4. Experiments

### Experiment 1: Retrieval method (ablation)

- **Hypothesis:** Hybrid search beats either method alone, because BM25 catches exact codes and embeddings catch paraphrases.
- **Change:** Only the retrieval method. Same 32 questions, same chunks, top 10 kept.
- **Result:**

| Mode | hit@1 | hit@3 | hit@5 | hit@10 | MRR |
|---|---|---|---|---|---|
| BM25 only | 9 | 16 | 20 | 23 | 0.40 |
| Embeddings only | 21 | 30 | 31 | 32 | 0.79 |
| Hybrid (RRF) | 19 | 27 | 29 | 29 | 0.71 |
| Hybrid + reranker | 21 | 27 | 30 | 31 | 0.77 |

Counts out of 32. All four modes find every exact-code question (4 of 4). At hit@5, embeddings beat BM25 on 11 questions and lost on none. Embeddings and hybrid + reranker differ on a single question.

- **Decision:** The hypothesis is not supported on this set. 25 of the 32 questions are paraphrases with few shared words, where BM25 adds noise. We keep hybrid + reranker, because the difference to embeddings alone is one question, and the larger catalogue planned next has many near-identical product codes, where embeddings place different codes close together (TR-220 against TR-310, cosine 0.77, `results/week3/embedding_similarity.json`).

### Experiment 2: Reranker on or off (ablation)

- **Hypothesis:** A cross-encoder that reads the question and passage together puts the right passage higher.
- **Change:** Only the reranker on the top 20 hybrid results.
- **Result:** hit@1 19 to 21, hit@5 29 to 30, MRR 0.71 to 0.77. At hit@5 the reranker fixed one question and broke none. At hit@1 it moved 6 questions up to first place and 4 down.
- **Decision:** Keep it on. The direction is consistent, but with 32 questions the gain is too small to call it a real improvement yet.

### Experiment 3: Does the faithfulness judge agree with a person?

- **Hypothesis:** The claim judge matches a human annotator.
- **Change:** Selim labelled 20 claims (both judge-unsupported claims and 18 judge-supported ones) without seeing the judge's verdicts.
- **Result:** Agreement 18 of 20. The only two disagreements are the judge's two "unsupported" claims, which the human marked supported (R13: "I can't confirm the next steps", R32: refusing to share another customer's address). κ = 0.00 is not informative, because the human sample has no unsupported claim.
- **Decision:** The judge is too strict on these cases, so 0.045 is an upper bound. Next time the sample must contain real unsupported claims and a second annotator. Details: `results/week3/faithfulness/human_labels_notes.md`.

## 5. Failure analysis

Five of 32 answers were not fully supported. Two were labelled retrieval failures, three generation failures. A manual review moved two of them to evaluation.

| # | Input (short) | What happened | Root cause | Fix (done or planned) |
|---|---|---|---|---|
| 1 | R22 "If you haven't shipped it yet, I would like to return it." | The rule is in "cancel before dispatch", which is not in the top 10. The customer said "return", so retrieval found the returns and dispatch passages. The answer was still correct but cited only the second half | retrieval | Planned: a FAQ entry linking "return before it ships" to cancellation, and query expansion for return and cancel |
| 2 | R29 "Is the HD-104 available in XL?" | The product page lists XS to XXL but not stock. The model gave the fixed reply instead of the part it could confirm | generation | Planned: a worked example of a partial answer in the prompt ("comes in XS–XXL, stock is not listed") |
| 3 | R13 "I noticed a fault two months after delivery." | The answer cited the 14-day rule, then said it could not confirm the next steps, because the warranty claim passage was not retrieved. The judge also marked that sentence unsupported, against its own rule | retrieval, evaluation | Planned: retrieval of the linked policy when a passage refers to it ("handled under the warranty policy") |

Also found: R02 (washed hoodie) counts as a retrieval miss, but the answer is correct from another passage, so the gold set is too narrow (evaluation). R32 (a mother asking for an address) was a judge error, and the human label overruled it.

## 6. Response to last week's feedback

| Feedback point | What we changed | Evidence |
|---|---|---|
| Show the architecture | A page with the seven layers, what is built and what is planned, the flow of one message and the design choices | [`docs/architecture.md`](../docs/architecture.md) |
| Live demo | One command that classifies, retrieves (BM25 rank, embedding rank, reranker score) and answers with the cited passages, about 1.2 s per message | [`src/demo.py`](../src/demo.py) |
| Show embeddings | A 2D map of the chunk embeddings with a query and its nearest passages, and a cosine table: "refund" and "money back" 0.76 without shared words, "TR-220" and "TR-310" 0.77 although different products | [`src/embedding_map.py`](../src/embedding_map.py), `results/week3/embedding_map.png`, `results/week3/embedding_similarity.json` |
| Use a much larger corpus, about 10,000 chunks | Not done this week. The corpus is 37 documents and 117 chunks. A generated product catalogue is planned for week 4 | section 10 |

## 7. Product track

Not done this week. We have not yet talked to potential customers. The interview questions are prepared: which questions take the most time, how returns are handled, what the assistant may answer, what it is worth per month or per message, and what worries them.

## 8. Contributions

| Member | Role | What they did this week | Commits or files | Hours |
|---|---|---|---|---|
| Orhun Cerit | Data and retrieval lead | Retrieval question set (W3.5), retrieval evaluation with the three-mode ablation, price-change rule in the sale policy | 91ff132, a822654, c60d559, a0d701c | not reported |
| Nurettin Selim Özyılmaz | Agent and tools lead | Store documents, chunking, hybrid search, reranker, cited answers, live demo, architecture page, embeddings view, faithfulness evaluation and failure labels, week 3 scoreboard, 20 human labels, this report | PR #7 | not reported |
| Yakup Berk Öngül | Evaluation and safety lead | No week 3 work in the repository | none | not reported |

## 9. AI tools used

| Tool | Used for |
|---|---|
| Claude Code (Selim) | Drafted the store documents, retrieval, reranker, citation, demo, embedding, faithfulness and scoreboard code with tests, the architecture page and this report. Re-checked two of Selim's labels at his request, and no label changed |
| Groq `openai/gpt-oss-20b` | The model under test, the classifier and the faithfulness judge |
| Orhun, Berk | Not reported |

## 10. Next week

| Priority | Metric it should move | Expected change |
|---|---|---|
| 1. A generated product catalogue to about 10,000 chunks, with near-identical codes, then re-run the retrieval evaluation | `hit_at_5`, `mrr` | `hit_at_5` stays at or above 0.90 at 10,000 chunks |
| 2. Three tools (document search, order data, sandbox return) and an agent loop with step, token and time limits (W4.1, W4.2) | `task_success`, cost per task | First measurement on at least 10 multi-step tasks |
| 3. A judge calibration sample with real unsupported claims and a second annotator, plus the fixes for R22, R29 and R13 | judge κ, `unsupported_claims` | κ measurable and at least 0.6 |
