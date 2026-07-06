#!/usr/bin/env bash
# memkey.sh — shared library for Claude Code cwd-key slug + memory-index logic.
# Sourceable; defines functions only. No side effects on source, no top-level execution.
# Dependencies: coreutils, grep, sed.

# memkey_slug "<abs_path>"
# stdout: the cwd-key slug — every '/' and '.' in the absolute path replaced with '-'.
memkey_slug() {
    printf '%s\n' "$1" | sed 's|[/.]|-|g'
}

# memkey_memdir "<abs_path>"
# stdout: "$HOME/.claude/projects/<slug>/memory"
memkey_memdir() {
    local slug
    slug="$(memkey_slug "$1")"
    printf '%s\n' "${HOME}/.claude/projects/${slug}/memory"
}

# memkey_is_worktree "<abs_path>"
# return code: 0 if path contains /.worktrees/ segment, else 1. No stdout.
memkey_is_worktree() {
    case "$1" in
        */.worktrees/*) return 0 ;;
        *)              return 1 ;;
    esac
}

# memkey_index_lines "<memdir>" "<max>"
# stdout: first <max> lines from "<memdir>/MEMORY.md" matching '^- \['.
# If MEMORY.md does not exist → empty stdout, return 0.
memkey_index_lines() {
    grep '^- \[' "$1/MEMORY.md" 2>/dev/null | head -n "$2"
}

# memkey_entry_genericity "<memdir>" "<index_line>"
# stdout: generic | specific | unknown
# Parses the referenced filename from the index line, reads its YAML frontmatter
# for "genericity:" field. Returns "unknown" if file missing, unparseable, or no field.
memkey_entry_genericity() {
    local memdir="$1"
    local index_line="$2"

    # Extract filename from the first ](...) group in the index line
    local filename
    filename="$(printf '%s' "$index_line" | sed -n 's/^- \[[^]]*\](\([^)]*\)).*/\1/p')"

    if [ -z "$filename" ]; then
        printf 'unknown\n'
        return 0
    fi

    local filepath="${memdir}/${filename}"

    if [ ! -f "$filepath" ]; then
        printf 'unknown\n'
        return 0
    fi

    # Read frontmatter (between first --- and second ---) and find genericity: field
    local value
    value="$(awk '
        /^---/ { if (in_fm) { exit } else { in_fm=1; next } }
        in_fm && /^[[:space:]]*genericity:/ {
            sub(/^[[:space:]]*genericity:[[:space:]]*/, "")
            print
            exit
        }
    ' "$filepath")"

    case "$value" in
        generic)  printf 'generic\n'  ;;
        specific) printf 'specific\n' ;;
        *)        printf 'unknown\n'  ;;
    esac
}
