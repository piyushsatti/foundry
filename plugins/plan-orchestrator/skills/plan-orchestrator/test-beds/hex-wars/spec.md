---
name: hex-wars
created: 2026-05-18
purpose: n=2 test bed for the plan-orchestrator skill
---

# Hex Wars — Test-Bed Spec

This is the user-provided spec the plan-orchestrator skill is invoked against. It must satisfy the input contract (decision 2): what / why / metrics / scope / constraints.

## What

Hot-seat (single device, multiple human players) turn-based hex strategy game playable in a web browser. Players take turns moving units on a hex grid. Three layered components:

- **Backend service** (Node + TypeScript + Express): validates moves, manages save state, exposes a REST API
- **Frontend** (React + Vite + TypeScript): renders the hex grid, handles input, displays game state
- **Shared package** (TypeScript): defines the `GameState` schema and move-validation pure functions consumed by both sides

Goal of play: eliminate all enemy units OR capture the central hex.

## Why

Serves as the n=2 test bed for the plan-orchestrator skill. Chosen because:

- **Multi-component with real contracts** — `GameState` is a genuine cross-layer contract (frontend renders it, backend validates against it, persistence serializes it)
- **Real audit surface** — server-side move validation (anti-cheat), save format safety (deserialization), input validation
- **Multi-day scope** — exercises the skill's phase decomposition + parallel planning
- **Greenfield** — no existing owner; clean evaluation of the skill's decisions
- **Lower domain risk than alternatives** — hex math and turn-based logic are well-trodden patterns; reduces "the test bed itself was broken" confounder

## Success criteria (metrics)

Each must be desk-evaluable or scriptable (per decision 22):

1. **Functional correctness** — All unit and integration tests pass; ≥30 tests covering: legal/illegal move validation, win-condition detection, save/load round-trip, state transitions
2. **Load performance** — Initial page loads in <2s on Chrome (cold cache) with a 12×12 grid populated
3. **Move validation** — Server-side validator rejects all 30 illegal moves in the fixture suite (false-positive rate = 0)
4. **Win-condition latency** — Win condition detected within 50ms of the triggering move (measured server-side)
5. **State coherence** — UI accurately reflects game state after every move; no desync after 100 random legal moves in a fuzz test
6. **Save round-trip** — Save → reload → resume produces byte-identical state across 20 random game positions
7. **Audit cleanliness** — `security-review` produces 0 blocking findings; `pr-review-toolkit:review-pr` produces 0 blocking findings

## Scope (in)

- **Players:** 2–4 hot-seat (everyone shares the screen, takes turns)
- **Map sizes:** configurable from 8×8 to 16×16; default 12×12
- **Map layout:** single symmetric two-territory map for v1
- **Unit types:** three — infantry (1 move, 1 attack), cavalry (3 moves, 1 attack), artillery (1 move, 2 attack range)
- **Combat:** deterministic — defender loses 1 HP per attack point; no RNG
- **Turn structure:** all of one player's units move, then turn ends; no action points budget
- **Win conditions:** elimination OR central-hex capture (held at end of player's turn)
- **Persistence:** filesystem-backed save files on the backend; frontend triggers save/load via API
- **State:** single active game per browser session

## Non-goals (explicit)

- Network multiplayer (no WebSocket layer, no matchmaking, no concurrency)
- AI opponent (hot-seat only)
- Sound, music, animations beyond CSS transitions
- Mobile / touch support (desktop browser only)
- Map editor; additional maps beyond the default
- Replay viewer
- Accessibility audit (WCAG); minimal a11y only

## Constraints

- **Languages:** TypeScript everywhere (backend, frontend, shared)
- **Frontend:** React + Vite (no game framework like Phaser; build hex rendering with SVG)
- **Backend:** Node + Express; no database — filesystem JSON for saves
- **Shared:** pure TypeScript package; no runtime side-effects in the contract module
- **Hex math:** use offset coordinates (column-row) for storage; convert to axial/cube for distance calculations
- **GameState:** must be JSON-serializable (no class instances, no Maps/Sets in serialized form)
- **Move validation:** must live in the shared package (single source of truth) and be invoked from both sides
- **Code budget:** 1500–3500 LOC total across the three components + tests

## Known context pointers

- Hex-grid reference: `https://www.redblobgames.com/grids/hexagons/`
- Suggested project structure: monorepo with `packages/shared`, `packages/backend`, `packages/frontend`, pnpm workspaces

## Output location

When the skill runs against this spec, the implementation should land at:
```
~/Desktop/hex-wars-testbed/
```

The skill's own work-dir will be at:
```
~/.claude/plan-orchestrator-runs/hex-wars/<timestamp>/
```
