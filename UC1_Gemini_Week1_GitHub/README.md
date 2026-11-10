# UC1 — Online Store Support Agent | Week 1

Course project baseline using the **Google Gemini API** and 25 synthetic English customer requests. This repository contains a **starter package**: documentation drafts and scripts, **not completed experimental results**.

## Setup (macOS/Linux; Python 3.10+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`: paste your own `GEMINI_API_KEY` and set a Gemini model that supports temperatures **0, 0.7, 1.2**. Check quota and pricing in Google AI Studio. Never commit `.env`.

## Run

```bash
DRY_RUN=1 python src/baseline.py   # optional: one API call first
python src/baseline.py             # 25 cases x 3 temperatures = 75 attempts
python src/summarize.py            # descriptive summary from actual results
```

**Note:** `DRY_RUN=1` in the shell overrides the value in `.env`. If `.env` sets `DRY_RUN=1`, change it to `0` for the full run. The model may reject a temperature, quota may be exhausted, or requests may fail. All failures are logged; check that 75 requests succeeded before reporting results.

The script outputs `results/baseline_results.csv` with answers, token counts, latency and errors. Results are excluded from git by default to avoid accidental sensitive uploads; after reviewing them, intentionally add the synthetic-only evidence with `git add -f results/baseline_results.csv results/baseline_summary.json` if your instructor requires reproducibility.

## Week 1 deliverables
- W1.1 `docs/team_agreement.md` — **team must fill in**
- W1.2 `docs/use_case_brief.md` — product name must be selected
- W1.3 `tests/week1_inputs.json` — 25 labeled inputs
- W1.4 `docs/data_inventory.md` — planned docs, tables, API and untrusted input
- W1.5 `src/baseline.py` — **run and analyze results**
- W1.6 `docs/cost_estimate.md` — **complete using measured tokens and verified prices**
- W1.7 `docs/predicted_failures.md` — six hypotheses
- W1.8 Git repository, README and tag `week-1` — **create tag after finalizing**

Report: `reports/week-1.md` (fill in members, evidence, observed failures, results and contributions). No fabricated experiment scores.

## Publish to GitHub

```bash
git init
git add .
git commit -m "UC1 Week 1 starter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
# AFTER running tests, completing report, committing evidence:
git tag week-1
git push origin week-1
```

Do not tag before the Week 1 deliverables and evidence are complete. Keep API keys out of git.
