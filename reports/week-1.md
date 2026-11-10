# Weekly report

| Field | Value |
|---|---|
| Team | [TEAM 6] |
| Use case | UC1 |
| Week | 1 |
| Repository | [https://github.com/berkongul/AIC390Project/] |
| Commit tag | week-1 (to be created) |
| Presenter | [NAME] |
| Members and roles | [Name] (data and retrieval lead); [Name] (agent and tools lead); [Name] (evaluation and safety lead) |

## 1. Summary

During Week 1, we selected UC1 and defined the scope of an online store customer support assistant. We prepared 25 labeled synthetic customer messages, documented the proposed data sources, and implemented a Python baseline runner using the Groq API. We completed 75 API requests across three temperature settings (0.0, 0.7, and 1.2). All 75 requests returned successfully, with no API errors. We recorded responses, token usage, and latency for further evaluation. Response correctness has not yet been formally measured.

## 2. Deliverables

| ID | Status | Evidence | Note |
|---|---|---|---|
| W1.1 | partial | `docs/team_agreement.md` | Complete and confirm team-specific details |
| W1.2 | partial | `docs/use_case_brief.md` | Finalize remaining product details |
| W1.3 | done | `tests/week1_inputs.json` | 25 labeled synthetic customer requests |
| W1.4 | done | `docs/data_inventory.md` | Planned documents, databases, and API sources |
| W1.5 | done | `src/baseline.py`, `results/baseline_results.csv` | 75 requests completed at three temperatures |
| W1.6 | partial | `docs/cost_estimate.md`, baseline CSV | Measured token counts available; update pricing calculations |
| W1.7 | done | `docs/predicted_failures.md` | Six predicted failure risks documented |
| W1.8 | partial | GitHub repository and `README.md` | Repository created; `week-1` tag still required |

## 3. Scoreboard

```json
{
  "week": 1,
  "test_set_size": 25,
  "e2e_accuracy": {"value": null, "ci95": null, "n": null, "script": null},
  "abstention_correct": {"value": null, "ci95": null, "n": null, "script": null},
  "unsupported_claims": {"value": null, "n": null, "script": null},
  "hit_at_5": {"value": null, "n": null, "script": null},
  "mrr": {"value": null, "n": null, "script": null},
  "task_success": {"value": null, "n": null, "script": null},
  "pass_k": {"k": null, "value": null, "n": null, "script": null},
  "injection_success": {"value": null, "n": null, "script": null},
  "cost_per_task_usd": null,
  "latency_p50_s": 0.417,
  "spend_week_usd": null,
  "spend_total_usd": null
}
```

Changes to any test set this week: none.

The baseline recorded 75 successful API responses, 12,177 input tokens, 10,973 output tokens, and 23,150 total tokens. API completion success is not equivalent to answer accuracy.

## 4. Experiments

### Experiment 1: Temperature sensitivity

- **Hypothesis:** Higher temperature may increase response variability and the likelihood of unsupported claims.
- **Change:** Temperature only (0.0, 0.7, 1.2), using the same system prompt and 25 test inputs.
- **Model:** `openai/gpt-oss-20b`, accessed through the Groq API.
- **Result:** All 25 requests succeeded at each temperature, producing 75 successful responses and zero API errors. The experiment recorded 23,150 tokens in total. Response correctness and unsupported-claim rates have not yet been formally evaluated.
- **Uncertainty:** The experiment used synthetic inputs and a single execution per input-temperature combination. No statistical confidence interval for response quality is available.
- **Decision:** Investigate response quality before selecting a final temperature. Retain the recorded baseline as a reference for future experiments.

## 5. Failure analysis

No API request failures occurred during the completed Groq baseline. However, the experiment has not yet established whether every response is factually correct, appropriately cautious, or consistent with store policies.

| # | Input (short) | What happened | Root cause | Fix (done or planned) |
|---|---|---|---|---|
| 1 | Order-status requests | Responses were generated without access to live order records | No connected order database | Add an authorized order-status lookup tool |
| 2 | Store policy questions | Policy accuracy has not been independently verified | No authoritative policy retrieval | Ground responses in versioned policy documents |
| 3 | Customer requests at different temperatures | Responses were generated, but consistency has not been formally scored | Sampling variability | Compare outputs using a documented evaluation rubric |

These are limitations and planned investigations, not three confirmed incorrect answers.

## 6. Response to last week's feedback

none this week

## 7. Product track

Our initial target customer is a small online retailer whose staff manually handle order, return, shipping, and product questions. The proposed assistant aims to reduce repetitive support work while avoiding unsupported claims about customer orders, refunds, and store policies.

The Week 1 baseline demonstrates that the model can generate responses to synthetic customer messages. It does not yet demonstrate reliable access to actual store information.

Evidence: `docs/use_case_brief.md`.

## 8. Contributions

| Member | Role | What they did this week | Commits or files | Hours |
|---|---|---|---|---|
| [NAME] | Data and retrieval | [ACTUAL WORK] | [ACTUAL FILES] | [HOURS] |
| [NAME] | Agent and tools | [ACTUAL WORK] | [ACTUAL FILES] | [HOURS] |
| [NAME] | Evaluation and safety | [ACTUAL WORK] | [ACTUAL FILES] | [HOURS] |

## 9. AI tools used

| Tool | Used for |
|---|---|
| ChatGPT | Assisting with starter code, documentation, experiment setup, and report drafting; outputs require team review |
| Gemini API | Initial baseline experimentation; not used for the final successful 75-request dataset |
| Groq API (`openai/gpt-oss-20b`) | Generating the final 75 baseline responses at three temperatures |

## 10. Next week

| Priority | Metric it should move | Expected change |
|---|---|---|
| 1 | Classification accuracy | Implement a structured JSON classifier and validate outputs |
| 2 | Response accuracy | Develop versioned prompts and at least 40 expected-output tests |
| 3 | Injection success | Test adversarial messages and document observed failures |
