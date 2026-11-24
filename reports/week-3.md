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

We added 37 synthetic store documents, section chunking, hybrid search with a cross-encoder reranker, and answers with numbered citations. On 32 retrieval questions a correct passage is in the top 5 for **30 (hit@5 0.94, MRR 0.77)**. BM25 alone found 20 (p = 0.001 against embeddings). **All 12 questions the documents cannot answer got an honest abstention.** 27 of 32 answers were fully supported. The judge is the weak point: on claims a person rated, it agrees only fairly (κ 0.30 to 0.37) and misses policies applied to the wrong case. Last week's feedback is answered.

## 2. Deliverables

| ID | Status | Evidence | Note |
|---|---|---|---|
| W3.1 | done | [`data/docs/`](../data/docs/) | 37 documents (17 policies, 4 guides, FAQ, 11 product pages, 4 staff-only procedures), each with id, title, type, access, version, updated and source. Synthetic, fictional store (R10). The instructor asked for about 10,000 chunks, which is not in this version (section 6) |
| W3.2 | done | [`src/corpus.py`](../src/corpus.py) | One chunk per section, with the document title and heading on top: 117 chunks, 109 public, median 29 words. Short sections hold one rule each, so a citation points to one rule |
| W3.3 | done | [`src/retrieval.py`](../src/retrieval.py) | BM25 with a tokenizer that keeps codes like `TR-220` whole, `BAAI/bge-small-en-v1.5` embeddings, reciprocal rank fusion, then `Xenova/ms-marco-MiniLM-L-6-v2` re-scores the top 20. Staff-only documents are never indexed for customers |
| W3.4 | done | [`src/rag_answer.py`](../src/rag_answer.py), [`prompts/rag_v1.txt`](../prompts/rag_v1.txt) | Every fact ends with [n]. A fixed reply when the passages do not answer. `check_citations()` flags missing or invalid citations |
| W3.5 | done | [`tests/retrieval_questions.json`](../tests/retrieval_questions.json), [`src/evaluate_retrieval.py`](../src/evaluate_retrieval.py), `results/week3/retrieval_eval.json` | 32 questions with gold passages: 25 paraphrases, 4 exact codes, 3 traps. hit@1, 3, 5, 10 and MRR@10 |
| W3.6 | done | [`src/evaluate_faithfulness.py`](../src/evaluate_faithfulness.py), `results/week3/faithfulness/` | 44 claims judged one by one against their cited passages. Judge checked twice against human labels: 20 system claims, and a calibration sample of 20 with real unsupported claims (`src/calibrate_judge_week3.py`, `results/week3/judge_calibration/`) |
| W3.7 | done | `results/week3/retrieval_eval.json` | Two ablations, one change each: the retrieval method (hybrid, embeddings only, BM25 only) and the reranker (on or off) |
| W3.8 | done | `results/week3/faithfulness/raw.jsonl` (`failure`), section 5 | Each failed answer labelled retrieval or generation, then checked by hand |

## 3. Scoreboard

```json
{
  "week": 3,
  "test_set_size": 32,
  "e2e_accuracy":       {"value": null, "ci95": null, "n": null, "script": null},
  "abstention_correct": {"value": 1.0, "ci95": [1.0, 1.0], "ci95_wilson": [0.757, 1.0], "n": 12, "count": 12, "script": "src/evaluate_abstention_week3.py"},
  "unsupported_claims": {"value": 0.045, "n": 44, "script": "src/evaluate_faithfulness.py"},
  "hit_at_5":           {"value": 0.938, "n": 32, "script": "src/evaluate_retrieval.py"},
  "mrr":                {"value": 0.77, "n": 32, "script": "src/evaluate_retrieval.py"},
  "task_success":       {"value": null, "n": null, "script": null},
  "pass_k":             {"k": null, "value": null, "n": null, "script": null},
  "injection_success":  {"value": null, "n": null, "script": null},
  "cost_per_task_usd":  0.00012414,
  "latency_p50_s":      0.548,
  "spend_week_usd":     0.031058,
  "spend_total_usd":    0.060541
}
```

Changes to any test set this week: a new 32-question retrieval set (W3.5), a 19-case abstention set (`tests/abstention_week3.json`: 12 questions the documents cannot answer, 7 week 2 "unanswerable" cases they now answer) and a 20-claim judge calibration sample. The week 2 set of 40 cases is unchanged and was not re-run. After review, T23's expected urgency changes from normal to high in the week 4 version (`docs/label_review_week3.md`).

`python src/scoreboard_week3.py` builds this block from the committed results (`results/scoreboard_week3.json`).

- `hit_at_5` and `mrr` are for the system as built (hybrid with reranker), main question set.
- `unsupported_claims` is the LLM judge's rate (Wilson 95% interval 0.01–0.15). Both flagged claims were judged supported by the human check, so it is an upper bound.
- `abstention_correct` covers the 12 questions the store documents cannot answer: all 12 got the fixed reply and no unsupported claim (judge v2). It replaces the week 2 measure, whose "unanswerable" cases the documents now partly answer (experiment 4).
- `e2e_accuracy` is null: the week 2 cases have rubrics written for an assistant without documents and were not re-run on the RAG pipeline. `injection_success` starts in week 5.
- Cost and latency are the answer call per question. Retrieval runs locally and costs nothing. Spend is list price of every committed call since the week 2 scoreboard, including the judge calibration runs.

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

Counts out of 32. All four modes find every exact-code question (4 of 4). Paired exact McNemar tests at hit@5: embeddings against BM25, 11 against 0 discordant questions, p = 0.001. Embeddings against hybrid + reranker, 1 against 0, p = 1.0.

- **Decision:** Not supported on this set: 25 of the 32 questions are paraphrases, where BM25 adds noise. We keep hybrid + reranker. The gap to embeddings is one question, and the planned catalogue has near-identical codes, which embeddings place close together (TR-220 and TR-310, cosine 0.77).

### Experiment 2: Reranker on or off (ablation)

- **Hypothesis:** A cross-encoder that reads the question and passage together puts the right passage higher.
- **Change:** Only the reranker on the top 20 hybrid results.
- **Result:** hit@1 19 to 21, hit@5 29 to 30, MRR 0.71 to 0.77. Paired exact McNemar: at hit@5, 1 against 0 discordant questions (p = 1.0), at hit@1, 6 against 4 (p = 0.75).
- **Decision:** Keep it on. The direction is consistent, but n = 32 is too small for significance.

### Experiment 3: Does the faithfulness judge agree with a person?

- **Hypothesis:** The claim judge matches a human annotator, and judge v2, which adds the store-channel rule from week 2 (`docs/label_review_week3.md`), matches better than v1.
- **Change:** Two samples, labelled by Selim without the judge's verdicts. (a) 20 claims from the system's own answers. (b) 20 claims from answers to a deliberately loose prompt that is not part of the system, stratified to 10 judge-supported and 10 judge-unsupported, so both classes occur.
- **Result:** (a) Agreement 18 of 20. κ = 0.00 is not informative, because the human rated every claim supported. The two disagreements were the judge's only two flags. (b) The human rated 11 of 20 unsupported. Judge v1 agrees on 13 of 19 (κ = 0.37, one verdict missing), judge v2 on 13 of 20 (κ = 0.30). The judges accepted 4 claims the human rejected, all applying a real policy to the wrong case (a competitor's price treated as our price drop, a sale-item rule applied to every hoodie). They rejected 3 the human accepted (two polite offers of help, one "no price matching").
- **Decision:** Not reliable yet. The κ ≥ 0.6 target from week 2 is missed, and the store-channel rule did not help. Next: a judge rule for policies applied outside their condition, an explicit rule for polite offers, and a second annotator on the same sheet (`results/week3/judge_calibration/sample.csv`). Until then `unsupported_claims` is an estimate with unknown bias. Details: `results/week3/faithfulness/human_labels_notes.md`, `results/week3/judge_calibration/calibration.json`.

### Experiment 4: Abstention on the RAG pipeline

- **Hypothesis:** With store documents, the assistant answers what the documents cover and abstains on the rest, instead of abstaining on everything (week 2) or guessing (week 1).
- **Change:** 12 questions the documents cannot answer (for example a shop visit, stock left, the next sale, the admin password), and the 7 week 2 "unanswerable" cases the documents now answer.
- **Result:** All 12 unanswerable questions got the fixed reply with no unsupported claim (12 of 12, Wilson 0.76 to 1.00), including the shop-visit question behind last week's invented "visit a store location". 5 of the 7 now-answerable cases were answered correctly with citations. T21 (restock day) gave the fixed reply because the FAQ line on restock dates was not in the top 5 (retrieval). T06 (returning shoes after two weeks) was answered correctly, but judge v2 rejected it because the passage says items, not shoes (judge too literal).
- **Decision:** Keep the prompt. Add T21 to the retrieval questions and count T06 in the judge's false rejections.

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

One of two conversations done. Selim talked with a software developer who runs a small streetwear shop on Instagram, selling limited drops through the ikas platform. It was an informal conversation in a live-stream chat in the week of 16 Nov 2026, with follow-up questions in Instagram chat. Notes were written up afterwards and are summarized here, not quoted. His name and shop are left out.

- **What he does by hand today.** Under half an hour a day in a normal week. In a drop week, Instagram messages take two to three hours a day: when the drop opens, whether a size is left, payment taken but no order, and in the following week whether the item will restock. ikas already sends shipping notifications, but customers still ask. Exchanges are rarely possible because limited stock is gone, so he refunds by hand in the ikas panel.
- **What he would let an assistant answer.** Drop time, size chart, stock and shipping status, all data his system already has. Not restock promises, return approvals or stuck payments. His worst case is the assistant inventing a restock in front of his community.
- **What he would pay.** His first reaction is that he could build it himself, since an answer costs very little in API fees. He would pay 500 to 750 TL a month if setup and upkeep were fully handled, but prefers paying per use, because some months have no drop. At 1 to 2 TL per answer he would question the margin.
- **What worries him.** A black box. He wants logs of what was answered and the ability to change the rules and prompts. Also where customer data is stored under KVKK, and whether the system holds up when hundreds of messages arrive at once on drop day.

What it changes for us:

1. His most common questions (size in stock, order status) cannot be answered from documents, so the week 4 data tool comes first.
2. Our assistant already refuses to invent restock dates, which matches his biggest fear. That stays a test case.
3. Payment problems go straight to a person and are never answered by the assistant.
4. An answer costs us about $0.00012, well under one kuruş, so usage-based pricing is realistic. The pricing hypothesis is the week 5 product task.
5. Logged runs and versioned prompts are already how we work. Drop-day bursts are a real risk: in week 2, rate limits made about half of our model calls fail.

The second conversation is still open.

## 8. Contributions

| Member | Role | What they did this week | Commits or files | Hours |
|---|---|---|---|---|
| Orhun Cerit | Data and retrieval lead | Retrieval question set (W3.5), retrieval evaluation with the three-mode ablation, price-change rule in the sale policy | 91ff132, a822654, c60d559, a0d701c | not reported |
| Nurettin Selim Özyılmaz | Agent and tools lead | Store documents, chunking, hybrid search, reranker, cited answers, live demo, architecture page, embeddings view, faithfulness evaluation and failure labels, abstention set and re-measure, judge v2 and the calibration sample, T23 and T34 label review, 40 human labels, the product-track conversation, week 3 scoreboard, this report | PR #7 | not reported |
| Yakup Berk Öngül | Evaluation and safety lead | No week 3 work in the repository | none | not reported |

## 9. AI tools used

| Tool | Used for |
|---|---|
| Claude Code (Selim) | Drafted the store documents, retrieval, reranker, citation, demo, embedding, faithfulness and scoreboard code with tests, the architecture page and this report. Re-checked two of Selim's labels at his request, and no label changed |
| Groq `openai/gpt-oss-20b` | The model under test, the classifier and the faithfulness judge |
| Claude (Orhun) | Learning the course topics, drafting the retrieval question set and src/evaluate_retrieval.py. Orhun checked every question, gold passage and result |
| Berk | Not reported |

## 10. Next week

| Priority | Metric it should move | Expected change |
|---|---|---|
| 1. A generated product catalogue to about 10,000 chunks, with near-identical codes, then re-run the retrieval evaluation | `hit_at_5`, `mrr` | `hit_at_5` stays at or above 0.90 at 10,000 chunks |
| 2. Three tools (document search, order data, sandbox return) and an agent loop with step, token and time limits (W4.1, W4.2) | `task_success`, cost per task | First measurement on at least 10 multi-step tasks |
| 3. Fix the judge where people disagree with it: a rule for policies applied outside their condition and one for polite offers, then the same 20-claim sheet labelled by a second annotator, plus the fixes for R22, R29, R13 and T21 | judge κ, `unsupported_claims` | κ ≥ 0.6 against both annotators |
