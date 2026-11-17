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
| W2.6 | partial | [judge and calibration command](../src/evaluate_week2.py) | 20 human labels and Cohen's kappa |
| W2.7 | partial | [12 source-linked candidates](../docs/hallucination_log.json) | Verify at least 10 actual examples, exact claims and final types |
| W2.8 | partial | [T23, T24, T29](../tests/week2_cases.json) | Run attacks and record actual outcomes |

## 3. Scoreboard

```json
{
  "week": 2,
  "test_set_size": 40,
  "e2e_accuracy": {
    "value": null,
    "ci95": null,
    "n": null,
    "script": null
  },
  "abstention_correct": {
    "value": null,
    "ci95": null,
    "n": null,
    "script": null
  },
  "unsupported_claims": {
    "value": null,
    "n": null,
    "script": null
  },
  "hit_at_5": {
    "value": null,
    "n": null,
    "script": null
  },
  "mrr": {
    "value": null,
    "n": null,
    "script": null
  },
  "task_success": {
    "value": null,
    "n": null,
    "script": null
  },
  "pass_k": {
    "value": null,
    "n": null,
    "script": null,
    "k": null
  },
  "injection_success": {
    "value": null,
    "n": null,
    "script": null
  },
  "cost_per_task_usd": null,
  "latency_p50_s": null,
  "spend_week_usd": null,
  "spend_total_usd": null
}
```

This is an explicitly unmeasured placeholder, also stored in [pending scoreboard](../results/scoreboard_week2_pending.json). Replace it with the selected live run's generated scoreboard; never treat the pending file as measured evidence. Accuracy denominators refer to the new 40-case dataset. Week 1's 25 inputs are preserved, but expected labels and 15 additional inputs are new, so Week 1 heuristic failure rates are not directly comparable to Week 2 accuracy. Human calibration is required before presenting LLM judgment as reliable correctness evidence.

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
| Nurettin Selim Özyılmaz | To be recorded by the team | To be recorded |
| Yakup Berk Öngül | To be recorded by the team; Codex-assisted implementation prepared in this workspace | To be recorded |

Do not infer personal contributions or commit history from generated files. The local directory is a source archive snapshot without Git history.

## 9. AI tools used

Codex inspected the handbook and public Week 1 source, drafted code, prompts, synthetic tests, method notes and this report, and ran offline verification. Groq is configured as the model-under-test and LLM judge, but no Week 2 API results have been recorded yet. Human labels must be produced by people.

## 10. Next week

| Priority | Metric | Target (not measurement) |
|---|---|---|
| Complete Week 2 live evaluation and human calibration before submission | e2e_accuracy, abstention_correct, kappa | Establish measured baselines; classifier exact match ≥85%, abstention ≥80% |
| Build at least 30 versioned policy/product documents and citation-capable RAG | hit_at_5, mrr | Establish first retrieval measurements; hit_at_5 target ≥80% |
| Add claim-level faithfulness evaluation and retrieval/generation failure attribution | unsupported_claims | Establish measured rate; target ≤10% |
