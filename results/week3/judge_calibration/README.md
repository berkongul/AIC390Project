# Judge calibration sample (week 3)

Built by `python src/calibrate_judge_week3.py`.
- 24 questions (the 12 unanswerable ones in `tests/abstention_week3.json` and R01–R12 of the retrieval set) were answered with `prompts/rag_loose_v0.txt`, a deliberately loose prompt that is not part of the system. That produced 83 claims, 47 of which judge v2 rejected.
- 20 claims were sampled with a fixed seed: 10 judge-supported and 10 judge-unsupported, shuffled.

| File | Contents |
|---|---|
| `sample.csv` | The blank sheet for annotators. No judge verdicts |
| `judge_verdicts.json` | Judge v1 and v2 verdict per claim. Do not open before labelling |
| `labels_selim.csv` | Annotator 1, 24 Nov 2026, labelled without seeing the verdicts: 9 supported, 11 not |
| `labels_berk.csv` | Annotator 2 (PR #12): 8 supported, 12 not |
| `calibration.json` | Cohen's κ of each annotator against judge v1 and v2, and between annotators |

Selim against judge v1: 13 of 19, κ 0.37 (v1 gave no verdict on one claim). Against judge v2: 13 of 20, κ 0.30.
Berk against judge v1: 14 of 19, κ 0.48. Against judge v2: 14 of 20, κ 0.40. Selim against Berk: 17 of 20, κ 0.69.

**Another annotator:**
1. Copy `sample.csv` to `labels_<your name>.csv`.
2. Fill `human_supported` (1 = the passages say it or it follows directly, 0 = it adds anything they don't have) and `annotator`.
3. Run `python src/calibrate_judge_week3.py --score`. The agreement between the two annotators is added automatically.
