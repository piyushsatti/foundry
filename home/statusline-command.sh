#!/usr/bin/env bash
input=$(cat)

# ── Catppuccin Mocha palette ───────────────────────────────
# Primary (bold, high contrast)
lavender='\033[38;2;180;190;254m'  # #b4befe — folder

# Secondary (medium contrast)
subtext1='\033[38;2;186;194;222m'  # #bac2de — branch
teal='\033[38;2;148;226;213m'      # #94e2d5 — venv
sky='\033[38;2;137;220;235m'       # #89dceb — session name
sapphire='\033[38;2;116;199;236m'  # #74c7ec — ctx usage (normal)
flamingo='\033[38;2;242;205;205m'  # #f2cdcd — output style
blue='\033[38;2;137;180;250m'      # #89b4fa — effort level

# Accent
mauve='\033[38;2;203;166;247m'     # #cba6f7 — model
red='\033[38;2;243;139;168m'       # #f38ba8 — model when >200k / ctx when >80%
green='\033[38;2;166;227;161m'     # #a6e3a1 — rate limit low
yellow='\033[38;2;249;226;175m'    # #f9e2af — rate limit mid
peach='\033[38;2;250;179;135m'     # #fab387 — rate limit high

# Chrome
overlay0='\033[38;2;108;112;134m'  # #6c7086 — brackets / muted labels
bold='\033[1m'
reset='\033[0m'

# ── Extract fields ─────────────────────────────────────────
cwd=$(echo "$input" | jq -r '.cwd // empty')
exceeds_200k=$(echo "$input" | jq -r '.exceeds_200k_tokens // false')
rate_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
rate_reset_5h=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
weekly_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
weekly_reset_7d=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')
thinking_enabled=$(echo "$input" | jq -r '.thinking.enabled // false')
ctx_used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
ctx_tokens=$(echo "$input" | jq -r '.context_window.total_input_tokens // empty')
ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // empty')
output_style=$(echo "$input" | jq -r '.output_style.name // empty')
effort_raw=$(echo "$input" | jq -r '.effort.level // empty')
git_worktree=$(echo "$input" | jq -r '.workspace.git_worktree // empty')
agent_name=$(echo "$input" | jq -r '.agent.name // empty')

# Use harness model.id — updated immediately on /model switch
live_model_id=$(echo "$input" | jq -r '.model.id // empty')

model=""
if [ -n "$live_model_id" ]; then
  model=$(python3 -c "
import sys
mid = '$live_model_id'
for family in ('haiku', 'sonnet', 'opus'):
    if family not in mid:
        continue
    suffix = mid.split(family + '-', 1)[1]
    suffix = suffix.split('[', 1)[0]
    parts = []
    for p in suffix.split('-'):
        if p.isdigit() and len(p) <= 2:
            parts.append(p)
        else:
            break
    version = '.'.join(parts) if parts else suffix.split('-')[0]
    print(family.capitalize() + ' ' + version)
    sys.exit(0)
print(mid)
" 2>/dev/null)
fi

# Fallback to harness display_name if model.id is missing or unparseable
if [ -z "$model" ]; then
  model_full=$(echo "$input" | jq -r '.model.display_name // empty')
  model="${model_full%% (*}"
fi

branch=""
[ -n "$cwd" ] && branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)

# Linked-worktree fallback detection: in a git worktree, .git is a FILE (gitdir pointer)
[ -z "$git_worktree" ] && [ -n "$cwd" ] && [ -f "$cwd/.git" ] && git_worktree="wt"

# CWD tail: tilde-substitute $HOME prefix, then fish-style abbreviation
folder=""
if [ -n "$cwd" ]; then
  home_dir="${HOME:-/home/$(whoami)}"
  # Replace $HOME prefix with ~
  if [ "$cwd" = "$home_dir" ]; then
    display_cwd="~"
  elif [ "${cwd#"$home_dir/"}" != "$cwd" ]; then
    display_cwd="~/${cwd#"$home_dir/"}"
  else
    display_cwd="$cwd"
  fi

  # Fish-style abbreviation: last 2 components full, every middle component
  # shortened to its first char (dot-dirs keep dot + first char: .worktrees → .w)
  if [ "$display_cwd" = "~" ] || [ "$display_cwd" = "/" ]; then
    folder="$display_cwd"
  else
    if [ "${display_cwd#\~/}" != "$display_cwd" ]; then
      anchor="~"
      rel="${display_cwd#\~/}"
    else
      anchor=""
      rel="${display_cwd#/}"
    fi
    IFS='/' read -r -a _parts <<< "$rel"
    _n=${#_parts[@]}
    abbrev=""
    for ((_i = 0; _i < _n; _i++)); do
      comp="${_parts[_i]}"
      if [ "$_i" -ge $((_n - 2)) ] || [ -z "$comp" ]; then
        seg="$comp"
      elif [ "${comp#.}" != "$comp" ]; then
        seg="${comp:0:2}"
      else
        seg="${comp:0:1}"
      fi
      abbrev="${abbrev:+${abbrev}/}${seg}"
    done
    if [ -n "$anchor" ]; then
      folder="${anchor}/${abbrev}"
    else
      folder="/${abbrev}"
    fi
    [ -z "$abbrev" ] && folder="$display_cwd"
  fi
fi

# Model color: red when >200k, mauve otherwise
if [ "$exceeds_200k" = "true" ]; then
    model_color="${red}${bold}"
else
    model_color="${mauve}"
fi

# Rate limit color: green < 50, yellow < 75, peach < 90, red >= 90
rate_int=${rate_pct%.*}
rate_int=${rate_int:-0}
if [ "$rate_int" -ge 90 ]; then
    rate_color="${red}${bold}"
elif [ "$rate_int" -ge 75 ]; then
    rate_color="${peach}"
elif [ "$rate_int" -ge 50 ]; then
    rate_color="${yellow}"
else
    rate_color="${green}"
fi

# Context usage color: sapphire < 60, yellow 60-79, red ≥ 80
ctx_int=${ctx_used%.*}
ctx_int=${ctx_int:-0}
if [ -n "$ctx_used" ] && [ "$ctx_int" -ge 80 ]; then
    ctx_color="${red}${bold}"
elif [ -n "$ctx_used" ] && [ "$ctx_int" -ge 60 ]; then
    ctx_color="${yellow}"
else
    ctx_color="${sapphire}"
fi

# Effort: pass through whatever the harness reports — future-proof (new levels
# render without a code change; empty when the model has no effort support)
effort_label="$effort_raw"

# Output style: omit when it is the default
style_label=""
if [ -n "$output_style" ] && [ "$output_style" != "default" ] && [ "$output_style" != "Default" ]; then
  style_label="$output_style"
fi

# ── Line 1: folder  branch ─────────────────────────────────────────
line1="${lavender}${bold}${folder}${reset}"
if [ -n "$branch" ]; then
  branch_prefix=$' '                                # plain repo (Nerd Font branch U+E0A0)
  [ -n "$git_worktree" ] && branch_prefix=$' wt:'   # linked worktree
  line1="${line1} ${subtext1}${branch_prefix}${branch}${reset}"
fi

# ── Line 2: model 🧠/💤 effort [style] [agent] [ctx X%] ────────────
line2="${model_color}${model}${reset}"
if [ "$thinking_enabled" = "true" ]; then
  line2="${line2} 🧠"
else
  line2="${line2} 💤"
fi
[ -n "$effort_label" ] && line2="${line2} ${blue}${effort_label}${reset}"
[ -n "$style_label" ]  && line2="${line2} ${overlay0}[${flamingo}${style_label}${overlay0}]${reset}"
[ -n "$agent_name" ]   && line2="${line2} ${overlay0}[${peach}${agent_name}${overlay0}]${reset}"
if [ -n "$ctx_used" ]; then
  ctx_seg="${overlay0}[${overlay0}ctx ${ctx_color}${ctx_int}%${overlay0}"
  # Current-context tokens vs window size (native fields; "lifetime" is not exposed)
  if [ -n "$ctx_tokens" ] && [ -n "$ctx_size" ]; then
    tok_lbl="$((ctx_tokens / 1000))k"
    if [ "$ctx_size" -ge 1000000 ]; then size_lbl="1M"; else size_lbl="$((ctx_size / 1000))k"; fi
    ctx_seg="${ctx_seg} ${subtext1}${tok_lbl}/${size_lbl}${overlay0}"
  fi
  line2="${line2} ${ctx_seg}]${reset}"
fi

# ── Line 3: [5h X% → HH:MM] [7d Y% → Day] ───────────────────────────
weekly_int=${weekly_pct%.*}
weekly_int=${weekly_int:-0}
if [ "$weekly_int" -ge 90 ]; then
    weekly_color="${red}${bold}"
elif [ "$weekly_int" -ge 75 ]; then
    weekly_color="${peach}"
elif [ "$weekly_int" -ge 50 ]; then
    weekly_color="${yellow}"
else
    weekly_color="${green}"
fi

reset_5h_str=""
[ -n "$rate_reset_5h" ] && reset_5h_str=$(date -d "@${rate_reset_5h}" +%H:%M 2>/dev/null)
reset_7d_str=""
[ -n "$weekly_reset_7d" ] && reset_7d_str=$(date -d "@${weekly_reset_7d}" +%a 2>/dev/null)

line3=""
if [ -n "$rate_pct" ]; then
  seg="${overlay0}[${overlay0}5h ${rate_color}${rate_int}%${overlay0}"
  [ -n "$reset_5h_str" ] && seg="${seg} → ${subtext1}${reset_5h_str}${overlay0}"
  seg="${seg}]${reset}"
  line3="${seg}"
fi
if [ -n "$weekly_pct" ]; then
  seg="${overlay0}[${overlay0}7d ${weekly_color}${weekly_int}%${overlay0}"
  [ -n "$reset_7d_str" ] && seg="${seg} → ${subtext1}${reset_7d_str}${overlay0}"
  seg="${seg}]${reset}"
  [ -n "$line3" ] && line3="${line3} ${seg}" || line3="${seg}"
fi

# ── Output ─────────────────────────────────────────────────────────────
printf "%b\n" "$line1"
printf "%b\n" "$line2"
[ -n "$line3" ] && printf "%b\n" "$line3"
exit 0
