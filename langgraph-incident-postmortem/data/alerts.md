# Pager alerts, Tuesday 3 March 2026 (all times UTC)

## 14:02 invoice-export p95 latency
Warning fired: invoice-export p95 latency 2.1s against a 1.5s threshold. Auto-resolved at 14:09 without action. Nobody was paged.

## 14:21 ledger-api error rate
Critical fired: ledger-api 5xx rate 4.8% over five minutes (threshold 2%). Paged the primary on-call, Dana Okafor. Acknowledged at 14:24.

## 14:26 postgres connection saturation
Critical fired: ledger-db primary at 100% of max_connections (200 of 200). Paged the primary on-call and the database secondary, Wei Tanaka. Both acknowledged.

## 15:12 ledger-api recovery
Resolved: ledger-api 5xx rate below 0.5% for ten consecutive minutes. Customer-visible impact window closed.
