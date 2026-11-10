# Weekly report

| Field | Value |
|---|---|
| Team | [TEAM NAME] |
| Use case | UC1 |
| Week | 1 |
| Repository | [GITHUB URL] |
| Commit tag | week-1 (create after completing evidence) |
| Presenter | [NAME] |
| Members and roles | [Name] (data and retrieval lead); [Name] (agent and tools lead); [Name] (evaluation and safety lead) |

## 1. Summary

We selected UC1, defined an online store support assistant, drafted a synthetic-data inventory, and prepared 25 labeled customer messages and a Gemini baseline runner. **Planned:** 75 model calls at three temperatures. **Measured successful calls:** [FILL AFTER RUN]. No results are claimed before execution.

## 2. Deliverables

| ID | Status | Evidence | Note |
|---|---|---|---|
| W1.1 | partial | docs/team_agreement.md | Team must agree and complete fields |
| W1.2 | partial | docs/use_case_brief.md | Choose product name |
| W1.3 | done | tests/week1_inputs.json | 25 labeled synthetic requests |
| W1.4 | done | docs/data_inventory.md | Planned data, documents, API |
| W1.5 | partial | src/baseline.py | Run 75 calls; analyze differences |
| W1.6 | partial | docs/cost_estimate.md | Fill in verified pricing and measured tokens |
| W1.7 | done | docs/predicted_failures.md | Six predicted risks |
| W1.8 | partial | README.md | Create repo, commit and week-1 tag |

## 3. Scoreboard

```json
{
  "week": 1,
  "test_set_size": null,
  "e2e_accuracy": {"value": null, "ci95": null, "n": null, "script": null},
  "abstention_correct": {"value": null, "ci95": null, "n": null, "script": null},
  "unsupported_claims": {"value": null, "n": null, "script": null},
  "hit_at_5": {"value": null, "n": null, "script": null},
  "mrr": {"value": null, "n": null, "script": null},
  "task_success": {"value": null, "n": null, "script": null},
  "pass_k": {"k": null, "value": null, "n": null, "script": null},
  "injection_success": {"value": null, "n": null, "script": null},
  "cost_per_task_usd": null,
  "latency_p50_s": null,
  "spend_week_usd": null,
  "spend_total_usd": null
}
```

Changes to any test set this week: none

## 4. Experiments

### Experiment 1: Temperature sensitivity

- **Hypothesis:** Increasing temperature may increase response variability and unsupported claims.
- **Change:** Temperature only (0, 0.7, 1.2), fixed system prompt and 25 inputs.
- **Result:** [FILL WITH ACTUAL COUNTS, COMPARISON AND UNCERTAINTY AFTER RUN; DO NOT GUESS].
- **Decision:** [keep, revert, or investigate further AFTER ANALYSIS].

## 5. Failure analysis

| # | Input (short) | What happened | Root cause | Fix (done or planned) |
|---|---|---|---|---|
| 1 | [OBSERVED TEST ID] | [OBSERVED RESPONSE] | [CLASSIFY] | [FIX] |
| 2 | [OBSERVED TEST ID] | [OBSERVED RESPONSE] | [CLASSIFY] | [FIX] |
| 3 | [OBSERVED TEST ID] | [OBSERVED RESPONSE] | [CLASSIFY] | [FIX] |

## 6. Response to last week's feedback

none this week

## 7. Product track

Our first customer is a small online retailer whose staff manually answer order, return and product questions. The proposed product reduces repetitive support work while escalating unverified order details and refund decisions. Evidence: `docs/use_case_brief.md`.

## 8. Contributions

| Member | Role | What they did this week | Commits or files | Hours |
|---|---|---|---|---|
| [NAME] | Data and retrieval | [ACTUAL WORK] | [ACTUAL COMMIT/FILE] | [ACTUAL HOURS] |
| [NAME] | Agent and tools | [ACTUAL WORK] | [ACTUAL COMMIT/FILE] | [ACTUAL HOURS] |
| [NAME] | Evaluation and safety | [ACTUAL WORK] | [ACTUAL COMMIT/FILE] | [ACTUAL HOURS] |

## 9. AI tools used

| Tool | Used for |
|---|---|
| ChatGPT | Drafting starter code and documentation; team must review and verify |
| Gemini API | [ONLY IF ACTUALLY USED: baseline responses] |

## 10. Next week

| Priority | Metric it should move | Expected change |
|---|---|---|
| 1 | Classification accuracy | Implement structured JSON classifier and validate outputs |
| 2 | Response accuracy | Build versioned prompts and 40+ expected-output tests |
| 3 | Injection success | Test adversarial messages and document failures |
