## What changed & why

Login is now **rate-limited per IP**. A new middleware sits in front of
`POST /login` and rejects a client with HTTP 429 once it makes more than 10
requests in a 60-second window. The intent is to slow down credential-stuffing
/ brute-force attacks against the login endpoint.

**Blast radius:** every request to `/login` now flows through new middleware,
and a new shared counter store is introduced. Nothing else routes through it yet.

## Risks worth your attention

1. **Fail-open behavior.** If the counter store throws, the middleware calls
   `next()` and lets the request through — so a fault in the store silently
   disables rate limiting rather than blocking traffic. That's a deliberate
   availability-over-security tradeoff; confirm it matches your stance for an
   auth endpoint.
2. **In-memory store won't scale.** The counter lives in process memory, so it
   resets on every restart and is **not shared across instances** — behind a
   load balancer with multiple replicas, each process keeps its own count and
   the effective limit multiplies. Fine for a single instance; a gap at scale.

## Annotated tour

1. `src/middleware/rateLimit.ts:15` — the entry point; every login request
   passes through here. Window and cap are the constants up top (60s / 10).
2. `src/middleware/rateLimit.ts:29` — the fail-open `catch` branch described above.
3. `src/store/ipCounter.ts:7` — `hit()`, the in-memory counter. Note the Map is
   module-level state, which is the source of the scaling limit.

You could now extend this (e.g. swap the store for Redis) — want me to go
deeper on any part?
