# settings/ — NOT merged (this needs a decision, not a pick)

There is **no single latest `settings.json`.** Five variants are kept side by side
so nothing is lost. They fall into two groups:

## Live per-machine files
| File | Size | Notes |
|------|------|-------|
| `mac.settings.json` | 2102 B (Jul 4) | This machine's live file. |
| `pslap-live.settings.json` | 1673 B (Jul 3) | Laptop's live file. |
| `psdev-live.settings.json` | 1760 B (Jul 3) | Desktop's live file. |
| `psdev-bundle.settings.json` | 1121 B | Older portable subset from the desktop bundle. |

These differ because they're **machine-specific** — per-machine plugin lists,
paths, model/permission choices. That's expected; a settings file is partly
config and partly per-host state.

## The template
| File | Size | Notes |
|------|------|-------|
| `overlay.settings.template.json` | 21210 B | ~10× any live file. The curated template from the pslap overlay — the "everything wired" version that diverged from what any machine actually runs. |

## What to do (later — deferred with distribution)
This is a **hand-merge**, not a "latest wins." The shape of the answer depends on
the distribution decision we deferred:
- If **chezmoi** → this becomes one templated `settings.json.tmpl` with per-host
  data (`.chezmoidata`) for the machine-specific bits.
- If **symlink / marketplace** → likely a shared base + a small per-machine
  `settings.local.json` overlay.

Either way: reconcile the template against what the machines actually run, decide
which keys are shared vs per-host, and collapse to one canonical file + per-host
deltas. Until then, **don't symlink any of these into `~/.claude`** — they're
reference copies.

⚠ Live settings files can reference machine hostnames / paths / employer detail —
sweep before any public publish. An employer/infra scrub was applied when these
were first committed; re-check after any refresh from a live machine file.
