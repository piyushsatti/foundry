# Mock C — a mega-session slice (pivots + one compaction seam)

## The situation

A long Claude Code session (surface: `claude-code`, fabricated project "tessel", a small Python library) that started as one refactor and turned into four causally-chained work items:

1. **The refactor** — extract tessel's monolithic `store.py` into a `storage/` package: a five-method `StorageBackend` ABC, `SqliteBackend` as the default, a new `JsonBackend`, and a compat shim.
2. **The flake it surfaced** — reorganizing the tests changed collection order and unmasked a pre-existing order-dependent failure in `test_concurrent_write` (shared module-scoped tmpdir). Two dead-end hypotheses before the real cause.
3. **The CI drift the flake fix exposed** — CI stayed red *after* the flake fix, for an unrelated refactor-triggered reason: the workflow matrix still tested Python 3.9 while `pyproject.toml` had required >=3.10 for months; the new ABC's `typing.Self` fails at import on 3.9.
4. **Release prep** — with CI trustworthy again, back to finish the refactor (JsonBackend + shim + deprecation policy), then version/changelog/build for 0.8.0.

**One auto-compaction event** fired mid-session (~148k tokens), while the CI diagnosis was concluding — chronologically after node `n13`, transcript line ~610. Work continued for a long stretch after it: the CI decision and verification, the *return to the refactor topic*, and all of release prep happened post-seam.

The chronological pivot order was: refactor → flake → CI → **[compaction]** → CI (finish) → refactor (finish) → release. The map does **not** show that zigzag as a zigzag — that is the point.

## What a correct render must show

- **Four top-level topics, each appearing exactly once**, in spine order: refactor (n01), flake (n07), CI drift (n12), release (n16). The session returned to the refactor after the seam, but the spine must NOT contain a second "refactor, continued" node — the return manifests as n01 bumping to v3 and new children (n05, n06) folding in under the original topic. Rework updates; it never appends to the spine.
- **Pivots as topic boundaries, not chaos.** The causal chain (refactor *surfaced* flake, flake fix *exposed* CI drift, CI fix *unblocked* the refactor) should be legible from the topic summaries reading top-to-bottom. The reader should finish the spine knowing what happened and why the session moved, without ever seeing a timeline.
- **The compaction seam, visibly.** `session.compaction_events[0]` says the seam falls after `n13`. However it's drawn (a rule, a marker, a shading change), it must convey "the agent's memory was rewritten here" — and it must **not** shatter topic A (n01) into pre/post fragments, even though n01 straddles the seam (created before it, v3'd and completed after it).
- **Two provenance flavors, visually distinguished.** Most provenance points at raw transcript spans (`c-mega-0630.jsonl`, line ranges). Three entries point at `c-mega-0630.compact-1.summary` — the compaction summary — on n01 v3 and n12 v2, the two nodes *updated after the seam about pre-seam events*. A render that shows all provenance chips identically is hiding the trust difference (see design questions).
- **Version history behind a click:** n01 (v3, two history entries), n04 (v2 — "premature green"), n07 (v2 — "we caused it" → "it predates us"), n12 (v2 — "flake fix incomplete" → "independent matrix drift"). The v1 readings are *wrong* readings that got corrected; they belong behind the node, never in the spine.
- **Dead ends folded:** n09 carries two disproved hypotheses (WAL race, backend-introduced) as residuals; n04 carries the premature-green residual. None of these may appear as spine entries.
- **Decisions as quotes:** n03, n06, n14, n17 each anchor to a verbatim quote with line spans. The render must visibly distinguish quoted words from inferred summary text.
- **One dangling open question:** n11 (pytest-randomly sweep, never run). It must still be findable and visibly *open* at the end of the map — a session map that lets open questions vanish is failing its job.

## Demonstrables this mock stresses

| Demonstrable | Where |
|---|---|
| **Compaction seam rendering** (the headline) | `compaction_events` after n13; straddling node n01 |
| **Topic/pivot boundaries in a long session** | four topics, causally chained, zigzag chronology |
| **Topic revisited after compaction → in-place update** | n01 v2→v3 + new children n05, n06 post-seam |
| Summary-derived vs raw provenance | n01, n12 mix `jsonl` spans with `compact-1.summary` spans |
| Updated-in-place vs new node treatment | n01/n04/n07/n12 (versioned) vs n05/n14 (new, post-seam) |
| Dead ends folded into residuals | n09 (two hypotheses), n04 (premature green) |
| Decision nodes with verbatim quotes | n03, n06, n14, n17 |
| Open question left dangling | n11 |
| Provenance on every node | all 18 nodes |

## Design questions this mock surfaces (for the orchestrator)

1. **A chronological seam has no natural home in a non-chronological artifact.** `after_node: n13` names the last node touched before compaction — but n05/n06 sit spine-*earlier* than n13 while being chronologically *later*. Should the seam render as a point in the spine at all, or as a property painted onto nodes/versions ("this version was produced post-seam")? The provisional `after_node` field may be the wrong shape.
2. **Summary-derived provenance is a different trust class and the schema can't say so.** This mock overloads the `transcript` field with a pseudo-id (`c-mega-0630.compact-1.summary`) to stay in-schema. Honest version: post-compaction, the reducer cannot see pre-seam raw content, so claims it writes about pre-seam events can only cite the summary — even though the raw JSONL still exists on disk and a *viewer* could deep-link into it. Phase 3 likely needs a provenance `kind` discriminator (`raw-span | compaction-summary | ...`), and the renderer needs distinct affordances for the two.
3. **The MAGE-style validate pass breaks at the seam.** Pre-seam nodes were validated against raw spans. n01 v3's consolidated claim about pre-seam work can only be validated against the summary — if the summary itself drifted, the map inherits the drift with no in-context way to catch it. Does the validate pass get to re-open the raw transcript from disk (it's just a file), or does summary-derived content carry a permanent "lower confidence" mark?
4. **Straddling nodes and annotation targeting (Phase 2 shadow).** Annotations reference `node@version`. n01@2 is pre-seam, n01@3 is post-seam. If an annotation on n01@2 goes outdated when v3 lands, the "view what changed" diff crosses the seam — the diff's own provenance is part-raw, part-summary. Flagging now so the Phase 2 lifecycle design doesn't assume uniform provenance under a version diff.

## Sanitization note

Fully fabricated: project "tessel", all file names, test names, line numbers, and quotes. No credentials, hostnames, IPs, or proprietary identifiers. Structure (message cadence, topic-drift shape, compaction placement) informed by skimming one real local transcript's *shape* only; no content reused.
