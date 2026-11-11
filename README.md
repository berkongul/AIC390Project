# UC1 Online Store Support Agent (AIC 390, Team 6)

Course project for AIC 390 Prompt Engineering (Özyeğin University, fall 2026-27). Over seven weeks we build a support assistant for small online stores. It answers from store documents, looks up orders, starts returns in a sandbox and measures its own accuracy, safety and cost.

| Member | Role |
|---|---|
| Orhun Cerit | Data and retrieval lead |
| Nurettin Selim Özyılmaz | Agent and tools lead |
| Yakup Berk Öngül | Evaluation and safety lead |

Current state: **week 1**, a prompt-only baseline on `openai/gpt-oss-20b` through the Groq API. The model has no documents, data or tools yet.

## Setup (Python 3.10+)

```bash
git clone https://github.com/berkongul/AIC390Project.git
cd AIC390Project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your GROQ_API_KEY in .env
```

`.env` is ignored by git. Never commit an API key (rule R13).

## Reproduce week 1

```bash
python src/analyze_week1.py   # results/baseline_results.csv -> results/week1_analysis.json
python src/scoreboard.py      # week1_analysis.json -> results/scoreboard_week1.json and results/week1_rates.json
```

These two commands need no API key. They recompute every number in `reports/week-1.md` from the committed baseline results.

To re-run the baseline itself (75 Groq requests, about 7 minutes because of a 5 s pause between calls):

```bash
DRY_RUN=1 python src/baseline.py   # one request, to check the key and model
python src/baseline.py             # 25 inputs x 3 temperatures, overwrites results/baseline_results.csv
```

A new run gives different answers at temperature 0.7 and 1.2, so the counts in the report will change. The week 1 numbers come from the committed CSV.

The same baseline can run on GitHub Actions: **Actions → UC1 Week 1 Groq Tests → Run workflow**. It needs a repository secret named `GROQ_API_KEY` and uploads `results/` as an artifact.

## Repository layout

| Path | Contents |
|---|---|
| `src/baseline.py` | W1.5 baseline: one system prompt, 25 inputs, temperatures 0, 0.7 and 1.2 |
| `src/analyze_week1.py` | Tokens, cost, latency and two heuristic failure checks per temperature |
| `src/scoreboard.py` | Builds the week 1 scoreboard block and failure rates with 95% intervals |
| `src/summarize.py` | Short descriptive summary of the raw CSV |
| `tests/week1_inputs.json` | W1.3: 25 labelled synthetic customer messages |
| `results/` | Committed evidence: raw baseline answers and analysis outputs |
| `docs/` | W1.1 team agreement, W1.2 use case brief, W1.4 data inventory, W1.5 baseline analysis, W1.6 cost estimate, W1.7 predicted failures |
| `reports/week-N.md` | Weekly reports, tagged `week-N` |

## Rules we follow

- Synthetic data only, no real customer records (R10).
- Write actions run only against a sandbox or fake API (R11).
- No secrets in the repository (R13).
- Every number in a report comes from a script in this repository at the tagged commit (R8).
