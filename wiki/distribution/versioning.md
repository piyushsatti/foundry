# Versioning

**A plugin's version lives only in its `plugin.json`.** The generated marketplace catalog carries no version key — a duplicate would silently mask bumps (per Claude Code's documented resolution order).

> **Status:** stable

## Rules

- **Per-bundle, independent.** Each bundle bumps on its own schedule; bumps don't couple across plugins.
- **Content change requires a bump.** `claude plugin update` is version-gated, not sha-gated. Ship a change without bumping and installs won't pick it up.
- **Shared library change bumps every consumer.** A `library/` capability change requires bumping each bundle that composes it (manual today).

## Publish path

Built plugins are published to the `release` branch; `marketplace.json` on `main` points each plugin there via `git-subdir` sources (`ref: release`). Rollback of a bad ship = repoint `release` to the last good sha; installs are pull-based and recover on the next marketplace update.
