#!/usr/bin/env bash
# Push foundry skills to a host install dir (optional). Repo is source of truth.
# In-repo workflow: skills_manifest.py sync-docs + validate (no host install).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST_PY="$REPO_ROOT/scripts/skills_manifest.py"
DRY_RUN=false
HOST=""
REPO_LINK=false

usage() {
  cat <<EOF
Usage: $0 --host <claude|cursor|codex|all> [--dry-run]
       $0 --repo [--dry-run]

Push allowlisted skills from skills/manifest.yaml to a host or into this repo.

Hosts (copy via rsync):
  claude   ~/.claude/skills          Claude Code user skills
  cursor   ~/.cursor/skills          Cursor personal skills
  codex    ~/.agents/skills          Codex user skills (Agent Skills standard)
  all      all three user dirs above

Repo (copy via rsync — same as host install):
  --repo   .agents/skills/ + .cursor/skills/ (copies, not symlinks)

In-repo only (no host install):
  python3 scripts/skills_manifest.py sync-docs
  python3 scripts/skills_manifest.py validate

Override install dir: FOUNDRY_SKILLS_INSTALL=/path $0 --host claude
EOF
}

host_dir() {
  case "$1" in
    claude) echo "${FOUNDRY_SKILLS_INSTALL:-$HOME/.claude/skills}" ;;
    cursor) echo "${FOUNDRY_SKILLS_INSTALL:-$HOME/.cursor/skills}" ;;
    codex)  echo "${FOUNDRY_SKILLS_INSTALL:-$HOME/.agents/skills}" ;;
    *) echo "unknown host: $1" >&2; return 1 ;;
  esac
}

sync_copy_to() {
  local install="$1"
  local count=0
  mkdir -p "$install"
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    local src="$REPO_ROOT/$(python3 "$MANIFEST_PY" path "$name")"
    local dest="$install/$name"
    if [[ ! -d "$src" ]]; then
      echo "ERROR: missing skill dir: $src" >&2
      exit 1
    fi
    if $DRY_RUN; then
      echo "would sync: $src/ → $dest/"
    else
      if [[ -e "$dest" ]]; then
        rm -rf "$dest"
      fi
      mkdir -p "$dest"
      rsync -a --exclude '__pycache__' --exclude '*.pyc' "$src/" "$dest/"
      bundle_rel="$(python3 "$MANIFEST_PY" mcp-bundle "$name" 2>/dev/null || true)"
      if [[ -n "$bundle_rel" ]]; then
        bundle_src="$REPO_ROOT/$bundle_rel"
        rsync -a --exclude '__pycache__' --exclude '*.pyc' "$bundle_src/" "$dest/"
        echo "synced: $name (+ MCP bundle) → $install"
      else
        echo "synced: $name → $install"
      fi
    fi
    count=$((count + 1))
  done < <(python3 "$MANIFEST_PY" list)
  echo "Done. $count skills → $install"
}

sync_repo_copies() {
  for base in ".agents/skills" ".cursor/skills"; do
    echo "--- repo:$base ---"
    sync_copy_to "$REPO_ROOT/$base"
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --host) HOST="${2:-}"; shift 2 ;;
    --repo) REPO_LINK=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if ! $REPO_LINK && [[ -z "$HOST" ]]; then
  usage >&2
  exit 1
fi

python3 "$MANIFEST_PY" validate

if $REPO_LINK; then
  sync_repo_copies
fi

if [[ -n "$HOST" ]]; then
  if [[ "$HOST" == "all" ]]; then
    for h in claude cursor codex; do
      echo "--- $h ---"
      sync_copy_to "$(host_dir "$h")"
    done
  else
    sync_copy_to "$(host_dir "$HOST")"
  fi
fi
