#!/usr/bin/env bash
# post-install-claude.sh — Apply the portable Claude Code layer to a fresh ~/.claude/.
#
# DRAFT — syntax-checked only; first real run is on an actual new machine / VM.
#
# What this does:
#   1. Deploy hooks/, commands/, statusline-command.sh, statuslines/, skills/, bin/bless,
#      CLAUDE.md → ~/.claude/
#   2. Render settings.template.json → ~/.claude/settings.json  ($HOME substitution)
#   3. Remap memory/*.md → ~/.claude/projects/<target-slug>/memory/
#      (slug derived same way Claude Code does: $HOME with /→- and leading -)
#
# Idempotency: skips byte-identical files; backs up (never clobbers) richer existing targets.
#
# Usage: bash infrastructure/claude/post-install-claude.sh
#        Run from anywhere; uses absolute paths.
#
# Prerequisites:
#   - Claude Code installed and ~/.claude/ exists (or will be created)
#   - jq available (for settings.json validation — soft dependency, skipped if absent)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR"
DEST="$HOME/.claude"
MEMORY_SRC="$SRC/memory"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# ── Helpers ───────────────────────────────────────────────────────────────────

step()   { printf "\n\033[1;34m[install %s]\033[0m %s\n" "$1" "$2"; }
ok()     { printf "  \033[0;32m✓\033[0m %s\n" "$1"; }
skip()   { printf "  \033[0;90m~\033[0m (unchanged) %s\n" "$1"; }
backed() { printf "  \033[0;33m↦\033[0m backed up  %s\n" "$1"; }
warn()   { printf "  \033[0;33m!\033[0m %s\n" "$1"; }

# install_file SRC DEST_FILE
# Skips if byte-identical. Backs up dest if it exists and differs (don't clobber richer target).
install_file() {
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
    if [[ -f "$dst" ]]; then
        cp --preserve=xattr "$dst" "${dst}.bak-${TIMESTAMP}"
        backed "$dst"
    fi
    cp --preserve=xattr "$src" "$dst"
    ok "$dst"
}

# install_dir SRC_DIR DEST_DIR
install_dir() {
    local src_dir="$1"
    local dst_dir="$2"
    if [[ ! -d "$src_dir" ]]; then
        warn "Source dir not found — skipping: $src_dir"
        return
    fi
    mkdir -p "$dst_dir"
    find "$src_dir" -type f | while IFS= read -r f; do
        local rel="${f#$src_dir/}"
        # Skip .gitkeep sentinel files
        [[ "$(basename "$f")" == ".gitkeep" ]] && continue
        install_file "$f" "$dst_dir/$rel"
    done
}

# ── Preflight ─────────────────────────────────────────────────────────────────

mkdir -p "$DEST"

# ── Step 1: hooks/ ────────────────────────────────────────────────────────────
step 1 "hooks/"

install_dir "$SRC/hooks" "$DEST/hooks"

# ── Step 2: commands/ ─────────────────────────────────────────────────────────
step 2 "commands/"

install_dir "$SRC/commands" "$DEST/commands"

# ── Step 3: statusline-command.sh ─────────────────────────────────────────────
step 3 "statusline-command.sh"

install_file "$SRC/statusline-command.sh" "$DEST/statusline-command.sh"
chmod +x "$DEST/statusline-command.sh" 2>/dev/null || true

# ── Step 4: statuslines/ ──────────────────────────────────────────────────────
step 4 "statuslines/"

if [[ -d "$SRC/statuslines" ]]; then
    install_dir "$SRC/statuslines" "$DEST/statuslines"
    ok "statuslines/ deployed"
else
    warn "statuslines/ not present in overlay — skipping"
fi

# ── Step 5: bin/bless ─────────────────────────────────────────────────────────
step 5 "bin/bless"

install_file "$SRC/bin/bless" "$DEST/bin/bless"
chmod +x "$DEST/bin/bless" 2>/dev/null || true

# ── Step 6: skills/** ─────────────────────────────────────────────────────────
step 6 "skills/"

install_dir "$SRC/skills" "$DEST/skills"

# ── Step 7: CLAUDE.md ─────────────────────────────────────────────────────────
step 7 "CLAUDE.md"

install_file "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"

# ── Step 8: settings.template.json → ~/.claude/settings.json ─────────────────
# Substitute $HOME placeholder with the target machine's actual $HOME.
# The template uses literal '$HOME' (dollar-sign string); sed expands it to the real path.
step 8 "settings.template.json → ~/.claude/settings.json"

TMPL="$SRC/settings.template.json"
SETTINGS_DEST="$DEST/settings.json"

if [[ ! -f "$TMPL" ]]; then
    warn "settings.template.json not found — skipping settings deployment"
else
    TMP_RENDERED="$(mktemp)"
    # Replace literal $HOME placeholder with the actual target $HOME path.
    sed "s|\\\$HOME|${HOME}|g" "$TMPL" > "$TMP_RENDERED"

    # Optional: validate the rendered JSON with jq if available.
    if command -v jq &>/dev/null; then
        if ! jq empty "$TMP_RENDERED" 2>/dev/null; then
            warn "Rendered settings.json failed JSON validation — NOT deploying (template may need updating)"
            rm -f "$TMP_RENDERED"
        else
            if [[ -f "$SETTINGS_DEST" ]] && cmp -s "$TMP_RENDERED" "$SETTINGS_DEST"; then
                skip "$SETTINGS_DEST"
                rm -f "$TMP_RENDERED"
            else
                if [[ -f "$SETTINGS_DEST" ]]; then
                    cp "$SETTINGS_DEST" "${SETTINGS_DEST}.bak-${TIMESTAMP}"
                    backed "$SETTINGS_DEST"
                fi
                cp "$TMP_RENDERED" "$SETTINGS_DEST"
                ok "$SETTINGS_DEST (rendered from template; $HOME substituted)"
                rm -f "$TMP_RENDERED"
            fi
        fi
    else
        warn "jq not found — deploying settings without JSON validation"
        if [[ -f "$SETTINGS_DEST" ]] && cmp -s "$TMP_RENDERED" "$SETTINGS_DEST"; then
            skip "$SETTINGS_DEST"
        else
            if [[ -f "$SETTINGS_DEST" ]]; then
                cp "$SETTINGS_DEST" "${SETTINGS_DEST}.bak-${TIMESTAMP}"
                backed "$SETTINGS_DEST"
            fi
            cp "$TMP_RENDERED" "$SETTINGS_DEST"
            ok "$SETTINGS_DEST (rendered from template; jq not available for validation)"
        fi
        rm -f "$TMP_RENDERED"
    fi
fi

# ── Step 9: Memory — slug remap ───────────────────────────────────────────────
# Claude Code derives a project slug from the working directory absolute path by
# replacing every '/' with '-' (with a leading '-' since the path starts with '/').
# Example: /home/<user>  →  -home-<user>
#
# The target slug is derived from $HOME on THIS machine.
# The source slug (from the capture machine) is recorded in memory/.source-slug.
# We install the memory files under the TARGET slug's directory.
step 9 "memory/ → ~/.claude/projects/<target-slug>/memory/"

TARGET_SLUG="$(echo "$HOME" | sed 's|/|-|g')"
PROJECTS_MEMORY="$DEST/projects/${TARGET_SLUG}/memory"

if [[ ! -d "$MEMORY_SRC" ]]; then
    warn "memory/ directory not found in overlay — skipping memory deployment"
else
    SOURCE_SLUG_FILE="$MEMORY_SRC/.source-slug"
    if [[ -f "$SOURCE_SLUG_FILE" ]]; then
        SOURCE_SLUG="$(cat "$SOURCE_SLUG_FILE")"
        if [[ "$SOURCE_SLUG" == "$TARGET_SLUG" ]]; then
            ok "Source and target slugs match ($TARGET_SLUG) — direct deploy"
        else
            warn "Slug remap: $SOURCE_SLUG (origin) → $TARGET_SLUG (this machine)"
        fi
    else
        warn ".source-slug not found — deploying to $PROJECTS_MEMORY regardless"
    fi

    mkdir -p "$PROJECTS_MEMORY"

    find "$MEMORY_SRC" -maxdepth 1 -name "*.md" -type f | sort | while IFS= read -r f; do
        install_file "$f" "$PROJECTS_MEMORY/$(basename "$f")"
    done
    ok "memory/*.md deployed to $PROJECTS_MEMORY"

    # Check if a richer existing memory dir exists at a DIFFERENT slug location
    # (e.g. the user already started Claude Code on this machine under a different slug).
    if [[ -f "$SOURCE_SLUG_FILE" ]]; then
        SOURCE_SLUG="$(cat "$SOURCE_SLUG_FILE")"
        ORIGIN_DIR="$DEST/projects/${SOURCE_SLUG}/memory"
        if [[ -d "$ORIGIN_DIR" ]] && [[ "$ORIGIN_DIR" != "$PROJECTS_MEMORY" ]]; then
            warn "Existing memory found at origin slug: $ORIGIN_DIR"
            warn "Review that directory — it may have machine-local notes not in this overlay."
        fi
    fi
fi

# ── Done ──────────────────────────────────────────────────────────────────────
printf "\n\033[1;32m[done]\033[0m Claude layer deployed to %s\n" "$DEST"
printf "\n\033[1;33m[POST-INSTALL NOTES]\033[0m\n"
printf "  1. Launch Claude Code to verify settings.json loaded without errors.\n"
printf "  2. settings.json is DRAFT — the template may be missing newer permission\n"
printf "     entries added after the last capture. Review and extend as needed.\n"
printf "  3. CLAUDE.md may contain employer/work refs (employer name, project names).\n"
printf "     Fine for your own machines; scrub before any public use.\n"
printf "  4. Hook scripts reference ~/.claude/hooks/ — verify absolute paths resolve\n"
printf "     on this machine (should be fine since $HOME is now substituted).\n"
printf "  5. bin/bless is deployed; ensure it is in PATH or update settings.json\n"
printf "     deny rules accordingly.\n"
