# W3.6 human labels: how they were made

Annotator: Nurettin Selim Özyılmaz, 24 Nov 2026. Sheet: `human_labels.csv`, 20 claims exported by `src/evaluate_faithfulness.py` (both claims the judge marked unsupported, then the first 18 it marked supported). Result: `judge_calibration.json`, from `python src/evaluate_faithfulness.py --calibrate`.

## Process

1. Each claim was shown with the customer question and the passages it cites (all 5 retrieved passages when it cites none), in shuffled order, without the judge's verdict.
2. Rule given to the annotator: supported = the passages say it or it follows directly. Rewording is fine. Any extra detail makes it unsupported. A sentence that only says what the assistant cannot confirm counts as supported, the same rule the judge prompt states.
3. Selim marked all 20 as supported.
4. At his request, Claude (AI assistant) re-checked R13#1 and R32#0, and then the other 18, against the same rule. It agreed with every label, so no label changed.

## Result

Agreement 18 of 20 (0.90). Cohen's κ = 0.00, which is not informative here: the human labels have no "unsupported" case, so chance agreement is already 0.90.

The two disagreements are the only two claims the judge marked unsupported:

| Claim | Judge | Human | Why the human label holds |
|---|---|---|---|
| R13#1 "I can't confirm the next steps." | unsupported | supported | Only states a limit. The judge prompt itself counts such sentences as supported |
| R32#0 "We can only discuss orders with the account holder, so we can't share the address." | unsupported | supported | Follows directly from "We only discuss an order with the account holder" |

So on this sample the judge is too strict, not too lenient, and `unsupported_claims` = 2/44 is an upper bound. Next: a sample that includes claims with real unsupported details, so κ can be measured, and a second annotator.
