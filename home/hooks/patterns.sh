#!/usr/bin/env bash
# Shared match patterns for ~/.claude/hooks/*.sh — sourced, not executed.
#
# Single source of truth for "what the guards look for", so hooks that must agree
# on a pattern stay in sync. Each entry is an ERE *alternation fragment* with NO
# anchors/boundaries — every consumer wraps it with the boundaries it needs (a deny
# guard wants strict word boundaries; a tagger wants a loose contains-match).
#
# Catalog:
#   CC_INSTALL_ALT — project-local package installs. Consumers:
#     unsandboxed-install-guard.sh (deny when unsandboxed) + install-tagger.sh (tag results).
#     GLOBAL/system installs (cargo install, pipx, poetry, gem, brew, apt, go install,
#     pre-commit install, uv pip uninstall, uv tool …) are intentionally NOT here — they
#     stay denied in BOTH tiers via settings.json deny rules.

CC_INSTALL_ALT='uvx|uv[[:space:]]+add|uv[[:space:]]+pip[[:space:]]+install|pip3?[[:space:]]+install|npm[[:space:]]+(install|i|add|ci)|pnpm[[:space:]]+(add|install|i)|yarn[[:space:]]+(add|install)|cargo[[:space:]]+add'
