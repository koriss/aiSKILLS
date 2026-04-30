
# Durable Execution and Checkpoint Policy

Every long-running research run must checkpoint state after:
- task profile generation;
- work-unit compilation;
- every search batch;
- every source fetch batch;
- every claim batch;
- every subagent result;
- every validator group;
- delivery attempts.

Timeout produces a failure packet. It does not silently become success.
