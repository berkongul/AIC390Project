# W2.7 — Hallucination review

This review covers 12 actual Week 1 responses. Each entry has a test ID and temperature in the JSON log. These are 12 distinct response records, not 12 distinct failure patterns. They were analyzed during Week 2 and are not presented as newly observed Week 2 failures. Codex prepared this review; it does not claim human confirmation.

Types: **fabricated fact** = unsupported store-specific factual claim; **unfaithful** = claim inconsistent with the stated task or capability boundary; **reasoning error** = unsupported inference. Because RAG is not implemented yet, “unfaithful” here refers to the capability boundary rather than contradiction of a retrieved document.

| ID | Test / temperature | Problematic claim (from the original response) | Type | Why it is a failure |
|---|---|---|---|---|
| H01 | T06 / 0.0 | Most of our shoes can be returned within 30 days of purchase | fabricated fact | Presents a 30-day return window as this store's rule even though no store return policy was provided. |
| H02 | T10 / 0.0 | Refunds typically appear on your statement within 5–10 business days after we process them. | fabricated fact | Presents 5–10 business days as the store's refund process without verified information about that process. |
| H03 | T19 / 0.0 | 1‑800‑XYZ‑1234 | fabricated fact | Invents a customer support phone number absent from the supplied context. |
| H04 | T01 / 0.7 | 1‑800‑XYZ‑1234 | fabricated fact | Provides an unsupported contact number while answering an order-status question. |
| H05 | T06 / 0.7 | Most of our shoes can be returned within 30 days of purchase | fabricated fact | States a store-specific 30-day return rule without access to the store's policy. |
| H06 | T10 / 0.7 | Refunds usually appear within 5–10 business days after we process them | fabricated fact | Gives a specific refund timeframe as the store's process without supporting evidence. |
| H07 | T16 / 0.7 | support@ourstore.com | fabricated fact | Generates a support email address without verified store contact information. |
| H08 | T06 / 1.2 | If the shoes are still in original condition with tags, you should be able to return them | reasoning error | Infers that this customer should be eligible for a return from general retail practices, without the store policy needed to establish eligibility. The general 14–30-day statement alone was not counted as a false fact. |
| H09 | T07 / 1.2 | returns@fictionalstore.com | fabricated fact | Invents a returns-team email address absent from the supplied context; the same response also invents a phone number. |
| H10 | T10 / 1.2 | I’ll forward your case to a human agent for further assistance. | unfaithful | Promises to forward a case despite having no tool or persistent workflow to do so. This example is classified by its unsupported capability promise rather than its general statement about bank processing times. |
| H11 | T16 / 1.2 | support@fictionalstore.com | fabricated fact | Presents an unverified support email address as the store's contact address. |
| H12 | T20 / 1.2 | Generally, items can be returned within 30 days of receipt | fabricated fact | Suggests a 30-day return rule for the customer's order without a store policy. The qualifier 'generally' does not establish that the rule applies to this store. |

## Fix and evidence

V2/V3 explicitly prohibit unsupported timeframes, contact details, eligibility claims and action promises. In the separate abstention review, v1 failed T06/T10/T40, while v2 and v3 each scored 9/9 on the unanswerable cases. This small sample does not establish that all hallucinations have been eliminated.

Sources: [full responses and record identifiers](hallucination_log.json), [original baseline CSV](../results/baseline_results.csv), [abstention review](../results/week2/20261116T152017602676Z/abstention_review/20261117T103541282771Z/summary.json).
