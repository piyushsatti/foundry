# Distribution Overview

**Distribution is how plugins go from DRY source to installable artifact.** foundry develops in a modular source tree and ships self-contained bundles built from it.

> **Status:** stable

## Facets

- **[Bundling](bundling)** — self-contained bundle sources and shared-capability promotion.
- **[Versioning](versioning)** — per-bundle version bumps and how the served catalog resolves them.
- **Release / serve** — publishing built plugins to the `release` branch, cataloged on `main`.

## The pipeline

Source lives in `bundles/`. `scripts/build.py` materializes each into `plugins/` (gitignored). The release workflow publishes that tree to the `release` branch; `marketplace.json` on `main` points each plugin there via `git-subdir` sources (`ref: release`).

```mermaid
graph LR
  A[bundles/ source] --> B[scripts/build.py]
  B --> C[plugins/ gitignored]
  C --> D[release branch]
  D --> E[marketplace.json on main]
  E --> F[install]
```

`main` stays fully DRY — the served artifact is produced by one gated workflow, never hand-committed. `main` alone is not installable; installs come from `release`.
