# Switchyard visual language — steal catalog for round 3

*Extends `ideation-patterns.md` (numbering continues at 44 — patterns 1–43 are not re-listed; cross-references by number point there). Chassis: `hybrid-ideation.md` Concept 2 "The Switchyard," chosen by Pi in Gate 1 round 2. His verdict carried a critique this catalog exists to fix: "a lot of visual clarity is being sacrificed there for text… there's not enough icons. There's not enough, like, feel and creative expression." His hard requirement: when a session has many parallel workstreams, each stream must be very clear. This is a fast breadth round organized by Switchyard ELEMENT, not by need. Every steal must make the surface clearer, not prettier — entries that risk decoration carry an honest cost note.*

*Standing non-negotiables still govern everything below: JSON is ground truth; node text verbatim; quotes never truncated; elide whole nodes, never shorten; corrections off the spine at rest; open questions loud at rest.*

## Three laws this catalog obeys

1. **Icons augment text; they never replace it at default altitude.** A glyph next to a verbatim title is clarity; a glyph instead of one is a puzzle. Icon-first rendering is legal only at a designed zoomed-out altitude (§H) where whole nodes are elided by rule.
2. **Every meaning has two channels.** Nothing is encoded in hue alone — every color signal is doubled by shape, fill, stroke style, or position (colorblind-safe by construction, print-safe for free).
3. **The hue budget.** Lane hues = stream identity, and nothing else. One reserved accent (amber) = open work, and nothing else. Everything remaining is achromatic ink on paper. Status is shape+fill (§B); trust is stroke style (§G). When every color question has exactly one answer, four parallel lanes stop being confetti — this law is the direct answer to Pi's parallel-streams requirement.

---

## A. Node-type iconography — topic / move / decision / open-question

**44. Station tick vs interchange roundel — TfL line diagrams (Beck grammar).** On the tube map, minor stations are small perpendicular ticks on the line; interchanges are bold ringed roundels — two weights of stop, ranked pre-attentively. On the Switchyard: **move** cards dock with a small tick-dot on the lane line; **decision** cards dock with a full double-ring roundel in lane color with a white core — larger, ringed, unmistakable. Clarity: the map's anchors (decisions) get the map vocabulary's own anchor glyph; scanning a lane for its decisions is the same learned act as finding interchanges on a tube line.

**45. Decision diamond — UML activity diagrams / railway signal shapes.** The decision card's header glyph is a filled diamond ◆, and the same diamond marks the register row where the decision landed (§F 75). Clarity: a borrowed grammar every developer already reads — "diamond = decision" needs no legend.

**46. Pull-quote typography as the quote glyph — editorial feature design (NYT/Guardian spreads).** The decision card's quote inset opens with an oversized quotation-mark ligature and sets the verbatim quote at a distinct size/leading from body prose — real pull-quote treatment, line span set as the citation line. Clarity: quoted-vs-inferred (a non-negotiable) becomes visible from across the room; typography does the provenance work before a single word is read. Quotes remain verbatim and untruncated — the treatment is furniture, never editing.

**47. Quest-marker loudness — RPG HUD design (WoW "!"/"?" markers).** The **open-question** glyph is a bold "?" badge that sits proud of the card — breaking the card's bounding box and slightly overlapping the lane line — in the reserved amber accent, with a static halo. A n17, B n12, C n11 each wear one. Clarity: "loud at rest" is a standing non-negotiable and games solved cannot-miss-this decades ago; breaking the bounding box is what makes it pre-attentive among uniform cards. Cost: a pulse animation is the tempting version — cap it at a slow breathe honoring `prefers-reduced-motion`, and the halo must survive as the static/print form, or the loudness dies on paper.

**48. Line bullet as the topic glyph — Vignelli NYC bullets / Tokyo Metro circles / Paris line discs.** The **topic** card's type glyph IS its lane's line bullet (colored disc, line number — §D 61), and the identical bullet recurs everywhere the topic is referenced: register entries, connector endpoints, breadcrumbs, the detail pane. Clarity: type glyph and stream identity collapse into one object — a topic card is unmistakably "the head of Line 2," not just a bigger card.

**49. Glyphs travel with the dot — Tokyo Metro station numbering discipline.** All four type glyphs render ON the docking dot at every altitude, not only in the card header: tick (move), roundel (decision), amber "?" (open question), bullet (topic head). Clarity: node type survives any zoom with zero text — the lane line alone is a typed sequence, which is what makes the icon-first altitude (§H) possible without inventing a second vocabulary.

## B. Status semantics — done / active / open / false-alarm / dead-end

**50. Fill-state dial — Linear's issue-status icons.** Status renders as the fill amount of the docking dot: hollow ring = open, half-filled pie = active, solid fill = done. Linear proved a five-state vocabulary lives legibly in a 14px circle using fill alone. On the Switchyard the fill-state composes with the type glyph (49): a decision roundel with solid core = done decision; A's n07 topic bullet with half-pie = batch 2 still pending. Clarity: colorblind-safe by construction (fill amount, not hue), readable on the line itself at every altitude.

**51. Buffer stop — rail track schematics.** Dead-end spurs terminate in the ⊥ buffer-stop glyph — the short bar across the track end that means "the line ends here on purpose." B's n05/n06 spurs each run a half-step off n04's dot and end at a buffer. Clarity: a killed hypothesis is precisely a track that was built, tested, and closed — real rail vocabulary, instantly read, and it gives dead-ends an ICON rather than only a dashed circle.

**52. Ghost station — Berlin U-Bahn Geisterbahnhöfe / disused stations on printed maps.** **False-alarm** nodes render as ghost stations: the docking dot is a dashed hollow circle with a single diagonal slash, the classic mark for a station that never opened — while the card itself stays at full text weight, because the spine reading is the conclusion ("notes only — no code ever existed, nothing lost") and must read at rest. A's n10 is the flagship. Clarity: "this stop is on the map so you know nothing is there" is the exact semantic job of a false alarm; the metaphor is doing argument, not charm.

**53. The closed-pair — GitHub's closed-as-completed vs closed-as-not-planned icons.** GitHub ships the exact terminal-state distinction the Switchyard needs: check-in-circle (completed) vs slash-in-circle (not planned), differing in glyph, not just color. Steal the pair drawn achromatic: done = check, false-alarm = slash. Clarity: pre-learned by every GitHub user; the two terminal states can never be confused even in grayscale.

**54. One accent, fixed semantics — F1 broadcast graphics.** F1 uses team colors for identity and exactly two universal colors (green/purple) whose meaning never varies. Transplant: the amber accent means OPEN — it appears on open-question badges, hollow status rings, open-entry rows in the register, and the masthead's open count, and appears nowhere else on the surface. Clarity: one eye-sweep finds all open work across four lanes; this is what makes "open questions loud" scale to parallel streams.

## C. Version & churn signals

**55. Countable rings, capped — tree-ring dating / Gerrit patchset ordinals.** Version rings on the docking dot render as discrete concentric strokes (lane color alternating with paper) — countable, not estimable — capped at three; v≥4 collapses to one heavy ring plus the numeral chip. n04@v3's two rings vs n09@v2's one is a subitizing read, no counting effort. Clarity: pre-attentive up to three, honest numeral beyond — never a vague "thicker border."

**56. Station-code capsule — Tokyo Metro numbered capsules (M-08).** The version chip is a metro station-code capsule: lane-color border, "v3" in tabular figures. Provenance chips reuse the identical capsule shape with span codes ("643–748"). Clarity: every chip on the surface shares one compact shape grammar — chips become scannable as a class instead of an assortment of ad-hoc badges.

**57. Force-push event — GitHub PR timeline's force-pushed line.** When a version bump superseded a *decision* (n04's history — the highest-stakes case, a build sequence re-derived by another topic's work), the register entry gets the force-push treatment: distinct glyph, heavier label ("decision re-derived"), not a plain bump tick. Clarity: not all churn is equal; the instrument should shout when an anchor moved and murmur when prose was consolidated.

**58. Churn heat column — GitHub contribution graph / Datadog host-map intensity.** A thin per-lane heat column beside the register: each stretch tinted by that lane's change-event density, luminance-ramped within the lane's own hue. "The mining lane changed a lot late in the day" becomes one glance. Clarity: churn location without counting ticks — the pre-attentive "changed a lot" cue Pi asked for. Cost: ramps must stay luminance-based within one hue per column or the register edge becomes confetti; if it fights the ticks, the ticks win and this is cut.

**59. The glint — Google Docs "See new changes" / Slack (edited).** Nodes bumped since Pi last opened the map carry a small glint dot on the version chip (pattern 11's seen-state, given a Switchyard surface). Clarity: separates "changed ever" (rings) from "changed since you looked" (glint) — two different questions, two different marks.

## D. Lane & line identity — the parallel-streams requirement

**60. Numbered line bullets — Vignelli NYC / Tokyo Metro / Beck's line index.** Every lane gets a numbered bullet (①②③… in spine order) in its lane color: on the lane header, at connector endpoints, on every register entry, in breadcrumbs and the detail pane. Clarity: hue-independent stream identity that survives grayscale, small sizes, and colorblindness — Pi's hard requirement answered with century-old, universally pre-learned technology. Number by spine order so bullets are stable across sessions of any topic count.

**61. Three-letter stream codes — F1 telemetry (VER/HAM/LEC) / airport codes.** Each topic also carries a three-letter code derived from its title (Mock A: MIN / CON / ORC; Mock C: REF / FLK / CID / REL), used at text sizes where a colored disc smears: register mini-labels, diff panels, connector labels. Clarity: stream identity that works in pure text; F1 proved twenty streams can stay distinguishable at a glance with codes + color together. Codes are derived furniture, not node text — they never substitute for the verbatim title anywhere the title is due.

**62. Line texture variants — engineering-works notation / Grafana series line-styles.** Lane lines get redundant stroke variants alongside hue: single stroke, cased stroke (color with darker outline), double stroke. Clarity: a second identity channel for adjacent same-luminance lanes. Cost — honest constraint: **dashes are forbidden here.** Dashed strokes are already the trust vocabulary (§G 76); a dashed lane line would say "this workstream is summary-derived." Solid-family variants only.

**63. Lane wash — Miro frames / FigJam sections.** Each lane's full column carries a 3–4% alpha wash of its line color; inter-lane gutters stay paper. Clarity: stream membership readable in peripheral vision even in the whitespace between cards — the eye never has to trace back to the line to know what lane it's in. Cost: at four lanes (Mock C) adjacent washes must pass a colorblind sim and never lift card backgrounds toward the text's contrast floor; the wash is the first thing dropped if it muddies.

**64. Terminus board — rail destination boards / Solari displays.** The pinned topic header card is styled as the line's terminus board: bullet + verbatim topic title + a computed status roll ("4 stations · 1 open · updated ×2"). All counts JSON-derived, no invented prose. Clarity: the pinned header row becomes the promised three-second session overview, and each header is unmistakably a different line's board rather than four similar gray cards — this is where lane identity is won or lost on Mock C.

**65. Route-focus ribbon — Citymapper / Transit app line focus.** Selecting any card thickens its lane's line one step and dims the other lanes' lines and washes one step (never the card text). Clarity: "which stream am I reading?" is always answered by the brightest ribbon, with zero re-layout. Cost: dimming applies to furniture only — unselected card text stays at full contrast or the law "text is the product" breaks.

## E. Interchange connectors & spurs

**66. Wire-hop — circuit-diagram crossing convention.** Where the interchange connector crosses an intervening lane's line (A: orchestration → n04 may cross the consolidation lane), it hops with a small semicircular arc — electronics grammar for "crossing, not connecting." Clarity: kills the false read that the connector touches every lane it passes through; on a four-lane canvas this is the difference between one causal edge and apparent spaghetti.

**67. Linked roundels — TfL interchange connector (the double-roundel/walking-link pill).** The connector's endpoints are places, not arrowheads: it emits from a small roundel on the source lane's line and terminates in a second ring wrapped around the target card's docking dot — n04's dot gains an interchange ring. Clarity: "these two stations are one interchange" is the pre-learned read; the cross-topic revision becomes a named place on both lines rather than a wire poking a card.

**68. Directional chevrons — wayfinding arrows / one-way street ticks.** Influence has direction (orchestration *revised* mining); transit maps are directionless, so this is the one place the Switchyard must add grammar rather than borrow: two or three small chevrons ›› along the run, pointing at the target. Clarity: causality direction without an aggressive arrowhead. Cost: sparse or nothing — a chevron every few hundred pixels; more and the connector becomes a zipper.

**69. Underpass elevation — metro-map tunnel shading / road-under-road casing.** At rest the connector renders one elevation below lane lines and cards — dimmed, passing behind everything, surfacing only at its two roundel endpoints. Selecting either endpoint (or n04) lifts it to the top elevation at full weight. Clarity: lanes stay visually sovereign and A's near-full-canvas connector stops being clutter — it reads as background infrastructure until it is the question being asked, then it glows. This is the delight moment that costs nothing: the reveal is the interaction.

**70. The siding, drawn honestly — track schematics.** The spur's geometry does the talking: track leaves the main line at 45°, runs a half-step at half the main line's stroke weight, ends at the buffer stop (51); the spur card sits at stub density on a ghosted wash. Clarity: "off the mainline, short, on purpose" is stated by geometry before any text is read — the demoted-at-rest rule made visible instead of merely enforced.

## F. The change register — the left-edge instrument

**71. Departure-board columns — Solari split-flap / airport FIDS typography.** Register entries set in tabular figures on a fixed column grid: line-position · lane bullet · event glyph · mini-label. Every row shares the grid. Clarity: scanning becomes mechanical — the eye walks one column at a time instead of reading rows; the register reads as one instrument, not a list of notifications.

**72. Micro-braid — git log --graph / GitHub network graph.** Inside the register, each lane owns a thin vertical thread in its color; change events are dots ON their lane's thread at their transcript position. The chronological braid banished from the canvas lives here at 10% scale, where it belongs — and since threads are parallel and never merge, there is no spaghetti to degenerate into. Clarity: Mock A's interleaving (mining opens, consolidation interrupts, mining returns, orchestration closes) is *visible* as alternating dot clusters across three threads while the lanes stay clean — the concept's "chronology as a lens" promise, made pre-attentive.

**73. Typed event glyphs — incident.io timeline / Grafana annotations.** Each register entry's glyph is typed with the same family as the canvas (49, at register scale): ● created · ◎ version bump · ◆ decision landed · ⊥ dead-end closed · amber ? opened · hatched ▮ seam. Clarity: the register answers "what kind of day was this" without reading a label; one glyph vocabulary across canvas and instrument means the legend is learned once.

**74. Ruler gutter — code-editor line-number gutters / Perfetto time ruler.** The register's spine is a true transcript-line ruler: faint line numbers every ~100 lines, entries positioned proportionally, so a long quiet tool-run reads as visible whitespace and a flurry reads as a dense cluster. Clarity: position means something — the register becomes an honest chronology instrument rather than an ordered list. Cost: proportional spacing wastes height on idle stretches; ship a compress-gaps toggle (Perfetto's own answer) with the seam and gaps still marked.

**75. Seismograph trace — strip-chart recorders.** Optional aggregate: the register's outer edge carries one thin continuous activity trace, tick density smoothed into an area line down the page — flat through quiet stretches, a visible bump at the mining lane's late flurry. Clarity: the day's rhythm in one glance without counting. Cost — flagged honestly: this is the most decoration-prone item in the catalog. It aggregates rather than renders JSON events, so it may never replace the discrete ticks, only accompany them; if it doesn't earn its column width on Mock B (one lane, modest churn), cut it first.

## G. Compaction seam & summary-derived provenance

**76. Drafting line-types — architectural working drawings (existing / demolished / proposed conventions).** Codify the stroke grammar once, apply it everywhere: **solid = raw-span-backed · dashed = summary-derived · dotted = residual/ghost.** Chips, docking-dot outlines, spur tracks, register entries, history-panel ghosts all obey it. Clarity: one stroke grammar, learned once, answers "how much do I trust this ink" on every element — the existing hollow/dashed vocabulary promoted from a chip style to a surface-wide law. (This is also why 62 bans dashed lane lines.)

**77. Engineering-works band — TfL disruption maps (hatched section notation).** The seam bar inside the register is a diagonal-hatched band across the register's full width at its true chronological position, labeled with the verbatim `compaction_events` note. Clarity: hatching is transit's native "service altered here" mark — loud, unambiguous, and honest about *where* the seam lives (the register owns chronology; the canvas would lie — the concept's own rule). C's seam after n13 is the flagship.

**78. Post-seam paper — print production's mid-book paper-stock change.** The painted-property half of the seam treatment: post-seam cards and versions shift card background one step (a just-perceptible paper change) AND carry a miniature hatched corner tab — the register band in miniature. Clarity: chronology-as-property, per the concept's seam rule, with the tab as the actual signal and the tint as ambience. Cost: the tint alone is too subtle to carry meaning and must never be the only channel — tab first, tint second, per law 2.

**79. Onion-skin history — Figma version compare / animation onion-skinning.** In the history panel, the superseded version renders under the current one at ~40% ghost with field-level change highlights (pattern 13's any-pair diff, given a visual body). When the diff crosses the seam (n01 v2→v3), the ghost layer itself renders in the dashed summary-derived stroke. Clarity: the diff shows not only what changed but what class of evidence backs each side — mock-c.md design question 4, rendered instead of debated.

**80. The ≈ honesty mark — weather apps' forecast-vs-observed split (grayed predicted hours).** Summary-derived provenance chips are forecast-grade evidence: hollow capsule, dashed border, and a one-character prefix — "≈ 610–642" — readable at chip size where dashed borders vanish. n01v3 and n12v2's `compact-1.summary` chips wear it. Clarity: the trust discount survives the smallest rendering the chip will ever get. Cost: one legend entry; self-teaching after the first click lands in a compaction summary instead of raw transcript.

## H. Density altitudes — icon-first, JSON-faithful

**81. Label-shedding generalization — Google Maps / cartographic generalization.** Zooming out sheds WHOLE stations by priority class and never shortens a title — exactly the sanctioned whole-node-elision rule, now with a principled ladder: open-question > decision > topic > versioned move > move (Maps keeps capitals while towns vanish). An elided station leaves its typed tick on the lane line, so the line never lies about how many stops exist. Clarity: every visible title is verbatim or absent; the familiar map behavior IS the non-negotiable, which means it never needs enforcement.

**82. Three named altitudes, stepped — Perfetto zoom levels / org-mode global cycling (pattern 3).** Designed altitudes, keyboard-cycled, never a continuous scale transform (pattern 41's cost honored): **A1 "platform"** — full cards, the default; **A2 "network"** — typed dots (49) + verbatim titles only; **A3 "line index"** — lane terminus boards + line geometry + decision roundels + amber badges only. Clarity: no mid-zoom mush where text is scaled-but-unreadable; each altitude is a designed view that is readable or absent, nothing in between. A2 is the icon-first altitude Pi's critique asks for — glyphs carry type/status/version, titles stay whole.

**83. Focus-lane altitude mixing — Perfetto expanded tracks / DOI without reflow (pattern 38's fix).** Per-lane altitude: the focused lane renders A1 while the others sit at A2 — lane slots and widths never change; unfocused cards shrink to glyph+title rows in place. Clarity: Mock C's four-lane squeeze answered without violating the fixed-slot law — read one stream deeply while three stay scannable and typed. Cost: uneven collapsed heights amplify the false-correspondence read (same-y ≠ same-time); the register highlight remains the only chronology truth, and the seam tab (78) must survive at A2.

**84. Size-ranked glyphs at altitude — Path of Exile skill tree / Zelda ability trees.** At A2/A3, glyph size ranks importance: decision roundels large, amber ? badges large, topic bullets large, move ticks small — the same priority order as the shedding ladder (81), expressed in size instead of survival. Clarity: zoomed out, the eye lands on anchors and open work first; skill trees prove a thousand-node graph stays navigable when keystones outweigh travel nodes.

## I. Color, depth, texture, personality

**85. The hue budget, stated fully — Beck's palette discipline + F1's fixed semantics (54).** Lane hues: max ~7, transit-grade, luminance-spread, identity only. Amber: open work only. All other ink achromatic. Status = fill (§B); trust = stroke (§G); churn = rings + register (§C). Clarity: the whole answer to "four lanes, five statuses, three trust classes, and versions on one canvas" — no channel ever collides with another, so nothing needs a tie-breaker rule.

**86. Elevation ladder — FigJam's sticky-note shadows, used sparingly.** Fixed z-order with matching shadow grammar: lane wash < lane lines < connectors (dimmed, 69) < spur tracks < cards (1px border, faint shadow) < pinned terminus boards (shadow strengthens only while scrolled) < lifted selection (card raise + connector glow). Clarity: depth encodes interaction state and nothing else — no element floats for looks, so when something lifts, it means something.

**87. Masthead as line-map frieze — in-car strip-map headers / printed network-map titles.** The session header: title verbatim in display type, date, a small "operator" mark for the surface (claude.ai and claude-code as two operator roundels), and a computed strapline — "17 stations · 3 lines · 1 open · 1 ghost station." Clarity: orientation and status bar in one, before the first card is read; every number JSON-derived, the strapline grammar fixed so it never drifts into invented prose.

**88. Depot art in empty states only — Duolingo empty states / game HUD "no active quests".** Micro-illustration is allowed exclusively where there is no data to obscure: an empty session ("no service today"), zero open questions (a small all-clear signal), Mock B's one-lane header badged "single-line service." Clarity: the personality budget spent only where it cannot compete with data — and Mock B's degenerate case is reframed as a legitimate service pattern instead of an embarrassment. Cost: this is the entire licensed surface for illustration; anywhere else it is decoration by definition.

**89. Paper, not chrome — editorial print restraint / Apple Freeform's canvas discipline.** The canvas is warm paper (near-black slate in dark mode); no gradients, no glass, no glow except the selection lift (86). If an art direction wants texture, it is sub-1% grain on the canvas only, never on cards. Clarity: card text contrast is the product; the background's one job is to disappear behind four colored lines.

**90. Legend as linter — printed transit-map legends.** A one-line legend strip at the map's foot: the five status glyphs, three stroke types, the bullet row, the ≈ mark — every symbol in use, nothing more, drawn in their exact shipped forms. Clarity: the grammar is learnable in one glance, and the legend doubles as a design gate — any glyph that can't justify a legend slot doesn't ship, which is this catalog's own enforcement mechanism against decoration.

---

## Art direction — three coherent personalities

Pi asked for feel and creative expression. These are three whole-surface commitments, not a mood-board average; every steal above renders in any of them, but each tunes typography, color, and icon temperament differently. Pick one; hybrids average away the feel.

### AD-1 · Network Modernism — transit-signage modernism

Johnston/Frutiger temperament. Typography: a humanist grotesque with true tabular figures (Inter/Public Sans class); caps reserved for bullets and stream codes. Color: paper white / slate dark, fully saturated transit-grade lane inks, black-ink glyphs, the amber accent at signal strength. Icons: geometric, stroke-consistent, roundel-first — the TfL/Tokyo lineage worn openly. **Reader-feel:** "the network is running" — calm municipal authority; the session reads as a system that is understood, even where it wasn't at the time.

### AD-2 · Working Drawing — technical drafting

Blueprint temperament. Typography: monospace for every chip, code, ruler, and register row (IBM Plex Mono/JetBrains Mono class); a plain grotesque for card text; thin rules everywhere. Color: drafting-paper white with graphite ink, lane colors desaturated one step so the line-type grammar (76) carries the trust story; an optional dark cyanotype variant. Icons: thin-stroke schematic — buffer stops, wire-hops, and sidings read like a signaling diagram. **Reader-feel:** an engineer's record of the day — auditable, provenance-first, every mark justified. **Honest cost:** round 1 cut the git-graph partly for coldness ("transparency, not tig") and Pi is a visual owner; this direction flirts with the same temperature and must buy warmth back through paper tone and generous spacing, or it reads as a tool, not a map.

### AD-3 · Sunday Supplement — warm editorial infographic

Feature-spread temperament. Typography: a display serif for the masthead and terminus boards (Tiempos/Source Serif class), humanist sans for card bodies, and the pull-quote treatment (46) at full editorial strength for decision quotes. Color: warm paper, softened-but-distinct lane inks, generous whitespace; the register styled as a printed timeline column; depot art (88) at its most charming. **Reader-feel:** a beautifully produced explainer of your own day — built for tired-end-of-day Pi; the map feels made, not emitted. **Honest cost:** the charm budget must live entirely in furniture — node text stays verbatim, quotes untruncated; if the editorial voice ever leaks into labels or straplines beyond the fixed computed grammar (87), it starts paraphrasing, which is a non-negotiable breach, not a style choice.

---

## For Pi to rule on (renderer must not decide these)

1. **Art direction** — AD-1 / AD-2 / AD-3. This is the round's actual gate.
2. **Primary stream identity mark** — numbered bullets (60) or three-letter codes (61) as the lead; both ship, one leads.
3. **The achromatic-status rule** — under the hue budget (85), done/active carry no hue of their own and only open work gets color (amber). Confirm Pi can live without green-means-done.
4. **Motion at rest** — is the open-question breathe (47) allowed, or static halo only?
5. **Register instrumentation ceiling** — ticks + micro-braid (72) is the floor; heat column (58) and seismograph trace (75) are additive and decoration-risky. How much instrument does he want?
6. **Depth of the transit fiction in copy** — glyph grammar only, or named moments too ("ghost station," "single-line service," "no service today")? The glyphs are load-bearing; the copy is personality.
