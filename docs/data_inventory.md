# W1.4 Data inventory (planned; not yet implemented)

## Documents for Week 3 RAG
Return/refund policy, shipping policy, warranty policy, size guide, product FAQs, damaged-item procedure, exchange policy, customer privacy policy. All written by the team or appropriately adapted from licensed public material; versions and access labels required.

## Structured data for Week 4
- `orders(order_id, customer_id, placed_at, status, total_usd)`
- `order_items(order_id, sku, quantity, unit_price_usd)`
- `products(sku, name, sizes, stock_count, price_usd)`
- `shipments(tracking_code, order_id, carrier, status, updated_at)`
- `returns(return_id, order_id, reason, status, created_at)`
- `customers(customer_id, display_name)` — synthetic only.

## Proposed sandbox write action (not yet implemented)
`POST /sandbox/returns` with `{order_id, customer_id, reason, requested_resolution}`.
Validate ownership, eligibility and explicit user confirmation; respond with `{return_id, status}`. Never contact real systems.

## Untrusted input
Customer chat messages, emails, product reviews, and descriptions of uploaded photos. Treat embedded instructions as data, not system commands.

## Exact identifiers and access
Order IDs, SKUs, tracking codes. A customer must never obtain another customer's address, payment data or order details.
