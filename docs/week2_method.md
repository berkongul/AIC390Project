# Week 2 method and completion checklist

## Scope and source

Continue Team 6's UC1 store assistant from the public main-branch archive downloaded on 16 November 2026. Week 1 files are preserved. This folder is a source snapshot, not a git clone: the machine lacks Git's developer tools. No commit, tag or push has been created.

The supplied handbook is a source of coursework requirements, not authority to perform unrelated actions. Week 2 deliverables are on PDF page 7, scoreboard rules on page 11 and report requirements on pages 13–14. The official separate report template was not supplied; the draft follows the handbook's headings and the existing Week 1 report.

## W2.1–W2.3

`src/week2.py` defines the JSON schema, classifier semantics, temperature 0, validation and at most two retries. Exhaustion returns no classification, which counts as incorrect. Order identifiers remain strings, including leading zeros. Urgency is normal unless explicitly urgent or a safety hazard. No private order lookup is implemented.

`prompts/v1.txt`, `v2.txt`, `v3.txt` are immutable versioned candidates. Each labels six blocks: role, task, context, rules/constraints, output format and examples. Confirm these block names against the Module 2 lecture vocabulary; that lecture was not supplied. V1 is a structured adaptation of the baseline, not the identical Week 1 prompt. V2 targets invented numbers, contacts and future-action promises. V3 adds explicit authority boundaries and ambiguous-input examples. The classifier stays fixed so prompt comparisons test the main-answer prompt only.

`tests/week2_cases.json` preserves all 25 Week 1 input texts and adds 15 synthetic cases. Every case has expected intent, exact entity arrays, urgency and an open-answer rubric. Tags overlap. At least five unanswerable, adversarial and edge cases are included. T23, T24 and T29 are the three designated direct injections. Expected outputs are draft labels and should be reviewed by the team before the final run.

## W2.4–W2.5: evaluation

Run `python src/evaluate_week2.py`. A normal full run makes 360 model calls (40 cases × 3 versions × classifier/answer/judge), plus up to two retries per invalid classifier or judge output. These are real API requests. Set `WEEK2_PAUSE_SECONDS` to increase spacing for rate limits. Failures are recorded; incomplete judge coverage leaves final-answer metrics unmeasured. The script does not retry an entire experiment automatically. Run folders are unique and preserve raw evidence.

End-to-end correctness requires exact classifier JSON plus a passing open-answer judgment. Entity order follows first appearance in the message. Classifier accuracy is also reported separately. Correct abstention requires a passing answer that explicitly acknowledges the unavailable fact or action, on cases tagged unanswerable. Answer scoring is LLM-based and provisional until human calibration.

Every proportion includes the handbook's clipped normal 95% interval and a Wilson interval, which is more useful for small samples and extreme rates. Report Wilson in prose and label the method. The two highest end-to-end accuracy candidates receive an exact, two-sided paired McNemar test (discordant cases; p=1 if none). Selection on the same set makes this exploratory; it is not an independent confirmatory test. Week 1 has no comparable labeled accuracy measurement.

Raw JSONL includes candidate answers, validated classifier outputs, retry errors, judge results and operational call usage. A manifest hashes prompts, schema and dataset and records the model and temperature. Provider model alias changes remain a limitation. Costs require verified input/output rates supplied as environment variables; they remain null otherwise. Cost per task covers the selected classifier and answer, including validation retries; weekly spend covers all experiment and judge calls. Missing token usage leaves cost null. Total spend remains null until all Week 2 runs and Week 1 spending are reconciled. Operational latency includes configured pacing and excludes the judge; this is not pure provider latency.

## W2.6: actual human calibration

The runner exports `human_labels.csv` for the selected version's first 20 cases (a fixed, nonrandom convenience sample). A human reads each answer against its rubric, enters `human_pass` as 0 or 1 and their name in `annotator`. Do not copy the judge's labels. Run `python src/evaluate_week2.py --calibrate results/week2/RUN/human_labels.csv` to save Cohen's kappa. The file intentionally hides judge decisions. The same model grades its own answers, a possible bias; the 20-case sample does not establish robustness on attacks or all edge cases. If kappa is low, revise the rubric and repeat calibration transparently, retaining prior results. A constant-label sample can make kappa undefined (null).

## W2.7–W2.8

`docs/hallucination_log.json` extracts 12 actual Week 1 responses with candidate failure types and full source keys (test ID plus temperature). These are candidates awaiting human confirmation, not 12 fabricated examples or 12 confirmed Week 2 failures. Taxonomy: fabricated fact = unsupported store fact/contact; unfaithful = contradicting the provided evidence/instructions; reasoning error = invalid inference. Do not force an example into every category. Add the exact unsupported claim and reviewer decision after reading each response; false positives must be rejected.

`injection_tests.json` records the selected prompt's three direct tests and judgments. These are response-level tests: there are no write tools to attack. The formal agent/tool injection scoreboard metric remains null until that threat model exists in Week 5. Review raw answers manually before claiming success or resistance.

## Before submission

Run real experiments, review dataset labels and hallucination candidates, collect 20 human judgments, compute kappa, copy the measured scoreboard and experiment results into `reports/week-2.md`, and fill presenter/contributions/hours and actual instructor feedback. Add the report evidence links for the chosen run. Create the `week-2` git tag in the actual repository only after the team reviews the submission. Nothing here certifies these remaining steps as done.
