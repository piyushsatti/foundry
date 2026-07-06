# Vendored skills

Third-party agent skills pinned in git. **Do not edit in place** — update from upstream or fork explicitly (see `mattpocock-trimmed/`).

Listed in `skills/manifest.yaml`. In-repo: `python3 scripts/skills_manifest.py validate`.

---

## mattpocock

**Upstream:** [github.com/mattpocock/skills](https://github.com/mattpocock/skills)  
**Pinned:** 2026-05-31 (manual copy via `npx skills add`)

| Skill | Upstream path |
|-------|---------------|
| [grill-with-docs](mattpocock/grill-with-docs/) | `skills/engineering/grill-with-docs` |
| [handoff](mattpocock/handoff/) | `skills/productivity/handoff` |
| [write-a-skill](mattpocock/write-a-skill/) | `skills/productivity/write-a-skill` |

Refresh:

```bash
npx skills add https://github.com/mattpocock/skills --skill <name>
# then copy into vendor/skills/mattpocock/<name>/ and diff
```

---

## mattpocock-trimmed (fork)

**Upstream:** [mattpocock/productivity/caveman](https://github.com/mattpocock/skills/tree/main/skills/productivity/caveman) (also popularized via [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman))

| Skill | Notes |
|-------|-------|
| [caveman](mattpocock-trimmed/caveman/) | Dropped lite/ultra/wenyan intensity levels; kept core + auto-clarity exception |

See [mattpocock-trimmed/UPSTREAM.md](mattpocock-trimmed/UPSTREAM.md).

---

## taste-skill

**Upstream:** [github.com/Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) · [tasteskill.dev](https://www.tasteskill.dev/)  
**Pinned:** 2026-04-05 (manual copy)

| Skill | Upstream folder |
|-------|-----------------|
| [design-taste-frontend](taste-skill/design-taste-frontend/) | `taste-skill` |
| [high-end-visual-design](taste-skill/high-end-visual-design/) | `soft-skill` |
| [minimalist-ui](taste-skill/minimalist-ui/) | `minimalist-skill` |
| [industrial-brutalist-ui](taste-skill/industrial-brutalist-ui/) | `brutalist-skill` |
| [redesign-existing-projects](taste-skill/redesign-existing-projects/) | `redesign-skill` |
| [full-output-enforcement](taste-skill/full-output-enforcement/) | `output-skill` |
| [stitch-design-taste](taste-skill/stitch-design-taste/) | Stitch variant (same ecosystem) |

Refresh bundle together:

```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill "<install-name>"
# then copy into vendor/skills/..., run:
python3 scripts/skills_manifest.py sync-docs
```

**Foundry markers:** `sync-docs` injects a `<!-- foundry:dependencies -->` block into each `SKILL.md`. Re-run after upstream pulls or manifest edits.

---

## Licenses — ⚠ capture before public redistribution

These are pinned copies of third-party work; their **upstream licenses govern**.
This repo does **not** yet vendor each upstream's LICENSE text. Before publishing
foundry publicly, for each bundle above: confirm the upstream license permits
redistribution, and add its `LICENSE` (or record the SPDX identifier) alongside
the bundle's `UPSTREAM.md`.

| Bundle | Upstream | License status |
|--------|----------|----------------|
| mattpocock | [mattpocock/skills](https://github.com/mattpocock/skills) | to verify + capture |
| mattpocock-trimmed | mattpocock/skills (fork of caveman) | to verify + capture |
| taste-skill | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | to verify + capture |
