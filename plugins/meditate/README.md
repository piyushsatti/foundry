# meditate

Reflective memory curation for Claude Code: **pause → review → consolidate → release.**

An agent that works with you every day accumulates memory — always-on rules in `CLAUDE.md`,
recalled facts in per-project memory files, code-coupled knowledge in serena. Unmaintained, that
memory rots: stale items, duplicates, mis-scoped facts, contradictions, and rulebooks that grow
until nothing in them is load-bearing. Claude Code's own docs tell you to "review your CLAUDE.md
files periodically to remove outdated or conflicting instructions" — by hand, in an editor.
meditate is tooling for exactly that maintenance loop.

## How it works — terraform for memory

```
/meditate:curate   →   /meditate:review   →   (you edit/approve)   →   /meditate:apply
     plan                    show                   gate                    apply
```

1. **curate** dispatches a **read-only** Opus curator agent over the opted-in stores. It
   classifies every item, checks destinations for collisions, adjudicates code-coupled claims
   against live code, and emits *proposals* — a YAML manifest written to disk. It cannot write a
   store: its tool grant contains no Write, no Edit, no Bash.
2. **review** renders a pending manifest read-only: disposition table, destructive-op flags, an
   explicit `⚠ CLAUDE.md changes` line, and the needs-human questions.
3. **You** are the gate. Approve a candidate by leaving it, reject it by deleting its block,
   modify it by editing any `proposed:` field. Nothing is self-executing.
4. **apply** is a dumb executor. It re-verifies a sha256 optimistic lock per item (captured at
   curation — if a file changed since, that item is skipped, not clobbered), then executes
   exactly what each approved block says. Every destructive verb archives a pre-image first and
   leaves a tombstone with a back-pointer; the agent never deletes — a final `rm` block is
   handed to you as optional cleanup.

## The model

- **Two axes.** *Scope* — the shallowest directory a memory is relevant to, expressed as
  `{depth, role}` (home / repo / worktree / sub / dir). *Genericity* — the **export fence**:
  `generic` knowledge is portable across employers; `specific` is bound and sensitive. Switching
  companies keeps generic, drops specific. When unsure: `specific` — a wrongly-specific memory
  merely fails to travel; a wrongly-generic one leaks.
- **Store routing.** Fires proactively every session → a `CLAUDE.md` rule. Recalled fact →
  Claude memory file. Code-coupled → serena. Promotion to rule passes a 5-test gate
  (universality, prevention-value, not-already-enforced, not-auto-recorded, recurrence) against
  a ~15-line budget per rulebook — at the cap, a promotion must name which existing rule demotes.
- **Fourteen verbs.** Vertical — `promote · merge · keep · drop · promote-to-rule · demote-rule
  · generalize · specialize · deprecate · retire` — move items between scopes and stores.
  Horizontal — `split · combine · link · amend` — re-draw item boundaries within a layer. A
  `split` must pass a lossless-join gate (the children, read together, entail everything the
  original said); a `combine` must be strictly richer than concatenation; cohesion is treated as
  a tolerance relation (reflexive, symmetric, **not** transitive), so similarity is never
  chained A~B~C into a mega-merge.
- **One verb per item per manifest** (stratification): no candidate may reference a path another
  candidate creates or destroys. Chains defer to the next sweep. This is what makes a dumb,
  order-free applier possible.

## Design bets, stated plainly

- **A human gates every mutation.** The field's center of gravity is fully-automated curation;
  meditate deliberately is not. Standing instructions steer every future session — the blast
  radius per item is too high for an unreviewed write path (see the literature below: write-path
  LLM judges measurably admit anomalies).
- **Proposer, approver, and executor are three different parties** with different privileges:
  a read-only high-capability judge, a human, and a mechanical applier.
- **Archive-never-delete.** Reversibility is a property of the system, not a habit of its user.
- **Conservative defaults.** Over-promotion is the cardinal sin; unsure → keep separate; unsure
  → `specific`; a zero-finding sweep is a success, not a failure.

## Layout

| Path | What |
|------|------|
| `skills/curate` · `skills/review` · `skills/apply` | The plan / show / apply pipeline |
| `agents/curator.md` | The read-only Opus curator (proposals only) |
| `config/targets.yaml` | **Opt-in** sweep targets — keys must be listed explicitly; worktree/tmp keys are refused |
| `docs/` | The vendored design contract — see [docs/README.md](docs/README.md) for reading order |
| `scripts/migrate_frontmatter.py` | One-time migration of memory frontmatter to schema v2 (`uv run scripts/migrate_frontmatter.py [--apply] <memdir>`) |
| `skills/apply/tests/` | Legacy fixture seed from the retired `apply-curation` skill — not a passing suite (see its NOTE.md) |

## Where this sits in the literature

The problem is variously called memory consolidation/maintenance, reflective memory management,
agentic context engineering, and (2026) **memory governance**. Approaches split by *when*
curation runs — write-time (Mem0, LangMem, Zep/Graphiti), background-automated (Letta sleep-time
agents, OpenAI "Dreaming", LightMem), post-task reflection (Reflexion, ACE) — and by *who
decides*: heuristic scores → LLM judge → learned policy → human. meditate occupies an otherwise
empty cell: **periodic human-gated sweep × flat files × rules + facts + code-coupled ×
audited-reversible.**

Original in meditate (nothing comparable found as of 2026-07-05): the genericity/export-fence
axis; the lossless-join gate on `split` (relational-database decomposition theory applied to
memory); tolerance-relation clustering; sha256 optimistic locks on memory files; the rule budget
with forced demotion pairing. Aligned-with-best-practice rather than novel: tombstones
(Graphiti invalidates edges; TOKI keeps audit rows), the read-only-proposer pattern (Letta
separates its memory editor; meditate additionally de-privileges it and adds the human).

Design-time grounding (six research streams, 2026-06-29) lives in
[docs/meditate-problem-domain-formalization.md](docs/meditate-problem-domain-formalization.md) §9.
A full state-of-the-art comparison was done 2026-07-05. Key references:

| Reference | Grounds |
|---|---|
| Park et al., *Generative Agents*, [arXiv:2304.03442](https://arxiv.org/abs/2304.03442) | Reflection ancestry: synthesizing raw memories into higher-level abstractions |
| Chhikara et al., *Mem0*, [arXiv:2504.19413](https://arxiv.org/abs/2504.19413) | ADD/UPDATE/DELETE/NOOP — the minimal op kernel the verb lexicon extends; write-time contrast class |
| Xu et al., *A-MEM*, [arXiv:2502.12110](https://arxiv.org/abs/2502.12110) | Prior art for `link`/`amend`; why unconstrained linking needs the tolerance-relation discipline |
| Zhang et al., *ACE*, [arXiv:2510.04618](https://arxiv.org/abs/2510.04618) | "Context collapse" and "brevity bias" — the diseases the lossless-join and information-content gates prevent |
| Lin et al., *Sleep-time Compute*, [arXiv:2504.13171](https://arxiv.org/abs/2504.13171) | Why memory work belongs offline ("meditation" = sleep-time compute for curation) |
| Letta, [sleep-time agents](https://docs.letta.com/guides/agents/architectures/sleeptime/) | Closest shipped analog: async memory editor — autonomous, unlike meditate's |
| Rasmussen et al., *Zep*, [arXiv:2501.13956](https://arxiv.org/abs/2501.13956) | Invalidate-don't-delete; bi-temporal edge validity; contradiction surfacing |
| Wang, *TOKI*, [arXiv:2606.06240](https://arxiv.org/abs/2606.06240) | Evidence that write-path LLM judges admit anomalies — the case for the human gate + dumb applier |
| Munirathinam, *memorywire*, [arXiv:2606.01138](https://arxiv.org/abs/2606.01138) | Independent 2026 convergence on diff-and-approve memory governance |
| Li et al., *MemOS*, [arXiv:2507.03724](https://arxiv.org/abs/2507.03724) | Memory lifecycle, provenance, versioning as first-class governance |
| Lin et al., *LTM Security survey / VMG*, [arXiv:2604.16548](https://arxiv.org/abs/2604.16548) | Verifiable memory governance; the Share & Propagate phase — formal home of the export fence |
| Tan et al., *RMM*, [arXiv:2503.08026](https://arxiv.org/abs/2503.08026) | Named the discipline; retrospective (usage-feedback) reflection is meditate's next frontier |
| Du et al., *Rethinking Memory in LLM Agents*, [arXiv:2505.00675](https://arxiv.org/abs/2505.00675) | The operations taxonomy (consolidation/updating/forgetting/…) meditate's verbs map onto |
| Wu et al., *LongMemEval*, [arXiv:2410.10813](https://arxiv.org/abs/2410.10813) | Evaluation template: knowledge-update + abstention probes for curation quality |
| Zhong et al., *MemoryBank*, [arXiv:2305.10250](https://arxiv.org/abs/2305.10250) | Forgetting curves / memory-strength signals — the score-based road not (yet) taken |

## Setup

1. **Opt in your targets.** Edit `config/targets.yaml` — each entry is an absolute-path `key`
   (only stable, long-lived scopes; never a worktree or tmp path) plus its rulebook files and an
   optional serena project. Keys are machine-specific: use *this* machine's `$HOME`.
2. **Migrate pre-v2 stores once** (only if your memory files predate `schema_version: 2`):
   `uv run scripts/migrate_frontmatter.py <memdir>` (dry-run) then `--apply`.
3. **serena is optional.** If the serena plugin is active, code-coupled memories are audited
   too; if not, serena items are skipped and reported as skipped.
4. Run `/meditate:curate`, read the manifest with `/meditate:review`, edit it, then
   `/meditate:apply <manifest-path>`.

## Known state (v0.1.0, 2026-07-05)

This copy is content-identical to the last pslap dev source (v1.2.1) and was re-versioned on
import into foundry. A full three-track review (design, implementation, literature) was completed
2026-07-05, followed by a **P0/P1 repair pass** the same day. The repair — landed and verified at
the unit/static level:

- Authority docs vendored into `docs/`; all skills + the curator now cite `${CLAUDE_PLUGIN_ROOT}/docs/`
  with a graceful degraded mode if a doc is missing.
- macOS portability: hashing/mtime/slug moved into portable `bin/` helpers (`meditate-lock`,
  `meditate-slug`, `meditate-manifest`); no more GNU-only `stat --format`.
- Manifest contract fixed: top-level `candidates:` container, sweep-mode `type`/`store`/`body`,
  a codified 14-verb enum (see `docs/meditate-decisions-and-findings.md`, 2026-07-05).
- Config is now per-machine: `config/targets.yaml` is gitignored; `config/targets.example.yaml`
  is the tracked template; the home key is derived from `$HOME`.
- Safety holes closed: fail-on-missing-lock, uniform execute-time lock re-verify (TOCTOU),
  tombstone-aware re-run, non-clobbering archives, and a fixed silent-corruption bug in the
  frontmatter migrator.
- `skills/apply/tests/` is now a runnable sandbox suite (`seed.sh` + a validated fixture).

**Verified end-to-end (2026-07-05):** the whole pipeline was exercised in a sandbox — a dispatched
curator agent produced a valid `candidates:` manifest, which flowed through extract → validate →
lock post-attach → written manifest, then driven `apply` runs executed **all 14 verbs** with correct
outcomes, the coupled-safety orderings (promote-to-rule, demote-rule), archive-never-delete, and the
optimistic locks (incl. the negative case — a tampered file is caught, nothing written). `merge` is
modelled as a 2-way fold (curator supplies the reconciled body; both endpoints locked). Plus the
unit/static checks (helpers, migrator on a real-data copy, manifest validation, cross-file
consistency).

**One environment caveat:** the meditate skills/agents are not registered as invocable slash
commands in a session that has the plugin only *linked* (as this repo does) — running
`/meditate:curate` natively needs a Claude Code plugin reload/reinstall so the components surface.
The logic is proven; only the native slash-command entrypoint depends on that registration.
