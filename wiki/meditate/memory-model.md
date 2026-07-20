---
title: Memory Model
status: stable
summary: The two-axis model — scope tier × genericity — over three stores differentiated by loading model.
sources:
  - bundles/meditate/docs/2026-06-24-memory-architecture-spec.md
updated: 2026-07-20
---

# Memory Model

**Every memory item is placed on two axes — its scope tier and its genericity — then stored in whichever of three stores matches its loading model.** This is the substrate meditate curates.

> **Status:** stable

## The two axes

- **Scope tier** — breadth of applicability: `Universal ⊃ Machine ⊃ Workspace ⊃ Project ⊃ Work-unit`. Lifecycle is implied by scope (Universal is permanent; Work-unit lasts days), so there is no separate time axis.
- **Genericity** — the **export fence**: `generic` knowledge is portable/company-safe; `specific` is bound and sensitive. The seam runs *vertically* through every tier — each tier has a generic base and a specific overlay.

**Company-switch = detach the specific overlays, keep the generic bases.** That is the whole portability mechanism. When unsure, tag `specific`: a wrongly-specific memory merely fails to travel; a wrongly-generic one leaks.

## Three stores, by loading model

The stores are not redundant — each has a different loading model, which is what routing keys on:

| Store | Role | Loading model |
|-------|------|---------------|
| **CLAUDE.md / `.local`** | Rulebook (always-on) | Full body injected every session in scope → keep lean, behavioral |
| **Claude memory** (`MEMORY.md` + files) | Knowledge base (on-demand) | Index always loaded; bodies recalled when relevant → scales |
| **serena** (`~/.serena/`) | Code intelligence (code-coupled) | Pulled via tools during code work; stored globally, git-safe |

**Routing heuristic:** fires proactively every session → CLAUDE.md rule · recalled fact → memory · code-coupled → serena. A decision routes the same way: code-coupled decision → serena; workflow/architecture decision → memory.

## Native walk-up composition

Claude Code loads `CLAUDE.md` then `CLAUDE.local.md` by **walking up the directory tree** from cwd, root→cwd, plus user-level `~/.claude/`. Because worktrees nest inside the repo and the Workspace file sits above every repo, **the whole ladder composes by location alone — zero `@import`.** Location encodes scope; the `.md` vs `.local` suffix encodes genericity.

Memory (off-tree, keyed by cwd) does *not* compose up the tiers — an accepted asymmetry, since anything that must apply across scopes is a rule and lives in the rulebook.

## The no-agent-files-in-git rule

**Hard rule: no agent-facing file is ever committed.** `CLAUDE.md`, memory, serena, and `.worktrees/` are all blocked by one global gitignore gate. Rationale is confidentiality (agent files carry infra topology, prefs, decisions) plus portability (knowledge rides the user's own layered setup, not the repo). This is deliberately contrarian — the industry default commits project rules for team-sharing.

## See also

- [Operation algebra](operation-algebra.md) — how items move between cells.
- [Overview](overview.md) — the curation pipeline over this model.
