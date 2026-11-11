## Week 1 Measured Token Usage and Cost

**Model:** `openai/gpt-oss-20b` (Groq API)

**Experiment:** 25 test inputs × 3 temperatures = 75 requests.

| Metric | Value |
|---|---:|
| Successful API requests | 75 |
| Failed API requests | 0 |
| Input tokens | 12,177 |
| Output tokens | 10,973 |
| Total tokens | 23,150 |
| Average tokens per request | 308.67 |

### Pricing Assumptions

- Input: $0.075 per 1 million tokens
- Output: $0.30 per 1 million tokens
- Source: Groq model page for `openai/gpt-oss-20b` (https://console.groq.com/docs/model/openai/gpt-oss-20b), checked on 11 Nov 2026. The cached-input price ($0.037 per 1 million) is not used.

### Formula

cost per request = (input tokens × $0.075 + output tokens × $0.30) / 1,000,000

With the week 1 averages (162.4 input and 146.3 output tokens per request):

(162.4 × 0.075 + 146.3 × 0.30) / 1,000,000 = $0.0000561 per request, or **$0.056 per 1,000 requests**.

### Assumptions behind the estimate

- The week 1 request is small: one system prompt and one customer message, with no documents, data or tool results.
- From week 3 each request also carries retrieved policy passages, and from week 4 tool calls and their results. Input tokens per request will grow, so we measure the cost again every week instead of extrapolating.
- Output is capped at `max_tokens = 300`.
- Prices can change. The prices live in `src/analyze_week1.py`, so a change is one edit followed by a re-run.

### Cost Calculation

Input cost = (12,177 / 1,000,000) × $0.075 = $0.000913275

Output cost = (10,973 / 1,000,000) × $0.30 = $0.0032919

**Estimated total cost for 75 requests = $0.004205175**

**Estimated cost per request = $0.00005607**

**Estimated cost per 1,000 similar requests = $0.05607**

These estimates use the recorded token counts and the stated model pricing. Actual billed spending may differ, especially when using a free API tier.

Evidence: `results/baseline_results.csv`. Reproduce with `python src/analyze_week1.py` (writes `results/week1_analysis.json`, including `cost_usd`, `cost_per_request_usd` and `cost_per_1000_requests_usd`) and `python src/scoreboard.py` (writes the scoreboard block).
