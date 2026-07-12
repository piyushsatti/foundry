# Ideation: rendering + interaction paradigms for the session map

*Phase 1, step 2 — divergent pass. This is a WIDE option map, not a shortlist. No ranking, no recommendation; narrowing happens with Pi, visually, against the three mocks.*

**What every paradigm must answer (from the brief):** clean top-to-bottom read ("what we did and how we approached it"); five demonstrables — (a) click-to-expand residual detail, (b) node-history access, (c) provenance to transcript spans, (d) updated-in-place vs genuinely-new node, (e) a compaction seam mid-session. Stress cases refer to **Mock A** (3 parallel workstreams + false-alarm fold), **Mock B** (debugging with dead ends), **Mock C** (mega-session, pivots, compaction).

## Index

| # | Paradigm | Borrowed from |
|---|----------|---------------|
| 1 | Lab notebook / literate document | Jupyter, Notion |
| 2 | Outliner with focus-and-context | Workflowy, org-mode |
| 3 | Spine + marginalia canvas | Illuminated manuscript, arterial road with lay-bys |
| 4 | Metro map | Beck's tube map |
| 5 | Git-graph spine | `git log --graph`, amend/reflog |
| 6 | Storyboard / film strip | Film production, contact sheets |
| 7 | Code-folding editor + minimap | VS Code, GitLens |
| 8 | Marey string diagram | 19th-c. train timetables |
| 9 | Stratigraphic column | Geology core samples |
| 10 | PR review split pane | GitHub files-changed |
| 11 | Mind map / radial canvas | XMind, concept maps |
| 12 | Gantt / swimlanes | Project schedules |
| 13 | Space-filling zoomable hierarchy | Treemap, icicle, ZUI |
| 14 | Transcript-with-marginalia | Talmud page, annotated screenplay |
| 15 | Wiki article + revision history | Wikipedia apparatus |
| 16 | Expedition map / fog-of-war | Game cartography, survey maps |

---

## 1. Lab notebook / literate document

**Core metaphor:** the session as a Jupyter/Notion document — sections are topics, cells are moves, prose-first.

**Spine legibility:** literally reading a document top to bottom; H2s = topic nodes, one summary cell per move. The strongest possible "reads clean" story because it *is* reading.

**Five demonstrables:**
- (a) Residuals: collapsed inline callouts — `▸ false alarm: "missing code repo" — resolved, no repo ever existed` — one line at rest, expands in place.
- (b) History: per-cell version chip (`v3`) opening a stacked deck of prior cell renders (Notion page-history, scoped per block).
- (c) Provenance: footnote superscripts per claim → transcript span in a side sheet.
- (d) Updated vs new: updated cell keeps its position and increments its version chip; new cell slides in with an accent bar. *Position stability is the update signal — updated nodes never move.*
- (e) Compaction: full-width chapter-break rule ("— context compacted here —"), styled as structure, not error.

**Stress case:** Mock A. A document is a sequence machine; three interleaved workstreams must be either de-interleaved (lying about time) or interleaved (destroying topic coherence).

**Steal/kill:** Steal position-stability + version chips as the mutation signal. Kill: parallelism has nowhere to live.

## 2. Outliner with focus-and-context

**Core metaphor:** Workflowy/org-mode — the session as an infinitely collapsible bullet tree with hoisting.

**Spine legibility:** top-level bullets are the whole story in ~7 lines; each disclosure level is a lower altitude. Reading depth is user-controlled per branch.

**Five demonstrables:**
- (a) Residuals: grayed bullets collapsed by default under their parent with a count badge (`+2 dead ends`).
- (b) History: hover clock icon per bullet → inline diff of that bullet's text versions.
- (c) Provenance: every leaf carries a ¶ jump-link to its span (org-mode link style).
- (d) Updated vs new: bullet glyph as state — change-dot on revised bullets, hollow vs filled for new; glyph becomes a legend.
- (e) Compaction: a divider bullet at top level — structurally just another bullet, which is the tell that this paradigm has no seam vocabulary.

**Stress case:** Mock C. Deep + wide outline makes focus fight context, and a compaction seam is invisible in a pure hierarchy (time is not an axis anywhere).

**Steal/kill:** Steal hoisting — zoom-into-a-node as the primary altitude control. Kill: everything is a bullet; decisions, dead ends, and topics are indistinguishable without inventing an icon language.

## 3. Spine + marginalia canvas

**Core metaphor:** illuminated manuscript / arterial road with lay-bys — one central column is the story; margins hold everything demoted.

**Spine legibility:** the center column reads clean top-down; margins at rest are dim stubs tethered to their fork point.

**Five demonstrables:**
- (a) Residuals: parked in the margin at the y-position where they forked, thin tether to the spine node; expand in place in the margin.
- (b) History: card edges peeking from *behind* each spine node (depth = version count); click fans the stack out.
- (c) Provenance: a persistent right-edge **transcript rail** — a skinny ruler of the raw session; each node projects a bracket onto it showing its span; click the bracket for raw text.
- (d) Updated vs new: card thickness (stacked edges) says "has history"; a new node is a single flat card. Thickness = churn, position = story.
- (e) Compaction: the seam crosses the whole canvas — spine, margins, and rail — and the rail changes texture after it (new source file).

**Stress case:** Mock A. Three workstreams compete for ONE spine; margins fill with tethers and "clean center" degrades into a braid.

**Steal/kill:** Steal the transcript rail with span brackets — provenance as an always-visible ruler, not a buried link. Kill: margin real estate is finite; a messy session inverts the hierarchy, with more content in margins than spine.

## 4. Metro map

**Core metaphor:** Beck's tube map — workstreams are colored lines, nodes are stations, cross-stream decisions are interchanges. Laid vertically: time flows down, lines run parallel.

**Spine legibility:** read the trunk line top-down for the main narrative; other lines join and leave it. Legible only if a trunk exists.

**Five demonstrables:**
- (a) Residuals: dead-end spurs — short thin stubs off a station ending in a "closed station" glyph (dashed open circle); click to expand the spur.
- (b) History: click a station → "station history" panel; superseded versions are ghost stations behind it.
- (c) Provenance: station panel → "view this line section" → transcript span.
- (d) Updated vs new: revised station accretes interchange-style rings per revision; new station is a plain dot.
- (e) Compaction: a **fare-zone boundary** — a shaded band crossing all lines at one vertical position. Elegant: it hits every workstream simultaneously, which is what compaction actually does.

**Stress case:** Mock B. Single-threaded debugging is one lonely line with stubs; the entire multi-line vocabulary buys nothing.

**Steal/kill:** Steal the fare-zone band (global seam crossing all lanes) and the closed-station glyph. Kill: metro maps need a stable line set; sessions birth and kill workstreams mid-flight, and a map that re-routes on every update reads as chaos.

## 5. Git-graph spine

**Core metaphor:** the session as a continuously rebased branch — the map is `git log --oneline --graph` of the *story*, where rework is `commit --amend`.

**Spine legibility:** the linear first-parent chain read top-down is the clean narrative; side branches are residuals merged back.

**Five demonstrables:**
- (a) Residuals: dead ends are branches closed with a "no-op merge" bubble, collapsed to the bubble; click expands the branch.
- (b) History: **the reflog** — the visible graph is the clean rebased history; each node's superseded versions live one level down in a per-node reflog panel. Perfect native vocabulary.
- (c) Provenance: every node has a "hash" that IS the span pointer (transcript path + lines); click = open span, like clicking a commit for its diff.
- (d) Updated vs new: amended nodes get the amend badge / changed-hash styling; new nodes are plain commits. Git users already read this fluently.
- (e) Compaction: a **graft point** — the glyph for "history before here was condensed into a synthetic root."

**Stress case:** Mock A. Three long-lived parallel branches with cross-merges is exactly where git graphs go spaghetti.

**Steal/kill:** Steal the log-vs-reflog split — polished history for reading, full mutation record one level down; this IS the reducer's philosophy drawn as UI. Kill: demands git literacy as UI literacy, and it's visually cold — Pi wants transparency, not `tig`.

## 6. Storyboard / film strip

**Core metaphor:** the session as scenes — each node a frame with a title and a thumbnail (key diff, artifact, or verbatim quote); topics are acts.

**Spine legibility:** read frames in order — vertical contact sheet or horizontal reel; act-break cards mark topic boundaries.

**Five demonstrables:**
- (a) Residuals: a **deleted-scenes tray** under each act — grayed half-size frames; click to restore to full frames.
- (b) History: **takes** — a "take 3" counter on the frame; click cycles superseded renders of the same scene.
- (c) Provenance: "watch the dailies" — frame → raw transcript span.
- (d) Updated vs new: take-counter badge vs pristine frame; a reshot frame keeps its slot in the reel.
- (e) Compaction: an intermission / act-break title card — "the reel was re-cut here."

**Stress case:** Mock C. Hundreds of frames make the strip endless and thumbnails meaningless at that count.

**Steal/kill:** Steal the takes vocabulary — "take 2" is the friendliest possible language for supersession — and the discipline that every node earns one *visual* (a diff, a quote), not just text. Kill: most session moves have no natural picture; thumbnails degenerate into text cards, i.e. a worse notebook.

## 7. Code-folding editor + minimap

**Core metaphor:** the session as a source file — topics are top-level functions, moves are statements, everything folds, minimap on the right.

**Spine legibility:** fold everything to level 1 and the file reads as a table of contents; unfold selectively to read the story.

**Five demonstrables:**
- (a) Residuals: folded regions with a summary line — `▸ // dead end: pip-cache theory — disproven (12 lines)`.
- (b) History: gutter blame — per-line change markers; click for that line's version history (GitLens inline blame).
- (c) Provenance: cmd-click "go to definition" jumps to the transcript span; the transcript is the compiled source.
- (d) Updated vs new: **gutter change bars** — blue = modified in place, green = new — the exact modified/added vocabulary editors already ship.
- (e) Compaction: a `#region compacted` seam — a fold that opens to an archive pointer rather than inline content.

**Stress case:** Mock A. A file is one sequence; three workstreams interleave into noise or get de-interleaved into fake "functions."

**Steal/kill:** Steal the **minimap** — a full-session silhouette showing where density and churn live, doubling as the scrollbar — plus gutter change bars. Kill: it looks like *work*; rendering your conversation as an IDE buffer makes the transparency tool feel like more IDE.

## 8. Marey string diagram

**Core metaphor:** E. J. Marey's graphical train timetable — time runs down, workstreams are vertical tracks, and the session's attention is ONE string weaving between tracks; nodes are beads where the string did work.

**Spine legibility:** the string itself, read top-down, is literally "what we did, in order, and where attention went."

**Five demonstrables:**
- (a) Residuals: **pinched loops** — the string entered a dead end and came back; at rest the loop is pinched into a single bead with a loop glyph; click to re-inflate the excursion.
- (b) History: beads accrete rings per revision (tree-ring bead); click for versions.
- (c) Provenance: the y-axis IS transcript time — drag-select any vertical extent to open the raw span; the axis is the affordance.
- (d) Updated vs new: when later work revises an earlier bead, a thin return-thread arcs up the page to it — "we went back" made visible; new beads just continue the string.
- (e) Compaction: a horizontal cut across all tracks with a visible axis re-scale (denser above the cut) — standard axis-break vocabulary.

**Stress case:** Mock B makes the weave trivial (one track), and Mock C's many return-threads risk a cat's cradle.

**Steal/kill:** Steal the pinched loop — a dead end as a literally collapsed excursion — and time-axis-as-provenance. Kill: time primacy contradicts the mandate; this is a log-faithful paradigm in better clothes.

## 9. Stratigraphic column

**Core metaphor:** the session as a drilled core sample — layers are phases/topics, layer thickness is effort, depth is time.

**Spine legibility:** the layer log read down the column, with labeled strata, is the narrative; thickness gives free "where the day went" at a glance.

**Five demonstrables:**
- (a) Residuals: **lenses/intrusions** — a dead end is a small hatched lens embedded in its layer; click to expand its mini-column.
- (b) History: metamorphism — a revised layer shows recrystallized texture; click for prior composition.
- (c) Provenance: the core-depth scale = transcript offsets; every layer maps to a depth interval; click depth for raw span.
- (d) Updated vs new: texture (recrystallized vs fresh deposit); new layers deposit on top.
- (e) Compaction: **the unconformity** — geology's exact concept for "record lost here, deposition resumed," drawn as the standard wavy erosional line. No paradigm has a better native compaction glyph.

**Stress case:** Mock A. Parallel workstreams need three correlated columns (a fence diagram); single-column strata are strictly sequential.

**Steal/kill:** Steal the unconformity as THE compaction seam glyph — a wavy line meaning "material is missing here and everyone knows it" — plus thickness = effort. Kill: metaphor overload; Pi shouldn't need a geology legend to read his own session.

## 10. PR review split pane

**Core metaphor:** the session as a pull request against the state of the world — left pane is the tree of nodes (files changed), right pane is the selected node's "diff."

**Spine legibility:** the left tree top-down is the summary; the right pane is detail-on-demand. Master-detail: the spine is a table of contents, not a story.

**Five demonstrables:**
- (a) Residuals: GitHub's collapsed-**outdated** sections in the right pane, repurposed for dead ends.
- (b) History: a per-node "commits" tab — current state by default, flip to version history with diffs between any two versions.
- (c) Provenance: every line in the right pane is line-linkable to the transcript, like linking a diff line.
- (d) Updated vs new: the left tree badges nodes **M / A** — the file-status vocabulary verbatim.
- (e) Compaction: a "force-pushed — comparison limited" event marker in the timeline ribbon; GitHub already renders this honest seam.

**Stress case:** Mock B. The interesting content (dead ends, hypotheses) hides behind the master-detail wall; the left tree reads "investigated, investigated, fixed" and Pi clicks nine times to get the story.

**Steal/kill:** Steal M/A badges for updated-vs-new AND the outdated-comment mechanic (already committed for Phase 2 annotations) — note this paradigm is the natural *host* for the Phase 2 review-packet flow: pending comments + submit-as-one-review is native here. Kill: master-detail murders top-to-bottom narrative.

## 11. Mind map / radial canvas

**Core metaphor:** session center → topics radiate → moves and decisions branch outward; XMind/concept-map.

**Spine legibility:** none native — must be faked with a clockwise reading convention or a numbered walk-path (①→②→③) drawn over the map.

**Five demonstrables:**
- (a) Residuals: withered branches collapsed to a bud glyph at the fork; click to bloom.
- (b) History: node halo/rings per revision; click halo for versions.
- (c) Provenance: per-leaf "root" link to its span.
- (d) Updated vs new: haloed node vs plain new leaf; branch **thickness = churn**.
- (e) Compaction: incoherent — radius isn't time, so no seam can be drawn; best effort is a badge on affected nodes.

**Stress case:** Mock C. Pivots + compaction: no time axis means a pivot-heavy mega-session becomes an undifferentiated starburst, and the seam has no home.

**Steal/kill:** Steal branch-thickness-as-effort — glanceable "where did today actually go." Kill: fails the core mandate outright; no clean top-to-bottom read exists in radial space. Included as the clearest example of spatiality purchased at narrative's expense.

## 12. Gantt / swimlanes

**Core metaphor:** workstreams as horizontal lanes, nodes as bars in time — the day as a retrospective project plan.

**Spine legibility:** lanes stacked by importance, each read left-to-right; per-workstream legibility is strong, whole-session top-down read is weak.

**Five demonstrables:**
- (a) Residuals: notched bars containing folded dead ends; click expands sub-lanes.
- (b) History: ghost outlines behind the current bar (earlier extents/labels).
- (c) Provenance: bars are extents, so bar → time range → span is native.
- (d) Updated vs new: hatched bar with revision count vs solid new bar.
- (e) Compaction: a vertical dashed line across all lanes with an axis-break (time compresses to its left).

**Stress case:** Mock B. One lane of sequential bars is a worse timeline — and rework renders as *appended* bars, the exact lie the brief forbids.

**Steal/kill:** Steal the cross-lane vertical seam and duration encoding (which nodes ATE the session). Kill: Gantt grammar is append-primal and duration-primal; upsert semantics fight it everywhere.

## 13. Space-filling zoomable hierarchy

**Core metaphor:** treemap/icicle with semantic zoom (ZUI) — the session as a bounded rectangle; topics tile it; area = effort/tokens; zooming descends the hierarchy.

**Spine legibility:** at rest it's a "state of the session" dashboard, not a story; the ordered-icicle variant (leftmost = first) preserves sequence, the treemap variant abandons it.

**Five demonstrables:**
- (a) Residuals: dimmed tiles shrunk to slivers at rest; click for temporary fisheye inflation.
- (b) History: z-axis **peel** — click-and-hold peels the current tile to reveal the version beneath.
- (c) Provenance: **semantic zoom terminates at the transcript** — keep zooming and you hit bedrock: the raw span. Zoom = altitude from map to ground truth.
- (d) Updated vs new: tile keeps position/color but gains a dog-ear fold per revision; new tile enters with a border flash.
- (e) Compaction: ordered-icicle mode gets a vertical seam band; treemap mode has no coherent seam (no time axis).

**Stress case:** Mock B. Deep-and-narrow debugging wastes the canvas on one dominant column of slivers; space-filling wants breadth.

**Steal/kill:** Steal zoom-as-provenance — the cleanest possible drill-down story, one gesture from overview to raw log. Kill: area encodings answer "where did effort go," not "what did we do" — analytics wearing a map costume.

## 14. Transcript-with-marginalia

**Core metaphor:** a Talmud page / annotated screenplay — the raw transcript stays primary; the map lives in a structured margin, with brackets grouping transcript spans into semantic nodes. The inversion of every other entry: map as overlay, not replacement.

**Spine legibility:** the margin column read top-down is the clean story; the bracketed transcript bulk collapses under each note ("show the 40 messages this node summarizes").

**Five demonstrables:**
- (a) Residuals: bracketed regions whose margin note is a gray "dead end" chip; the region auto-collapses; click the chip to reopen the raw exchange.
- (b) History: margin notes are versioned stickies; superseded notes stack behind the current one.
- (c) Provenance: trivial — the note is physically attached to its span. The only paradigm where provenance *cannot drift*.
- (d) Updated vs new: rewritten note shows an edit tick + stack; a node consolidating scattered evidence shows **multi-span tethers** — several bracket lines converging on one note, making "this consolidates dispersed work" visible.
- (e) Compaction: the substrate itself changes — pre-compaction transcript replaced by a summary block behind a seam banner; notes above the seam point into the archived file.

**Stress case:** Mock C. A mega-session's transcript dominates by mass; the clean read requires collapsing ~95% of the substrate — at which point, why is the transcript primary?

**Steal/kill:** Steal unbreakable provenance (annotation ON the evidence) and multi-span tethers. Kill: it is log-faithful by construction — the brief's entire bet is that the map, not the log, is the primary surface. Worth mocking precisely as the null hypothesis the map must beat.

## 15. Wiki article + revision history

**Core metaphor:** the session as a living encyclopedia entry — "What we did today," continuously edited, with Wikipedia's full apparatus: lede, sections, footnotes, revision history, hatnotes.

**Spine legibility:** lede + section structure is the most literate top-down read available; the lede doubles as an auto-maintained session abstract.

**Five demonstrables:**
- (a) Residuals: collapsed endnotes / a "disputed" hatnote per section — dead ends live in the apparatus, never the body text.
- (b) History: the revision-history tab, per section — view any prior state and **diff any two versions**; wiki diffing is the most mature version-viewing UX in existence.
- (c) Provenance: **citations** — every claim carries [n] into a references panel of transcript spans; "citation needed" styling marks unvalidated reducer claims, mapping exactly onto the brief's validate-pass and quoted-vs-inferred ruling.
- (d) Updated vs new: section edit-timestamps and updated markers; new sections appear in the TOC with a new-badge.
- (e) Compaction: the article-split hatnote — "this article summarizes material archived at X."

**Stress case:** Mock A. An article is linear; parallel workstreams flatten into serial sections and simultaneity is lost (arguably acceptable for an end-of-day read, fatal for a live one).

**Steal/kill:** Steal the citation apparatus with "citation needed" as the visible marker of unverified reducer output, and diff-any-two-versions for node history. Kill: prose invites the reducer to write paragraphs, and long reducer prose is where summarization drift breeds — the looser the node grammar, the less trustworthy the tool.

## 16. Expedition map / fog-of-war

**Core metaphor:** the plugin's own name, taken literally — the session as explored territory: regions = topics, trails = paths of work, camps = decisions, trails that stop = dead ends, fog = the unexplored.

**Spine legibility:** maps aren't linear — legibility comes from an **expedition log strip** pinned to the map edge (numbered route ①→②→…) read top-down while glancing at territory.

**Five demonstrables:**
- (a) Residuals: trails that visibly stop at an ✕ cairn ("turned back here"); click the cairn for the excursion.
- (b) History: settlements grow — a revised node's camp upgrades (camp → village); click for founding history.
- (c) Provenance: survey grid references — every feature carries a grid ref = transcript span.
- (d) Updated vs new: grown settlement vs fresh camp; re-trodden trails render doubled.
- (e) Compaction: "here the old map ends" — the region before the seam rendered in faded archival parchment behind a torn edge.

**Stress case:** Mock B. Debugging is a corridor, not a territory; spatial metaphor buys nothing deep-and-narrow, and the fog becomes decoration.

**Steal/kill:** Steal **fog for open questions** — rendering what was NOT explored (open threads, unanswered questions) as first-class negative space; no other paradigm renders the unknown at all. Kill: whimsy tax undercuts a work tool's credibility, and free 2D placement forces the reducer to invent geography — unstable layout on every update.

---

## Axes of the space

The sixteen paradigms differ along six real dimensions. This is the map of the option space — still no ranking. A chosen direction is effectively a coordinate on these axes, and hybrids can mix coordinates (e.g. a notebook spine with a treemap's zoom-to-transcript).

1. **Layout driver: time vs structure.** What determines where a node sits — chronology (Marey, Gantt, storyboard, stratigraphy) or semantics (outliner, mind map, treemap, wiki)? Hybrids anchor structure but preserve order (notebook, git-graph, metro). The brief's upsert semantics pull toward structure; the compaction seam pulls back toward time — every paradigm negotiates this tension somewhere.
2. **Linearity vs spatiality.** 1-D scroll (notebook, outliner, wiki, code-fold, stratigraphy), 2-D canvas (metro, mind map, expedition, treemap, Marey), or master-detail split (PR pane, and partially spine+marginalia). Scroll buys the clean read; canvas buys parallelism; split buys detail without clutter — pick which one is paid for by interaction instead.
3. **Where residuals live.** Inline-folded at the point of occurrence (notebook, code-fold, outliner, Marey's pinched loop), in a margin/apparatus (spine+marginalia, wiki endnotes, transcript-marginalia), as topological stubs (metro spurs, git branches, expedition cairns), behind zoom/peel (treemap), or in a segregated tray (storyboard's deleted scenes).
4. **Relationship to the transcript.** Map replaces transcript (most entries), map annotates transcript (transcript-with-marginalia — the null hypothesis), transcript reachable by a continuous gesture (treemap's zoom, Marey's axis), or transcript as a persistent parallel rail (spine+marginalia). This axis decides how provenance *feels*: a link, a zoom, or a physical attachment.
5. **Native mutation vocabulary.** Does the paradigm arrive with an existing grammar for "this changed" — git's amend/reflog, wiki revisions/diffs, PR M/A + outdated, film takes — or must one be invented (metro rings, geology textures, settlement growth)? Borrowed grammars are pre-learned but carry their source culture; invented ones are clean but need a legend.
6. **Density at rest (default altitude).** TOC-first — everything folded, story behind clicks (outliner, code-fold, PR tree); story-first — full spine readable without interaction (notebook, wiki, spine+marginalia, Marey); overview-first — a glanceable state dashboard before any reading (treemap, metro, expedition, stratigraphy). This is the axis Pi will feel most immediately in the mocks: what does the map show in the first three seconds?
