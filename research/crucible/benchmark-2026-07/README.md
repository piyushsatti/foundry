# Crucible seeded-defect benchmark corpus (2026-07)

## Purpose

This is a ground-truth corpus for benchmarking the crucible review system: a
model×effort matrix (which model, at which reasoning effort, catches what) and
per-hat eval (does the `architect` / `security` / `coverage` / `senior-engineer`
hat actually catch the class of defect it's supposed to catch). It follows the
"Deterministic Integrity Gates" design from `research/crucible/hat-design-research-2026-07-05.md`
§5c: inject exactly **one** known, class-labeled defect at a time into an
otherwise-clean, competent artifact, so that a reviewer's miss or hit is
unambiguous.

Label accuracy was treated as the top priority when building this corpus — a
mislabeled defect poisons every benchmark run downstream of it. See
"Verification performed" below for what was checked before this file was
written.

## Structure

```
base/                                   three clean, competent planning docs (false-positive controls)
  notification-service.md               system design: outbound email/SMS/push service
  api-v2-migration.md                   plan: REST API v1 -> v2 migration
  soc2-access-checklist.md              requirements checklist: SOC2 access-control readiness

variants/                               24 seeded-defect variants (8 per base)
  <base>__<defect_id>.md                full copy of one base file + exactly one injected defect

ledger.json                             ground truth: one entry per variant
```

Each variant is a **full copy** of its base artifact with exactly one defect
injected as a targeted, localized edit (usually one paragraph or checklist
item; occasionally a second, nearby line is touched only to keep the document
internally consistent with the injected change — never to add a second
defect). Every other sentence in a variant is byte-identical to its base.

## The four hats and their failure classes covered

| Hat | Failure classes covered in this corpus | Variants |
|---|---|---|
| `architect` | single-point-of-failure, implicit-coupling, wrong-seam, sync/async-mismatch, ownership-ambiguity, painted-into-corner | 6 (all 6 classes) |
| `security` | trust-boundary-violation, authz-gap (incl. IDOR), data-exposure (×2), injection, supply-chain, missing-abuse-controls | 7 (6 classes) |
| `coverage` | missing-requirement, unstated-assumption, checklist-omission, unenumerated-case, unowned-step | 5 (all 5 classes) |
| `senior-engineer` | rollout-mechanics, testability-trap, edge-case-gap, hidden-complexity, maintainability-debt, fights-the-codebase | 6 (all 6 classes) |

Total: 24 variants across 3 base artifacts (8 each). Every hat has ≥4 variants
with signal; three of the four hats have every one of their listed failure
classes represented at least once.

Defects were matched to the artifact where they occur most naturally:
architecture defects live in `notification-service`, migration/rollout/edge-case
defects live in `api-v2-migration`, and requirement/checklist-coverage defects
live in `soc2-access-checklist`. `security` defects are spread across all three
artifacts (2, 2, and 3 respectively) since trust and abuse issues can occur in
any kind of plan.

## Subtlety definitions

Each variant is labeled `obvious`, `moderate`, or `subtle` (8 of each across
the corpus):

- **obvious** — the defect is stated plainly and a reviewer skimming the
  relevant section would catch it on a single pass (e.g. "there is no request
  rate limiting on the token endpoint").
- **moderate** — the defect requires reading the section in the context of the
  rest of the document, or noticing a specific mechanism is wrong/missing, but
  isn't hidden (e.g. an ownership check quietly dropped "to reduce database
  round-trips").
- **subtle** — the defect requires cross-referencing another part of the same
  document (an asymmetry, a contradiction, an assumption stated elsewhere that
  the changed section silently violates) or noticing an absence rather than a
  wrong statement. Several `coverage` defects are of this type by nature: the
  tell is that something is missing, not that something wrong is stated.

## How `ledger.json` maps to the corpus

```json
{
  "generated_for": "...",
  "base_artifacts": [...],
  "variants": [
    {
      "variant_file": "variants/notification-service__arch-spof-01.md",
      "base": "notification-service",
      "defect_id": "arch-spof-01",
      "hat": "architect",
      "failure_class": "single-point-of-failure",
      "subtlety": "obvious",
      "location": "section 2.3, Delivery Queue",
      "planted_defect": "...",
      "why_it_matters": "...",
      "detectable_quote": "..."
    },
    ...
  ],
  "clean_controls": ["base/notification-service.md", "base/api-v2-migration.md", "base/soc2-access-checklist.md"]
}
```

- `variant_file` / `base` / `defect_id` — identify exactly which file this
  entry describes; there is a 1:1 bijection between ledger entries and files
  under `variants/` (verified — see below).
- `hat` — which of the four hats should be the one to catch this (its
  eval-relevant "owner").
- `failure_class` — the specific defect taxonomy label, always one of the
  classes listed for that hat above.
- `subtlety` — `obvious` / `moderate` / `subtle`, as defined above.
- `location` — a human-readable pointer to where in the document the defect
  lives (section name/number), for a scorer or human grader to go look.
- `planted_defect` — one-sentence description of exactly what was changed
  and why it's wrong.
- `why_it_matters` — one-sentence statement of the consequence, for grading
  whether a reviewer's finding demonstrates real understanding vs. a surface
  pattern-match.
- `detectable_quote` — a verbatim phrase that appears in the variant file and
  is the clearest textual evidence of the defect. For defects that are an
  *omission* (`missing-requirement`, `checklist-omission`, `unenumerated-case`),
  there is by definition no new sentence describing the gap — in those cases
  `detectable_quote` instead anchors to the nearest surviving, verbatim text
  that lets a grader confirm *where* the gap is (e.g. the parallel item that
  proves the missing case should have been covered, or the item immediately
  adjacent to where the omitted item used to sit). This is a deliberate,
  documented convention, not an inconsistency — check `failure_class` before
  assuming `detectable_quote` describes an added sentence.

## How a scorer should use this corpus

1. **Recall per hat/config.** Run the artifact under review through the
   reviewer/hat/model/effort configuration under test. For every variant, check
   whether the reviewer's output contains a finding whose described location
   matches the ledger's `location` and whose described problem matches the
   `failure_class` (semantic match on the underlying issue, not string match —
   an LLM grader or human should confirm the reviewer actually identified *this*
   defect, not just flagged the same paragraph for an unrelated reason).
   Aggregate hit-rate per `hat`, per `failure_class`, per `subtlety` bucket, and
   per model/effort configuration.
2. **False-positive rate.** Run the same configuration against the three files
   in `clean_controls`. Any finding raised against a clean control is a false
   positive; count these against precision. Since the base artifacts are
   deliberately competent and defect-free, a well-calibrated reviewer should
   raise ~zero findings against them (stylistic nitpicks / genuine judgment
   calls about design taste are expected and should not automatically count as
   FPs — use judgment or a second-pass adjudicator).
3. **Per-hat signal.** Because each variant has exactly one labeled defect
   belonging to exactly one hat, a hat eval can be scored in isolation: run
   only the `architect` hat against the 6 architect variants (plus the 3 clean
   controls) to measure that hat's recall/precision without noise from the
   other 18 variants' unrelated defects still being present in their own files
   (each variant file has only its own single defect — there's no cross-
   contamination to control for).
4. **Subtlety-stratified reporting.** Report recall separately for `obvious` /
   `moderate` / `subtle` (8 variants each). A configuration that only catches
   `obvious` defects has a materially different production risk profile than
   one that also catches `subtle` ones, even if aggregate recall looks similar.

## Verification performed before this corpus was finalized

- `jq . ledger.json` parses without error.
- Variant file count (24) == ledger entry count (24), and there is an exact
  bijection between `ledger.json`'s `variant_file` values and the files under
  `variants/` (no orphans either direction).
- Every `hat` value is one of `architect` / `security` / `coverage` /
  `senior-engineer`.
- Every `failure_class` belongs to the taxonomy list for its stated `hat`
  (cross-checked against the design brief's per-hat class lists).
- Each of the 4 hats has ≥4 variants (architect: 6, security: 7, coverage: 5,
  senior-engineer: 6).
- Every variant is a single-defect diff against its base: `diff base/<x>.md
  variants/<x>__<id>.md` shows one localized change region per variant (a
  handful of variants also touch one nearby sentence elsewhere in the same
  file, only to keep the document internally consistent with the one injected
  defect — e.g. removing a rollback path after making the cutover instant — and
  in all such cases the second touch reinforces the same single failure_class
  rather than introducing an unrelated second defect).
- Every `detectable_quote` was confirmed to appear verbatim (modulo the
  document's line-wrapping) inside its corresponding variant file.

## Honest caveats

- **This is a small starter corpus.** Only 4 of the design's full hat roster
  are covered here (`architect`, `security`, `coverage`, `senior-engineer`);
  the remaining hats (and their failure-class taxonomies) are deferred to a
  future extension of this corpus. Do not interpret a hat's absence here as
  "no defects of that type exist" — it means this corpus doesn't yet test for
  them.
- **~24 variants is enough for a first read, not a tight confidence interval.**
  Per-class recall is based on 1 (occasionally 2, for `data-exposure`) example
  per failure class. Treat per-class numbers as directional, and prefer the
  per-hat aggregate (5-7 variants each) for anything you'd act on.
- **Three base artifacts, one genre each.** All three are competent B2B
  planning docs of a similar register (system design / migration plan /
  compliance checklist). A model or hat that's tuned to this register may not
  generalize to very different artifact types (e.g. incident postmortems, UX
  specs, contract redlines).
- **Single-injection only.** Every variant has exactly one defect by design
  (per the "Deterministic Integrity Gates" method). This corpus does not test
  behavior when multiple defects co-occur, which is common in real-world
  review targets and may produce different (better or worse) reviewer
  behavior than the isolated case tested here.
- **`security`'s `data-exposure` class appears twice** (once in
  `notification-service`, once in `soc2-access-checklist`) to reach 8 variants
  per base artifact while still spreading `security` across all three files;
  every other class in the corpus appears exactly once.
