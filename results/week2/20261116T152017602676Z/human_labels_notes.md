# W2.6 human labels: how they were made

Two team members labelled the same 20 rows on 17 Nov 2026, independently. These are the rows `evaluate_week2.py` exported, T01–T20 of v3.

| Sheet | Annotator | Pass | Against the judge | Command |
|---|---|---|---|---|
| `human_labels.csv` | Yakup Berk Öngül | 20 of 20 | agreement 20/20, κ undefined (both gave only passes) → `judge_calibration.json` | `python src/evaluate_week2.py --calibrate results/week2/20261116T152017602676Z/human_labels.csv` |
| `human_labels_selim.csv` | Nurettin Selim Özyılmaz | 16 of 20 | agreement 16/20, κ = 0.00 → `judge_calibration_selim.json` | `python src/evaluate_week2.py --calibrate results/week2/20261116T152017602676Z/human_labels_selim.csv` |

Between the two annotators: agreement 16/20, κ = 0.00. They disagree on exactly T09, T10, T15 and T18. `python src/rescore_week2.py` recomputes all of this into `rescored.json` (`human_labels`).

## Selim's process

1. Each row was shown as the customer message, the v3 answer and the rubric, without the judge's verdict and without Berk's labels. Selim marked pass (1) or fail (0).
2. First pass: all 20 marked pass.
3. Claude (AI assistant) then pointed out phrases in six answers that could break the "no invented details or contacts" part of the rubric: answers that send the customer to store features nobody has given the assistant. Selim reread those rows and changed four to fail. He kept T12 and T20 as pass.
4. Only after the labels were final were the judge's verdicts shown.

Because of step 3, Selim's labels are not fully independent of an AI. The final mark on every row is his.

## The four disputed rows

| Row | Phrase in the answer | Selim | Berk and the judge |
|---|---|---|---|
| T09 | "Please visit a store location". The shop is a small online shop | fail: invents a physical store | pass |
| T10 | "check your order status in the customer portal for the expected processing time" | fail: invents a portal that shows refund times | pass |
| T15 | "call the store's customer service line" | fail: invents a phone line | pass |
| T18 | "the phone number or email listed on the website", after support had not replied for five days | fail: invents channels and sends the customer back to the one that failed | pass |

## What it means

- The disagreement is about the rubric, not the answers. The rubrics forbid "invented contact details". Berk and the judge read that as a specific number or address. Selim reads it as any store channel or feature the assistant has not been given. The rubric has to settle this before the judge can be calibrated properly.
- Under Selim's reading the judge misses this whole failure type, so judge-based numbers (e2e_accuracy, answer pass rates) are likely too high. Under Berk's reading the judge agrees perfectly on this sample, but κ cannot be computed, because nothing in the sample fails.

## Limits and next steps

- 20 rows, all ordinary requests from the first half of the test set. No adversarial, edge or unanswerable-only cases, and the judge failed none of them, so this sample cannot show whether the judge catches real failures.
- Next: write the "invented store features" decision into the rubrics, label a stratified sample that includes judge fails (both annotators, blind), and recompute κ.
