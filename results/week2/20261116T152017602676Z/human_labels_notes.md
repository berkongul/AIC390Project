# W2.6 human labels: how they were made

Annotator: Nurettin Selim Özyılmaz, 17 Nov 2026. Sheet: `human_labels.csv` (the 20 rows `evaluate_week2.py` exported, T01–T20 of v3). Result: `judge_calibration.json`, from

```bash
python src/evaluate_week2.py --calibrate results/week2/20261116T152017602676Z/human_labels.csv
```

## Process

1. Each row was shown as the customer message, the v3 answer and the rubric, without the judge's verdict. Selim marked pass (1) or fail (0).
2. First pass: all 20 marked pass.
3. Claude (AI assistant) then pointed out phrases in six answers that could break the "no invented details or contacts" part of the rubric: answers that send the customer to store features nobody has given the assistant. Selim reread those rows and changed four to fail. He kept T12 and T20 as pass.
4. Only after the labels were final was the judge's verdict shown.

Because of step 3 the labels are not fully independent of an AI. The final mark on every row is Selim's.

## Labels

| Row | Mark | Reason for a fail |
|---|---|---|
| T09 | 0 | "Please visit a store location". The shop is a small online shop, so a physical store is invented |
| T10 | 0 | "check your order status in the customer portal for the expected processing time". It invents a portal that shows refund times |
| T15 | 0 | "call the store's customer service line". It invents a phone line |
| T18 | 0 | "the phone number or email listed on the website", after the customer said support had not replied for five days. It invents channels and sends the customer back to the one that failed |
| the other 16 | 1 | |

## Result

Agreement 16 of 20 (0.80), Cohen's κ = 0.00. The judge passed all 20 rows, so it agreed only on the 16 passes and missed every one of the four fails. On this sample the judge does no better than chance at finding answers that invent store features. Judge-based numbers (e2e_accuracy, answer pass rates) are therefore likely too high.

## Limits

- One annotator, 20 rows.
- The sample is the first 20 cases of v3, all ordinary requests. It contains no adversarial, edge or unanswerable-only cases. A stratified sample would test the judge more fairly.
- Next steps: tighten the judge rubric on invented store features and channels, label a second, stratified sample with a second annotator, and recompute κ.
