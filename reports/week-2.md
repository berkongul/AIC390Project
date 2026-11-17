# Weekly report — draft, not ready for submission

| Field | Value |
|---|---|
| Team | Team 6 |
| Use case | UC1 Online store support agent |
| Week | 2 |
| Repository | https://github.com/berkongul/AIC390Project |
| Commit tag | week-2 (not created) |
| Presenter | Yakup Berk Öngül (proposed rotation; confirm) |

## 1. Summary

Implemented a temperature-zero JSON classifier with schema validation and bounded retry, three versioned main prompts, a 40-case labeled dataset and a one-command evaluation harness. Offline validation and unit tests pass. Real Groq measurements, the 20 human labels and judge calibration are pending. We preserve Week 1 evidence and extract 12 candidate hallucination observations for review. No model accuracy, significance, safety improvement or spending is claimed before a live run.

## 2. Deliverables

| ID | Status | Evidence | Remaining |
|---|---|---|---|
| W2.1 | partial | [classifier](../src/week2.py), [offline tests](../tests/test_week2.py) | Demonstrate real model output and retry traces |
| W2.2 | done | [v1](../prompts/v1.txt), [v2](../prompts/v2.txt), [v3](../prompts/v3.txt) | Confirm six-block terminology against Module 2 slides |
| W2.3 | done | [40 cases](../tests/week2_cases.json) | Team review of draft expected labels |
| W2.4 | partial | [harness](../src/evaluate_week2.py), [workflow](../.github/workflows/week2.yml) | Save full live-run evidence |
| W2.5 | partial | [statistical functions](../src/week2_stats.py) | Three measured accuracies, intervals and paired McNemar result |
| W2.6 | done | [labels, Berk](../results/week2/20261116T152017602676Z/human_labels.csv), [labels, Selim](../results/week2/20261116T152017602676Z/human_labels_selim.csv), [calibration](../results/week2/20261116T152017602676Z/judge_calibration.json), [calibration, Selim](../results/week2/20261116T152017602676Z/judge_calibration_selim.json), [notes](../results/week2/20261116T152017602676Z/human_labels_notes.md) | Two annotators, 20 rows. Berk passed all 20 (agreement with the judge 20/20, κ undefined). Selim failed 4 answers that invent store features (16/20, κ = 0.00). The rubric must say whether that counts as an invented contact |
| W2.7 | partial | [12 source-linked candidates](../docs/hallucination_log.json) | Verify at least 10 actual examples, exact claims and final types |
| W2.8 | partial | [T23, T24, T29](../tests/week2_cases.json) | Run attacks and record actual outcomes |

## 3. Scoreboard

```json
{
  "week": 2,
  "test_set_size": 40,
  "e2e_accuracy":       {"value": 0.875, "ci95": [0.773, 0.977], "ci95_wilson": [0.739, 0.945], "n": 40, "count": 35, "script": "src/rescore_week2.py"},
  "abstention_correct": {"value": 1.0, "ci95": [1.0, 1.0], "ci95_wilson": [0.701, 1.0], "n": 9, "count": 9, "script": "src/rescore_week2.py"},
  "unsupported_claims": {"value": null, "n": null, "script": null},
  "hit_at_5":           {"value": null, "n": null, "script": null},
  "mrr":                {"value": null, "n": null, "script": null},
  "task_success":       {"value": null, "n": null, "script": null},
  "pass_k":             {"k": null, "value": null, "n": null, "script": null},
  "injection_success":  {"value": 0.0, "n": 3, "script": "src/rescore_week2.py"},
  "cost_per_task_usd":  0.00012456,
  "latency_p50_s":      1.223,
  "spend_week_usd":     0.025278,
  "spend_total_usd":    0.029483
}
```

Changes to any test set this week: the 25 week 1 inputs now have expected outputs, and 15 synthetic cases were added (40 in total). Week 1 heuristic failure rates are not directly comparable to week 2 accuracy.

Every value comes from `python src/rescore_week2.py`, which reads the complete run `results/week2/20261116T152017602676Z` (120 records, made by `src/evaluate_week2.py`) without new API calls and writes `results/scoreboard_week2.json`. The selected prompt is v3, tied with v2 on e2e_accuracy (35 of 40 each, McNemar 2 vs 2 discordant, p = 1.0).

- `abstention_correct` counts an unanswerable case when the answer passes the judge and says it cannot give the fact or action. The judge's own `abstained` flag was false on all 120 answers, including plain "I can't confirm that" answers, so it is not used (details in `rescored.json`).
- `cost_per_task_usd` is the Groq list price ($0.075 input and $0.30 output per million tokens, checked 11 Nov 2026) of the v3 classifier and answer calls, per task. Failed calls (322 of 681, mostly rate limits) return no token usage and are left out.
- `latency_p50_s` is model time per task. The run's own figure of 20.0 s also counts the 15 s pause the script adds after every call.
- `spend_total_usd` adds week 1 spend ($0.004205). Spend is list price, not an invoice.
- The judge was checked against two annotators on 20 rows (W2.6). Berk agreed with it on all 20. Selim failed four answers that point customers to store features nobody gave the assistant (a physical store, a customer portal, a phone line, website contacts), which the judge passed (κ = 0.00). If the rubric counts these as invented contacts, judge-based numbers here are too high.

## 4. Experiments

Planned hypothesis: explicit evidence boundaries reduce invented facts and action promises. Compare v1, v2 and v3 at temperature zero on identical cases, with one fixed classifier and judge. Report each accuracy with n and Wilson 95% intervals; the machine output also includes the handbook normal intervals. Apply an exact paired McNemar test to the best two, documenting discordant counts and the exploratory selection. Results and decisions are pending; no winning prompt is declared.

Second planned experiment: compare the judge's pass/fail output with 20 independent human labels. Report agreement and Cohen's kappa, including undefined kappa for constant labels. Results pending. See [method](../docs/week2_method.md) for the rubric, metrics, limitations and commands.

## 5. Failure analysis

These are observed Week 1 failures motivating Week 2 changes, not claimed Week 2 outcomes.

| Input | What happened in Week 1 | Root cause | Implemented change; verification |
|---|---|---|---|
| T11, TR-220 fit | Conflicting unsupported fit advice across temperatures | generation | V2/V3 prohibit unsupported product facts; live regression pending |
| T06/T10, return/refund timeframe | Unsupported return window and refund durations | prompt | Explicit evidence boundary; expected-output cases retained; live regression pending |
| T16/T19, wrong/damaged item | Unsupported contact details and action promises | prompt | Forbid invented contacts and promised checks/forwarding; live regression pending |

Raw examples are linked by test ID and temperature in the hallucination candidate log. Team review must confirm types and remove false positives.

## 6. Response to last week's feedback

Instructor feedback has not been supplied; team must enter the actual points. Week 1's own priorities are addressed by explicit factuality constraints, schema validation/retry and expanded abstention/adversarial coverage. Their measured effect is pending.

## 7. Product track

No specific Week 2 product-track task. Scope remains the small clothing/shoe store described in [use case brief](../docs/use_case_brief.md). No new interviews or customer evidence are claimed.

## 8. Contributions

| Member | Work and evidence | Hours |
|---|---|---|
| Orhun Cerit | To be recorded by the team | To be recorded |
| Nurettin Selim Özyılmaz | Agent and tools lead. Review of the week 2 run. `src/rescore_week2.py` and `tests/test_rescore_week2.py`: cost per task, spend and model-time latency from the saved run, the abstention and injection metrics, and this scoreboard. Week 2 workflow (`.github/workflows/week2.yml`) and price settings in `.env.example`. Second annotator for W2.6 (20 labels), calibration for both annotators and the comparison between them | To be recorded |
| Yakup Berk Öngül | To be recorded by the team; Codex-assisted implementation prepared in this workspace | To be recorded |

Do not infer personal contributions or commit history from generated files. The local directory is a source archive snapshot without Git history.

## 9. AI tools used

Codex inspected the handbook and public Week 1 source, drafted code, prompts, synthetic tests, method notes and this report, and ran offline verification. Groq is configured as the model-under-test and LLM judge, but no Week 2 API results have been recorded yet. Human labels must be produced by people. Selim used Claude Code to review the week 2 run, draft `src/rescore_week2.py` with its tests and the workflow, and check every number in section 3 against the committed run.

## 10. Next week

| Priority | Metric | Target (not measurement) |
|---|---|---|
| Complete Week 2 live evaluation and human calibration before submission | e2e_accuracy, abstention_correct, kappa | Establish measured baselines; classifier exact match ≥85%, abstention ≥80% |
| Build at least 30 versioned policy/product documents and citation-capable RAG | hit_at_5, mrr | Establish first retrieval measurements; hit_at_5 target ≥80% |
| Add claim-level faithfulness evaluation and retrieval/generation failure attribution | unsupported_claims | Establish measured rate; target ≤10% |
