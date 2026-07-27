# Manifold rituals

Weekly cadence for keeping a tracked project trustworthy. For compass routing (which surface answers which question), see [`docs/manifold/how-to-use.md`](../../../docs/manifold/how-to-use.md) — do not duplicate that table here.

---

## Weekly ritual (in order)

1. **Spec audit** — `spec-audit <project>` or MCP `spec_audit`. Are spec changes documented with `change_reason` and rationale? Flags revision hygiene only; does not read the codebase.

   **MCP-only caveat:** MCP `update_node` requires `change_reason` at the schema layer, so agent writes routed through MCP cannot produce the revision violations spec-audit flags. A clean spec-audit after MCP-only sessions is expected — not proof the audit is broken. To exercise spec-audit failure paths, create revisions via CLI `edit`, raw SQL, or imports without `change_reason`.
2. **Drift report** — `drift-report <project> --repo <checkout>` or MCP `drift_report` with `project_root` (required unless `spec_config.project_root` is set). For projects with verdicts wired, does code still match spec? Interpret **violated** / **errored** / **unverified** / **satisfied** — see [`verdicts.md`](verdicts.md). CLI exit 1 = violated only.
3. **Next-leaves** — `next-leaves <project>` (add `--verbose` for cross-blocked exclusions; add `--repo` for live computed verdict column — see [`verdicts.md`](verdicts.md)). Is the open frontier what you expect?

Run all three before trusting the graph for dispatch or "what's next" decisions.

---

## After findings: when to suggest red-vs-blue

Suggest the **red-vs-blue** skill (do not auto-chain) when spec-audit or drift-report surfaces:

- **Pivot without documented rationale** — spec changed direction but `change_reason` / rationale don't explain why
- **High-stakes gap** — blocker chain or violated verdict affects a release, compliance, or cross-project dependency
- **Disputed interpretation** — team disagrees whether drift is acceptable or the spec should evolve

Use red-vs-blue for adversarial attack vs defend on the *decision*, not for routine hygiene fixes (those are writeback + re-run validation).
