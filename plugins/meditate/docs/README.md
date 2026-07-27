# meditate — authority docs (the contract)

This directory is the **canonical home of the meditate design contract**, vendored from the
pslap machine on 2026-07-05. These documents were previously cited by the skills and the curator
agent at `~/Documents/personal/notes/infrastructure/…` — a path that only existed on pslap. The
copies here are now the ones that count; the pslap originals are historical snapshots.

New design decisions append to `meditate-decisions-and-findings.md` (here, not on pslap).

## Reading order

| File | Role | Cited by |
|------|------|----------|
| [mem-arch-interface-contract.md](mem-arch-interface-contract.md) | **The spec.** §1 frontmatter vocabulary · §2 verb lexicon · §3 manifest schema · §5 curator role. | `agents/curator.md`, all three skills |
| [meditate-problem-domain-formalization.md](meditate-problem-domain-formalization.md) | The horizontal-layer theory: cohesion as a tolerance relation, the lossless-join gate, the cardinality floor, split/combine/link/amend design. §9 is the design-time research appendix (six research streams, 2026-06-29). | `agents/curator.md` (relational pass) |
| [2026-06-24-memory-architecture-spec.md](2026-06-24-memory-architecture-spec.md) | The full memory-architecture model: two axes, stores, directory layout, ownership matrix. | `agents/curator.md` (background) |
| [mem-arch-planner-handoff-2026-06-25.md](mem-arch-planner-handoff-2026-06-25.md) | Snapshot: the FINAL §4.1 frontmatter schema + routing test. Post-handoff changes live in the decisions log. | `agents/curator.md` |
| [meditate-decisions-and-findings.md](meditate-decisions-and-findings.md) | **Append-only decisions log.** Post-handoff locks (scope vocab, `schema_version`, T2 fate, fit strategy). Always read last — it supersedes anything older. | `agents/curator.md`, `TODO.md` |
| [mem-arch-applier-design.md](mem-arch-applier-design.md) | The applier's design authority (pre-dates the horizontal verbs; `skills/apply/SKILL.md` is more current where they disagree). | `skills/apply/SKILL.md` |

## Old-path mapping

Plugin prose still cites the dead pslap paths; until the repair pass repoints them, translate:

```
~/Documents/personal/notes/infrastructure/<name>.md  →  ${CLAUDE_PLUGIN_ROOT}/docs/<name>.md
```

The wider set of historical plans/handoffs (implementation plans, gap analyses, phase docs,
`mem-arch-00-orchestrator.md`, etc.) was archived to
`.gitignored/reference/pslap-meditate-docs/` in the foundry repo — reference material, not
contract, deliberately not vendored here.
