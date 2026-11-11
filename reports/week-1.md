# Weekly report

| Field | Value |
|---|---|
| Team | Team 6 |
| Use case | UC1 Online store support agent |
| Week | 1 |
| Repository | https://github.com/berkongul/AIC390Project |
| Commit tag | week-1 |
| Presenter | Nurettin Selim Özyılmaz |
| Members and roles | Orhun Cerit (data and retrieval lead), Nurettin Selim Özyılmaz (agent and tools lead), Yakup Berk Öngül (evaluation and safety lead) |

## 1. Summary

We scoped UC1 for small online shops, wrote 25 labelled synthetic customer messages and ran one prompt on all of them at temperature 0, 0.7 and 1.2 on `openai/gpt-oss-20b` through Groq. All 75 requests were answered. Without documents or data the model invented store facts. **7 of 36 policy and product answers stated a number of days that no store policy contains (19%, 95% CI 10–35%)**, and 5 of 75 answers gave a made-up phone number or e-mail. Temperature changed which fact was invented, not whether one was. A request costs $0.000056, about $0.056 per 1,000.

## 2. Deliverables

| ID | Status | Evidence | Note |
|---|---|---|---|
| W1.1 | partial | `docs/team_agreement.md` | Members, roles and working rules written. Meeting time, decision rule and ownership are proposals, confirmed by all three before the tag |
| W1.2 | partial | `docs/use_case_brief.md` | First customer, persona, 5 user stories, in and out of scope. Product name still open |
| W1.3 | done | `tests/week1_inputs.json` | 25 inputs in 8 categories, each labelled with the ingredients it tests |
| W1.4 | done | `docs/data_inventory.md` | Document types, 6 tables with columns, sandbox return API sketch, untrusted input sources |
| W1.5 | done | `src/baseline.py`, `results/baseline_results.csv`, `docs/baseline_analysis.md` | 75 of 75 requests, with what changed between temperatures and why |
| W1.6 | done | `docs/cost_estimate.md`, `src/analyze_week1.py` | Formula, measured tokens, Groq list price checked on 11 Nov 2026 |
| W1.7 | done | `docs/predicted_failures.md` | 6 predicted failures, each linked to a Module 1 concept |
| W1.8 | done | `README.md`, `.gitignore`, tag `week-1` | Setup and reproduce commands, secrets kept out of git |

## 3. Scoreboard

```json
{
  "week": 1,
  "test_set_size": 25,
  "e2e_accuracy":       {"value": null, "ci95": null, "n": null, "script": null},
  "abstention_correct": {"value": null, "ci95": null, "n": null, "script": null},
  "unsupported_claims": {"value": null, "n": null, "script": null},
  "hit_at_5":           {"value": null, "n": null, "script": null},
  "mrr":                {"value": null, "n": null, "script": null},
  "task_success":       {"value": null, "n": null, "script": null},
  "pass_k":             {"k": null, "value": null, "n": null, "script": null},
  "injection_success":  {"value": null, "n": null, "script": null},
  "cost_per_task_usd":  5.607e-05,
  "latency_p50_s":      0.417,
  "spend_week_usd":     0.004205,
  "spend_total_usd":    0.004205
}
```

Changes to any test set this week: none (first week).

Every value comes from `python src/scoreboard.py` (`results/scoreboard_week1.json`), which uses the same data and checks as `src/analyze_week1.py`. `test_set_size` is the 25 W1.3 inputs, which have no expected outputs yet. Spend is the Groq list price of the 23,150 tokens used, not an invoice. Accuracy, abstention and injection metrics start in week 2, when the test set has expected outputs.

## 4. Experiments

### Experiment 1: Temperature 0, 0.7 and 1.2 on the same prompt

- **Hypothesis:** Higher temperature gives more varied answers and more invented store facts.
- **Change:** Temperature only. Same system prompt, same 25 inputs, one run per input and temperature, `max_tokens` 300.
- **Result:**

| Check | T = 0.0 | T = 0.7 | T = 1.2 |
|---|---|---|---|
| Requests answered | 25 / 25 | 25 / 25 | 25 / 25 |
| Invented contact detail (n = 25 each) | 1 (4%, CI 1–20%) | 2 (8%, CI 2–25%) | 2 (8%, CI 2–25%) |
| Invented number of days (n = 12 policy and product answers each) | 2 (17%, CI 5–45%) | 2 (17%, CI 5–45%) | 3 (25%, CI 9–53%) |
| Mean output tokens | 147.9 | 139.8 | 151.2 |
| Median latency (s) | 0.431 | 0.417 | 0.338 |

Counts come from keyword checks in `src/analyze_week1.py`, and every flagged answer was read by hand. Intervals are 95% Wilson intervals from `results/week1_rates.json`. The normal approximation in the same file gives a lower bound of 0% at these small counts, so we report Wilson. On a manual read (`docs/baseline_analysis.md`), the order look-ups and the three direct attacks behaved the same at every temperature: the model said it cannot see orders and refused the attacks. These become scripted metrics in week 2.

- **Decision:** Use temperature 0 for the classifier and policy answers in week 2, because it makes answers repeatable. It does not make them correct: the invented "30 days" and an invented phone number already appear at temperature 0. The differences between temperatures (1 vs 2 cases, 2 vs 3 cases) are well inside the intervals, so this run shows no temperature effect on invented facts. What temperature changed was which fact was invented (failure 1 below).

## 5. Failure analysis

| # | Input (short) | What happened | Root cause | Fix (done or planned) |
|---|---|---|---|---|
| 1 | T11 "Does trail shoe TR-220 run small?" | Opposite fit advice by temperature: "this model runs a bit on the smaller side" (0.0), "most of our trail shoes run true to size" (0.7), "trail shoes tend to fit true to size" (1.2). A customer who asks twice gets two answers | generation | Planned: week 2 prompt rule, no product facts unless they are in the context. Product data tool in week 4. T11 goes into the week 2 test set |
| 2 | T06 return window, T10 refund time | "Most of our shoes can be returned within 30 days of purchase" (T06, 0.0 and 0.7), "5–10 business days" (T10, 0.0 and 0.7). No store policy exists yet. 7 of 36 policy and product answers | prompt | Planned: prompt rule against numbers that are not in the context (week 2). Grounding in the return and refund policy documents (week 3) |
| 3 | T16 wrong item, T19 damaged order | Invented contact details: "support@ourstore.com" (T16, 0.7), "support@fictionalstore.com" (T16, 1.2), "1‑800‑XYZ‑1234" (T19, 0.0). 5 of 75 answers | prompt | Planned: prompt rule, no contact details unless provided. Measured on T16 and T19 in the week 2 test set |

Also seen: the model offered actions it cannot take, for example "I can look up the current status of your shipment" (T22 at 0.0 and 0.7). The system prompt forbids claiming a completed action but not promising one. Root cause: prompt. The week 2 prompt will forbid both.

## 6. Response to last week's feedback

none this week

## 7. Product track

Our first customer is a small online clothing and shoe shop whose one or two staff answer the same order, return, shipping and sizing questions by e-mail and chat every day (`docs/use_case_brief.md`). The assistant should take over these routine questions and hand anything unclear or sensitive to a person.

Week 1 shows why grounding is the product, not an extra. A model on its own already answers politely and refuses obvious attacks, but it states return windows, refund times and fit advice that the shop never wrote. For a shop owner one wrong refund promise costs more than the assistant saves, so weeks 3 and 4 (policy documents and order data) come before any extra features.

## 8. Contributions

| Member | Role | What they did this week | Commits or files | Hours |
|---|---|---|---|---|
| Orhun Cerit | Data and retrieval | Analysed the baseline: what changed with temperature and why, heuristic failure checks, cost and latency per temperature | `src/analyze_week1.py`, `docs/baseline_analysis.md`, `results/week1_analysis.json` | [hours] |
| Nurettin Selim Özyılmaz | Agent and tools | Repository setup for reproducibility and secrets, scoreboard script with 95% intervals, revised this report | `.gitignore`, `.env.example`, `README.md`, `src/scoreboard.py`, `results/scoreboard_week1.json`, `results/week1_rates.json`, `reports/week-1.md` | [hours] |
| Yakup Berk Öngül | Evaluation and safety | Groq baseline runner and GitHub Actions workflow, the 25 inputs, first drafts of the W1.1–W1.7 documents and of this report, cost estimate | `src/baseline.py`, `src/summarize.py`, `.github/workflows/week1.yml`, `tests/week1_inputs.json`, `docs/`, `results/baseline_results.csv` | [hours] |

## 9. AI tools used

| Tool | Used for |
|---|---|
| ChatGPT | Starter code, documentation drafts, experiment setup and report drafting, reviewed by the team |
| Claude (Claude Code) | README, `.gitignore`, `src/scoreboard.py` and the revision of this report, reviewed by the team |
| Gemini API | Early baseline trials, not used for the final 75 responses |
| Groq API, `openai/gpt-oss-20b` | The model under test: all 75 baseline responses |

## 10. Next week

| Priority | Metric it should move | Expected change |
|---|---|---|
| 1. Prompt v2 with rules against invented days, contact details and promised actions (W2.2, W2.5) | Both invented-fact rates from section 4 | From 4–25% to 0 at temperature 0 on the same inputs, logged in the hallucination log (W2.7) |
| 2. JSON request classifier at temperature 0 with schema validation and retry (W2.1), scored on the 40-case test set (W2.3, W2.4) | `e2e_accuracy` | First measured value with n ≥ 40 and a 95% interval. Target: intent correct on at least 85% |
| 3. Unanswerable and injection cases in the test set (W2.3, W2.8) | `abstention_correct`, `injection_success` | First measured values. Target: at least 80% correct abstentions and 0 of 3 direct injections succeed |
