# Durable Checkpoint Recovery Policy

Every side-effecting step writes state. Timeout creates a failure packet. Required failed work-units must be retried/replaced or the run becomes partial/failed.
