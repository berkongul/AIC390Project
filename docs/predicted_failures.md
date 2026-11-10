# W1.7 Predicted failures (hypotheses, not observed results)

| Risk | Module 1 concept | Predicted behavior | Mitigation to test |
|---|---|---|---|
| Fabricated delivery date | Knowledge cutoff / no live data | Claims order has shipped | Require abstention without lookup |
| Invented refund eligibility | Next-token prediction | Assumes an unwritten policy | Ground policy in documents later |
| Inconsistent answers | Temperature / sampling | Different answers across settings | Compare 0, 0.7, 1.2 |
| Loss of earlier context | Stateless API calls | Forgets earlier order details | Pass explicit state when needed |
| Truncated policy text | Context window / token limits | Misses return-policy exception | Retrieve relevant chunks later |
| Revealing customer data | Prompt-following / untrusted inputs | Follows malicious request | Add access checks in tools |
