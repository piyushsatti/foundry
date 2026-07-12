# cartographer — round 3: lock the visual language, gate the structure

**Round-2 verdict.** The Switchyard is THE direction — the other two hybrids are cut. Pi's verdict carried a critique this round exists to fix: "a lot of visual clarity is being sacrificed there for text… there's not enough icons. There's not enough feel and creative expression" — plus one hard requirement: when a session has many parallel workstreams, **each stream must be very clear**. Round 3 locks two things through two gates: **Gate A — art direction** (three full-dress renders of the same design, pick one), **Gate B — structural stack** (does the pannable canvas earn its keep over the baseline?). Rulings already made, baked in below, not up for re-litigation: the three laws are standing design law; the System Map's four-clause stability law is adopted; a canvas unit = one topic's lane-cluster within a single session; the churn heat column, seismograph trace, and lane wash are OFF this round (decoration-risk).

**Context (skip if you rendered rounds 1–2).** Cartographer renders a session map: a consolidated semantic tree of one AI working session. State-faithful, not log-faithful: rework UPDATES nodes in place (version bump + history entry); dead ends fold into per-node `residuals`; decisions anchor to verbatim transcript `quote`s; every node carries `provenance` line-spans. Node fields: `id`, `version`, `type` (topic/move/decision/open-question), `title`, `summary`, `status` (done/active/open/false-alarm/dead-end), `parent`, `residuals`, `history`, `provenance`, `quote`. Reader: Pi, one strongly visual developer, tired at end of day — the at-rest render must work with zero interaction. Three data files are uploaded: `mock-a.json` (3 parallel workstreams, 17 nodes), `mock-b.json` (single-topic debugging, 12 nodes), `mock-c.json` (unused this round). This round renders A and B only.

---

## 1 · The visual language (render ALL of this in every frame)

### Three laws — standing design law

1. **Icons augment text; they never replace it at default altitude.** Icon-first rendering is legal only at designed zoomed-out altitudes where whole nodes are elided by rule.
2. **Every meaning has two channels.** Nothing is encoded in hue alone — every color signal is doubled by shape, fill, stroke style, or position.
3. **The hue budget.** Lane hues = stream identity, nothing else. One reserved amber accent = open work, nothing else. Everything remaining is achromatic ink on paper. Status is shape+fill; trust is stroke style.

### Glyph grammar, by element

- **Docking dots & node types.** Every card docks on its lane line via a dot; the type glyph rides the dot at every altitude, not only the card header. Move = small perpendicular tick-dot. Decision = double-ring roundel in lane color with white core, plus a filled ◆ diamond in the card header (and on its register row). Topic = the lane's own numbered line bullet — the topic card is the head of the line, not just a bigger card. Open question = amber "?" badge.
- **Decision quotes = pull-quote typography.** Oversized quotation-mark ligature, distinct size/leading from body prose, line span set as the citation line. Verbatim, never edited — the treatment is furniture.
- **Status = fill-state, never hue.** Dot fill: hollow ring = open · half-filled pie = active · solid = done. Terminal pair drawn achromatic: check-in-circle = done, slash-in-circle = false-alarm. Fill composes with type glyph (decision roundel with solid core = done decision).
- **Version rings.** Discrete countable concentric strokes on the dot (lane color alternating with paper), capped at three; v≥4 = one heavy ring + numeral chip. B n04@v3 vs B n09@v2 must be a subitizing read.
- **Capsule chips.** Version chip = metro station-code capsule (lane-color border, tabular figures, "v3"); provenance chips reuse the identical capsule with span codes ("643–748"). One chip shape grammar surface-wide. A glint dot on the chip = changed since Pi last opened the map.
- **Force-push event.** Where a version bump superseded a *decision* (A n04 — build sequence re-derived by another topic's work), its register entry gets a distinct glyph and a heavier "decision re-derived" label, not a plain bump tick.
- **Lane identity — the parallel-streams answer.** Every lane gets a numbered bullet (①②③ in spine order, lane color) AND a three-letter code (Mock A: MIN / CON / ORC); both recur on register entries, connector endpoints, breadcrumbs, the detail pane. Codes are derived furniture — they never substitute for the verbatim title. Lane header = **terminus board**: bullet + verbatim topic title + a computed status roll ("4 stations · 1 open · updated ×2"), all counts JSON-derived. Selecting a card thickens its lane's line one step and dims other lanes' furniture — never any card's text.
- **Interchange connectors.** Endpoints are places, not arrowheads: a small roundel on the source lane's line, and an interchange ring wrapped around the target's docking dot (A: orchestration → n04's dot gains the ring). Crossing an intervening lane = wire-hop (small semicircular arc: crossing, not connecting). Direction = two-three sparse chevrons ›› toward the target — sparse or nothing. At rest the connector sits one elevation below lanes and cards, dimmed; selecting either endpoint lifts it to the top at full weight.
- **Spurs (dead ends).** Track leaves the mainline at 45°, half the mainline's stroke weight, runs a half-step, ends at a ⊥ buffer stop; the spur card sits at one-line stub density. B n05/n06 under n04 are the flagships.
- **Ghost station (false-alarm).** Dashed hollow dot with a single diagonal slash — the station that never opened. The card stays at full text weight: the spine reading is the conclusion. A n10 is the flagship.
- **Open questions — quest-marker loud.** Bold amber "?" badge sitting proud of the card: breaks the bounding box, overlaps the lane line, static halo. A n17 and B n12 each wear one, at every altitude. If motion at all: a slow breathe, honoring `prefers-reduced-motion`; the halo must survive as the static/print form.
- **The change register (left edge, viewport-pinned, full height).** Entries in transcript order on a fixed column grid, tabular figures: line-position · lane bullet · event glyph · mini-label. **Micro-braid:** each lane owns a thin vertical thread in its color; events are dots ON their thread at transcript position — Mock A's interleave (mining opens, consolidation interrupts, mining returns, orchestration closes) lives here while the lanes stay clean. **Typed event glyphs**, same family as the canvas: ● created · ◎ version bump · ◆ decision landed · ⊥ dead-end closed · amber ? opened · hatched ▮ seam. **Ruler gutter:** faint transcript-line numbers every ~100 lines, entries positioned proportionally (quiet stretches read as whitespace); a compress-gaps toggle exists. Heat column and seismograph trace: OFF this round.
- **Seam grammar** (spec'd for completeness — A and B carry no compaction events, so no seam renders this round): a diagonal-hatched engineering-works band across the register's full width at its true chronological position, labeled with the verbatim `compaction_events` note; post-seam cards shift paper one step AND carry a miniature hatched corner tab — tab is the signal, tint is ambience.
- **Stroke grammar = trust, surface-wide.** Solid = raw-span-backed · dashed = summary-derived · dotted = residual/ghost — on chips, dot outlines, spur tracks, register entries, history ghosts alike. Summary-derived chips additionally carry the ≈ prefix ("≈ 610–642") so the trust discount survives chip size. Corollary: lane lines never dash — line-texture variants are solid-family only (single / cased / double stroke).
- **Altitudes.** Four snap altitudes — designed views, keyboard-stepped, never a continuous scale: **A3** line-index/glyph (lane lines + terminus boards + typed dots only), **A2** titles (typed dots + verbatim titles, nothing else), **A1** cards (the default at-rest view), **A0** bedrock (zooming past a card opens its deep-linked transcript span in place, map still visible around it). Label-shedding sheds WHOLE nodes by priority — open-question > decision > topic > versioned move > move — never shortens a title; an elided station leaves its typed tick on the line. At A3/A2, glyph size ranks the same priority: decision roundels and amber badges large, move ticks small.
- **Hue budget, stated fully.** Lane hues: max ~7, transit-grade, luminance-spread, identity only. Amber: open-question badges, hollow open rings, open register rows, the masthead open count — and nowhere else. All other ink achromatic. Status = fill; trust = stroke; churn = rings + register.
- **Elevation ladder.** Fixed z-order: lane lines < connectors (dimmed) < spur tracks < cards (1px border, faint shadow) < pinned terminus boards < lifted selection (card raise + connector glow). Depth encodes interaction state and nothing else. Canvas is warm paper (near-black slate in dark mode); no gradients, no glass, no glow except the selection lift.
- **Masthead.** Session title verbatim in display type, date, operator roundels (claude.ai / claude-code), and a computed strapline in fixed grammar — Mock A: "17 stations · 3 lines · 1 open · 1 ghost station." Every number JSON-derived; the grammar never drifts into invented prose.
- **Legend strip** at the map's foot: the five status glyphs, three stroke types, the bullet row, the ≈ mark — every symbol in use, nothing more, drawn in their exact shipped forms. Any glyph that can't justify a legend slot doesn't ship.
- **Empty states only** may carry micro-illustration: Mock B's one-lane header badged "single-line service" is the licensed instance this round. Anywhere else, illustration is decoration by definition.

---

## 2 · The three art directions (Gate A)

Whole-surface commitments — pick one, hybrids average away the feel. Every glyph above renders in any of them.

- **AD-1 · Network Modernism** — transit-signage modernism, Johnston/Frutiger temperament. Type: humanist grotesque with true tabular figures (Inter/Public Sans class); caps reserved for bullets and stream codes. Color: paper white / slate dark, fully saturated transit-grade lane inks, black-ink glyphs, amber at signal strength. Icons: geometric, stroke-consistent, roundel-first — the TfL/Tokyo lineage worn openly. Reader-feel: "the network is running" — calm municipal authority.
- **AD-2 · Working Drawing** — technical drafting, blueprint temperament. Type: monospace for every chip, code, ruler, and register row (IBM Plex Mono class); plain grotesque for card text; thin rules everywhere. Color: drafting-paper white with graphite ink, lane colors desaturated one step so the stroke grammar carries the trust story; optional dark cyanotype variant. Icons: thin-stroke schematic — buffer stops and wire-hops read like a signaling diagram. Reader-feel: an engineer's record of the day. **Honest cost:** round 1 cut the git-graph partly for coldness; this direction flirts with the same temperature and must buy warmth back through paper tone and generous spacing, or it reads as a tool, not a map.
- **AD-3 · Sunday Supplement** — warm editorial infographic. Type: display serif for masthead and terminus boards (Tiempos/Source Serif class), humanist sans for card bodies, pull-quote treatment at full editorial strength. Color: warm paper, softened-but-distinct lane inks, generous whitespace; the register styled as a printed timeline column. Reader-feel: a beautifully produced explainer of your own day — built for tired-end-of-day Pi. **Honest cost:** the charm budget lives entirely in furniture; if the editorial voice leaks into labels or straplines beyond the fixed computed grammar, that is paraphrase — a non-negotiable breach, not a style choice.

---

## 3 · The structural stacks (Gate B)

### 3a · Baseline chassis + the Departures Board

Baseline (fixed): fixed-width topic lanes (~360–420px), left-to-right in spine order, each headed by its pinned topic card; the lane's colored line runs straight down through each docking dot; cards stack in spine order; the change register on the left edge; a detail-on-select pane that never navigates away; shared card anatomy (header band / body summary / quote inset on decisions / footer strip with provenance chips + collapsed residual stubs). No force layout, no re-routing, ever.

**The board:** a viewport-pinned instrument band across the top, in departures-board visual language — one row per lane, in lane order, lane color as row livery: **verbatim topic title + status mark · a churn sparkline** (that lane's register ticks projected on a tiny transcript-time axis; clicking a tick = clicking that register entry) **· amber open-question beacons** (count + glow — A n17 stays loud even scrolled out of view) **· a seam tick** where the lane has post-seam content (none this round). Below the board, a thin **yard strip with brush**: the whole session in spine order, chapter ticks at topic boundaries, drag to scroll. The two axes are visually distinct on purpose — sparklines speak transcript order, the brush speaks spine order. The board has zero canvas geometry: rows mirror lane order, never reorder, never affect lane layout. **Mock B degradation rule:** with one lane, the board must collapse to a slim single-row status bar (title, status, sparkline, open beacon) badged **"single-line service"** — a grand header over one lane is cockpit cosplay and fails B's floor.

### 3b · The System Map + Flyover stack (the canvas)

Units on an infinite pannable/zoomable canvas. **A unit = one topic's lane-cluster within a single session** (ruled) — header card, line, docked cards, spurs, internally identical to a baseline lane. The canvas arranges units; it never reaches inside one.

**Stability law — four clauses, adopted:**
1. **Deterministic seed layout.** Units spawn on a fixed-pitch grid, one column per topic, spine order, single row — the canvas at rest, zoomed to fit, IS the baseline Switchyard. No force layout, no packing, no aesthetic optimizer.
2. **Drags are durable pins.** Engine updates change a unit's contents (cards append downward, badges accrete, rings grow) — never its coordinate. New topics take the next free seed slot, displacing nothing. Curation is per-viewer state stored outside the map artifact; the map exports in seed order.
3. **Internal geometry stays lawful.** The baseline lane law governs inside every unit; the canvas has no jurisdiction over a unit's innards.
4. **Connectors degrade honestly.** In seed layout they render exactly as baseline. Once curation moves units apart, a connector that can no longer route cleanly collapses to a **paired interchange-port glyph** on both endpoints — selecting either port draws the full link temporarily with the partner highlighted. Re-routing happens only at drop time of a Pi-initiated drag, never on engine update.

**Named regions** (lasso'd, labeled, color-washed) are the ONLY meaning-carrier on the canvas — proximity means nothing unless a label Pi typed declares it. **The register stays viewport-pinned left** — it is an instrument, not geography; one global register; clicking an entry flies the canvas to the unit and flashes the card. **Zoom = the four snap altitudes** (A3/A2/A1/A0), pure scale-about-anchors: every docking dot is the altitude-invariant anchor, lane pitch per altitude is a fixed constant, zero reflow, nothing re-routes. **Home is fit-zoom, always** — the app opens there.

### 3c · Working Line focus = an overlay frame

On the canvas, focus never widens a unit in place (it would collide with pinned neighbors, and the engine may not move them). Clicking a unit's terminus board opens an **overlay lightbox**: the focused lane at full reading measure (~680px) — summaries breathe, quote insets render wide, residual wells open — floating above the canvas, which dims one step with the other units still visible as A3 strips beneath. Escape closes; nothing beneath has moved.

---

## 4 · Render plan — exactly these sets, in order

**SET 1 — art-direction gate.** Mock A. Baseline chassis + full glyph grammar (§1) + Departures Board (§3a). Render **three times — once per art direction (AD-1, AD-2, AD-3)**. The information design must be IDENTICAL across the three: same viewport, same layout, same data, same states — only typography, color, and icon temperament vary. Primary frame at rest (zero interaction); in each, one identical inset showing n04 selected — interchange connector lifted from the orchestration lane, its register entries lit, the "decision re-derived" force-push row visible. If two of the three renders differ in anything but art direction, that is a spec breach — re-converge them.

**SET 2 — structure gate.** Mock A, System Map + Flyover stack (§3b–c), **AD-1 only**. Four frames:
1. Canvas at fit-zoom, **A3** — seed layout; must read as terminus boards + line geometry + size-ranked glyphs, with MIN/CON/ORC unmistakable.
2. Canvas at fit-zoom, **A2** — typed dots + verbatim titles only.
3. **One unit at A1** with the persistent side panel open on n04 — full card, history (superseded summary + `superseded_because`), multi-span provenance, verbatim quote.
4. **A Working-Line focus overlay** on the consolidation unit (n07, active) — full measure in the lightbox, the mining unit's ringed stations and ORC's line still legible as strips beneath.

**SET 3 — floor checks.** Mock B, both frames:
1. Baseline + the board degraded to its **slim single-row form, badged "single-line service"** — one lane carrying the full grammar: n04@v3's rings, n05/n06 spurs with buffer stops, n08's pull-quote, n12's amber badge.
2. The canvas at fit-zoom — which must be **indistinguishable from frame 1's baseline**. If visible "canvas-ness" appears (grid dots, empty vastness, a minimap for one unit), that is the variant failing its floor — render it honestly; a visible failure is a finding, not something to design around.

---

## 5 · Standing non-negotiables (unchanged; every frame obeys them)

- **The JSON is ground truth.** Titles, summaries, quotes, statuses, versions, spans render verbatim from the uploaded files. Never invent, paraphrase, or truncate node text. Quotes are NEVER ellipsized.
- **Elide whole nodes, never shorten one.** Title-only and glyph-only are sanctioned altitudes; truncation is not.
- **Quoted vs inferred, always** typographically distinct (A: n04, n06, n11, n15; B: n08).
- **Corrections stay off the spine at rest** — residuals, dead ends, superseded versions are one interaction away. **Open questions stay loud at rest and at every altitude** (A n17, B n12).
- **Desktop-first**, generous landscape viewport; no mobile variants.
- **Renders differ where the spec says and nowhere else** — SET 1 varies only art direction; SET 2/3 vary only structure.

---

## 6 · What Pi decides from these renders

1. **Art direction** — AD-1 / AD-2 / AD-3. The round's actual gate; hybrids not on offer.
2. **Lead stream-identity mark** — numbered bullets or three-letter codes lead (both ship; one leads).
3. **Achromatic done/active** — confirm he can live without green-means-done; only open work gets color.
4. **Motion at rest** — slow breathe on the open-question badge, or static halo only.
5. **Register instrument ceiling** — ticks + micro-braid is the floor; heat column and seismograph trace stay off unless he asks them back on.
6. **Depth of the transit fiction in copy** — glyph grammar only, or named moments too ("ghost station," "single-line service," "no service today"). Glyphs are load-bearing; copy is personality.
7. **Default fit-zoom altitude** — A2 titles vs A3 glyphs (SET 2 frames 1–2 exist to settle this by taste).
8. **Board default** — always-on vs summoned. Recommendation: always-on (a summoned instrument cannot serve the three-second read), contingent on SET 3's slim degradation passing.
9. **The canvas verdict** — does spatial curation (drag, regions, fly-to) earn its keep over the baseline, given the floor checks? This is Gate B itself.

*Noted as veto-able:* the unit ruling — unit = one topic's lane-cluster, single session; a multi-session atlas is a different, bigger product and stays post-v0. If Pi's mental model is whole-session switchyards on a shared canvas, he should say so before these renders bake the assumption in.
