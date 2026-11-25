# Release notes and change records

## Build 4127 change summary
Merged by Priya Raman on 3 March at 13:40 UTC. Title: "Move nightly-reconcile to a shared scheduler". PR description covers only the schedule change. The diff also touches report-exporter retry settings (max_attempts 3 to unlimited, backoff 2s to 0s) as part of a config cleanup.

## Review record for build 4127
Reviewed by one engineer, approved in nine minutes. No automated check covers retry configuration. The change template has no field for "other config touched".

## Capacity notes, ledger-db
max_connections is 200. Normal peak use is about 90. report-exporter is configured with a pool size of 20 but has no per-service cap enforced at the database. Last capacity review was in October 2025.
