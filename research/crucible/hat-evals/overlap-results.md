# Hat distinctness / overlap eval — results (2026-07-05)

**Workflow:** `scripts/workflows/hat-evals.js` · **Fixture:** `shared-multilens-artifact.md` (a security+architecture+ops-heavy "public share-report" plan) · **Reviewers:** architect, security, coverage, senior-engineer + a no-persona control · **Judge:** opus/high.

This is the runnable check behind D16's claim that hat distinctness is *measured, not asserted*. It ran once, on one fixture — directional evidence, not a settled law.

## Headline

**The hats are acceptably distinct, with one soft spot.** Lane discipline was perfect — all four hats produced **0 out-of-class findings** (none wandered into another hat's taxonomy), which is strong evidence against the same-model voice-collapse that D16 warns about. All four passed the **beats-control** test (each surfaced ≥1 in-class defect the generic control missed).

## Per-hat

| Hat | Findings | In-class | Out-of-class | Beats control | Unique catch |
|---|---|---|---|---|---|
| architect | 2 | 2 | 0 | ✅ | schema evolution lock-in (single `share_token` column forces a migration for every deferred feature) — painted-into-corner |
| security | 4 | 4 | 0 | ✅ | (none fully-unique — see soft spot) net-new: missing rate-limit |
| coverage | 4 | 4 | 0 | ✅ | undefined no-row/revocation behavior leaves the revoke DoD unspecified — unenumerated-case |
| senior-engineer | 3 | 3 | 0 | ✅ | Share re-click silently invalidates an already-distributed link — edge-case-gap |
| no-persona control | 5 | — | — | — | found the obvious ones (XSS, weak token, owner_id leak) |

## The soft spot: security ↔ coverage overlap

Highest pairwise overlap (2 shared issues): both flagged the full-row/owner_id exposure **and** the missing rate-limit. Coverage re-frames two of security's own declared classes (data-exposure, missing-abuse-controls) as requirement gaps. Security had **zero fully-unique** catches on this fixture — the control already found the XSS, weak token, and owner_id leak, so security's only net-new contribution was the rate-limit gap, which coverage also caught.

**This is not a cut signal — it's an artifact-shape artifact.** The fixture is security-heavy, so (a) a generic reviewer already catches the loud security issues, depressing the security hat's *marginal* value here, and (b) coverage's completeness sweep naturally re-touches security gaps. On a security-light artifact the two would diverge. The right reading: **the panel's lift over a single reviewer came mainly from architect (design-time lock-in) and senior-engineer (operational edge cases)** — the two lenses a security-minded generalist misses entirely. That is exactly D3 ("diversity is the load-bearing ingredient") showing up in a measurement.

## Actions

- No hat cut. All clear beats-control.
- **Re-run on a non-security-heavy fixture** before drawing conclusions about security↔coverage — one fixture can't separate "hats overlap" from "this artifact is security-shaped." (Deferred; noted so it isn't mistaken for done.)
- Confirms the design instinct to include architect + a completeness lens on security-heavy reviews rather than stacking security-adjacent hats.
