#!/usr/bin/env bash
# memory-durability.sh — Claude Code SessionStart hook.
# Re-injects the durable memory index after session start (and future: post-compaction).
# Sourceable for testing; runs main() only when executed directly.
#
# Dependencies: bash, coreutils (readlink/realpath), jq, grep, sed.

SCRIPT_DIR=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")" && pwd)
source "$SCRIPT_DIR/lib/memkey.sh"

# PREAMBLE — first line of every context block.
_MD_PREAMBLE="Durable memory index (re-anchored across compaction). Open a listed file for detail:"

# collect_levels "<cwd>"
# stdout: ordered list of dirs (NEAREST FIRST) to scan: <cwd>, then parents up to $HOME.
# If <cwd> is not under $HOME (and not $HOME), emit only <cwd> (never walk to /).
collect_levels() {
    local cwd="$1"
    local home_dir="$HOME"

    # Normalise: strip trailing slashes
    cwd="${cwd%/}"
    home_dir="${home_dir%/}"

    # Check whether cwd is under HOME (or IS home)
    local is_under_home=0
    if [ "$cwd" = "$home_dir" ]; then
        is_under_home=1
    else
        # cwd starts with home_dir + /
        case "$cwd" in
            "$home_dir"/*)
                is_under_home=1
                ;;
        esac
    fi

    if [ "$is_under_home" -eq 0 ]; then
        # Not under HOME — emit only cwd itself
        printf '%s\n' "$cwd"
        return 0
    fi

    # Walk from cwd up to (and including) HOME
    local dir="$cwd"
    while true; do
        printf '%s\n' "$dir"
        if [ "$dir" = "$home_dir" ]; then
            break
        fi
        local parent
        parent="$(dirname "$dir")"
        if [ "$parent" = "$dir" ]; then
            # Reached filesystem root — safety stop
            break
        fi
        dir="$parent"
    done
}

# gather_level "<dir>"
# stdout: a level block (header + index lines), or empty if no memory for this dir.
gather_level() {
    local dir="$1"
    local memdir
    memdir="$(memkey_memdir "$dir")"

    # Check MEMORY.md exists
    if [ ! -f "$memdir/MEMORY.md" ]; then
        return 0
    fi

    # Get index lines (up to 500)
    local lines
    lines="$(memkey_index_lines "$memdir" 500)"

    if [ -z "$lines" ]; then
        return 0
    fi

    # Count lines
    local n
    n="$(printf '%s\n' "$lines" | wc -l | tr -d ' ')"

    # Abbreviate dir: replace leading $HOME with ~
    local abbrev_dir="$dir"
    local home_dir="${HOME%/}"
    if [ "$dir" = "$home_dir" ]; then
        abbrev_dir="~"
    else
        case "$dir" in
            "$home_dir"/*)
                abbrev_dir="~${dir#"$home_dir"}"
                ;;
        esac
    fi

    printf '## %s (%s) — %s/MEMORY.md\n' "$abbrev_dir" "$n" "$memdir"
    printf '%s\n' "$lines"
}

# assemble_levels "<cwd>"
# stdout: assembled context string (empty if no level had memory), nearest-first, no truncation.
# Claude Code archives hook output >10k chars to a file + preview (no data loss), so we emit
# all levels in full and rely on that platform behaviour rather than truncating.
assemble_levels() {
    local cwd="$1"

    # Collect ordered dirs (nearest first)
    local dirs
    dirs="$(collect_levels "$cwd")"

    local accumulated=""
    local seen_realpaths=""  # newline-separated list of seen realpath strings

    while IFS= read -r dir; do
        local memdir
        memdir="$(memkey_memdir "$dir")"

        # Dedup by realpath
        local real_memdir
        real_memdir="$(realpath "$memdir" 2>/dev/null || readlink -f "$memdir" 2>/dev/null || printf '%s' "$memdir")"

        # Check if this realpath has been seen
        local already_seen=0
        while IFS= read -r seen; do
            if [ "$seen" = "$real_memdir" ]; then
                already_seen=1
                break
            fi
        done <<< "$seen_realpaths"

        if [ "$already_seen" -eq 1 ]; then
            continue
        fi

        # Mark as seen
        if [ -n "$seen_realpaths" ]; then
            seen_realpaths="$seen_realpaths
$real_memdir"
        else
            seen_realpaths="$real_memdir"
        fi

        # Only proceed if MEMORY.md exists with entries
        if [ ! -f "$memdir/MEMORY.md" ]; then
            continue
        fi
        local lines
        lines="$(memkey_index_lines "$memdir" 500)"
        if [ -z "$lines" ]; then
            continue
        fi

        # Build the level block
        local block
        block="$(gather_level "$dir")"

        if [ -z "$block" ]; then
            continue
        fi

        if [ -n "$accumulated" ]; then
            accumulated="$accumulated
$block"
        else
            accumulated="$block"
        fi
    done <<< "$dirs"

    # If nothing accumulated, return empty
    if [ -z "$accumulated" ]; then
        return 0
    fi

    printf '%s' "$_MD_PREAMBLE
$accumulated"
}

# emit_json "<ctx>"
# stdout: JSON hook payload.
emit_json() {
    local ctx="$1"
    jq -n --arg ctx "$ctx" \
        '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$ctx}}'
}

# main "$@"
# Entry point: parse --mode, read cwd from stdin JSON, build context, emit or exit.
main() {
    local mode="sessionstart"

    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --mode=*)
                mode="${1#--mode=}"
                shift
                ;;
            --mode)
                mode="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    # Branch point for future modes
    case "$mode" in
        sessionstart)
            # Read cwd from stdin JSON; fallback to $PWD
            local stdin_data
            stdin_data="$(cat 2>/dev/null)"
            local cwd=""
            if [ -n "$stdin_data" ]; then
                cwd="$(printf '%s' "$stdin_data" | jq -r '.cwd // empty' 2>/dev/null)"
            fi
            if [ -z "$cwd" ]; then
                cwd="$PWD"
            fi

            local ctx
            ctx="$(assemble_levels "$cwd")"

            if [ -z "$ctx" ]; then
                exit 0
            fi

            emit_json "$ctx"
            ;;
        postcompact)
            # Future: post-compaction re-injection
            # TODO: implement --mode=postcompact
            exit 0
            ;;
        *)
            printf 'memory-durability.sh: unknown mode: %s\n' "$mode" >&2
            exit 1
            ;;
    esac
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
