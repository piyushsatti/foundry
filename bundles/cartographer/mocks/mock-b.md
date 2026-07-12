# Mock B — a work debugging session

## Situation

A Claude Code session on the work machine, 2026-07-04, ~4 hours. The nightly `revenue_rollup_daily` DAG run for logical date 2026-07-03 pages at 02:31 UTC: the `check_rollup_quality` gate failed because the day's rollup produced 11,842 rows against a 196.4k trailing 7-day mean (−94%). No task crashed; the SQL ran clean and genuinely produced almost nothing.

The investigation forms a hypothesis that is **rewritten twice as evidence lands**:

1. **v1 — partial upstream landing.** Killed: `meta.load_audit` shows the `orders_enriched` partition landed complete, on time, at normal volume.
2. **v2 — scheduler-upgrade interval shift.** The platform team upgraded Airflow 2.8.4 → 2.9.1 three days earlier, which smelled like the classic `data_interval` regression. Killed: interval bounds and rendered SQL byte-identical to the last green run except the date literal.
3. **v3 (current) — upstream status-enum rename.** A `SELECT status, COUNT(*)` on the partition breaks it open: the ingest team's `orders-enriched-export` v4.2.0 deploy (2026-07-02, 18:40 UTC) renamed order status `'completed'` → `'settled'`; the rollup's `WHERE status = 'completed'` silently filtered 94% of rows. A legacy writer path still emitting `'completed'` explains why the run produced a small result instead of zero.

Decision (verbatim, anchored to the transcript): patch the consumer side rather than wait on upstream. The fix widens the filter to `IN ('completed', 'settled')` in **both** the daily and weekly rollup SQL (the weekly copy was found by grep after the first fix attempt covered only the daily — the fix node is v2 for exactly this reason). Verification re-runs 07-03 green **and** discovers that 07-02 had silently passed the gate while undercounting revenue ~29% (the deploy landed mid-day), so it gets backfilled too. Closeout posts an incident note and files an upstream ticket. One hardening follow-up — an enum-drift sentinel on `orders_enriched` — is drafted in the plan file and never done: it stays on the map as an open question.

**Sanitization:** every DAG, task, table, service, repo, and file name is invented (`revenue_rollup_daily`, `orders-enriched-export`, `analytics.orders_enriched`, `meta.load_audit`, `pipelines/…`). No real credentials, hostnames, IPs, ticket ids, or employer-identifiable details. Airflow version numbers are generic public software facts.

## What a correct render must show

- **A clean spine, top to bottom, under one topic (`n01`):** triage (`n02`) → facts from logs (`n03`) → hypothesis (`n04`) → root cause (`n07`) → decision (`n08`) → fix (`n09`) → verify (`n10`) → closeout (`n11`) → open question (`n12`). Read cold, the spine alone must tell the story: *fail → investigate → root cause → fix → verify*.
- **Dead ends folded, never a timeline.** `n05` (partial landing) and `n06` (interval shift) carry status `dead-end` and are parented **under the hypothesis node `n04`** — they are the tests that killed hypothesis v1 and v2. At rest they must render demoted (collapsed/folded behind `n04`), with their full detail one interaction away. A render that lays n05/n06 inline on the spine as chronological steps fails this mock.
- **Updated-in-place vs new node.** `n04` is at version 3 with a full history chain (v1 partial-data → v2 interval-shift → v3 enum rename, each with a `superseded_because`). `n09` is at version 2 (daily-only fix widened to daily+weekly). Both must be visually distinguishable from the v1 nodes around them, with superseded versions reachable behind interaction — not shown by default, not lost.
- **Verbatim vs inferred.** `n08` is the only node with a `quote`; the quoted decision text must render visibly distinct from the inferred summaries on every other node.
- **Residuals behind a click.** `n02` folds a misread-alert wrong turn; `n07` folds a brief false suspicion of the DQ check itself. Neither appears on the spine at rest.
- **Provenance affordance on every node** — each node (and each residual) points at spans of `cc-session-2026-07-04-rollup-debug`; `n04` carries three disjoint spans, one per hypothesis version. The design must show how a user reaches the raw transcript span from any node.
- **Open work stays loud.** `n12` (status `open`) must remain visible at rest — an unresolved follow-up is not mess to demote.

## Demonstrables this mock stresses

1. **Folded dead ends** — two `dead-end` nodes off the spine plus two residuals (the core Mock B requirement from the brief).
2. **Node-history access** — `n04@v3` with a two-entry history chain; `n09@v2` as a second, smaller instance.
3. **Updated-in-place vs new-node visual treatment** — v3/v2 nodes sitting between v1 nodes.
4. **Provenance drill-down** — spans on all 12 nodes; multi-span provenance on `n04`.
5. **Quoted vs inferred content** — decision node `n08` with verbatim quote at lines 878–881.
6. **Open-question visibility** — `n12` as never-done hardening work.

## Annotation targets (Phase 2 acceptance scenario runs on THIS mock)

The scenario — *"in step 3, this assumption is wrong; separately, this plan file is affected by it"* — two selections, two comments, one review packet:

- **The assumption:** `n04@v3` (third step of the spine), final sentence of `summary`: **"ASSUMPTION: 'settled' is a pure rename of 'completed' — the two states are disjoint per order, and no third status value carries revenue (unverified with the ingest team)."** This is the selectable-assumption-inside-a-node target, and it is deliberately plausible to be wrong (a third revenue-bearing status would corrupt the fix).
- **The artifact reference:** `n09@v2` `summary` names the plan file **`.gitignored/plans/rollup-status-hotfix-2026-07-03.md`** — the selectable-referenced-artifact target. If the n04 assumption is wrong, this plan file (which encodes the two-value `IN` list and the follow-ups) is exactly what's affected. The same file is referenced again in `n12`, giving the prototype a second place the artifact selection could surface.

Both annotations target versioned nodes (`n04@3`, `n09@2`), so the outdated-annotation mechanic from Phase 2 §5 has real version numbers to bind to.
