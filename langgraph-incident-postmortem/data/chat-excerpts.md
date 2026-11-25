# #inc-ledger-2026-03-03 chat excerpts (lightly trimmed)

## 14:24 to 14:31 first response
Dana: ack. 5xx on ledger-api, looks like pool timeouts. Checking the dashboards.
Dana: db is at 200/200. Who is hammering it?
Wei: joining. I see mostly report-exporter and ledger-api sessions. Pulling a breakdown.
Dana: opening an incident, I'll be incident commander for now.

## 14:33 to 14:41 mitigation
Wei: report-exporter has 94 connections, way over its normal 20 or so. Many idle in transaction.
Dana: I would rather not restart the exporter, it holds a lock on the month-end batch.
Wei: terminating the exporter sessions with pg_terminate_backend, not restarting the pods. Doing it now.
Wei: connections down to 74. ledger-api pool recovering.

## 14:50 to 15:15 follow-up
Priya: build 4127 also changed the retry policy in report-exporter, from 3 attempts with backoff to unlimited, no backoff. That was in the diff but nobody flagged it.
Dana: the reviewer approved because the PR description only mentioned the reconcile schedule.
Priya: the new retry loop is what opened 38 connections a minute. Query timeouts were from the reconcile job landing in business hours.
Dana: we need a connection cap on the exporter and a lint on retry settings. Writing it up as actions.
