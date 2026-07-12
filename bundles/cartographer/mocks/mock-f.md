# Mock F — the commit train and the install that crashed (real session, mined at schema v2)

**Surface:** claude-code · **Date:** 2026-07-05 → 06 (22:56–02:51, ~4h) · **Nodes:** 14 · **Lines:** 3 · **Beats:** 3 · **Artifacts:** 8 · **Intent:** v3 · **Frontier:** n13 (session at rest) · **Source:** `06454cdf-5eb4-4c28-9e51-4c5fceb2b4f3.jsonl`, captured at line 1066 — the session had ended.

This is foundry's first-commits-ever session: 505 untracked files sectioned into 15 clean commits, an employer-identity scrub forced mid-train, then — across a /compact seam — a full dogfood install from the freshly published marketplace that crashed on a real defect and ended with the fix verified from the installed cache. Chosen as the **mostly-linear** counterpoint to mock-d2: one long grind spine, dead ends folded, with a compaction seam that cleanly splits the session into two missions.

## Structure summary

```
SECTION — "Can 505 untracked files become clean commits?"
  n01──n02━━━━━━━━━━━━━━▶ n03 (v1 ▸ v2)──n04──n05 ── answered, line ends
        │ fork              ▲                    │
        │ (the leak)        │ merge-update       │ succession
        ▼                   │ (home/ = commit 15)│ (across the /compact seam)
  SCRUB — "Is this tree     │                    ▼
  safe to go public?"       │            DOGFOOD — "Does a fresh install work?"
  n06──n07 ─────────────────┘            n08──n09──n10──n11──n12──n13   n14 ◇open
                                                    ▲setback  ▲fix   ▲verified
```

- **Anchor rhythm, not fan rhythm**: exactly three real user prose turns exist in 1066 lines (L12, L715, L775) — every other steering input arrived through AskUserQuestion gates. The map is long assistant-driven stretches punctuated by rulings; mock-d2 and mock-e are conversation-dense by comparison.
- **The loop-back merge with different content**: SCRUB forks from n02 (the leak finding) and lands as `merge-update` into n03 — v1 "fourteen commits, home/ held back" becomes v2 "the train is complete". Same mechanism as mock-d2's RESCUE→synthesis, different story shape (the merge *finishes* the target's job rather than resolving a critical inside it).
- **A textbook debugging arc, folded**: DOGFOOD is install → crash (n10, setback) → decision (n11) → fix-that-fails-one-layer-deeper (n12, residual) → push/reinstall/verify (n13). The second-layer failure (schema file outside the vendored package) is a residual, not a spine station — the fold rule working as intended.
- **Cross-session interference, from the observer side**: n05's residual records four wardrobe hats *appearing* in the working tree mid-commit — written by the concurrent crucible session (mock-e's subject). The two mocks document the same event from opposite sides.

## What was folded

- **The five-Explore recon fan-out → one node (n02).** Homogeneous probes, one merged section map; flagged as a fold in n02's residual with the dispatch/landing span. (Contrast deliberately with mock-e, where a homogeneous two-track fan *is* rendered as segments — this pair of mocks brackets the fold-vs-segment judgment call.)
- **The 15-commit train → one versioned node (n03).** Each commit's per-section doc repair lives in summary prose; three representative detours (the tool-count chase, the license gap, the deeper-than-scanned stale paths) are residuals. A per-commit rendering would be 15 stations of grind — exactly the audit-trail-not-story failure Round 5 rejected.
- **home/ file-by-file redaction detail → n07 summary.** The source lines enumerate specific employer markers; the mock keeps categories only (see sanitization).

## Sanitization + fabrication notes

**Sanitization holds** (grep-verified at build time): no hostnames, IPs, SSH usernames, employer identifiers, or work email in mock-f.json/md. This mock needed the most active scrubbing of the three: the source transcript *names* the employer, a work email, a private work-project, an infra mount path, a tenant hostname, and two personal machine names — all in spans that n03/n07 summarize. The mock's prose uses only categories ("employer identity", "an infra mount path", "an identifying tenant hostname"); the n07 residual states the exclusion explicitly, mock-d-style. Provenance spans still point into those raw lines — the known provenance-reveals-what-summaries-scrub issue, unchanged.

**Verbatim inventory:** 8 quotes, all byte-exact (programmatically verified). L12/L715/L775 are Pi's prose (typos preserved: "cusom", "everythign", "speicifc", "crednetials"). **n06/SCRUB's quote is typed user prose living inside an AskUserQuestion tool_result** — his words, but not a user message. **n04 and n11 quotes are selected option labels** ("Strip both from all 15", "Bundle the lib into the plugin"), flagged with `quote.note`.

**Inferred/editorialized (flagged):** intent wording (3 versions; shifts anchored at decision nodes n06/n09); line labels/outcomes; beat titles; moment classes; `settled` on n03. The claim in n13's residual that the version-gate gotcha "independently bit the concurrent crucible session hours later" is cross-checked against that session's transcript (mock-e n23), not visible in this one — an editorial cross-reference, not extraction.

## Where schema v2 fought this session (friction)

1. **User prose inside tool_results is a provenance blind spot.** The single most consequential ruling of the session ("its going to go public for sure…") is byte-exact user typing, but it lives inside an AskUserQuestion `tool_result` on a line whose `type` is `user` only by transport. The verbatim rule needs to say whether gate-answers count as user prose (this mock says yes, with a `note`); `because.note`/`quote.note` carry it as free text where a structured `quote.kind: prose | option-label | gate-answer | assistant-articulation` is wanted.
2. **A 15-station grind has no schema-native compression.** n03 holds 15 commits because beats/moments operate at node granularity — there is no "repeated unit ×N" affordance. The train wants something like a collapsed-sequence glyph (15 ticks in one station); today that's summary prose.
3. **`merge-update` covered a new case but the vocabulary is drifting.** Mock-d2's merge resolved a critical inside the target; this one *completes* the target (v1 was "…held back", v2 is "…complete"). Both are honest `merge-update`s, but "what kind of update" lives only in `superseded_because`. With mock-g needing plain `merge` (feeds a node's creation), the relation enum is now `fork | merge | merge-update | succession` — Phase 3 should decide the closed set.
4. **Intent v1→v2 was ruled by a question the reducer asked.** The public-posture shift wasn't volunteered by Pi mid-work — the assistant *forced* the decision via a gate when the leak was found. Intent shifts caused by agent-initiated questions vs. user-initiated redirections feel different (proactive vs reactive drift) and the schema can't distinguish them.
5. **Holdbacks are neither open questions nor artifacts.** cartographer/, the alien hats, and the license gap are "deliberately not done" — n14 models them as one open-question node, but they're really three tracked exclusions with owners. A `holdbacks[]` or artifact `status: excluded` might fit better than overloading open-question.
6. **The two-mission session tests line-vs-session identity.** SECTION+SCRUB and DOGFOOD share almost nothing — different verbs, different risk, different artifacts; only the compaction seam and Pi's "leave both for now" stitch them. A reasonable cartographer could have called this two maps. The schema has no notion of a session containing near-disjoint episodes beyond beats; the succession edge across the seam is doing a lot of silent work.
