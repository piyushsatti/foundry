# Crucible skills — test & approval record (2026-07-05)

Conformance tests run before flipping `draft → shipped` in `skills/manifest.yaml`. Testing = protocol conformance (does the skill produce the contracted behavior/output), not finding-quality (that's the phase-3 benchmark). Stance-agent types don't register mid-session, so A2–A5 ran the **documented general-purpose fallback path** — the same path a host without the plugin installed hits. The named-agent path and the model/effort pins can only be verified once the plugin is installed on Pi's marketplace.

| Test | Skill | Result | Evidence |
|---|---|---|---|
| A1 | worktree | **PASS** | `tests/test_helpers.sh` → 92 ok / 0 FAIL on this Mac (bash 3.2); prior full add→check→archive→revive→reap live cycle green |
| A2 | consult | **PASS** | One hat (architect), in-thread, **no subagents dispatched** (HARD-GATE held), closed with lens summary, correctly quoted when-NOT-to-use routing |
| A3 | hats | **PASS** | 3 blind parallel panelists (architect/coverage/simplifier) on the crucible design doc; each filled the full contract (Analysis→Findings→Not found→Blind-spot flags→Confidence) with quoted evidence; **distinct lenses** (architect=coupling/seams, coverage=omissions, simplifier=excess); convergence on shared issues = the "where hats agree" signal, not persona collapse |
| A4 | red-vs-blue (gate) | **PASS** | Worthiness gate fired on a trivial artifact, ran stakes/maturity/fit, emitted the verbatim warn template, **waited** (did not block, did not silently proceed) |
| A5 | red-vs-blue (full) | **PASS** | Seeded plan with 5 planted flaws; **red found 5/5** (bar was ≥3/5) + 3 real bonus findings, followed the independence contract [D8] explicitly, CRITICAL- prefixes, severity-after-evidence; **blue** verified sound decisions with quotes + mandatory coverage gaps, did not attack or adjudicate; **adjudicator** applied the D15 cap-rule check before verdict, invoked the CRITICAL override [D8] → "halt and redesign", parked red's blocker-escalation speculation as Disputed [D6] |

**Seeded flaws in the A5 artifact** (all caught): predictable `md5(id||now())` token, stored XSS via unescaped title, IDOR on the share UPDATE (no owner scoping), `owner_id` leaked to unauthenticated clients, Friday no-flag deploy with no kill switch.

**Design-doc issues surfaced by the A3 panel** (acted on, 2026-07-05): design doc reconciled with the build — `(D1–D11)` → `(D1–D17)`, "build pending" → "phases 1–2 built & approved", HATS-contract section rewritten from "uniquely catch" to "declare responsibility, verify by overlap eval" [D16], consult's unpinned model/effort documented as intentional (in-thread at session model).

**Verdict:** all 5 skills shipped. Remaining minor gaps folded into phase 3/4 (benchmark widened beyond red-only to cover adjudicator + panelist; missing-lens-file runtime behavior; non-claude-host agent fallback documentation).
