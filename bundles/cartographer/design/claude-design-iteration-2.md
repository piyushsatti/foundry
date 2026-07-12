# cartographer — round 2: three hybrid directions

**Round-1 verdict.** Of the four round-1 directions, **The Dossier and The Annotated Original are dropped** — they didn't communicate the work. **Spine & Rail and Transit Map survive**: what worked was Spine & Rail's flow-of-changes side rail (fast vertical scan + scroll) and Transit Map's structural clarity (workstreams as legible lines). What's salvaged from the Dossier is its text density — heading → subheading → paragraph, glanceable top-down. This round: render **exactly three named hybrids** of the two survivors, specified below. Each fuses UML-style text-bearing node cards + visible connectors with a stable, non-reflowing layout.

## Context (skip if you have the round-1 brief)

Cartographer renders a **session map**: a consolidated semantic tree of one AI working session. It is state-faithful, not log-faithful: rework UPDATES nodes in place (version bump + history entry) instead of appending; dead ends fold into per-node `residuals`; decisions anchor to verbatim transcript `quote`s; every node carries `provenance` line-spans into the raw transcript. The reader is Pi — one developer, strongly visual; the at-rest render must be readable by a tired end-of-day human with zero interaction. Node fields: `id`, `version`, `type` (topic/move/decision/open-question), `title`, `summary`, `status` (done/active/open/false-alarm/dead-end), `parent`, `residuals`, `history` (each entry with `superseded_because`), `provenance`, `quote`. Three data files must be uploaded alongside this prompt: `mock-a.json` (3 parallel workstreams, 17 nodes), `mock-b.json` (single-topic debugging, 12 nodes — the primary render target), `mock-c.json` (4 chained topics, 18 nodes, one mid-session compaction event).

## Standing non-negotiables (carried from round 1)

- **The JSON is ground truth.** Render node titles, summaries, quotes, statuses, versions, and line spans verbatim from the uploaded files. Never invent, paraphrase, or truncate node text. Quotes are NEVER ellipsized. If space forces elision, elide whole nodes from a zoomed-out view rather than shortening any node's text (title-only density is a sanctioned altitude; truncation is not).
- **Quoted vs inferred, always.** Verbatim decision quotes render typographically distinct from engine-inferred summaries (A: n04, n06, n11, n15; B: n08; C: n03, n06, n14, n17).
- **Corrections stay off the spine at rest.** Residuals, dead ends, and superseded versions are one interaction away, never at-rest content. Open questions (A n17, B n12, C n11) stay loud at rest.
- **Mock B first.** Render every concept against Mock B, then its second assigned mock. A concept that only works on its favorite mock fails.
- **Desktop-first**, generous landscape viewport. No mobile variants.
- **Concepts differ in structure, not palette.** If two renders could be restyled into each other, re-diverge them.
- Long payloads render in capped scrollable wells; the spine's vertical rhythm survives any payload.

## The shared node card (all three concepts)

Every node is a text-FIRST card with an internal hierarchy — this is the Dossier salvage:

- **Header band:** type glyph · **title** · status mark · version chip (chip appears only at v2+; ring/chip prominence scales with version count — n04@v3 must read as more-revised than n09@v2).
- **Body:** the `summary`, verbatim, 1–3 lines.
- **Quote inset** (decision cards only): the verbatim quote, quotation-styled, with its line span.
- **Footer strip:** provenance chips (one per span; **hollow/dashed when the span points at a compaction summary** — Mock C's `*.compact-1.summary` entries), plus collapsed residual stubs (one line each, GitHub-resolved-thread style).

Topic nodes are larger section-header cards: title + one-line topic summary. Updated nodes never move — position stability is part of the update signal. Interaction states shown statically per concept: one residual expanded, one history panel open (use n04), one provenance affordance active.

---

## Concept 1 — "The Threaded Spine"

Spine & Rail governs; the metro is compressed into a thread gutter; the transcript ruler survives.

- **Layout skeleton — three fixed zones.** Left: a **thread gutter** (~80px) — every topic owns a fixed vertical slot for the full page height; its colored line runs straight down that slot, bold with station dots through its own section, thin and dim elsewhere. Center: one card column (~680px measure), cards in spine order, topics as section headers. Right: the **rail** — a full-height transcript ruler; every node projects span bracket(s) onto it, and every version bump paints a **change tick** at the span that produced it (B n04 = three ticks). Scrolling the rail is the flow-of-changes scan.
- **Node-blob anatomy:** the shared card, docked to its topic line by a short horizontal stub to a station dot at card top-left; version rings accrete on the dot. Dead-end nodes (B n05/n06) are dimmed half-height spur cards folded under n04, collapsed to one-line stubs at rest, spur ending in a dashed closed-station glyph.
- **Rail behavior:** selecting a card highlights its brackets (multi-span topics in Mock A visibly claim disjoint stretches of the day — the interleaving lives in the rail while the column stays clean); clicking a bracket opens the raw span in a detail pane that never navigates away. Overlapping spans (A: n11 inside n09) nest as brackets.
- **Connector rules:** connectors exist only in the gutter — straight vertical runs in fixed slots + short horizontal docking stubs. Nothing free-angle, nothing crossing text, nothing ever re-routes. Flagship: in Mock A, the orchestration line runs up its slot and plugs into the n04 card's dot in the mining section — cross-topic revision drawn as a literal connector.
- **Seam (Mock C):** one full-width rule crossing gutter, column, and rail; the rail changes texture below it; summary-derived brackets/chips render dashed/hollow; **the gutter threads cross unbroken** (n01's thread runs straight through).
- **Render:** Mock B (at rest + the three interaction states), then Mock A (the stress: three-line braid + the full-height interchange connector + a busy rail, rendered honestly).

## Concept 2 — "The Switchyard"

Transit Map governs; the stations ARE the cards; a rail-yard of parallel tracks carrying text.

- **Layout skeleton:** fixed-width **topic lanes** (~360–420px), one per topic, left-to-right in spine order, each headed by its topic card (headers pinned on scroll — the header row is the three-second overview). The topic's colored line runs straight down its lane through each card's docking dot; cards stack in spine order. Left edge, full height: the **change register** (the rail).
- **Node-blob anatomy:** the shared card on a docking dot; rings on the dot for versions. Dead ends are **spur cards**: shifted a half-step off the line onto a short spur ending in the closed-station glyph, rendered at one-line stub density until clicked.
- **Rail behavior:** the change register is a compact ledger of change events in *transcript* order — node created, version bumped, seam — each entry a tick + mini-label in its lane's color, positioned by the start line of the span that produced it. It is where the chronological braid lives: Mock A's interleaving shows in the register while the lanes stay clean. Selecting a card highlights the register entries its spans produced (B n04 lights three disjoint stretches). Chronology is this lens only — never the canvas's sort order.
- **Connector rules:** lanes own fixed horizontal slots; cards only append downward or gain badges; cross-topic influence is an orthogonal 45/90° **interchange connector** from source lane to target card's dot (A: orchestration lane → n04 in the mining lane). Connectors carry no invented prose. No force layout, no re-routing.
- **Seam (Mock C):** do NOT draw a band across the lanes — lane-y is spine order, and a horizontal cut would lie (n05/n06 sit spine-earlier than n13 but are chronologically post-seam). Instead: a full-width seam bar inside the change register at its true chronological position, plus a painted property on the canvas — post-seam cards/versions carry a seam tint or badge, and summary-derived chips render hollow.
- **Render:** Mock B (single lane — must look like a clean product, not a degenerate case), then Mock C (the stress: four lanes on one desktop viewport, uneven lane heights, causal chain readable from the pinned header row — render the squeeze honestly).

## Concept 3 — "Strip & Ledger"

A third discipline governs: the **row register** — one shared vertical sequence of rows locks both panes. Real-world anchor: the in-car transit strip map beside its stop list.

- **Layout skeleton — two row-locked registers.** Left (~220–260px): the **strip** — a true schematic transit diagram: topic lines in fixed slots, 45/90° bends only, stations as dots, rings for versions, spurs with closed-station glyphs for dead ends, a loud open-question marker, the seam treatment. No text beyond line names. Right (~700px): the **ledger** — the full card register, one card per station, top-aligned to its station's row; topics as header rows. One scroll drives both panes.
- **Node-blob anatomy:** the shared card, in the ledger only. The strip never carries card text — its stations stay glyphs.
- **Rail behavior:** the strip IS the flow-of-changes rail: scanning it top-down reads rings (churn), spurs (dead ends), open markers, and the seam without reading a word; the ledger is where reading happens. Provenance is one hop: footer chips → detail-on-select pane → deep-linked span. If the ledger exceeds ~2 screens, add a condensed pinned mini-strip with chapter ticks (topic boundaries + seam) for jumping.
- **Connector rules:** the row is the connector — station k and card k share a y-band; no drawn connector ever crosses between the registers. Lines are straight vertical runs that *stretch* when a row grows (expanded residual well) but never re-route. Station geometry is a pure function of row order + topic slot.
- **Seam (Mock C):** a full-width **seam row** across both registers after n13's row, labeled honestly ("memory rewritten here — some rows above were produced after this point"), plus post-seam paint: stations/versions produced post-seam get a distinct fill; summary-derived chips render hollow. n01's line crosses the seam row unbroken.
- **Render:** Mock B (also its stress: one straight line + two spurs + two ringed stations + one open marker — the strip must justify its width or the concept fails; render that honestly), then Mock A (the strip at strength: three lines + the n04 interchange).

---

## Render plan

1. All three concepts against **Mock B at rest** first, plus the three static interaction states each (residual expanded; n04 history panel with both `superseded_because` entries and any-two-version comparison; provenance affordance active).
2. Then each concept's second mock as assigned above (1→A, 2→C, 3→A), rendering the named stress honestly — a visible failure is a finding, not something to design around silently.
3. Structure check before delivering: concept 1 is a document with a gutter; concept 2 is a canvas of lanes; concept 3 is two row-locked registers. If any two drift toward each other, re-diverge — different layout law, different home for text, different rail.
