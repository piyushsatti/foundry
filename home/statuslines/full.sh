#!/usr/bin/env bash
# Claude statusline: Full
# Line 1: folder [branch] [±dirty] [venv]
# Line 2: model [tokens] [rate%] [session time]
# Maximum awareness. Shows token usage and session duration.

input=$(cat)

lavender='\033[38;2;180;190;254m'
subtext1='\033[38;2;186;194;222m'
teal='\033[38;2;148;226;213m'
mauve='\033[38;2;203;166;247m'
red='\033[38;2;243;139;168m'
green='\033[38;2;166;227;161m'
yellow='\033[38;2;249;226;175m'
peach='\033[38;2;250;179;135m'
sky='\033[38;2;137;220;235m'
sapphire='\033[38;2;116;199;236m'
overlay0='\033[38;2;108;112;134m'
bold='\033[1m'
reset='\033[0m'

cwd=$(echo "$input" | jq -r '.cwd // empty')
model_full=$(echo "$input" | jq -r '.model.display_name // empty')
model="${model_full%% (*}"
exceeds_200k=$(echo "$input" | jq -r '.exceeds_200k_tokens // false')
rate_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
total_tokens=$(echo "$input" | jq -r '.total_tokens // empty')
session_start=$(echo "$input" | jq -r '.session_start // empty')

branch=""
dirty=""
if [ -n "$cwd" ]; then
    branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ -n "$branch" ]; then
        changes=$(git -C "$cwd" --no-optional-locks status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        [ "$changes" -gt 0 ] 2>/dev/null && dirty="±${changes}"
    fi
fi

venv=""
if [ -n "$cwd" ] && [ -d "$cwd/.venv" ]; then
    venv=".venv"
elif [ -n "$VIRTUAL_ENV" ]; then
    venv=$(basename "$VIRTUAL_ENV")
fi

folder=""
[ -n "$cwd" ] && folder=$(basename "$cwd")

# Token count formatting (e.g., 150k, 1.2M)
tokens_fmt=""
if [ -n "$total_tokens" ] && [ "$total_tokens" != "null" ]; then
    if [ "$total_tokens" -ge 1000000 ] 2>/dev/null; then
        tokens_fmt="$(awk "BEGIN{printf \"%.1fM\", $total_tokens/1000000}")"
    elif [ "$total_tokens" -ge 1000 ] 2>/dev/null; then
        tokens_fmt="$(awk "BEGIN{printf \"%.0fk\", $total_tokens/1000}")"
    else
        tokens_fmt="${total_tokens}"
    fi
fi

# Session duration
session_dur=""
if [ -n "$session_start" ] && [ "$session_start" != "null" ]; then
    start_epoch=$(date -d "$session_start" +%s 2>/dev/null || date -jf "%Y-%m-%dT%H:%M:%S" "$session_start" +%s 2>/dev/null)
    if [ -n "$start_epoch" ]; then
        now_epoch=$(date +%s)
        elapsed=$((now_epoch - start_epoch))
        hours=$((elapsed / 3600))
        mins=$(( (elapsed % 3600) / 60))
        if [ "$hours" -gt 0 ]; then
            session_dur="${hours}h${mins}m"
        else
            session_dur="${mins}m"
        fi
    fi
fi

if [ "$exceeds_200k" = "true" ]; then mc="${red}${bold}"; else mc="${mauve}"; fi

rate_int=${rate_pct%.*}; rate_int=${rate_int:-0}
if [ "$rate_int" -ge 90 ]; then rc="${red}${bold}"
elif [ "$rate_int" -ge 75 ]; then rc="${peach}"
elif [ "$rate_int" -ge 50 ]; then rc="${yellow}"
else rc="${green}"; fi

# Token color: green < 100k, yellow < 200k, red >= 200k
if [ "$exceeds_200k" = "true" ]; then tc="${red}"
elif [ -n "$total_tokens" ] && [ "$total_tokens" -ge 100000 ] 2>/dev/null; then tc="${yellow}"
else tc="${green}"; fi

# Line 1: folder [branch] [±dirty] [venv]
line1="${lavender}${bold}${folder}${reset}"
if [ -n "$branch" ]; then
    line1="${line1} ${overlay0}[${subtext1}${branch}${reset}"
    [ -n "$dirty" ] && line1="${line1} ${yellow}${dirty}${reset}"
    line1="${line1}${overlay0}]${reset}"
fi
[ -n "$venv" ] && line1="${line1} ${overlay0}[${teal}${venv}${overlay0}]${reset}"

# Line 2: model [tokens] [rate%] [session]
line2="${mc}${model}${reset}"
[ -n "$tokens_fmt" ] && line2="${line2} ${overlay0}[${tc}${tokens_fmt}${overlay0}]${reset}"
[ -n "$rate_pct" ] && line2="${line2} ${overlay0}[${rc}${rate_int}%${overlay0}]${reset}"
[ -n "$session_dur" ] && line2="${line2} ${overlay0}[${sky}${session_dur}${overlay0}]${reset}"

printf "%b\n" "$line1"
printf "%b\n" "$line2"
