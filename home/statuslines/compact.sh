#!/usr/bin/env bash
# Claude statusline: Compact
# Single line with symbols instead of words.
# folder  branch  model ◆ 42% ● 150k
# Dense but scannable. For small terminals or tiling WMs.

input=$(cat)

lavender='\033[38;2;180;190;254m'
subtext1='\033[38;2;186;194;222m'
mauve='\033[38;2;203;166;247m'
red='\033[38;2;243;139;168m'
green='\033[38;2;166;227;161m'
yellow='\033[38;2;249;226;175m'
peach='\033[38;2;250;179;135m'
overlay0='\033[38;2;108;112;134m'
bold='\033[1m'
reset='\033[0m'

cwd=$(echo "$input" | jq -r '.cwd // empty')
model_full=$(echo "$input" | jq -r '.model.display_name // empty')
model="${model_full%% (*}"
exceeds_200k=$(echo "$input" | jq -r '.exceeds_200k_tokens // false')
rate_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
total_tokens=$(echo "$input" | jq -r '.total_tokens // empty')

branch=""
[ -n "$cwd" ] && branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)
folder=""
[ -n "$cwd" ] && folder=$(basename "$cwd")

# Shorten model name
case "$model" in
    *opus*|*Opus*)   model_short="opus" ;;
    *sonnet*|*Sonnet*) model_short="snnt" ;;
    *haiku*|*Haiku*) model_short="hku" ;;
    *)               model_short="$model" ;;
esac

# Tokens
tokens_fmt=""
if [ -n "$total_tokens" ] && [ "$total_tokens" != "null" ]; then
    if [ "$total_tokens" -ge 1000000 ] 2>/dev/null; then
        tokens_fmt="$(awk "BEGIN{printf \"%.1fM\", $total_tokens/1000000}")"
    elif [ "$total_tokens" -ge 1000 ] 2>/dev/null; then
        tokens_fmt="$(awk "BEGIN{printf \"%.0fk\", $total_tokens/1000}")"
    fi
fi

if [ "$exceeds_200k" = "true" ]; then mc="${red}${bold}"; else mc="${mauve}"; fi

rate_int=${rate_pct%.*}; rate_int=${rate_int:-0}
if [ "$rate_int" -ge 90 ]; then rc="${red}${bold}"
elif [ "$rate_int" -ge 75 ]; then rc="${peach}"
elif [ "$rate_int" -ge 50 ]; then rc="${yellow}"
else rc="${green}"; fi

# Single line: folder  branch  model ◆ rate ● tokens
line="${lavender}${folder}${reset}"
[ -n "$branch" ] && line="${line} ${overlay0}${reset}${subtext1}${branch}${reset}"
line="${line} ${overlay0}│${reset} ${mc}${model_short}${reset}"
[ -n "$rate_pct" ] && line="${line} ${rc}◆${rate_int}%${reset}"
[ -n "$tokens_fmt" ] && line="${line} ${overlay0}●${reset}${tokens_fmt}"

printf "%b\n" "$line"
