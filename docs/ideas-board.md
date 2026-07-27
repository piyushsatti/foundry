# Foundry Ideas Board — intake discipline

**Surface:** GitHub Project [#5 "Foundry Ideas"](https://github.com/users/piyushsatti/projects/5) (user-owned, linked to this repo).
**Established:** 2026-07-05. Owner: Pi — sole decision-maker; sessions may add/move cards, only Pi approves graduations.

## Why this exists

Foundry needs a standing place where feature ideas land, wait, and earn their way into builds — the
2026-07 buildout pack proved the pattern (mine → adversarial review → approved items → one fresh
session per item) but was a one-off. This board makes it permanent. Foundry is not just the skills
being authored here; it is the whole curated stack being accumulated and believed in — ideas about
that stack need a durable home too.

## Lanes (the `Status` field)

| Lane | Meaning |
|---|---|
| **Inbox** | Raw idea, just captured. Zero rigor required. |
| **Shaping** | Being sketched/refined; not yet committed to. |
| **Approved** | Graduated (see rule below). Ready to be picked up. |
| **Building** | Actively being built — one fresh session per item, kickoff-prompt style. |
| **Shipped** | Done: merged/in the marketplace. |
| **Icebox** | Consciously parked. Not dead — revisit deliberately, not by accident. |

## Card format (draft cards)

Three lines, no more at intake:

- **Itch:** the problem or friction, in one sentence.
- **Sketch:** roughest plausible shape of a solution.
- **Why foundry:** why this belongs in the curated stack at all.

## The graduation rule (the only hard rule)

A card may not leave **Shaping** until:

1. It is converted to a real GitHub **issue** on `piyushsatti/foundry` (referenceable from commits,
   closable on ship), **and**
2. If non-trivial, it has survived an **adversarial review pass** (crucible: red-vs-blue or a hats
   panel) and the surviving design is written to `docs/` as a dated design note.

Trivial ideas (docs, small config) need only the issue. Pi approves every graduation; nothing is
self-graduating.

## Seeded 2026-07-05 (first four cards, all Inbox)

1. **Draft-PR quality gate** — sequential simplifier → review agent passes, pinned model+effort,
   before any draft PR is created.
2. **Frontend-design auto-invocation policy** — UI thinking must route through the frontend-design
   skill, enforced, not remembered.
3. **LSP inventory** — per-LSP: what it provides, which machine carries it, when it earns its place.
4. **External dependencies / dependency-chain model** — a manifest of imported-and-believed-in
   skills/plugins (superpowers, caveman, official core, …), what wraps what, so a machine bootstrap
   reproduces the whole belief-set, not just the self-authored plugins. Likely wants a crucible pass
   before graduating.

## Session etiquette

- Any Claude session may capture a new idea as an Inbox draft card (`gh project item-create 5
  --owner piyushsatti --title … --body …`) — capture is cheap, do it liberally.
- Sessions move cards only with Pi's say-so, except Inbox additions.
- When a Building item ships, close its issue (`closes #N` in the PR) and move the card to Shipped.
