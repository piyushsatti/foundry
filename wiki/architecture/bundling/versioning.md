---
title: Versioning
category: architecture
status: draft
summary: How versioning works in the bundling model — version lives only in plugin.json, per-bundle independent bumps, and the release-branch / git-subdir publish mechanism.
sources:
  - docs/adr/0001-materialized-plugin-bundles.md
  - CLAUDE.md
related: [Why Bundling, Architecture Overview, Decisions Ledger]
updated: 2026-07-20
---

# Versioning

> **Status:** draft · **Consolidated from** `ADR-0001` + `CLAUDE.md`.

## Overview

<TODO: versioning is per-bundle and independent; the version of record lives in
one place only.>

## Version of record

<TODO: version lives only in plugin.json; bundle.yaml flags single-own the root
catalog + generated doc blocks (--sync / --check-sync).>

## Independent per-bundle versioning

<TODO: why materialized copy (not symlinks) enables this.>

## Release / publish mechanism

<TODO: build.py materializes to gitignored plugins/; release workflow publishes
to the release branch; catalog on main points there via git-subdir (ref: release).>

## See also

- [Why bundling](why-bundling.md)
