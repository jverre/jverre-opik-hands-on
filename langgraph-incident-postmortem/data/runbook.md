# Ledger on-call runbook (excerpt)

## Connection saturation
If ledger-db active connections exceed 85% of max_connections: identify the top three clients, terminate idle-in-transaction sessions older than 30 seconds, and only then consider restarting a client service. Escalate to the database secondary.

## Customer communication
Post to the status page within 15 minutes of a critical alert affecting invoices. The status page was updated at 14:52 during this incident, 31 minutes after the first critical alert.

## Severity and ownership
A critical alert on ledger-api is severity 2 by default. The incident commander is the primary on-call unless handed off. Post-mortems are blameless: describe systems and decisions, never individuals' fault.
