# cartographer — tiered map spec (round 4: convergence)

*Round-3 verdict (Pi, 2026-07-05): the Set-2 high-level view won — "that train station tree look at the very high level that goes top to bottom… lines, nodes, and trees sort of representation as well as the different icons — very visually clear." The hard negative: "there seems to be a lot of visual noise in the entire UI that I don't think is needed." He endorsed layers in principle, near-verbatim — "two or more layers now instead of just one view… something that's more abstract, and then something that's abstract plus the headings plus the subheadings or the tallies, and then maybe something that's like 'this is the changes we have made here'… if you click on any of these lines it opens up into a view that is more like a sector" — but also: "I'm not really sure how I want the layers structured," so this spec presents candidate structurings, not a locked ladder. A second temperament ruling governs everything here: Pi rejected round 3's instrument-grade rail treatment — "I rather enjoy the round one or round two's version… a lot more friendly and intuitive" — so instrument-grade/technical now counts AGAINST an element in the noise audit, not for it. Carried unchanged: AD-1 Network Modernism as working default (the AD gate stays open); the spatial canvas's drag/regions/curation is PARKED — not spec'd here, not killed; the three laws, the stroke-trust grammar, and the JSON non-negotiables survive intact — anti-noise infrastructure, exempt from the knife. The round-4 render prompt is authored separately against a new mock; this file is its design substrate.*

## 1 · Candidate layer structurings — for Pi to react to visually

Whichever wins, layers are an IA, not a zoom dial (pattern 41's cost honored: each layer is a designed view; no in-betweens). Round 3's A0 bedrock stops being a zoom everywhere: transcript access is a click on a provenance chip, from any layer. Geometry in every candidate: topic lines as vertical columns, stations descending in spine order, top-to-bottom — the train-station tree. Three shared density bands recur across candidates and anchor everything below: **MAP** (abstract tree: lines, typed+status dots, icons, topic titles, nothing else), **OUTLINE** (MAP plus exactly one verbatim heading per dot plus small tally chips — version count, residual count, open marker, all JSON-derived), **SECTOR** (one line's dedicated reading view: full cards at ~680px measure, history and changes visible — version chips, onion-skin diffs, `superseded_because`, spur cards, pull-quotes, provenance).

- **L-A · Three-tier ladder** *(the structure closest to Pi's words).* T1 = MAP, T2 = OUTLINE, T3 = SECTOR; node detail panel available at T1/T2 without leaving the tier. Trade-offs: cleanest separation of densities and a genuinely quiet top view; but the most navigation of the three candidates, and it forces a landing-tier decision (T1 vs T2).
- **L-B · Two layers — Overview + Sector.** One map layer at OUTLINE density (headings always on); click a line → SECTOR; click a dot → panel. MAP exists only as a density toggle, not a place. Trade-offs: fewest moves, one obvious home; but the abstract hero view Pi admired stops being a resting state — the quietness is opt-in.
- **L-C · Hub and detail.** The map never changes and is the only map (OUTLINE density); SECTOR opens as an overlay lightbox above the dimmed hub (round 3's Working-Line overlay, inherited); node detail is the panel. Trade-offs: maximal spatial stability — the hub itself is the landmark and Escape always means "home"; but deep reading is never a *place*, always a layer floating above one, and long sectors scroll inside a lightbox.

**The node detail surface — common to all candidates.** Click a dot or heading → node detail opens *without leaving the layer*. Pi said "a modal or something" — the pick is the **detail-on-select side panel** (pattern 16), the program's established instrument: a modal occludes the very map the layers exist to keep visible; the panel keeps tree + rail on screen while detail is read — and it is the friendlier of the two. The modal stays on the table for Pi's veto (more reading width, harder focus, total occlusion). Panel contents: the full card as SECTOR renders it, history with diffs and `superseded_because`, residuals expanded on demand, provenance chips opening the deep-linked transcript span in a capped scrollable well. Selecting a node also lights its marks on the rail.

## 2 · Shared navigation contract (holds in every candidate)

- **Click a line** (head, title, or the line itself) → its SECTOR (as a tier in L-A/L-B, as an overlay in L-C).
- **Click a dot or heading** → node detail panel; the layer underneath does not change.
- **In SECTOR:** cards are already full — chips act (version chip → history; provenance chip → span well). Cross-line links render as **interchange ports** naming the partner line (bullet + verbatim title); clicking a port switches sectors at the linked node.
- **Hover:** a line → route-focus ribbon (thicken one step, dim other lines' furniture, never card text). A dot at MAP density → transient verbatim title label (a one-node OUTLINE peek — flagged in §5). A rail mark → its label.
- **Escape unwinds one level:** span well → history → panel → sector → home layer → no-op. Getting back is never more than Escape or one breadcrumb click.
- **Breadcrumb** lives in the masthead line, always: root = verbatim session title; inside a sector it grows "▸ ① Transcript mining." Clicking the root returns home.
- **Landing:** in every candidate the home view is the headings-on density (OUTLINE) — the tired-end-of-day zero-interaction read needs headings, and law 1 (icons never replace text at default altitude) makes OUTLINE-as-home law-clean. In L-A that means landing at T2 with T1 one keystroke up; if Pi wants the quiet MAP as home, law 1's "default altitude" clause needs a formal amendment — noted, not made.
- **The compaction seam** (spec'd for completeness; renders only when a mock carries `compaction_events`): a labeled band on the rail at true chronological position — the rail is the chronology surface, so the seam survives even MAP density. On the map: MAP carries nothing extra (dashed outlines on summary-derived dots already mark the trust consequence, per the stroke law); OUTLINE title rows post-seam carry a small hatched corner tab; SECTOR cards carry tab plus the one-step paper shift (tab is the signal, tint is ambience).

## 3 · The rail — the friendly chronology sidebar

This is round 1's sidebar revived, as Pi asked: "parallel colored lines that basically told you where in the transcript something happened." Full transcript height, viewport-pinned left (the register's old slot), **identical in every layer of every candidate** — the stable landmark that keeps drill-down from disorienting (pattern 38's warning answered). Its JOB is unchanged from the register: per-stream colored lines + where-in-the-transcript each change happened + click to go there. Its FORM is rounds-1/2 temperament, not round 3's: **the instrument-grade micro-braid — fixed column grid, tabular figures, six-glyph event code, printed ruler — is this rail's rejected-styling ancestor.** Same bones, wrong temperament; what changed is styling and element count, not the job.

- **One soft thread per topic line**, lane hue, generous spacing, headed by its numbered bullet. Threads parallel, never merging.
- **Marks at true transcript position — three forms only:** a plain lane-colored dot (something happened: created or updated), ◆ (a decision landed), amber ? (a question opened). The six-glyph typed family (⊥, ◎, force-push variants) is off the at-rest surface — full event type appears on hover.
- **Dots only at rest; labels on hover** (event · node title · line position); click a mark → navigate to that node in the current layer (scroll + flash; panel optional). Round 2's mini-labels-at-rest variant is the friendlier-but-busier alternative — flagged in §5.
- **Positions proportional** to transcript position, so quiet stretches read as whitespace — but no printed ruler numbers at rest; line numbers surface on hover. Compress-gaps survives as a toggle.
- **The seam band** renders here, full-width across threads, labeled with the verbatim `compaction_events` note.

**What it absorbs:** the change register's ledger (labels → hover), the departures board's churn sparklines (per-thread mark density IS the churn shape, on one shared axis), the board's open-question beacons (amber marks, viewport-pinned, cannot scroll away), and round 1's where-in-the-day rail. **What it settles:** heat column and seismograph trace go from "off this round" to permanently redundant. **What it is:** the ONLY chronology surface — the map speaks spine order in every layer; Mock A's interleave (mining opens, consolidation interrupts, mining returns, orchestration closes) lives here and nowhere else. (Pattern 37's break respected by division of labor: the rail speaks transcript order because that is the register's licensed job — chronology as a lens, never the spine's sort order.)

## 4 · The noise audit — every round-3 §1 element, one verdict each

Verdict = the least-detailed density band where the element first appears (it persists in denser bands; MAP = everywhere). **int** = renders only on hover/selection/summon. **CUT** = does not ship; revivable by Pi only. Biases applied: when in doubt, demote; instrument-grade/technical temperament counts against. Exempt by standing law: the three laws and the stroke-trust grammar.

| Element (round-3 §1) | Verdict | Why |
|---|---|---|
| Docking dots + type glyphs on dots | MAP | The tree's alphabet — typed dots are what make the abstract view a map, not a sketch |
| Status fill-states (hollow/half/solid; check/slash pair) | MAP | Status is spine reading; fill composes with type at dot scale, zero extra ink |
| Ghost station (false-alarm dot) | MAP | It IS a status; n10's conclusion must read at rest |
| Quest-marker amber ? badge | MAP | "Open questions loud at every altitude" is standing law |
| Numbered line bullets | MAP | Stream identity at every line head; the lead mark now that codes are cut |
| Interchange ring on target dot | MAP | The place is marked; the wire is OUTLINE ink — a ring is one glyph, not a crossing line |
| Full interchange connector | OUT | The run earns its ink only where headings give it context |
| Wire-hops | OUT | Small friendly arc; kills the false touches-every-lane read wherever a connector crosses |
| Underpass elevation (connector dimmed at rest) | OUT | A quietness device — keeps the at-rest surface calm; pro-friendly by construction |
| Directional chevrons | int | Direction renders when selection lifts the connector; at rest the ring says "linked," not "which way" |
| Route-focus ribbon | int | Hover/selection instrument by definition; never at-rest ink |
| Version rings | CUT | Churn triple-encoded (rings + tally chip + rail marks) and instrument-flavored; chip and rail survive; every revised dot gets quieter |
| Capsule chips → tally chips (version · residuals · open) | OUT | Pi's "tallies," verbatim — small, countable, JSON-derived; one chip grammar |
| Provenance chips (capsule + span) | SEC | Evidence ink belongs at reading measure and in the panel |
| ≈ prefix on summary-derived spans | SEC | One character of load-bearing trust; rides provenance chips |
| Glint (changed since last opened) | CUT | Per-viewer seen-state is a feature, not this round's ink; revives with patterns 11/39 |
| Pull-quote typography | SEC | Quotes need measure; editorial-warm, exactly the temperament asked for (also in the detail panel) |
| Force-push "decision re-derived" row | SEC | PR-timeline jargon off the surface; the rail shows a plain mark — the heavy label lives in n04's sector history |
| Terminus board (computed status roll) | OUT | At MAP the line head is bullet + verbatim title, unboxed; the roll is tally ink |
| 3-letter codes (MIN/CON/ORC) | CUT | Cockpit vocabulary — F1 telemetry temperament; bullets + verbatim titles carry identity everywhere |
| Spurs + buffer stops | OUT | Glyph-only stubs at OUTLINE; full spur cards in SECTOR; MAP elides dead ends whole (sanctioned) |
| Register column grid (FIDS/tabular ledger styling) | CUT | The instrument-grade form is the rejected temperament; the rail keeps the job in round-2's plain-ledger spirit |
| Typed rail event glyphs | MAP | Simplified from six to three friendly marks (dot / ◆ / amber ?); full typing on hover |
| Ruler gutter (printed line numbers) | int | Proportional positions stay; printed numbers are Perfetto temperament — numbers on hover only |
| Seam band (labeled, full width of rail) | MAP | Rail-borne; the chronology surface owns the seam, so it survives the most abstract view |
| Post-seam corner tab | OUT | The signal — tiny, countable — on title rows and cards |
| Post-seam paper shift | SEC | Ambience under the tab, never the only channel (law 2) |
| Stroke-trust grammar (solid/dashed/dotted) | MAP | EXEMPT — surface-wide law; how summary-derived survives even the abstract view |
| Masthead full strapline + operator roundels | CUT | "17 stations · 3 lines · 1 ghost" is inventory, not orientation; roundels are livery |
| Masthead (slimmed) | MAP | Verbatim title + date + amber open count — orientation plus the one number that demands action |
| Legend strip | int | Summoned via "?"; legend-as-linter survives as a design gate even unprinted |
| Empty-state art ("single-line service" et al.) | MAP | Kept — licensed only where there is no data to obscure; the friendliness ruling argues for the one charm instance, not against it |
| Departures board (rows, sparklines, beacons, seam ticks) | CUT | A Solari cockpit above the map is the rejected temperament twice over; the map's own top layer is the overview, the rail carries churn and beacons, the masthead the count |
| Yard strip + brush | CUT | Nothing overflows at MAP/OUTLINE on current mocks; revives on its original trigger (renders overflowing a screen) |
| Elevation ladder | MAP | Kept, trimmed to four rungs: lines < connectors < cards/rows < lifted selection + panel |

**Counts:** MAP × 12 · OUTLINE × 7 · SECTOR × 5 · on-interaction × 4 · CUT × 7.

## 5 · Open questions for Pi

1. **Which layer structuring** — L-A ladder / L-B two-layer / L-C hub-and-detail. The round-4 renders exist to settle this visually; nothing here locks it.
2. **If L-A wins: landing tier** — OUTLINE recommended (law-1-clean); choosing the quiet MAP as home requires the law-1 amendment noted in §2.
3. **Panel vs modal** for node detail — panel picked; modal is the standing veto alternative.
4. **Rail labels at rest** — dots-only (spec'd) vs round-2-style mini-labels always on: quieter vs more immediately informative. Both are friendly; pick by eye.
5. **Cut ratifications** — board, yard strip, FIDS ledger styling, version rings, 3-letter codes, glint: each revivable on request, none returns by default. Does he miss any in the renders?
6. **MAP hover peek** — the transient one-node title label: useful, or hover-noise that undermines the density boundary?
7. **Transit-fiction copy depth** (carried from round 3) — named moments like "single-line service" survive as captions under the kept empty-state license, or glyphs-only?
