# Research: How Software Makes Structure Narrate

Web research, 2026-07-05. Domain: systems where a network/timeline/pipeline view must answer "what was this, how did it go, what came out" at a glance. Fresh-eyes pass; no other design docs consulted.

## Executive answer

1. Pi's failure mode is documented in the metro-map literature itself: Shahaf et al. built maximally coherent metro lines and found them "discouraging — coherent, they were not important." Geometry alone provably cannot narrate; lines must be *labeled*, weighted by importance, and diverse in coverage (Information Cartography, CACM 2015).
2. Every successful system narrates by attaching **words to structure at three altitudes**: a goal/outcome banner (Wardley anchor, Strava summary panel), per-line and per-station labels (Shahaf line legends), and a generated prose synopsis docked with the graphic (GitHub Actions job summaries, incident.io AI postmortems). The map is the spine; prose is the story.
3. **Outputs must be first-class nodes**, not properties of steps: Dagster inverted "runs produce logs" into "runs materialize assets" — the deliverables shelf is a validated pattern, not a nice-to-have.
4. **Churn compresses by curation, not layout**: incident.io explicitly says a timeline should be "less of an audit trail, more of a story that hits the key moments and turning points"; Figma's fix for the micro-save thicket is named versions. Fourteen back-and-forth exchanges = one titled beat.
5. **Drill-in that deepens is semantic zoom / focus+context** (DOI trees, Strava split-hover): the station expands in place while the rest of the map dims but stays; navigation-to-another-screen is the anti-pattern Pi hit.

## Systems

### Information Cartography / "Metro Maps of Information" (Shahaf, Guestrin, Horvitz, Leskovec)
- **Problem**: complex news stories "spaghetti into branches, side stories, dead ends, and intertwining narratives" — readers with full coverage still don't understand what it was about.
- **Device**: lines = *coherent narrative threads* scored by their weakest transition (one bad hop kills a storyline); **coverage** forces lines onto diverse important topics; **connectivity** = minimum lines covering all stops, so linear stories render linear. Each line carries a *legend of its important words*; callout bubbles annotate key stops; a shared time axis runs beneath the map.
- **Steal**: line legends ("this line is the schema-refactor thread"); coherence as an edit test — if a line doesn't read as one evolving thread, re-cut the lines; time ruler under the map; annotation callouts on turning-point stations.
- **Kill**: their stops are document clusters chosen post-hoc for story quality; a session map can't discard events, but it can demote them.
- Sources: https://cs.stanford.edu/people/jure/pubs/cartography-cacm15.pdf ; https://arxiv.org/abs/2008.09367 (MetroSets)

### Metro-map layout literature (MetroSets, Beck's Tube map, project-plan metro layouts)
- **Problem**: showing membership/connectivity of pathways through a system.
- **Device**: Beck's insight — topology over geography; the *interchange* is the payload. MetroSets: element-in-multiple-sets = interchange station. Stott et al. laid out project plans as metro lines (one line per team, stations = tasks).
- **Steal**: interchanges must carry meaning — draw a fork/merge only where context actually transferred; if interchanges are decoration, the metaphor is wasted.
- **Kill**: octolinearity and uniform station spacing destroy time; the literature optimizes legibility of *structure*, and says nothing about goal or outcome — this genre is exactly where cartographer currently is.

### AI agent trace viewers (LangSmith, Langfuse, AgentOps)
- **Problem**: our exact domain — "what happened in this run?"
- **Device (and failure)**: waterfalls/trees/agent-graphs — structure without story; they answer "where did time/tokens go," never "what was this run for and did it succeed." Telling: Langfuse's newest fix for loopy agents is a flat, Cmd+F-able **Log View** — when the graph fails to narrate, users regress to reading text. AgentOps color-codes event types on a session waterfall; still an audit trail.
- **Steal**: their honesty about levels — session list (one row, one outcome) vs. session detail; tool calls surfaced above the payload.
- **Kill**: the waterfall itself; per-call granularity as the default altitude.
- Sources: https://langfuse.com/changelog/2025-11-05-langfuse-for-agents ; https://langfuse.com/docs/observability/features/agent-graphs ; https://docs.agentops.ai/v1/usage/dashboard-info

### GitHub Actions — job summaries over the job graph
- **Problem**: a green/red DAG says nothing about *what the run produced*.
- **Device**: `$GITHUB_STEP_SUMMARY` — each job writes its own Markdown synopsis (test tables, build reports), rendered *above* the graph on the run page; annotations (errors/warnings) float to the summary; artifacts get a dedicated shelf at the bottom.
- **Steal**: the layered page — synopsis prose on top, graph below, artifacts shelf; steps that self-report in prose, not logs.
- **Kill**: summaries are author-written per-step; cartographer must generate them.
- Sources: https://github.blog/news-insights/product-news/supercharging-github-actions-with-job-summaries/

### Dagster — asset-first runs
- **Problem**: pipeline UIs showed execution, users cared about data produced.
- **Device**: inversion — the **asset** (table, file, model) is the first-class node; a run is just "these assets got materialized"; materialization metadata ("what happened during a run": row counts, charts) hangs off the asset, not the task. Gantt chart is demoted to a debugging tab.
- **Steal**: the deliverables shelf, literally — "we produced a plan file" renders as an asset node with its history; sessions become "materializations of artifacts."
- **Kill**: assets need stable identities across runs; a one-off session has mostly one-off outputs — shelf, not catalog.
- Sources: https://dagster.io/blog/thinking-in-assets

### incident.io — timeline as curated story + AI postmortem
- **Problem**: the retrospective "what happened" genre, under time pressure.
- **Device**: timeline is explicitly "less of an audit trail, more of a story that hits the key moments and turning points"; auto-events (severity/status changes) mix with human-**pinned** messages; roles structure the arc (trigger → escalation → resolution → follow-ups); an AI writes the postmortem prose *from* the timeline, per-section.
- **Steal**: beat vocabulary for sessions (kickoff, pivot, blocker, resolution, deliverable); pin/promote gesture for turning points; generated synopsis whose every sentence cites a timeline element; follow-ups as first-class ending.
- **Kill**: incident severity gives free stakes/tension; sessions need the goal statement to supply stakes instead.
- Sources: https://help.incident.io/articles/7767182003-generating-your-incident-timeline ; https://docs.incident.io/post-incident/postmortem-ai

### Version-history storytelling (Figma named versions; GitHub PR conversation vs. files; GitKraken)
- **Problem**: minute-by-minute history is "great for crash recovery, terrible for storytelling."
- **Device**: **named versions** — a human (or agent) stamps a milestone title + description onto the stream, collapsing the micro-save thicket. GitHub renders the *same PR* twice: "Conversation" (chronological narrative with prose interleaved) and "Files" (structure); people read Conversation first. GitKraken's commit graph is the cautionary tale — pure structure, story only in the messages.
- **Steal**: two projections of one session — narrative view and map view — cross-linked; milestone stamps as the churn-compression unit.
- **Kill**: relying on humans to name versions mid-session; generate candidate beat titles instead.
- Sources: https://www.figma.com/blog/now-you-can-name-and-annotate-your-figma-version-history/

### User story mapping (Jeff Patton) + journey maps
- **Problem**: flat backlogs lose the big picture of what the product is *for*.
- **Device**: the **backbone** — a left-to-right spine ordered as "the order in which you'd tell the story," with detail hanging vertically beneath; the **walking skeleton** slice = smallest end-to-end telling.
- **Steal**: give the session map a backbone lane — the goal's major phases in narrative order — and hang the transit lines beneath it; the backbone is readable alone in 5 seconds.
- **Kill**: backbones are planned in advance; a session's backbone must be inferred after the fact.
- Sources: https://jpattonassociates.com/the-new-backlog/

### Wardley maps — the anchor
- **Problem**: diagrams where position is arbitrary carry no meaning.
- **Device**: the **anchor** (user need) at top; every component's position derives meaning from its chain to the anchor — "if you move a piece around without an anchor, it changes the meaning of the map completely."
- **Steal**: goal anchoring literally — the session goal is a fixed node/banner the whole map visibly hangs from; every line's label phrased as its relation to the goal ("blocking," "exploratory," "produced deliverable").
- **Kill**: the evolution x-axis; sessions don't commoditize.
- Sources: https://blog.gardeviance.org/2016/04/whats-in-wardley-map-and-need-for-cheat.html

### Scrollytelling steppers (NYT, The Pudding)
- **Problem**: readers can't self-navigate a complex graphic to its meaning.
- **Device**: the **stepper** — the graphic stays pinned while text steps scroll past, each step re-styling/zooming the *same* graphic; text walks you through the map, and the map never leaves the screen.
- **Steal**: a "replay" mode — the generated synopsis rendered as steps; each step highlights the corresponding line segment on the pinned session map. This single device fixes both "no story" and "drill-in teleports me."
- **Kill**: forced linearity as the only mode — keep free exploration as the default, stepper as the guided entry.
- Sources: https://pudding.cool/process/how-to-implement-scrollytelling/

### Focus+context / DOI trees / semantic zoom
- **Problem**: drill-down that discards context (Pi's "just switches me to something else").
- **Device**: **degree-of-interest** — the focused node enlarges and semantically changes representation (label → card → full transcript) *in place*; distant nodes shrink/aggregate but never vanish (SpaceTree, DOITrees; Cockburn's overview+detail survey).
- **Steal**: click a station → it inflates into a detail card on the map, its line stays lit, the rest dims; zoom levels change what a station *is* (beat → steps → exchanges).
- **Kill**: continuous geometric zoom (fisheye distortion) — discrete DOI levels read better.
- Sources: https://faculty.cc.gatech.edu/~stasko/7450/Papers/cockburn-surveys08.pdf

### Canvas boards vs. auto-graphs (Heptabase/Obsidian Canvas vs. Obsidian graph view)
- **Problem**: why do some node boards feel narratable and others like spaghetti?
- **Device**: **authored position**. Heptabase boards are narratable because a human *placed* things — position encodes intent; Obsidian's force-directed graph is computed, so position means nothing and no one can retell it.
- **Steal**: layout choices must encode session semantics (lane order = importance to goal, left-to-right = time), never solver convenience; anything the layout engine decides "for free" is narrative surface wasted.
- **Kill**: freeform canvas itself — sessions need automatic layout; the lesson is a constraint on it.

### Glance-summary genre (Strava activity page; Monzo unified feed; Flightradar24 playback)
- **Problem**: "understand what happened here in 10 seconds."
- **Device**: Strava — a **persistent summary panel** (distance/time/achievements) pinned above every view of the activity; splits list ↔ map ↔ elevation **hover cross-highlighting**; achievements as celebrated outcomes. Monzo/Flightradar: one legible stream with the noteworthy enriched, replay for the curious.
- **Steal**: the pinned session stat-card (goal, duration, N deliverables, verdict) that survives every drill-in; hover a synopsis sentence → its map segment lights up.
- **Kill**: fitness metrics have universal meaning; session metrics (tokens, tool calls) don't — the stat-card must lead with goal/outcome, not counts.
- Sources: https://support.strava.com/hc/en-us/articles/216919567-Run-Activity-Pages

## The transplant set (ranked)

1. **Goal banner + deliverables shelf** (Wardley anchor + Dagster assets): header states "Goal: X → Produced: plan-file.md, 2 decisions"; artifacts are drawn as terminus stations feeding the shelf. Fixes "what was this FOR" at rest.
2. **Line legends + beat-titled stations** (Shahaf): every line gets a 3–6 word thread label; stations get episode titles ("chose SQLite over JSON"), never tool names.
3. **Docked generated synopsis** (GitHub Actions summaries + incident.io AI postmortem): 4–6 sentence prose block above the map, every sentence hyperlinked to a line/station; hover cross-highlights (Strava).
4. **Beat compression via pin/promote** (incident.io + Figma named versions): loops of back-and-forth collapse into one station titled for the turning point, badge "14 exchanges," expandable.
5. **Stepper replay** (scrollytelling): synopsis-as-steps walking the pinned map — the guided first read of any session.
6. **In-place semantic zoom** (DOI trees): station click inflates a card on the map; line stays lit, context dims but remains. Kills the teleport.
7. **Meaningful interchanges only** (Beck/MetroSets): render forks/merges solely where context transferred; a backbone lane (Patton) carries the goal's phases above the lines.

## Contradictions worth flagging

- Shahaf et al. is direct evidence that a *well-laid-out* transit map still fails without importance-weighting and labels — layout work alone cannot rescue the current renders.
- When agent-trace vendors hit this wall, users regressed to flat text (Langfuse Log View); and incident.io's artifact of record is a prose doc, with the timeline as evidence. Strong signal: the prose synopsis may be the primary surface and the map its illustration — not vice versa.
