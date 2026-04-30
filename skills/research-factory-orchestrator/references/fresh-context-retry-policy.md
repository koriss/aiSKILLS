
# Fresh Context Retry Policy

On timeout, crash, invalid output, or context overflow:

1. save partial artifacts;
2. create failure packet;
3. retry with fresh context;
4. keep same work-unit contract;
5. pass only needed partial artifacts and failure summary.

Do not restart completed work unless required.
