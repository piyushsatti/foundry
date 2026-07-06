# Crucible research

Evidence and evaluation behind the **crucible** plugin (lens × stance review
system — `plugins/crucible/`). The hat wardrobe, adversarial methodology, and
skill roster were built on this basis.

## Contents

| Artifact | What it is |
|----------|-----------|
| [`hat-design-research-2026-07-05.md`](hat-design-research-2026-07-05.md) | Evidence review (≈40-source table) grounding the 10-hat wardrobe and the professional-lens model |
| [`benchmark-2026-07/`](benchmark-2026-07/) | Seeded-defect corpus — 3 clean base artifacts + 24 defect variants across security / architecture / coverage / software-engineering lenses, with `ledger.json`, `results.md`, and a verification log (see its [README](benchmark-2026-07/README.md)) |
| [`hat-evals/`](hat-evals/) | Hat-overlap evaluation — `overlap-results.md` + the `shared-multilens-artifact.md` used to test whether distinct hats surface distinct findings |
| [`test-approval-2026-07-05.md`](test-approval-2026-07-05.md) | Conformance record (A1–A5) run before flipping the crucible skills draft → shipped in `skills/manifest.yaml` |

## Status

**Complete for v1** — the crucible skills shipped and were packaged into
`plugins/crucible/` on 2026-07-05. Open follow-ups (adjudicator benchmark, a
harder corpus v2) are tracked with the plugin, not here.

The base/variant artifacts are **synthetic** — fictional projects (an API
migration, a notification service, a SOC 2 access checklist) authored purely as
review targets. No real project or organizational data.
