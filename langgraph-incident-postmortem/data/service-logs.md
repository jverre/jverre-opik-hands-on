# Service log excerpts, Tuesday 3 March 2026

## ledger-api, 13:58 to 14:05
13:58:41 INFO  deploy ledger-api build 4127 rolled out to 12 of 12 pods
14:03:10 WARN  report-exporter: pool checkout slow (1.8s), waiting=14
14:04:55 WARN  report-exporter: opened 38 new connections in 60s (retry loop on query timeout)
14:05:02 INFO  nightly-reconcile job moved to run at 14:00 (schedule override from build 4127)

## ledger-api, 14:18 to 14:30
14:18:30 ERROR connect: remaining connection slots are reserved for non-replication superuser connections
14:21:07 ERROR POST /v1/invoices 500 (PoolTimeout after 5.0s)
14:21:09 ERROR POST /v1/invoices 500 (PoolTimeout after 5.0s)
14:27:44 WARN  circuit breaker open for ledger-db, serving cached reads only

## ledger-db, 14:15 to 14:40
14:15:02 LOG   active connections: 171 (report-exporter 94, ledger-api 61, other 16)
14:24:51 LOG   active connections: 200, 63 sessions idle in transaction for more than 30s
14:38:12 LOG   pg_terminate_backend run by on-call on 55 report-exporter sessions
14:40:03 LOG   active connections: 74
