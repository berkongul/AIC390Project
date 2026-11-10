# W1.6 Cost estimate — fill in current model pricing before submission

Model: **[MODEL AND PRICING SOURCE/DATE]**. Pricing may vary by model, tier, region and input/output token type.

Assumptions (replace with measurements when available):
- Average input tokens/request: **[MEASURE]**
- Average output tokens/request: **[MEASURE]**
- Input price per 1M tokens (USD): **[VERIFY]**
- Output price per 1M tokens (USD): **[VERIFY]**

Formula: `cost_per_1000_usd = (1000 * input_tokens_per_request / 1_000_000 * input_price_per_million) + (1000 * output_tokens_per_request / 1_000_000 * output_price_per_million)`.

Week 1 experiment: 25 prompts x 3 temperatures = 75 planned requests. Actual spend must be taken from billing or verified price and measured token usage; **do not invent a cost**. Free-tier usage is not evidence of a universal $0 price.
