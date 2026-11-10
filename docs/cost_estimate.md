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

### Cost Calculation

Input cost = (12,177 / 1,000,000) × $0.075 = $0.000913275

Output cost = (10,973 / 1,000,000) × $0.30 = $0.0032919

**Estimated total cost for 75 requests = $0.004205175**

**Estimated cost per request = $0.00005607**

**Estimated cost per 1,000 similar requests = $0.05607**

These estimates use the recorded token counts and the stated model pricing. Actual billed spending may differ, especially when using a free API tier.

Evidence: `results/baseline_results.csv`.
