#!/usr/bin/env bash
# capture-claude.sh — Snapshot the portable Claude Code layer from ~/.claude/ → this repo.
#
# Re-runnable: skips byte-identical files; backs up differing files before overwriting.
# After running, review the Phase 2 checklist in README.md (employer/work-ref taint in
# CLAUDE.md and settings.template.json is NOT auto-stripped — see README).
#
# Usage: bash infrastructure/claude/capture-claude.sh
# Run from anywhere; uses absolute paths.
#
# EXCLUDES (intentional):
#   .credentials.json, audit.jsonl, *.jsonl transcripts, cache/, telemetry/,
#   image-cache/, tasks/, agents/, sessions/, shell-snapshots/, daemon*,
#   and ALL of projects/*/  EXCEPT the memory/ subdir.
# MEMORY (Decision A):
#   Copies ~/.claude/projects/<source-slug>/memory/*.md → infrastructure/claude/memory/
#   Records the origin slug in infrastructure/claude/memory/.source-slug

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIVE="$HOME/.claude"
DEST="$SCRIPT_DIR"
MEMORY_DEST="$DEST/memory"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# ── Helpers ───────────────────────────────────────────────────────────────────

step()   { printf "\n\033[1;34m[capture %s]\033[0m %s\n" "$1" "$2"; }
ok()     { printf "  \033[0;32m✓\033[0m %s\n" "$1"; }
skip()   { printf "  \033[0;90m~\033[0m (unchanged) %s\n" "$1"; }
backed() { printf "  \033[0;33m↦\033[0m backed up  %s\n" "$1"; }
warn()   { printf "  \033[0;33m!\033[0m %s\n" "$1"; }

# copy_file SRC DEST_FILE
# Skips if byte-identical; backs up dest first if content differs.
copy_file() {
    local src="$1"
    local dst="$2"
    if [[ ! -f "$src" ]]; then
        warn "Source not found — skipping: $src"
        return
    fi
    mkdir -p "$(dirname "$dst")"
    if [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
        skip "$dst"
        return
    fi
    # ── Section B: last_updated conflict guard ──────────────────────────────────
    # If the vault copy (dst) carries a last_updated: NEWER than the live copy (src),
    # it was likely edited on another machine — do NOT clobber it with an older live
    # copy. Only engages when BOTH files have the field (ISO YYYY-MM-DD, so string
    # comparison == chronological); otherwise behaves exactly as before (no regression).
    if [[ -f "$dst" ]]; then
        local src_lu dst_lu
        src_lu=$(grep -m1 '^last_updated:' "$src" 2>/dev/null | sed 's/^last_updated:[[:space:]]*//; s/[[:space:]]*$//') || true
        dst_lu=$(grep -m1 '^last_updated:' "$dst" 2>/dev/null | sed 's/^last_updated:[[:space:]]*//; s/[[:space:]]*$//') || true
        if [[ -n "$src_lu" && -n "$dst_lu" && "$dst_lu" > "$src_lu" ]]; then
            warn "vault copy NEWER than live ($dst_lu > $src_lu) — likely edited on another machine; skipping to avoid clobber. Resolve manually: $dst"
            return
        fi
    fi
    if [[ -f "$dst" ]]; then
        cp --preserve=xattr "$dst" "${dst}.bak-${TIMESTAMP}"
        backed "$dst"
    fi
    cp --preserve=xattr "$src" "$dst"
    ok "$dst"
}

# copy_dir SRC_DIR DEST_DIR [--include-pattern GLOB]
# Copies regular files (recursively) from SRC_DIR into DEST_DIR.
copy_dir() {
    local src_dir="$1"
    local dst_dir="$2"
    if [[ ! -d "$src_dir" ]]; then
        warn "Source dir not found — skipping: $src_dir"
        return
    fi
    mkdir -p "$dst_dir"
    # Use find to recurse; preserve xattr on each file.
    find "$src_dir" -type f | while IFS= read -r f; do
        local rel="${f#$src_dir/}"
        copy_file "$f" "$dst_dir/$rel"
    done
}

# ── Step 1: hooks/ ────────────────────────────────────────────────────────────
step 1 "hooks/*.sh (+ stats.sh)"

if [[ -d "$LIVE/hooks" ]]; then
    mkdir -p "$DEST/hooks"
    find "$LIVE/hooks" -maxdepth 1 -name "*.sh" -type f | sort | while IFS= read -r f; do
        copy_file "$f" "$DEST/hooks/$(basename "$f")"
    done
    ok "hooks/ synced"
else
    warn "$LIVE/hooks not found — skipping"
fi

# ── Step 2: commands/ ─────────────────────────────────────────────────────────
step 2 "commands/*"

if [[ -d "$LIVE/commands" ]]; then
    copy_dir "$LIVE/commands" "$DEST/commands"
    ok "commands/ synced"
else
    warn "$LIVE/commands not found — skipping"
fi

# ── Step 3: statusline-command.sh ─────────────────────────────────────────────
step 3 "statusline-command.sh"

copy_file "$LIVE/statusline-command.sh" "$DEST/statusline-command.sh"

# ── Step 4: statuslines/ ──────────────────────────────────────────────────────
# Note: live ~/.claude/ may not have a statuslines/ dir (the overlay carries the
# canonical copies from a prior sync). Capture if the dir exists; warn if absent.
step 4 "statuslines/"

if [[ -d "$LIVE/statuslines" ]]; then
    copy_dir "$LIVE/statuslines" "$DEST/statuslines"
    ok "statuslines/ synced"
else
    warn "$LIVE/statuslines not found — overlay copy kept as-is (already committed)"
fi

# ── Step 5: bin/bless ─────────────────────────────────────────────────────────
step 5 "bin/bless"

copy_file "$LIVE/bin/bless" "$DEST/bin/bless"

# ── Step 6: skills/** ─────────────────────────────────────────────────────────
step 6 "skills/**"

if [[ -d "$LIVE/skills" ]]; then
    copy_dir "$LIVE/skills" "$DEST/skills"
    ok "skills/ synced"
else
    warn "$LIVE/skills not found — skipping"
fi

# ── Step 7: CLAUDE.md ─────────────────────────────────────────────────────────
step 7 "CLAUDE.md"

copy_file "$LIVE/CLAUDE.md" "$DEST/CLAUDE.md"

# ── Step 8: settings.json → settings.template.json ───────────────────────────
# Replace machine-absolute paths with portable placeholders:
#   /home/<user>  →  $HOME
#   $HOME paths in sandbox.filesystem.*  (already use $HOME in live settings)
# Carry NO secrets: .credentials.json is excluded at the source level.
step 8 "settings.json → settings.template.json"

SETTINGS_SRC="$LIVE/settings.json"
SETTINGS_TMPL="$DEST/settings.template.json"

if [[ ! -f "$SETTINGS_SRC" ]]; then
    warn "$SETTINGS_SRC not found — skipping settings template"
else
    # Build the substituted template in a temp file, then use copy_file logic.
    TMP_TMPL="$(mktemp)"
    # Replace /home/<current-user> (and any /home/<user> hardcoded in sandbox paths)
    # with $HOME so the template is portable.
    sed "s|/home/${USER}|\$HOME|g" "$SETTINGS_SRC" > "$TMP_TMPL"

    if [[ -f "$SETTINGS_TMPL" ]] && cmp -s "$TMP_TMPL" "$SETTINGS_TMPL"; then
        skip "$SETTINGS_TMPL"
    else
        if [[ -f "$SETTINGS_TMPL" ]]; then
            cp --preserve=xattr "$SETTINGS_TMPL" "${SETTINGS_TMPL}.bak-${TIMESTAMP}"
            backed "$SETTINGS_TMPL"
        fi
        cp "$TMP_TMPL" "$SETTINGS_TMPL"
        ok "$SETTINGS_TMPL"
    fi
    rm -f "$TMP_TMPL"
fi

# ── Step 9: Memory (Decision A) ───────────────────────────────────────────────
# Derive the source slug: abs path of HOME with / replaced by - and leading -.
# e.g. /home/<user>  →  -home-<user>   (verified against existing projects/ dir)
step 9 "memory/ from ~/.claude/projects/<slug>/memory/"

SOURCE_SLUG="$(echo "$HOME" | sed 's|/|-|g')"
MEMORY_SRC="$LIVE/projects/${SOURCE_SLUG}/memory"

mkdir -p "$MEMORY_DEST"

if [[ -d "$MEMORY_SRC" ]]; then
    find "$MEMORY_SRC" -maxdepth 1 -name "*.md" -type f | sort | while IFS= read -r f; do
        copy_file "$f" "$MEMORY_DEST/$(basename "$f")"
    done

    # Record origin slug so post-install can remap if the target machine slug differs.
    SLUG_FILE="$MEMORY_DEST/.source-slug"
    if [[ ! -f "$SLUG_FILE" ]] || [[ "$(cat "$SLUG_FILE")" != "$SOURCE_SLUG" ]]; then
        printf '%s\n' "$SOURCE_SLUG" > "$SLUG_FILE"
        ok "$SLUG_FILE (source slug: $SOURCE_SLUG)"
    else
        skip "$SLUG_FILE"
    fi
    ok "memory/ synced from $MEMORY_SRC"
else
    warn "Memory source not found: $MEMORY_SRC"
    warn "Expected slug: $SOURCE_SLUG  — check that ~/.claude/projects/<slug>/memory/ exists"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
printf "\n\033[1;32m[done]\033[0m Claude layer captured → %s\n" "$DEST"
printf "\n\033[1;33m[IMPORTANT — Phase 2]\033[0m Review before committing:\n"
printf "  1. CLAUDE.md may contain employer/work references (your work email,\n"
printf "     employer name, project names). Fine for own-machine use; MUST scrub before any\n"
printf "     public push. See README.md 'Employer-Clean Seam' section.\n"
printf "  2. settings.template.json: verify no hardcoded /home/%s paths leaked through.\n" "$USER"
printf "     Run: grep -n 'home/%s' %s/settings.template.json\n" "$USER" "$DEST"
printf "  3. memory/*.md may contain employer/project context — same scrub applies.\n"
printf "  See README.md for the full Phase 2 checklist.\n"
