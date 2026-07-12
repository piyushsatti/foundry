# Mock D2 — schema v2: the story-capable cut of the same real session

**Surface:** claude-code · **Date:** 2026-07-05 · **Nodes:** 19 (ids unchanged from mock-d) · **Lines:** 3 (was 5) · **Beats:** 3 · **Artifacts:** 13 · **Intent:** v3 · **Frontier:** n17 · **Source:** the same real transcript as mock-d (`ae18157a-…jsonl`, captured at line 718).

**mock-d (v1) stays untouched as the structural-faithfulness record.** This file upgrades the *same* session data to schema v2 — the story-capable version. Nothing was re-mined from the raw transcript; every fact here comes from mock-d.json + mock-d.md.

## What changed vs mock-d, and why

Round 4 rendered mock-d and Pi couldn't tell what the session *was*, what it *meant*, or what it was *getting towards* — his own words landed on "we produced a plan file," which the JSON couldn't show. The diagnosis (`design/narrative-diagnosis.md`): mock-d carries a WHERE (parent tree, lines, forks, merges, provenance) with **no WHY** (no intent at any level) and **no WHAT-FOR** (no artifacts, no outcomes, no settlements). Six of seven glance-test questions fail *in the data*, not the render.

Schema v2 adds eight things on top of mock-d's structure, all converged on by the research passes (Shahaf's Information Cartography, chess.com Game Review, incident.io, Dagster, Golden Idol):

| # | Addition | Where | Answers |
|---|---|---|---|
| 1 | `session.intent`, versioned | `session.intent{version, text, history[]}` | Q1/Q2/Q7 — what was this FOR, and did the goal drift |
| 2 | `artifacts[]`, first-class | top-level array, `produced_by: node@version` | Q5 — "we produced a plan file" |
| 3 | `session.frontier` | `{node: "n17@1", detail}` | Q6/Q7 — where the cursor was at capture |
| 4 | Editorial line re-cut | `lines[]` — 3 narrative threads replace 5 mechanical streams | the heart; see below |
| 5 | `beats[]` | `{title, from_node, to_node}` — acts, not topics, not lines | Q3 — chapters |
| 6 | `moment` on every node | `breakthrough \| setback \| pivot \| grind` | key-moments default density |
| 7 | `settled` one-liners | on nodes with history (n07, n14) | Q4 — what the back-and-forth settled |
| 8 | Decision `standing` | `active \| expired` + `superseded_by` | the dead-rule fix: n02 is expired |

Everything real is preserved byte-exact: all four quotes, every provenance span, every residual, every history entry, all statuses, parents, versions, summaries. Two prose edits only, both because the re-cut retired the old line names (flagged in fabrication notes): `n03.title` "review lines" → "review lenses", and `n14`'s residual "Folded into line M" → "Folded into the RUNNABLE line". The build was done programmatically from mock-d.json to guarantee this.

## The editorial re-cut (addition 4 — the heart)

### Rationale

Mock-d's five lines were **mechanical**: M = "the chat window," D/I/L = "one background agent each," R = "the recovery workstream." Shahaf's core result says exactly why that failed to narrate: metro lines only tell a story when each is a *coherence-selected thread toward one question* — "maximally coherent" mechanical lines were "discouraging — coherent, they were not important." The chat window is not a question. An agent is not a question.

The session actually pursued **three questions/missions**, and those are the new lines:

| Line | Label (the question/mission) | `because` (verbatim where it exists) | Nodes |
|---|---|---|---|
| `REVIEW` | *What state is meditate in?* | "…I want you to do information gathering…" (Pi, line 8 — carries the mode; scope wording editorial, see friction #2) | n01–n07 |
| `RESCUE` | *Rescue the lost spec* | "So the first thing that makes sense to me is creating the README… we do have the file system of the laptop that originally created, Meditate… It's in the m n t folder." (Pi, line 196) | n08–n11 |
| `RUNNABLE` | *Make meditate run here* | "make a plan for the natural next moves" (Pi, line 340) | n12–n19 |

### What the re-cut demotes

- **Per-agent identity → segment metadata.** The three review agents (old lines D/I/L) are not stories; they are three parallel *branch segments of the review question*. They live as `lines[REVIEW].segments[]` (`REVIEW/design`, `REVIEW/impl`, `REVIEW/literature`), each with its fan-out node (n03) and landing node (n07); n04/n05/n06 carry a `segment` field. One question, three probes.
- **The mainline "M" → gone as an identity.** "Same chat window" carried two different missions; v2 splits it into REVIEW and RUNNABLE, joined by a `succession` edge. A surface is not a thread.
- **One-node lines → impossible by construction.** A line must be a thread; a single station is a segment or just a node.

### Topology against the new cut

```
REVIEW — "What state is meditate in?"
  n01──n02──n03━━━━━━━━━━━━━━━━━━▶ n07 (v1 ▸ v2) ─── answered, line ends
             │  fan-out ×3         ▲▲▲    ▲                        │
             ├─⟨design⟩     n04 ───┘││    │                        │ succession
             ├─⟨impl⟩       n05 ────┘│    │ merge-update           ▼
             └─⟨literature⟩ n06 ─────┘    │ (bumps n07 → v2)   RUNNABLE — "Make meditate run here"
                                          │                     n12──n13──n14──n15──n16──n17──n18──n19
  RESCUE — "Rescue the lost spec"         │                                        ▲frontier        ◇open
  n07@1 ──fork──▶ n08(n09──n10──n11) ─────┘
  (the lost-spec critical spawns the line;
   it loops back into the node it forked from)
```

- **The fan-out ×3** is now *intra-line*: three segments of REVIEW departing at n03 and landing together in n07. The mainline still visibly continues during the fan-out (n03's summary: scope notes, insurance wakeup).
- **The loop-back merge survives — flagship moment intact.** RESCUE has `from: {REVIEW, n07, version 1, relation: "fork"}` and `into: {REVIEW, n07, version 2, relation: "merge-update"}`. New in v2: the edge targets **node@version**, which fixes mock-d.md's known limitation that "merge-as-update vs merge-as-new-node is invisible" — `merge-update` + a version-addressed target says it in structure, not prose.
- **`succession` is a new relation** (see friction #1): RUNNABLE doesn't fork off a continuing REVIEW; REVIEW ends answered and RUNNABLE takes over from its final state (n07@2).

### Node mapping (ids unchanged; old line → new line)

| Node | mock-d line | mock-d2 line | segment | moment |
|---|---|---|---|---|
| n01 | M | REVIEW | — | grind |
| n02 | M | REVIEW | — | grind (decision, **expired**) |
| n03 | M | REVIEW | — | grind |
| n04 | D | REVIEW | REVIEW/design | setback |
| n05 | I | REVIEW | REVIEW/impl | setback |
| n06 | L | REVIEW | REVIEW/literature | breakthrough |
| n07 | M | REVIEW | — | pivot |
| n08 | R | RESCUE | — | grind |
| n09 | R | RESCUE | — | pivot |
| n10 | R | RESCUE | — | breakthrough |
| n11 | R | RESCUE | — | grind |
| n12 | M | RUNNABLE | — | grind |
| n13 | M | RUNNABLE | — | pivot |
| n14 | M | RUNNABLE | — | breakthrough |
| n15 | M | RUNNABLE | — | pivot |
| n16 | M | RUNNABLE | — | grind |
| n17 | M | RUNNABLE | — | grind (**frontier**) |
| n18 | M | RUNNABLE | — | breakthrough |
| n19 | M | RUNNABLE | — | grind (**open**) |

## Intent (addition 1)

Versioned like a node; shift boundaries anchored to *decision* nodes (the ruling, not the finding that precipitated it — see friction #7).

| v | Intent | Held from → shifted at | Shift cause |
|---|---|---|---|
| 1 | Assess meditate end to end — design, implementation quality, standing against the memory-curation field — as read-only reconnaissance: no plugin edits, no version bump, findings to .gitignored/. | n01 → **n09@1** | The synthesis's scariest critical (spec only on the old laptop) was ruled a workstream, not just a finding — recovery entered the goal. |
| 2 | Assess meditate **and recover its lost spec**: vendor the authority docs into the repo and build the README around them, so the verdict rests on a spec that exists here. | n09 → **n15@1** | Pi returned asking for "a plan for the natural next moves"; the plan's approval retired the read-only rule and turned assessment into repair. |
| 3 (current) | **Make meditate run on this machine**: execute the approved repair plan (workstreams A–E + no-live-mutation verification) on top of the recovered spec. | n15 → capture | — |

`session.title` is unchanged and stays a *structural* synopsis; `intent` now carries the goal. The two answer different questions and both belong in the masthead.

## Beats (addition 5)

The session's acts — mock-d.md's three narrated phases, now data. Episode titles, never tool names. Explicitly ≠ topics (recovery is topic n08) and ≠ lines (but see friction #6).

| Beat | Span |
|---|---|
| "Three lenses, one verdict" | n01 → n07 |
| "The spec was on the old laptop" | n08 → n11 |
| "From verdict to repair" *(opens after a ~5-hour gap)* | n12 → n19 |

The 5-hour gap — previously only rail whitespace and prose inside n12.summary — is now a beat-boundary `note`.

## Artifacts (addition 2)

Every produced thing named in mock-d's summaries, first-class. 13 entries:

| id | kind | name | produced_by | status |
|---|---|---|---|---|
| a01 | file | 00-scope-and-method.md — scope + firsthand findings | n03@1 | created |
| a02 | report | design/architecture review report | n04@1 | created |
| a03 | report | implementation-quality review report | n05@1 | created |
| a04 | report | memory-curation literature survey | n06@1 | created |
| a05 | report | SYNTHESIS.md — combined verdict, doc-update plan, phased code plan, open decisions | n07@1 | **updated** (by n07@2) |
| a06 | docs | vendored authority docs ×6 → plugins/meditate/docs/ | n10@1 | created |
| a07 | file | plugins/meditate/README.md — the plugin's front door | n11@1 | created |
| a08 | plan | repair plan — workstreams A–E + verification pass | n15@1 | created |
| a09 | code | bin/ helpers ×3 — meditate-lock, meditate-slug, manifest extract+validate | n16@1 | created |
| a10 | code | curate/curator/review skills rewired | n17@1 | updated |
| a11 | config | per-machine config split — example template + gitignored real config | n17@1 | created |
| a12 | code | apply/SKILL.md rewiring | n17@1 | **in-progress** |
| a13 | code | migrate_frontmatter.py hardened | n18@1 | updated |

Shelf rendering groups naturally: `synthesis · reports ×3 · docs ×6 · README · plan A–E · bin/ ×3 · skills · config · migrate` — with a12 as the shelf's live edge (it *is* the frontier's object). a05 needed an `updated_by` field beyond the spec'd shape (friction #4); a12 needed status `in-progress` beyond the diagnosis's `created|updated|superseded` enum (friction #5).

## Moments (addition 6)

Chess-review classification, one per node. Distribution: **4 breakthrough · 2 setback · 4 pivot · 9 grind.**

**Default render density: 10 of 19 stations full-size, 9 demoted to ticks** (n01, n02, n03, n08, n11, n12, n16, n17, n19) — with two overrides that must survive demotion: **n19 stays loud** (open-question status trumps grind) and **n17 carries the frontier caret** (you-are-here trumps tick size). n02, though a tick, must still show its expired standing (struck corner at tick scale or at first zoom).

Contentious calls, justified:

- **n07 = pivot, not setback.** The lost-spec finding inside it is the setback, but the node's narrative function is redirection: v1's finding spawned RESCUE and shifted the intent. When a node both drops the eval and changes the plan, the classification takes the plan change.
- **n05 = setback despite being excellent work.** Moments grade the story's fortunes, not the work's quality — reproducing a silent-corruption bug is a diagnostic win that delivers bad news.
- **n11 = grind despite producing the README.** Payoff lives on the artifact shelf (a07); moment class tracks *turns*. An artifact-producing grind node is exactly why the shelf exists.
- **n13 AND n15 both pivot.** Two real turns back-to-back: n13 turns findings→plan (Pi's return + "make a plan for the natural next moves"); n15 turns plan→execution and kills the read-only rule. Collapsing them would hide that the mode change was *ratified*, not just requested.

## Settled + standing (additions 7, 8)

- **n07.settled:** "The lost-spec critical is resolved: the authority docs live in plugins/meditate/docs/ and the synthesis reads against a spec that exists in this repo."
- **n14.settled:** "The manifest container is candidates:, the slug rule follows the canonical decisions log, and the verb lexicon is the 14-verb superset — the review's 'neither shape works' ambiguity is closed."

These are the forward-facing rewrite of `superseded_because` — churn rendered as what it *bought*, not as a correction count.

- **n02 `standing: "expired"`, `superseded_by: "n15@1"`** — the diagnosis's dead-rule example, fixed. The "information-gathering only / don't update the version number" rule died when the plan was approved. Note: n02's own summary says the rule holds "until a repair plan is approved" — the decision carried its own expiry condition, so the expiry is *derivable from the decision's text* (a real reducer could auto-detect conditional decisions).
- n09, n13, n15: `standing: "active"`. Expired ≠ completed — a fulfilled decision stays active unless something supersedes it.

## What a correct render must now show

Everything mock-d.md demanded (fan-out with a non-idle trunk, three-into-one merge, loop-back as in-place update, clean per-line spine, verbatim-vs-inferred distinction, residuals folded, mixed statuses, lines ⊥ tree) **plus**:

1. **The thesis slots fill from data alone** — no prose spelunking:
   > Set out to **assess meditate end to end, read-only** *(intent v1)* — the goal grew into **rescuing its lost spec** *(v2, at n09)* and then **making it run on this machine** *(v3, at n15)* · produced **13 artifacts** — 3 lens reports + a twice-written synthesis, 6 vendored spec docs, a README, an approved A–E plan, 3 bin/ helpers, a hardened migrate, rewired skills · open: **workstream E, the verification pass, the unapplied literature citations** *(n19)*, frontier **mid-edit in apply/SKILL.md** *(n17@1)*.

   Every slot cites a field: `session.intent` + history · `artifacts[]` · `n19` + `session.frontier`.
2. **The artifact shelf is populated** — 13 chips, each lighting its producing node; a05 shows its update by the loop-back; a12 renders as live/in-progress at the frontier.
3. **Key-moments default:** 10 stations full-size, 9 ticks; n19 loud and n17 careted despite being grind. The map should skim as: two setbacks and a breakthrough land in a pivot (n07) → a pivot–breakthrough rescue (n09, n10) → pivot, breakthrough, pivot (n13–n15) → breakthrough (n18) → open (n19).
4. **The loop-back merge survives the re-cut** — RESCUE departs n07@1 and lands as `merge-update` into n07@2. Still the single hardest moment, now with the fork's cause carried by `lines[RESCUE].because` (Pi's verbatim charter) instead of being buried in summary prose.
5. **The expired rule reads as not-current.** n02 must be visibly struck/dimmed wherever it appears; its `superseded_by` points at n15. A render that shows n02's ground rules as live law fails this mock.
6. **Beat bands** ("Three lenses, one verdict" / "The spec was on the old laptop" / "From verdict to repair") chapter the map, with the ~5-hour gap at the beat-3 boundary.
7. **Line labels narrate as questions.** REVIEW's terminus shows its `outcome` (answered), RESCUE's shows the resolution, RUNNABLE's shows the open state. Segments render as thin parallel strands *within* REVIEW's color, not as three independent line identities.

## Where schema v2 fought the real data (honest friction — Phase-3 findings)

1. **Line succession is not fork/merge.** RUNNABLE doesn't fork off a continuing line: REVIEW *ends answered* and RUNNABLE takes over from its final state. Had to invent `relation: "succession"`. Mock-d's mechanical mainline hid this by simply never ending — editorial cuts surface line *lifecycles* (a line can end) and need an edge vocabulary for it.
2. **The kickoff ask has no verbatim charter.** RESCUE and RUNNABLE got byte-exact `because` quotes; REVIEW could not — the full-review ask exists in mock-d only as summarized prose, so its `because` uses n02's mode-setting fragment ("I want you to do information gathering") with the scope editorial. Same class of problem as n15's UI-gate approval: *editorial lines demand charters the transcript doesn't always yield verbatim.* The verbatim rule needs a defined fallback for line-`because`, not just for decisions.
3. **Demoted structure doesn't disappear — it moves down a level.** Per-agent identity became segment metadata, but the render still needs each segment's fan-out and landing nodes, so segments carry their own mini-topology. Mock-d.md's open question ("is FORK-1 one fork event or three edges?") survives the re-cut unchanged, one level down.
4. **`produced_by: node@version` can't say who changed an artifact later.** SYNTHESIS.md was produced by n07@1 and rewritten by the loop-back at n07@2 — needed an extra `updated_by`. Real fix is probably per-artifact history, mirroring node history.
5. **Artifact status needed `in-progress`.** Capture mid-session means an artifact can be mid-write (apply/SKILL.md). The diagnosis's `created|updated|superseded` enum assumes a session at rest.
6. **Beats ≅ lines in this session.** The three beats coincide almost exactly with the three lines — *because* the editorial re-cut made lines narrative and this session ran its acts sequentially. The beats/lines distinction only pays off when acts interleave across lines (or a line spans acts); here it's near-redundant. Worth watching: if most real sessions are act-sequential, beats may be derivable from line boundaries + gaps rather than authored.
7. **Intent shift boundaries are judgment calls needing an explicit rule.** v1→v2 could anchor at n07@1 (the finding) or n09 (the ruling); v2→v3 at n13 (the ask) or n15 (the approval). Chose *decision nodes* both times — findings create pressure, rulings change the goal — but a reducer must adopt that rule consciously.
8. **Moment classification fits container nodes poorly.** n01/n08/n12 are topics — grading them "grind" is filler, not judgment. Topics probably shouldn't take moments at all; their weight is the sum of their children.

## Sanitization + fabrication notes

**Sanitization holds.** No hostnames, IPs, usernames, or work identifiers anywhere; the n10 residual's meta-note about excluded identifiers is preserved verbatim from mock-d. Checked programmatically at build time.

**Inherited from mock-d, unchanged:** all four quotes byte-exact (n02, n09, n13 are Pi's transcribed voice; **n15's quote remains the assistant's articulation** — the plan-mode gate leaves no user prose; flag preserved in the node summary); all provenance spans; all residuals, history, statuses, versions, parents; `captured_at_line: 718`.

**Inferred / editorialized in this upgrade (inferences by nature — flagged):**

- **Intent wording (all three versions).** The *shifts* and their anchor nodes are grounded (n02's quote, n09's quote, n13's quote + n15's approval), but the sentences are mine. No transcript line says "the goal is now X."
- **Beat titles.** "Three lenses, one verdict" / "The spec was on the old laptop" / "From verdict to repair" are authored episode titles; the phase *boundaries* come from mock-d.md's three-phase narration and the 5-hour gap in n12.summary.
- **Line labels and REVIEW's `because` scope note** (friction #2). RESCUE's and RUNNABLE's `because` texts are byte-exact quotes.
- **Line `outcome` one-liners** — a small extension beyond the eight mandated additions (quest-log research: line-head objective + retrospective); derived from n07/n11/n19 summaries.
- **Moment classes** are judgments (contentious ones argued above); `settled` sentences are rewrites of the corresponding `superseded_because` entries, no new facts.
- **Two prose edits to mock-d text**, both because the old line names died with the re-cut: n03.title ("review lines" → "review lenses") and n14's residual ("line M" → "the RUNNABLE line"). Everything else that came from mock-d is byte-identical, enforced by the build script's fidelity check.
- **Not shelved as an artifact:** the memory update mentioned in n07's history ("synthesis and memory were updated in place") — judged session-external state, not a session product. Debatable; noted for Phase 3.
