#!/usr/bin/env bash
# Claude statusline: Standard (default)
# Line 1: folder [branch] [venv]
# Line 2: model [rate%]
# Balanced info density. Good for daily work.

input=$(cat)

lavender='\033[38;2;180;190;254m'
subtext1='\033[38;2;186;194;222m'
teal='\033[38;2;148;226;213m'
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

branch=""
[ -n "$cwd" ] && branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)

venv=""
if [ -n "$cwd" ] && [ -d "$cwd/.venv" ]; then
    venv=".venv"
elif [ -n "$VIRTUAL_ENV" ]; then
    venv=$(basename "$VIRTUAL_ENV")
fi

folder=""
[ -n "$cwd" ] && folder=$(basename "$cwd")

if [ "$exceeds_200k" = "true" ]; then mc="${red}${bold}"; else mc="${mauve}"; fi

rate_int=${rate_pct%.*}; rate_int=${rate_int:-0}
if [ "$rate_int" -ge 90 ]; then rc="${red}${bold}"
elif [ "$rate_int" -ge 75 ]; then rc="${peach}"
elif [ "$rate_int" -ge 50 ]; then rc="${yellow}"
else rc="${green}"; fi

line1="${lavender}${bold}${folder}${reset}"
[ -n "$branch" ] && line1="${line1} ${overlay0}[${subtext1}${branch}${overlay0}]${reset}"
[ -n "$venv" ] && line1="${line1} ${overlay0}[${teal}${venv}${overlay0}]${reset}"

line2="${mc}${model}${reset}"
[ -n "$rate_pct" ] && line2="${line2} ${overlay0}[${rc}${rate_int}%${reset}${overlay0}]${reset}"

printf "%b\n" "$line1"
printf "%b\n" "$line2"
