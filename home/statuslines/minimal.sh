#!/usr/bin/env bash
# Claude statusline: Minimal
# Shows: model [rate%]
# One clean line. Maximum focus, minimum chrome.

input=$(cat)

mauve='\033[38;2;203;166;247m'
red='\033[38;2;243;139;168m'
green='\033[38;2;166;227;161m'
yellow='\033[38;2;249;226;175m'
peach='\033[38;2;250;179;135m'
overlay0='\033[38;2;108;112;134m'
bold='\033[1m'
reset='\033[0m'

model_full=$(echo "$input" | jq -r '.model.display_name // empty')
model="${model_full%% (*}"
exceeds_200k=$(echo "$input" | jq -r '.exceeds_200k_tokens // false')
rate_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')

if [ "$exceeds_200k" = "true" ]; then
    mc="${red}${bold}"
else
    mc="${mauve}"
fi

rate_int=${rate_pct%.*}; rate_int=${rate_int:-0}
if [ "$rate_int" -ge 90 ]; then rc="${red}${bold}"
elif [ "$rate_int" -ge 75 ]; then rc="${peach}"
elif [ "$rate_int" -ge 50 ]; then rc="${yellow}"
else rc="${green}"; fi

line="${mc}${model}${reset}"
[ -n "$rate_pct" ] && line="${line} ${overlay0}${rc}${rate_int}%${reset}"

printf "%b\n" "$line"
