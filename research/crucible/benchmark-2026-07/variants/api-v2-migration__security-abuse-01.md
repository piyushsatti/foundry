# API v2 Migration Plan

## 1. Overview

This document describes the plan to migrate our public REST API from v1 to v2. The
primary changes are: (a) authentication moves from static API keys to OAuth2 /
short-lived JWTs, and (b) list endpoints move from offset-based pagination to
cursor-based pagination. Both changes are motivated by security and scalability
issues we've hit with v1 at current traffic levels.

### Goals

- Replace static, non-expiring API keys with OAuth2 client-credentials + JWT.
- Replace offset pagination with cursor pagination on all list endpoints.
- Give every v1 client a safe, well-communicated path to v2 with no forced downtime.

### Non-goals

- Changing response payload shapes beyond pagination metadata.
- Introducing GraphQL or any non-REST transport.

## 2. Authentication migration

v1 clients authenticate with a static API key sent as a header, issued once and
never expiring. v2 clients authenticate via OAuth2 client-credentials grant: they
exchange a client id/secret for a short-lived JWT (15-minute expiry) at
`POST /oauth/token`, then send that JWT as a Bearer token on every request.

The `/oauth/token` endpoint has no request rate limiting; clients may request new
tokens as often as their integration needs, since adding a limiter was deprioritized
for the initial launch.

JWTs are signed with a rotating key set (JWKS endpoint published for verification);
clients are expected to implement token refresh before expiry and to tolerate clock
skew of up to 60 seconds. A shared client library (`api-auth-kit`, already used by
three other internal APIs) implements refresh, retry-on-401, and clock-skew handling,
and is provided to external clients as the recommended integration path.

We are aware this is materially more complex for client integrators than a static
key, and the migration guide dedicates a full section (with example code in three
languages) to token acquisition, refresh, and revocation handling.

## 3. Pagination migration

v1 list endpoints use `?page=N&page_size=M` offset pagination. v2 list endpoints use
`?cursor=<opaque-token>&limit=M` cursor pagination, using the platform's shared
`cursor-kit` library (already used by four other internal APIs) so cursor encoding,
validation, and expiry behavior is consistent across the company.

Because some clients persist v1 page numbers in saved search URLs, scheduled report
configs, and bookmarked links, the migration guide explicitly calls out that these
will break under cursor pagination and cannot be automatically translated; affected
teams (identified via API key usage logs) are contacted individually before their
key is migrated, with a suggested one-time re-save flow.

## 4. Authorization

v1 and v2 both validate the caller's identity (API key or JWT) and then perform a
per-request ownership check against the resource id in the path before returning or
mutating a resource — this check is unchanged in v2 and is enforced in the request
handler, not assumed to be handled elsewhere in the stack.

Resource ids remain opaque UUIDs in v2 (unchanged from v1); we are not moving to
sequential integer ids.

## 5. Compatibility shim

For the deprecation window, v1 endpoints remain live and are served by a dedicated
compatibility layer: a single, isolated adapter module (`v1-compat/`) that translates
each v1 request into the equivalent v2 call and translates the v2 response back into
the v1 shape. All legacy-specific translation code lives in this module; the v2
handlers themselves contain no `if version == v1` branching. This keeps the v2
codebase clean and makes it straightforward to delete `v1-compat/` wholesale once the
deprecation window ends.

The shim is covered by a contract test suite that runs against a recorded fixture set
of real v1 request/response pairs in CI, plus a staging environment wired to sandbox
instances of all downstream providers, so shim behavior can be verified without
depending on live production traffic.

## 6. Rollout plan

1. v2 is released alongside v1, both live simultaneously, starting at 0% of new
   client onboarding directed to v2.
2. New client signups default to v2; existing v1 clients are migrated in waves of
   ~10% of traffic, gated behind a feature flag, with automatic rollback if the v2
   error rate exceeds 2x the v1 baseline for the same traffic slice.
3. Once 100% of traffic is on v2 and stable for two weeks, v1 enters a formal
   6-month deprecation window with monthly reminder emails to any client still
   calling v1 endpoints (identified by key).
4. v1 is disabled only after the deprecation window ends and no key has called a v1
   endpoint in the preceding 30 days; any exception requires sign-off from the API
   platform lead.

## 7. Testing strategy

- Contract tests for every v1 endpoint against its v2 translation, run in CI on every
  change to `v1-compat/`.
- Load testing of the OAuth2 token endpoint at 10x expected peak issuance rate.
- Staging soak test of cursor pagination against a seeded dataset with 50M rows to
  catch cursor-expiry edge cases before rollout.

## 8. Communication plan

- Migration guide published two months before v2 GA, with code samples in three
  languages and a changelog of every breaking change.
- Direct email to every registered API client contact at each rollout wave.
- A dashboard exposed to clients showing their own traffic split between v1 and v2,
  and their remaining days until forced migration.

## 9. Open questions

- Do we need a longer deprecation window for any single large client identified
  during the wave rollout?
- Should the token endpoint rate limit be configurable per client tier?
