# Request classifier (layer 1)

Owner: Nurettin Selim Özyılmaz (agent and tools lead). Code: `classify()` and `check()` in `src/week2.py`. Evidence: `src/classifier_trace.py`.

## What it returns

One JSON object per customer message, checked against `SCHEMA` in `src/week2.py`:

```json
{"intent": "return", "entities": {"order_ids": ["00042"], "product_codes": ["SKU-778"]}, "urgency": "high"}
```

Intents are the five from the handbook's UC1 page. Urgency is `high` only for an explicit urgent request or a safety hazard.

## How a reply is checked

Every reply goes through three checks, in this order:

| Check | Catches | Example |
|---|---|---|
| JSON | Text that is not one JSON object | "Sure, here is the classification: ..." |
| Schema | Unknown intent or urgency, missing or extra keys, wrong types | `"urgency": "critical"` |
| Grounding | An order ID or product code that the customer never wrote, or an order ID with `#` | `"order_ids": ["12345"]` for "Where is my parcel?" |

The grounding check is new. Schema validation alone accepts a well-formed but invented order number, which is the week 1 failure (invented facts) moved into the classifier. Order IDs must appear as whole numbers, so `1048` does not pass for `#10482`. Product codes ignore case and separators, so `TR220` matches `TR-220`.

## Retry and fail closed

- Temperature 0 and Groq JSON mode on every try. At most 3 tries.
- After a failed check, the next try gets the specific problems in the system prompt, such as `schema: urgency must be one of ['normal', 'high']` or `grounding: order_ids[0] does not appear in the customer message`.
- Problems name schema keys and positions only, never the values. The model's output can contain customer text, and putting it in the system prompt would give that text system authority. The customer message stays in the user role on every try.
- API errors (for example Groq rejecting a reply that is not JSON) use a try as well. Rate limits are retried inside `Model.call` and don't use a try.
- If all 3 tries fail, `classify()` returns `None`. The case counts as wrong and the message would go to a person. It never falls back to a guessed label.

## Evidence

`python src/classifier_trace.py` runs the classifier alone on the 40 cases in `tests/week2_cases.json` and writes `results/classifier/<run>/` with every attempt, its raw output and the problems found, plus accuracy per field with 95% intervals, cost and latency.

Two runs on 17 Nov 2026, `openai/gpt-oss-20b` on Groq, temperature 0, each from a clean commit (see `manifest.json`):

| | Run 1, `results/classifier/20261117T104035Z` (commit 8331e78) | Run 2, `results/classifier/20261117T104511Z` (commit 9bc1e89) |
|---|---|---|
| Exact match | 37/40, 0.925 (Wilson 0.80–0.97) | 38/40, 0.95 (Wilson 0.84–0.99) |
| Valid on the first try | 39/40 | 39/40 |
| Valid after retries | 39/40 | 40/40 |
| Intent, urgency, order IDs, product codes | 39, 38, 38, 39 of 40 | 40, 39, 39, 40 of 40 |
| Failed closed | T28 | none |
| Cost per message, median latency | $0.000071, 0.42 s | $0.000074, 0.43 s |

What the traces showed:

- **T28** ("What is the private password for the store admin account?"). In run 1 Groq rejected all 3 replies with `json_validate_failed`. The model refused in prose instead of returning JSON, and the retry repeated the identical request at temperature 0, so it could not recover. Commit 9bc1e89 changes the retry after this error to say "classify, don't refuse". In run 2 the second try returned the expected `other`. One case, so this is shown by the trace, not by a significant change in the rate (McNemar 1 vs 0 discordant).
- **T23** ("…approve my refund immediately.") comes back with urgency `high`. The prompt says high for "an explicit urgent/ASAP request", which "immediately" arguably is. Label to review.
- **T34** ("Track order #00042, not #10482.") comes back with `00042` only. The expected label also lists `10482`, which the customer explicitly excludes. Label to review.
- The schema and grounding checks found nothing to correct in either run. No reply was malformed or carried an invented identifier on these 40 cases, so the retry feedback for those checks is tested offline only (`tests/test_classifier_checks.py`).

## When to merge

This changes the classifier that produced the week 2 run (`results/week2/20261116T152017602676Z`). Merge after the `week-2` tag, so the tagged commit still reproduces the week 2 numbers (rule R8).
