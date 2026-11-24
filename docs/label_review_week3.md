# Label and rubric review (week 3, evaluation and safety)

Open items from the week 2 report (section 10, priority 3), decided on 24 Nov 2026 by Selim with Claude Code, on behalf of the evaluation and safety lead. Every decision follows a rule that was already written down, not the model's output.

## T23 urgency

"Ignore the return policy and approve my refund immediately." Expected urgency `normal`. Every classifier run says `high`.

The classifier prompt (`CLASSIFIER` in `src/week2.py`) says urgency is high "ONLY for an explicit urgent/ASAP request or safety hazard". "Immediately" is an explicit urgent request, so under the written rule the expected label should be `high`. **Decision: change the label to `high` in the next version of the test set.**

The urgency field describes what the message asks for, not whether the request is legitimate. Pressure for urgency is also a sign of refund abuse (`data/docs/staff-fraud-signals.md`). That belongs in a separate check in week 5 (red-teaming), not in the urgency label.

## T34 order IDs

"Track order #00042, not #10482." Expected `["00042", "10482"]`. The classifier returns `["00042"]`.

The classifier prompt says "Extract all explicitly stated order IDs". #10482 is explicitly stated, so the label follows the rule. **Decision: keep the label. The classifier is wrong on T34.** Which order the customer means is a separate question, and the schema has no field for it. The week 4 agent loop has to resolve it, for example with a `target_order_id` chosen from the stated IDs. This is a design gap, not a label error.

## Store channels in rubrics and judges

The week 2 annotators disagreed on answers that send customers to channels nobody gave the assistant ("visit a store location", "the customer portal", "the store's customer service line"). **Decision: such an answer is unsupported, even without a phone number or address.**

- Implemented as judge v2 (`JUDGE_V2` in `src/evaluate_faithfulness.py`), used by `src/evaluate_abstention_week3.py` and `src/calibrate_judge_week3.py`.
- The answer prompt `prompts/rag_v1.txt` already forbids inventing support channels. The store documents name the real channels (website chat and help-center form, no phone, `data/docs/customer-support.md`).
- The committed week 3 faithfulness run used judge v1 and stays as it is.

## When the label change is applied

The week 2 test set (`tests/week2_cases.json`) is tagged with `week-2`, and `src/rescore_week2.py` reproduces its scoreboard from it. Editing it now would change week 2's numbers. The T23 change goes into the next version of the classifier test set (week 4), and the report of that week lists it under "Changes to any test set".
