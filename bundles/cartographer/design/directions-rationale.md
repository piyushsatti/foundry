# Phase 1 step 3 — the four directions: picks, axes, runners-up

*Internal doc for the orchestrator and Pi. The upload artifact for Claude Design is `claude-design-brief.md` (self-contained). The option map stays alive: any runner-up below can be revived after Pi sees renders.*

## The four picks

**1. The Dossier — literate document with revision apparatus** (paradigms 1+15: lab notebook fused with wiki apparatus). The mandated conventional-linear workhorse, but sharpened: the notebook contributes position-stability-as-update-signal and inline folded callouts; the wiki contributes the history tab, citation chips, and the "citation needed" treatment for summary-derived provenance. Fusing them costs nothing (they sit at the same axis coordinates) and buys the strongest version of the likely winner. Its known weakness — serializing Mock A's parallel workstreams — is acceptable-by-hypothesis for an end-of-day read; the render will show whether that hypothesis holds.

**2. Spine & Rail — central spine, margin residuals, persistent transcript rail** (paradigm 3). Picked for axis 4: it is the only paradigm where provenance is an always-visible instrument (span brackets on a full-session ruler) rather than a per-node link. Given the identity ruling — trust and transparency are the product — "which stretch of the day does this node consolidate" being visible at rest is a bet worth one slot. Also carries the best pre-attentive history signal (card-stack thickness) and the most natural whole-canvas seam. Stress: Mock A margin/rail congestion.

**3. Transit Map — vertical metro diagram** (paradigm 4). The genuinely-spatial slot, chosen over icicle/expedition/mind-map because it is the only spatial paradigm with a coherent answer to *all six* demonstrables — including the best seam glyph of any paradigm (the fare-zone band crossing all lines, which is literally what compaction does) and the only native vocabulary for Mock A's cross-topic revision (n04 as an interchange between the mining and orchestration lines). Defensible on all three mocks: A is its showcase, C exercises the band + straddling line, and B degrades to a single spine with spurs — ugly-but-legible, which is exactly what the render must prove or disprove.

**4. The Annotated Original — transcript-with-marginalia** (paradigm 14). The null-hypothesis control, included per the standing argument: cartographer's core bet is state-primacy over log-primacy, and no argument for that bet is as cheap or as honest as rendering the strongest log-primary alternative next to the other three. It also happens to carry two patterns worth seeing rendered regardless of outcome: unbreakable provenance (note physically on its span) and multi-span tethers (convergence as consolidation-made-visible). The brief instructs Claude Design to render its failure mode honestly (Mock A's margin cannot group topics without fighting its anchors) — if Pi still prefers it, that is a real finding about the product, caught before any reducer is built.

## Axis coordinates

| Axis | 1 Dossier | 2 Spine & Rail | 3 Transit Map | 4 Annotated Original |
|---|---|---|---|---|
| 1. Layout driver | structure | structure (rail carries time) | structure per line, parallel topics | **time (log substrate)** |
| 2. Linearity | 1-D scroll | spine + split margin/rail | **2-D canvas** | 1-D scroll, dual column |
| 3. Residuals live | inline-folded | margin stubs | topological spurs | collapsed bracketed regions |
| 4. Transcript relation | link (citations) | **persistent parallel rail** | link (station panel) | **map annotates transcript** |
| 5. Mutation vocabulary | borrowed (wiki revisions, version chips) | invented (card-stack depth) | invented (station rings) | borrowed-ish (versioned stickies) |
| 6. Density at rest | story-first (explores TOC-first via org-cycle) | story-first | **overview-first** | story-first margin over folded substrate |

Coverage: all three linearity classes, three of four transcript relations (missing only zoom-as-provenance — see icicle below), both mutation-vocabulary families, and two-and-a-half of three density classes (TOC-first is covered as Direction 1's density-dial exploration rather than a dedicated slot).

## Left on the table

- **Git-graph spine (paradigm 5) — the top runner-up.** Its log-vs-reflog split is the reducer's philosophy drawn as UI, and Pi reads git fluently. Cut because (a) its three best mechanics are already absorbed — reflog-style per-node history is in every direction's history panel, amend-badge semantics are Direction 1's version chips, the graft-point seam is outclassed by the fare-zone band — and (b) what remains after the theft is the liability: git-literacy as UI-literacy and a visually cold surface for a visual owner ("transparency, not tig"). Revive if Pi's reaction to the four is "too soft, give me something more technical."
- **Outliner with focus-and-context (paradigm 2).** Not a fourth paradigm so much as Direction 1 at a different density setting; its signature moves (hoisting, three-state cycling) are stolen into Direction 1's density exploration and the everything-is-a-bullet type-blindness is a real cost. Revive as a variant pass on Direction 1 if Pi wants more fold control.
- **Zoomable icicle / semantic-zoom canvas (paradigm 13).** Zoom-as-provenance (keep zooming until you hit raw transcript) is the single cleanest drill-down story in the catalog and the only axis-4 value not represented. Cut because its at-rest face is an effort dashboard, not a story — it fails demonstrable 1 before interaction begins, and Mock B wastes its canvas. Revive as a *lens* on a chosen direction (zoom gesture grafted onto Dossier sections or Transit stations) rather than as a paradigm.
- **PR review split pane (paradigm 10).** Master-detail hides the story behind clicks — wrong for Phase 1's readability gate — but it is the natural *host* for Phase 2's review-packet flow (pending comments, submit-as-one, outdated mechanic are native). Expect it to return as an interaction chassis under whichever paradigm wins, not as a look.
- **Expedition map (16), storyboard (6), stratigraphy (9), Marey (8), Gantt (12), mind map (11), code-fold (7), wiki-as-standalone (15).** Each contributed a stolen pattern (fog-for-open-questions, takes vocabulary, the unconformity glyph, pinched loops, cross-lane seam, branch-thickness, minimap, citation apparatus) but fails a core test as a whole paradigm: layout instability (16, 11), no time/seam vocabulary (11), time-primacy (8, 12), thumbnail/metaphor tax (6, 9), IDE-feel (7). Wiki was not cut — it was merged into Direction 1.

## Pattern-theft: visible in Phase 1 renders vs deferred

**Should be visible in the Phase 1 renders** (all encoded in the brief):
- Version chips minted only on semantic change (Figma named-vs-autosave; anti-pattern: version-noise fatigue) — all directions.
- Resolved-stub collapse for residuals (GitHub resolved threads) — Directions 1, 4.
- Quoted-vs-inferred typography + "citation needed"-style marking of summary-derived provenance (wiki apparatus; Mock C's two provenance flavors) — all directions, the trust surface.
- Span-to-log one-hop deep link and detail-on-select pane that never navigates away (Jaeger, DevTools/Perfetto) — Directions 2, 3 explicitly.
- Multi-span tethers / brackets ("consolidates dispersed work" made visible) — Directions 2, 4.
- Seam styled as provenance annotation, not rupture (Perfetto discontinuity markers; the map is what *survives* compaction) — all directions, distinct mechanisms (chapter rule / whole-canvas seam / fare-zone band / substrate swap).
- Position stability as the update signal (notebook) — Directions 1, 2; fixed-slot lines in 3.
- Density cycling (org-mode three-state) — Direction 1's explicit exploration variable.
- Capped scrollable wells for payloads (Jupyter scrolled outputs) — all.
- Diff-any-two-versions in history panels (Gerrit patchsets) — flagged as a bonus in acceptance criterion 3.

**Deferred to Phase 2** (interaction design; noted in the brief's closing instruction only so no direction forecloses node-level selection):
- Pending-review batch + submit-as-one (GitHub PR reviews) and the composing-while-map-mutates staleness check.
- Outdated-annotation mechanic with node@version anchoring; outdate on semantic change only (GitHub #86527 lesson).
- Gerrit ported-comments for unresolved annotations; resolved-stays-behind.
- Honest orphan tray over confident reattachment (Brush et al.); payload-carrying selections (Docs/W3C).
- incident.io curate-pins (Pi's demote/promote overrides as durable curation the reducer can't overwrite) — an interaction, not a render; but the *existence* of a residual/spine boundary in every direction is its prerequisite and is in Phase 1.
- "Changed since you last looked" glint + mark-as-caught-up, pinning rails (per-viewer state; post-hoc v0 makes it low-value in Phase 1 statics).
- Minimap-with-brush (Perfetto/VS Code) — deferred *as interaction*, but Direction 1's scroll-rail TOC and Direction 3's line index are its static precursors; if Mock C renders overflow one screen badly, promote the minimap into Phase 1 iteration.

## Claude Design feasibility note

The three JSONs total ~43KB / 47 nodes — well within upload limits, but the risk is fidelity, not size: a design tool paraphrasing node text, dropping residuals, or inventing content would silently destroy the demonstrables (the brief's whole premise is real data). Mitigations already in the brief: JSON-is-ground-truth rule (§1 and §5.5, quotes never truncated), Mock B first (smallest full-featured mock), per-mock inventories naming every load-bearing node ID so omissions are checkable against the text. Fallback per the project brief stands: two failed attempts at faithful data-dense renders → static HTML via Claude Code with the frontend-design skill.
