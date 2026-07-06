---
name: hats
description: Use when a plan, design, decision, or document should be reviewed from several distinct professional perspectives before proceeding — the user says different hats, different perspectives, panel review, or names roles to apply; or when a single reviewer's lens would miss whole failure classes (security vs ops vs UX vs domain).
argument-hint: "Artifact to review + hats to wear (or 'pick hats for me')"
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../../../../skills/manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **requires** | `wardrobe` | Must exist in bundle before running |
| **suggests** | `audit`, `red-vs-blue` | Soft handoff after this skill — suggest, do not auto-chain |

**Used by:** `audit` (suggests), `brief` (suggests), `consult` (suggests), `grill-with-docs` (suggests), `plan-orchestrator` (dispatches), `red-vs-blue` (suggests)

<!-- foundry:dependencies:end -->

# Hats

Fan out **3–4 parallel reviewers**, each a genuinely distinct professional lens on the same artifact, each blind to the others. One review round, one synthesis pass. The output is diverse, structured, evidence-cited findings — not a consensus vote.

<HARD-GATE>
Reviewers raise, don't fix. No hat sees another hat's output before submitting its own. Synthesis surfaces agreement AND disagreement — it does not rewrite the artifact and does not manufacture consensus. No exceptions for "it's a one-line fix" or "the user obviously wants it" — findings route to the user/synthesis, not to your own edits.
</HARD-GATE>

## Why this shape

Every rule below cites a design decision (D-number) in `${CLAUDE_PLUGIN_ROOT}/docs/adversarial-review-methodology.md` (if `${CLAUDE_PLUGIN_ROOT}` is unset, it sits at `../../docs/adversarial-review-methodology.md` relative to this file):

- **3–4 hats, not 5+** — panel quality peaks at 3–4 roles and declines at 5; extra rounds stagnate or degrade. [D5]
- **Lenses must be genuinely distinct** — identical-role panels gain *zero* over a single reviewer; diversity is the load-bearing ingredient. [D3]
- **Blind, parallel first pass** — reviewers who see peers conform sycophantically (weak reviewers correct a wrong majority in only 3.6% of cases). [D4, D11]
- **External review, not self-critique** — self-critique underperforms even a single fresh reviewer. [D1]
- Panels are for richer findings, not raw accuracy — don't sell this as an accuracy booster. [D2]

## Protocol

### 1. Scope
Confirm the artifact — plan, design doc, code, architecture, decision.

### 2. Pick 3–4 hats — from the wardrobe
Hats are **chosen from the shared wardrobe** ([`../wardrobe/`](../wardrobe/SKILL.md)), not invented per-run. Propose 3–4 roster hats that fit the artifact and confirm; the user may name others. **Distinctness test** [D3/D16, formalized in [`HATS.md`](../wardrobe/hats/HATS.md)]: each hat must own a failure class the others do not — compare each candidate's `## Failure classes` (body) against the `overlaps` field (frontmatter); if two would flag the same issues, swap one out. Distinctness is declared here, then *measured* by the overlap eval — never assumed [D16]. If the artifact's value is exhaustiveness (requirements, checklist, migration inventory), one hat must be the **coverage** lens [D9].

A requested lens that isn't in the wardrobe: draft it inline for this run following the HATS.md contract, and flag it for wardrobe addition — don't silently improvise a vibe.

Roster (full table in [`../wardrobe/SKILL.md`](../wardrobe/SKILL.md)) — general software: `architect`, `senior-engineer`, `security`, `sre`, `frontend`, `product`, `coverage`, `simplifier`, `finance`, `coach`; agentic-infra (skills/agents/prompts/harness): `prompt-engineer`, `harness-engineer`, `skill-designer`, `eval-engineer`. Example sets — API design: security, sre, senior-engineer, coverage. Life/personal decision: finance, coach, product. Reviewing a skill/plugin: prompt-engineer, harness-engineer, skill-designer, eval-engineer.

### 3. Dispatch — parallel, blind
Each hat runs as its own subagent, all in parallel, blind to each other.

**Run from the main thread only.** These skills fan out to parallel subagents; a subagent has no dispatch tool, so if you are yourself a dispatched subagent, do NOT try to fan out — review the artifact in-thread through the relevant lens(es) and say explicitly that you ran single-threaded.

**A dropped hat is a missing lens, not a clean one.** If a dispatched panelist dies, times out, errors, or returns empty, do not silently synthesize the survivors as if the panel were complete — a missing lens means its whole failure class went unreviewed. Re-dispatch that one hat once; if it fails again, name it in the synthesis as **not reviewed** and do not imply its classes are clean.

**Prefer the `panelist` agent type** (`subagent_type: panelist`) when available — it carries the neutral-stance protocol and a pinned model. Pass it the composed prompt: the **hat file's body** (`../wardrobe/hats/<name>.md`, `## Role` through `## Severity anchors` — **exclude the frontmatter**; `overlaps` is registry metadata and irrelevant detail in the payload [D16, D13]) + the artifact (or paths to read). When `panelist` isn't available, dispatch a **general-purpose** subagent and inline the neutral-stance rules below alongside the hat body.

Default to the session model; the user may override — e.g. diversify models across hats, which may matter as much as personas [D3, D16, open Q3].

Every panelist prompt — via the agent type or inlined — carries the artifact and enforces:

- Evaluate only through your lens (the hat body); cite evidence (location + verbatim quote) for every finding [D15].
- Commit to your positions — do not hedge toward what other reviewers might think [D4].
- Raise, don't fix.
- **Reason first, structure last** — fill `## Analysis` as free prose before any finding; assign severity only after the evidence is quoted [D14, D15].
- Use the CRITICAL flag for hallucinated claims, internal contradictions, or showstoppers.

### 4. Per-hat output contract — reasoning-first [D14]

Analysis comes first as free prose; structured findings come last. Never assign a
severity or verdict before the evidence is quoted [D14, D15].

```markdown
# [Hat] review

## Analysis
[Free prose — no format requirements. Reason through the artifact in this lens,
quote what you see, explore. This section exists before any finding so severity is
never assigned answer-first [D14].]

## Findings
[One block per finding. Severity is set ONLY after evidence is quoted; a finding
with no verbatim-quote evidence is capped at the lowest band (nit) [D15].]
- id:              F1
  failure_class:   [from this hat's declared `## Failure classes`]
  severity:        blocker · major · minor · nit   (shared taxonomy — HATS.md)
  evidence:        "[verbatim quote]" — [location: file/section/line]
  claim:           [one sentence]
  suggested_probe: [how the synthesizer/author could verify this]
Prefix an id with CRITICAL- for override-level issues (hallucinated claim,
internal contradiction, showstopper) [D8].

## Not found
[One explicit "checked X — clean" line per `## Always ask` item, so completeness
is visible, not inferred.]

## Blind-spot flags
[Anything observed outside this hat's declared classes — routed to synthesis, not
scored [D13].]

## Confidence
[high/medium/low — and what would change it]
```

### 5. Synthesis — main thread, never one of the hats [D10]

```markdown
# Hats synthesis: [artifact]
## Executive summary
[verdict + the 3 things that matter most]
## Where hats agree
## Where hats disagree
| Topic | Hat A | Hat B | Tension |
Disagreement is signal — present it, don't average it away.
## Severity rollup
| ID | Severity | Finding | Hats flagging |
## Recommended next steps
```

Rules: CRITICAL findings surface in the summary even if only one hat raised them [D8]. Treat a hat's stated confidence as calibration context, not severity — severity comes from evidence [D6]. One round: do not send synthesis back to the hats for another pass [D5].

## After synthesis
Present to user. Wait for direction. Do not implement. No exceptions for "it's a one-line fix" or "the user obviously wants it" — findings route to the user/synthesis, not to your own edits.

## Not this skill
- **audit** — one neutral reviewer, one findings report
- **red-vs-blue** — adversarial attack/verify pair for high-stakes artifacts
- **grill-with-docs** — interactive interview against domain docs

## Evidence basis
Full findings, refuted claims, and caveats: `${CLAUDE_PLUGIN_ROOT}/docs/adversarial-review-methodology.md` (if `${CLAUDE_PLUGIN_ROOT}` is unset, it sits at `../../docs/adversarial-review-methodology.md` relative to this file)
