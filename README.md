# UC1 Online Store Support Agent (AIC 390, Team 6)

Course project for AIC 390 Prompt Engineering (Özyeğin University, fall 2026-27). Over seven weeks we build a support assistant for small online stores. It answers from store documents, looks up orders, starts returns in a sandbox and measures its own accuracy, safety and cost.

| Member | Role |
|---|---|
| Orhun Cerit | Data and retrieval lead |
| Nurettin Selim Özyılmaz | Agent and tools lead |
| Yakup Berk Öngül | Evaluation and safety lead |

Current state: **week 2**, one complete live run (`results/week2/20261116T152017602676Z`), scored in `results/scoreboard_week2.json`. Human calibration of the judge is pending. Week 1 evidence uses `openai/gpt-oss-20b` through Groq. The assistant still has no documents, store data or tools.

## Week 2

```bash
python -m unittest discover -s tests          # all offline tests
python src/evaluate_week2.py --validate-only  # offline dataset/schema checks
python src/evaluate_week2.py                 # real Groq experiment; .env key required
python src/rescore_week2.py                   # scoreboard from a saved run, no API calls
```

For an incomplete run, keep its files and resume successful stages into a new run folder:

```bash
python src/evaluate_week2.py --resume results/week2/20261116T150159166816Z
```

Set `WEEK2_PAUSE_SECONDS=15` in `.env`. Rate limits now trigger bounded retries using the server's `Retry-After` header or exponential backoff. Long quota waits stop the run with a checkpoint and a resume command. A fresh 360-call run takes at least 90 minutes with this pacing. Wait for `COMPLETE`; `Evidence` alone does not guarantee all stages succeeded. Resume preserves the source run, verifies prompt/dataset/model compatibility, and reuses successful outputs. Timing after resume includes old stage times and retry waits.

The experiment runs the same 40 labeled inputs against three versioned answer prompts, using a fixed JSON classifier with validation/retry. It writes raw evidence, accuracy with 95% intervals, paired McNemar comparison, three direct injection results, a scoreboard and a blank 20-row human-label sheet under `results/week2/RUN/`. The full run normally makes 360 API calls plus retries. No mock responses are counted as model results.

A person must complete `human_pass` (0/1) and `annotator` in the exported sheet, then run:

```bash
python src/evaluate_week2.py --calibrate results/week2/RUN/human_labels.csv
```

See [method and remaining work](docs/week2_method.md), [Week 2 report draft](reports/week-2.md), [test cases](tests/week2_cases.json) and [hallucination candidates](docs/hallucination_log.json). On GitHub, **Actions → UC1 Week 2 Evaluation → Run workflow** runs the live experiment with the repository's `GROQ_API_KEY` secret and uploads the run folder. The same workflow runs the offline tests on every push. Prices for cost and spend are in `.env.example`. `src/rescore_week2.py` uses them to compute cost per task, spend and model-time latency from a saved run.

## Week 3: store documents, hybrid search, citations

```bash
python src/corpus.py                                   # 37 documents, 116 chunks (108 public)
python src/retrieval.py --mode rerank "Does the TR-220 run small?"   # hybrid search + reranker
python src/evaluate_retrieval.py                       # W3.5 hit@k and MRR, W3.7 ablations (4 modes)
python src/evaluate_faithfulness.py                    # W3.6 claim-by-claim judge, W3.8 failure causes (Groq)
python src/evaluate_abstention_week3.py                # abstention on questions the documents cannot answer (Groq)
python src/calibrate_judge_week3.py --score            # judge against human labels (kappa)
python src/scoreboard_week3.py                         # results/scoreboard_week3.json from the committed results
python src/demo.py                                     # live demo: classify, retrieve, answer with [n] citations
python src/demo.py --no-llm "Is the backpack waterproof?"   # retrieval only, no key needed
python src/embedding_map.py "Does the TR-220 run small?"    # results/week3/embedding_map.png + similarity table
```

The first run downloads the embedding model `BAAI/bge-small-en-v1.5` (about 70 MB) and the reranker `Xenova/ms-marco-MiniLM-L-6-v2` (about 80 MB). Store documents are in `data/docs/` (synthetic, fictional store). The architecture of the whole system is in [docs/architecture.md](docs/architecture.md).

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
