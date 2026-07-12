#!/usr/bin/env bash
# Deterministic worktree mechanics — sourced by SKILL.md and by tests.

# Sanitize an absolute path to Claude Code's project-key form: '/', '.' and '_' → '-'.
# Must match CC's own key sanitization exactly (it converts '_' too) — otherwise the
# per-key memory symlink lands in a different dir than the session reads from.
wt_key() { printf '%s' "$1" | sed 's#[/._]#-#g'; }

# The canonical brain dir = main clone's project-key dir. Main clone = first
# `worktree` entry of `git worktree list` (the original, non-linked checkout).
canonical_dir() {
  local anchor="$1" main
  main=$(git -C "$anchor" worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2; exit}')
  [ -z "$main" ] && return 1
  printf '%s/.claude/projects/%s' "$HOME" "$(wt_key "$main")"
}

# Map marker files to a stack label. Order-aware: ros2 (package.xml) before bare cpp.
detect_stack() {
  local d="$1"
  if [ -f "$d/package.xml" ]; then echo ros2
  # requirements*.txt probed via find, not a glob: zsh's default nomatch errors on an
  # unmatched glob ("no matches found") — find is silent and portable in both shells.
  elif [ -f "$d/pyproject.toml" ] || [ -f "$d/uv.lock" ] \
    || [ -n "$(find "$d" -mindepth 1 -maxdepth 1 -name 'requirements*.txt' 2>/dev/null)" ]; then echo python
  elif [ -f "$d/package.json" ]; then echo node
  elif [ -f "$d/CMakeLists.txt" ] || [ -f "$d/Makefile" ]; then echo cpp
  else echo unknown; fi
}

# Stack → "WEIGHT<TAB>COMMAND". [dir] lets node pick its package manager by lockfile.
wt_env_cmd() {
  local dir="${2:-.}"
  case "$1" in
    python) printf 'auto\tuv venv && uv pip install -e ".[dev]"' ;;
    node)
      if   [ -f "$dir/pnpm-lock.yaml" ]; then printf 'auto\tpnpm install'
      elif [ -f "$dir/yarn.lock" ];      then printf 'auto\tyarn install'
      else printf 'auto\tnpm ci 2>/dev/null || npm install'; fi ;;
    ros2)   printf 'propose\tcolcon build' ;;
    cpp)    printf 'none\t# C++: build dir is regenerated on demand' ;;
    *)      printf 'none\t# unknown stack: set up env manually' ;;
  esac
}

# wt_wire <worktree> <main-clone> [canonical-dir] [artifacts-dir]: wire the worktree to main
# (brain stub + shared memory link + a REAL .claude dir copied from main + artifacts). Idempotent.
wt_wire() {
  # Resolve to absolute paths immediately — prevents wrong-canonical bugs when called from loops
  # where the caller's cwd changes between iterations.
  local wt; wt="$(cd "$1" 2>/dev/null && pwd)" \
    || { printf 'wt_wire: ERROR: worktree "%s" not accessible\n' "$1" >&2; return 1; }
  local main; main="$(cd "$2" 2>/dev/null && pwd)" \
    || { printf 'wt_wire: ERROR: main "%s" not accessible\n' "$2" >&2; return 1; }
  local canon="${3:-$(canonical_dir "$main")}"
  printf 'wt_wire: wt   = %s\n' "$wt"
  printf 'wt_wire: main = %s\n' "$main"
  printf 'wt_wire: canon= %s\n' "$canon"
  # 1. Project pair (scaffold if absent) + empty work-unit stub in the worktree.
  #    No @import bridge: with in-repo nesting, native CLAUDE.md walk-up from
  #    <repo>/.worktrees/<branch> reaches <repo>/CLAUDE.md automatically. The
  #    worktree's own CLAUDE.local.md is the Work-unit layer (branch-local notes).
  #    Both <repo>/CLAUDE.md and <repo>/CLAUDE.local.md are gitignored by the global gate.
  [ -f "$main/CLAUDE.md" ]       || : > "$main/CLAUDE.md"
  [ -f "$main/CLAUDE.local.md" ] || : > "$main/CLAUDE.local.md"
  if [ -n "${WT_TICKET:-}" ] || [ -n "${WT_PURPOSE:-}" ] || [ -n "${WT_HANDOFF:-}" ]; then
    printf '# Work unit: %s\nTicket: %s\nPurpose: %s\nHandoff: %s\nCreated: %s\n' \
      "$(basename "$wt")" "${WT_TICKET:-}" "${WT_PURPOSE:-}" "${WT_HANDOFF:-}" "$(date +%F)" \
      > "$wt/CLAUDE.local.md"
  else
    : > "$wt/CLAUDE.local.md"
  fi
  printf 'wt_wire: [1/4] project pair ensured at %s; empty work-unit stub written\n' "$main"
  # 2. per-worktree claude memory bucket (own dir, NOT a symlink to canon).
  # Worktree accumulates its own memories; harvested up to parent at wt_reap_promote.
  # canon is kept as the parent-dest for collision checks at reap time.
  local wtkey; wtkey="$HOME/.claude/projects/$(wt_key "$wt")"
  mkdir -p "$wtkey/memory"        # worktree's OWN claude memory bucket (pure-add; harvested up at reap).
  printf 'wt_wire: [2/4] memory → %s/memory (own bucket)\n' "$wtkey"
  # 3. project .claude as a REAL dir copied from main — NEVER a symlink. A symlinked .claude
  #    breaks the bwrap sandbox: bwrap binds a file at the .claude path, follows the link into
  #    the dir target, and dies with EISDIR → all Bash in the worktree is blocked. (Shared
  #    brain/memory ride CLAUDE.local.md + the memory symlink above, not .claude.)
  if [ -L "$wt/.claude" ]; then rm "$wt/.claude"; fi          # retire any legacy symlink
  mkdir -p "$wt/.claude"
  [ -d "$main/.claude" ] && cp -a "$main/.claude/." "$wt/.claude/" 2>/dev/null
  # Ensure BUILD-tier sandbox settings in the worktree copy (sandbox.enabled + autoAllowBashIfSandboxed).
  # The main clone's settings.local.json may have sandbox:false (investigation tier); worktrees default
  # to sandbox:true (build tier). jq merges; if settings.local.json is absent, creates it from scratch.
  local sl="$wt/.claude/settings.local.json"
  if command -v jq >/dev/null 2>&1; then
    local tmp; tmp="$(mktemp)"
    jq '. + {"sandbox": ((.sandbox // {}) + {"enabled": true, "autoAllowBashIfSandboxed": true})}' \
      "${sl:-/dev/null}" > "$tmp" 2>/dev/null
    if [ -s "$tmp" ]; then mv "$tmp" "$sl"
    else rm -f "$tmp"; printf '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true}}\n' > "$sl"
    fi
  fi
  printf 'wt_wire: [3/4] .claude dir copied\n'
  # 4. artifacts (absolute-target symlinks). Derive from $main with ONE dirname.
  local art; art="${4:-$(dirname "$main")/artifacts/$(basename "$main")}"
  if [ -d "$art" ] && [ -n "$(ls -A "$art" 2>/dev/null)" ]; then
    # Absolutize (defensive — callers may pass a relative 4th arg).
    art="$(cd "$art" && pwd)"
    # F2: use 'artifacts/' as dest dir unless the repo already tracks that path (collision probe).
    local dest_dir
    if git -C "$wt" ls-files --error-unmatch artifacts >/dev/null 2>&1; then
      printf 'wt_wire: WARN repo tracks artifacts/ — linking into .gitignored/ instead\n'
      dest_dir=".gitignored"
    else
      dest_dir="artifacts"
      # Append /artifacts/ to git common-dir info/exclude (idempotent)
      local gitcommon; gitcommon="$(git -C "$wt" rev-parse --git-common-dir 2>/dev/null)"
      if [ -n "$gitcommon" ]; then
        local exclude="$gitcommon/info/exclude"
        # fix5: exact whole-line match (read line-by-line); append only if no line equals exactly '/artifacts/'
        local _found_art=0 _excline
        if [ -f "$exclude" ]; then
          while IFS= read -r _excline; do
            [ "$_excline" = '/artifacts/' ] && { _found_art=1; break; }
          done < "$exclude"
        fi
        [ "$_found_art" = 0 ] && printf '/artifacts/\n' >> "$exclude"
      fi
    fi
    mkdir -p "$wt/$dest_dir"
    # ABSOLUTE symlink targets, on purpose: BSD/macOS ln has no -r (GNU-only), and absolute
    # links also survive `git worktree move` on archive/revive — the artifacts store lives
    # OUTSIDE the worktree, so a relative link's ../ depth breaks when the worktree moves.
    # find (not "$art"/*/ glob): a no-subdir store must be a clean no-op — bash would pass the
    # literal unmatched glob through, and zsh's default nomatch would abort the function.
    local a
    while IFS= read -r a; do
      [ -n "$a" ] && ln -sfn "$a" "$wt/$dest_dir/$(basename "$a")"
    done < <(find "$art" -mindepth 1 -maxdepth 1 -type d ! -name '.*' 2>/dev/null)
    printf 'wt_wire: [4/4] artifacts linked from %s into %s/\n' "$art" "$dest_dir"
  else
    printf 'wt_wire: [4/4] artifacts: none (dir absent or empty)\n'
  fi
  # 5. serena pre-staging: register wt as a serena project (copies main's config on first create).
  wt_serena_prestage "$wt" "$main"
  # Post-wire self-check — surface wiring failures immediately rather than silently.
  printf 'wt_wire: --- verify ---\n'
  wt_check "$wt" "$canon"
}

# wt_check <worktree> <canonical-dir> → prints "<name>: OK|FAIL|NA <detail>"; returns 1 if any FAIL.
wt_check() {
  local wt="$1" canon="$2" rc=0
  # The MAIN clone is the first `worktree list` entry; the Project pair lives there.
  local mainclone; mainclone=$(git -C "$wt" worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2; exit}')
  local stub="$wt/CLAUDE.local.md"
  if [ -n "$mainclone" ] && [ -f "$mainclone/CLAUDE.md" ] && [ -f "$mainclone/CLAUDE.local.md" ]; then
    echo "brain: OK (project pair at $mainclone)"
  else echo "brain: FAIL (project pair <repo>/CLAUDE.md+CLAUDE.local.md missing)"; rc=1; fi
  if [ -f "$stub" ] && grep -q '^@' "$stub"; then echo "bridge: FAIL (@import present — must be dropped for native walk-up)"; rc=1; else echo "bridge: OK (no @import)"; fi
  case "$wt" in */.worktrees/*) echo "nest: OK" ;; *) echo "nest: FAIL (worktree not under <repo>/.worktrees/)"; rc=1 ;; esac
  local memk="$HOME/.claude/projects/$(wt_key "$wt")/memory"
  if [ -d "$memk" ] && [ ! -L "$memk" ]; then echo "memory: OK (own bucket)"; else echo "memory: FAIL (key memory/ must be a real dir, not a symlink)"; rc=1; fi
  if [ -L "$wt/.claude" ]; then echo "settings: FAIL (.claude is a symlink — breaks bwrap sandbox; must be a real dir)"; rc=1
  elif [ -d "$wt/.claude" ]; then echo "settings: OK"
  else echo "settings: FAIL (.claude missing — should be a real dir copied from main)"; rc=1; fi
  # artifacts: prefer $wt/artifacts (new default), fallback $wt/.gitignored, else NA
  local _art_dir=""
  [ -d "$wt/artifacts" ] && _art_dir="$wt/artifacts"
  [ -z "$_art_dir" ] && [ -d "$wt/.gitignored" ] && _art_dir="$wt/.gitignored"
  if [ -n "$_art_dir" ]; then
    # fix7 + portability: probe with find alone — no empty-glob false positive, and no
    # `read -d ''` (bash-only NUL-delimiter idiom; zsh's read does not treat '' as NUL).
    # Broken entry == a symlink whose target fails `test -e`; plain files/dirs always pass.
    local broken
    broken=$(find "$_art_dir" -maxdepth 1 -mindepth 1 -type l ! -exec test -e {} \; -print 2>/dev/null)
    [ -z "$broken" ] && echo "artifacts: OK" || { echo "artifacts: FAIL (broken symlink in $_art_dir)"; rc=1; }
  else echo "artifacts: NA"; fi
  local br; br=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ -n "$br" ] && [ "$br" != HEAD ] && [ "$br" != main ] && [ "$br" != master ]; then echo "branch: OK ($br)"; else echo "branch: FAIL (on '${br:-none}')"; rc=1; fi
  git -C "$wt" rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1 && echo "remote: OK" || echo "remote: NA (no upstream)"
  case "$(detect_stack "$wt")" in
    python) [ -d "$wt/.venv" ] && echo "env: OK (.venv)" || echo "env: NA (.venv absent)" ;;
    node)   [ -d "$wt/node_modules" ] && echo "env: OK (node_modules)" || echo "env: NA (node_modules absent)" ;;
    *)      echo "env: NA" ;;
  esac
  # serena: check if wt abs path is in ~/.serena/serena_config.yml projects: list
  local _ser_cfg="$HOME/.serena/serena_config.yml"
  if [ -f "$_ser_cfg" ] && python3 - "$_ser_cfg" "$wt" <<'PYEOF' 2>/dev/null
import sys
cfg, wt_path = sys.argv[1], sys.argv[2]
with open(cfg) as f:
    content = f.read()
entry = '- ' + wt_path
for line in content.splitlines():
    if line.strip() == entry:
        sys.exit(0)
sys.exit(1)
PYEOF
  then
    echo "serena: OK"
  else
    echo "serena: NA"
  fi
  return $rc
}

# wt_serena_prestage <wt> <main>: pre-stage a serena project for the worktree branch.
# Keys storage by wt basename (= branch). Copies main's project.yml on first creation;
# worktree serena memories/ starts EMPTY (pure-new — no copy from parent, no drift).
# Skips project.yml copy if project dir already exists (revive case — memories preserved).
# Always registers the wt abs path in serena_config.yml (idempotent, via python).
wt_serena_prestage() {
  local wt="$1" main="$2"
  local name; name=$(basename "$wt")
  local proj="$HOME/.serena/projects/$name"
  local mainproj="$HOME/.serena/projects/$(basename "$main")"
  if [ ! -d "$proj" ]; then
    mkdir -p "$proj"
    if [ -f "$mainproj/project.yml" ]; then
      cp "$mainproj/project.yml" "$proj/project.yml"
      # Portable in-place edit: BSD/macOS sed -i requires an explicit suffix arg ('' vs GNU's
      # bare -i), so `sed -i "s/…/"` is a GNU-ism — write to a temp file and move it back.
      local _tmp; _tmp=$(mktemp)
      if sed "s/^project_name:.*$/project_name: \"$name\"/" "$proj/project.yml" > "$_tmp"; then
        mv "$_tmp" "$proj/project.yml"
      else
        rm -f "$_tmp"
      fi
    fi
    # D1: memories/ starts EMPTY — no copy from parent. Parent knowledge comes from
    # ~/.serena/memories/global/ + live LSP. No copy → no drift → reap harvest is pure-add.
  fi
  # Register the worktree abs path in serena_config.yml (idempotent, python)
  local cfg="$HOME/.serena/serena_config.yml"
  local _py_rc=0
  if [ -f "$cfg" ]; then
    python3 - "$cfg" "$wt" <<'PYEOF'
import sys, os
cfg_path, wt_path = sys.argv[1], sys.argv[2]
with open(cfg_path, 'r') as f:
    content = f.read()
lines = content.splitlines(keepends=True)
entry = '- ' + wt_path
# Check if already present
for line in lines:
    if line.strip() == entry:
        sys.exit(0)
# Find projects: key and insert after the last existing list item under it
in_projects = False
insert_at = None
for i, line in enumerate(lines):
    if line.rstrip() == 'projects:':
        in_projects = True
        insert_at = i + 1
        continue
    if in_projects:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped == '':
            if stripped.startswith('- '):
                insert_at = i + 1
        else:
            break
if insert_at is not None:
    lines.insert(insert_at, entry + '\n')
with open(cfg_path, 'w') as f:
    f.writelines(lines)
PYEOF
    _py_rc=$?
  fi
  if [ "$_py_rc" = "0" ]; then
    printf 'wt_wire: [serena] registered %s\n' "$name"
  else
    printf 'wt_serena_prestage: WARN python registry update failed for %s\n' "$name" >&2
  fi
}

# wt_setup_env <worktree>: run the stack's env command unconditionally for 'auto'-weight stacks.
# 'propose' prints the command for the caller to confirm; 'none' prints a note.
# This helper removes agent discretion — 'auto' ALWAYS runs (never defer, even in fork mode).
wt_setup_env() {
  local wt; wt="$(cd "$1" 2>/dev/null && pwd)" \
    || { printf 'wt_setup_env: ERROR: worktree "%s" not accessible\n' "$1" >&2; return 1; }
  local s; s="$(detect_stack "$wt")"
  local w cmd; IFS=$'\t' read -r w cmd <<<"$(wt_env_cmd "$s" "$wt")"
  printf 'wt_setup_env: stack=%s weight=%s\n' "$s" "$w"
  case "$w" in
    auto)    printf 'wt_setup_env: running: %s\n' "$cmd"; ( cd "$wt" && eval "$cmd" ) ;;
    propose) printf 'wt_setup_env: PROPOSE (confirm to run): %s\n' "$cmd" ;;
    *)       printf 'wt_setup_env: %s\n' "$cmd" ;;
  esac
}

# wt_add [--ticket X] [--purpose Y] [--handoff Z] <main-clone> <branch> <base> [new-branch=1]:
# the single correct entrypoint for worktree creation. Flags are set as WT_TICKET/PURPOSE/HANDOFF
# so wt_wire's F3 context template picks them up. Positional behavior preserved.
# Runs git worktree add → wt_wire (brain/memory/.claude/artifacts/serena) → wt_setup_env.
wt_add() {
  local _ticket="" _purpose="" _handoff=""
  # Positionals go into plain scalars, NOT an array: zsh indexes arrays from 1 while bash
  # indexes from 0, so ${_pos[0]} silently comes back empty when sourced into zsh.
  local _main_arg="" _branch="" _base="" _newb="" _n=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --ticket)  _ticket="$2";  shift 2 ;;
      --purpose) _purpose="$2"; shift 2 ;;
      --handoff) _handoff="$2"; shift 2 ;;
      *)
        _n=$((_n + 1))
        case "$_n" in
          1) _main_arg="$1" ;;
          2) _branch="$1" ;;
          3) _base="$1" ;;
          4) _newb="$1" ;;
        esac
        shift ;;
    esac
  done
  # Set as plain (NON-exported) vars: same-shell function calls (wt_wire) still see them, but they
  # do NOT leak into the session env where a later wt_archive would read a stale ${WT_TICKET}.
  # Unset at the end of this function regardless of outcome.
  WT_TICKET="$_ticket" WT_PURPOSE="$_purpose" WT_HANDOFF="$_handoff"
  local main; main="$(cd "$_main_arg" 2>/dev/null && pwd)" \
    || { unset WT_TICKET WT_PURPOSE WT_HANDOFF; printf 'wt_add: ERROR: main "%s" not accessible\n' "$_main_arg" >&2; return 1; }
  local branch="$_branch" base="$_base" newb="${_newb:-1}"
  local wt="$main/.worktrees/$branch"
  # Slashed branches (e.g. hotfix/x) nest: $wt's parent dir must exist before `git worktree add`,
  # else git fails. Mirrors the mkdir -p guard in wt_archive/wt_revive.
  mkdir -p "$(dirname "$wt")"
  local rc=0
  if [ "$newb" = 1 ]; then
    git -C "$main" worktree add -b "$branch" "$wt" "$base" || rc=1
  else
    git -C "$main" worktree add "$wt" "$base" || rc=1
  fi
  if [ "$rc" = 0 ]; then
    wt_wire "$wt" "$main"    # brain stub + memory symlink + .claude real dir + artifacts + serena
    wt_setup_env "$wt"       # auto env runs deterministically here
  fi
  unset WT_TICKET WT_PURPOSE WT_HANDOFF
  return "$rc"
}

# wt_serena_deregister <wt> [--purge]: remove wt abs path from ~/.serena/serena_config.yml projects: list
# (idempotent — no error if absent). With --purge, also deletes ~/.serena/projects/<basename wt>.
wt_serena_deregister() {
  local wt="$1" purge=0
  [ "${2:-}" = "--purge" ] && purge=1
  local cfg="$HOME/.serena/serena_config.yml"
  if [ -f "$cfg" ]; then
    python3 - "$cfg" "$wt" <<'PYEOF'
import sys
cfg_path, wt_path = sys.argv[1], sys.argv[2]
with open(cfg_path, 'r') as f:
    lines = f.readlines()
entry = '- ' + wt_path
new_lines = [l for l in lines if l.strip() != entry]
with open(cfg_path, 'w') as f:
    f.writelines(new_lines)
PYEOF
    printf 'wt_serena_deregister: removed %s from serena_config.yml (if present)\n' "$wt"
  else
    printf 'wt_serena_deregister: serena_config.yml not found — skipping\n'
  fi
  if [ "$purge" = 1 ]; then
    local proj_dir="$HOME/.serena/projects/$(basename "$wt")"
    rm -rf "$proj_dir"
    printf 'wt_serena_deregister: purged serena project dir %s\n' "$proj_dir"
  fi
}

# wt_archive <main> <wt>: move wt to _archive/<branch>, lock it, deregister from serena.
# Records branch/orig_path/date/ticket in _archive/index.tsv.
wt_archive() {
  local main; main="$(cd "$1" 2>/dev/null && pwd)" \
    || { printf 'wt_archive: ERROR: main "%s" not accessible\n' "$1" >&2; return 1; }
  local wt; wt="$(cd "$2" 2>/dev/null && pwd)" \
    || { printf 'wt_archive: ERROR: worktree "%s" not accessible\n' "$2" >&2; return 1; }
  # fix3: refuse archiving the main clone itself
  [ "$wt" = "$main" ] && { printf 'wt_archive: ERROR: refusing to archive the main clone (%s)\n' "$main" >&2; return 1; }
  local br; br=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)
  [ -z "$br" ] && { printf 'wt_archive: ERROR: cannot resolve branch in %s\n' "$wt" >&2; return 1; }
  local tgt="$main/.worktrees/_archive/$br"
  if [ -e "$tgt" ]; then
    printf 'wt_archive: ERROR target exists: %s\n' "$tgt" >&2
    return 1
  fi
  mkdir -p "$(dirname "$tgt")"
  git -C "$main" worktree move "$wt" "$tgt" || return 1
  git -C "$main" worktree lock "$tgt" --reason "archived $(date +%F)"
  wt_serena_deregister "$wt"  # keep project folder — revivable
  # append TSV row to index.tsv (create with header if absent)
  local idx="$main/.worktrees/_archive/index.tsv"
  if [ ! -f "$idx" ]; then
    printf 'branch\torig_path\tdate\tticket\n' > "$idx"
  fi
  printf '%s\t%s\t%s\t%s\n' "$br" "$wt" "$(date +%F)" "${WT_TICKET:-}" >> "$idx"
  printf 'wt_archive: archived %s → %s (locked)\n' "$wt" "$tgt"
}

# wt_revive <main> <branch>: move archived worktree back to .worktrees/<branch>, re-register serena.
wt_revive() {
  local main; main="$(cd "$1" 2>/dev/null && pwd)" \
    || { printf 'wt_revive: ERROR: main "%s" not accessible\n' "$1" >&2; return 1; }
  local branch="$2"
  local arch="$main/.worktrees/_archive/$branch"
  # Verify the archive path exists (may need to query porcelain for non-standard cases)
  if [ ! -d "$arch" ]; then
    printf 'wt_revive: ERROR: archive path not found: %s\n' "$arch" >&2
    return 1
  fi
  # Unlock the archive location before moving
  git -C "$main" worktree unlock "$arch" 2>/dev/null || true
  local dst="$main/.worktrees/$branch"
  if [ -e "$dst" ]; then
    printf 'wt_revive: ERROR dst exists: %s\n' "$dst" >&2
    return 1
  fi
  mkdir -p "$(dirname "$dst")"
  git -C "$main" worktree move "$arch" "$dst" || return 1
  # Re-register with serena (project dir already exists → memories PRESERVED)
  wt_serena_prestage "$dst" "$main"
  # Remove the branch row from index.tsv
  local idx="$main/.worktrees/_archive/index.tsv"
  if [ -f "$idx" ]; then
    python3 - "$idx" "$branch" <<'PYEOF'
import sys
idx_path, branch = sys.argv[1], sys.argv[2]
with open(idx_path, 'r') as f:
    lines = f.readlines()
# fix7: keep header (first field == 'branch') and rows where first field != branch
new_lines = [l for l in lines if l.split('\t')[0] != branch]
with open(idx_path, 'w') as f:
    f.writelines(new_lines)
PYEOF
  fi
  printf 'wt_revive: revived %s → %s\n' "$arch" "$dst"
}

# wt_reap_promote <wt> <main>: write a .reap-manifest.md with a YAML candidates: document
# harvesting from BOTH stores (serena + claude). No file moves; manifest is written to
# $wt/.reap-manifest.md for memory-curator review.
wt_reap_promote() {
  local wt="$1" main="$2"
  local br; br=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)
  local repo; repo=$(basename "$main")
  local ticket="${WT_TICKET:-}"
  # Try to pull ticket from CLAUDE.local.md if not in env
  if [ -z "$ticket" ] && [ -f "$wt/CLAUDE.local.md" ]; then
    ticket=$(grep -i '^Ticket:' "$wt/CLAUDE.local.md" 2>/dev/null | head -1 | sed 's/^[Tt]icket: *//')
  fi
  local manifest="$wt/.reap-manifest.md"
  # Candidate stores
  local wt_name; wt_name=$(basename "$wt")
  local main_name; main_name=$(basename "$main")
  local serena_src="$HOME/.serena/projects/$wt_name/memories"
  local claude_src="$HOME/.claude/projects/$(wt_key "$wt")/memory"
  # Parent-dest for collision checks
  local serena_parent_dest="$HOME/.serena/projects/$main_name/memories"
  local canon="$HOME/.claude/projects/$(wt_key "$main")"
  local claude_parent_dest="$canon/memory"
  # D2: build the candidates YAML via python (safe YAML, block scalar for body)
  {
    printf '%s\n' '---'
    printf 'worktree: %s\n' "$wt"
    printf 'branch: %s\n' "$br"
    printf 'repo: %s\n' "$repo"
    printf 'ticket: %s\n' "${ticket:-unknown}"
    printf 'date: %s\n' "$(date +%F)"
    printf '%s\n' '---'
    printf '\n'
    python3 - "$serena_src" "$claude_src" "$serena_parent_dest" "$claude_parent_dest" <<'PYEOF'
import sys, os

def read_type(path):
    """Read type from frontmatter type: or metadata.type: if present."""
    try:
        with open(path) as f:
            lines = f.readlines()
    except OSError:
        return "reference"
    in_fm = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == '---':
            in_fm = True
            continue
        if in_fm:
            if stripped == '---':
                break
            if stripped.startswith('type:'):
                return stripped.split(':', 1)[1].strip().strip('"\'')
            if stripped.startswith('metadata:'):
                # look ahead for type: nested under metadata:
                pass
            # simple nested: '  type: foo' inside metadata block
            if stripped.startswith('type:'):
                return stripped.split(':', 1)[1].strip().strip('"\'')
    return "reference"

def block_scalar(content, indent=6):
    """Indent content for a YAML block scalar (already anchored with |)."""
    pad = ' ' * indent
    return '\n'.join(pad + l for l in content.splitlines())

def collect(dirpath, store, parent_dest):
    candidates = []
    if not os.path.isdir(dirpath):
        return candidates
    for fname in sorted(os.listdir(dirpath)):
        src = os.path.join(dirpath, fname)
        if not os.path.isfile(src):
            continue
        cid = fname[:-3] if fname.endswith('.md') else fname
        try:
            with open(src) as f:
                body = f.read()
        except OSError:
            body = ''
        typ = read_type(src)
        parent_file = os.path.join(parent_dest, fname)
        collision = parent_file if os.path.exists(parent_file) else "none"
        candidates.append({
            'id': cid,
            'store': store,
            'source': src,
            'type': typ,
            'body': body,
            'collision': collision,
        })
    return candidates

serena_src, claude_src, serena_dest, claude_dest = sys.argv[1:]
candidates = collect(serena_src, 'serena', serena_dest) + collect(claude_src, 'claude', claude_dest)

print('candidates:')
if not candidates:
    print('  []')
else:
    for c in candidates:
        print(f"  - id: {c['id']}")
        print(f"    store: {c['store']}")
        print(f"    source: {c['source']}")
        print(f"    type: {c['type']}")
        body_block = block_scalar(c['body'])
        print(f"    body: |")
        if body_block:
            print(body_block)
        col = c['collision']
        print(f"    collision: {col}")
        print(f"    proposed: {{}}")
PYEOF
  } > "$manifest"
  printf 'reap: promotion pending (memory-curator not yet built) — manifest at %s\n' "$manifest"
}

# wt_reap <main> <wt> [--force]: gate-check, promote, then remove a worktree.
# Merge gate: branch must be merged into main (or --force). Dirty gate: no uncommitted changes (or --force).
# Confirm prompt: skipped with --force or WT_ASSUME_YES=1.
wt_reap() {
  local main; main="$(cd "$1" 2>/dev/null && pwd)" \
    || { printf 'wt_reap: ERROR: main "%s" not accessible\n' "$1" >&2; return 1; }
  local wt; wt="$(cd "$2" 2>/dev/null && pwd)" \
    || { printf 'wt_reap: ERROR: worktree "%s" not accessible\n' "$2" >&2; return 1; }
  # fix3: refuse reaping the main clone itself
  [ "$wt" = "$main" ] && { printf 'wt_reap: ERROR: refusing to reap the main clone (%s)\n' "$main" >&2; return 1; }
  local force=0
  # Scan remaining args for --force
  local _a; for _a in "${@:3}"; do [ "$_a" = "--force" ] && force=1; done

  local br; br=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)
  [ -z "$br" ] && { printf 'wt_reap: ERROR: cannot resolve branch in %s\n' "$wt" >&2; return 1; }

  # Trunk = the main clone's checked-out branch (worktree-first: main clone stays on the
  # default branch). NEVER hardcode 'main' — repos may use 'master' (and a HOME-faked test
  # env defaults git to 'master'), so a literal 'main' ref → "malformed object name main".
  local trunk; trunk=$(git -C "$main" rev-parse --abbrev-ref HEAD 2>/dev/null); trunk=${trunk:-main}

  # Hard merge gate. Whole-line membership test done in pure bash (NOT `grep -qx`): the
  # interactive shell aliases `grep` to ugrep with file-oriented flags (--ignore-files/--hidden/-I)
  # that can misbehave on piped stdin, and `-x` semantics differ — so we read the ref list into an
  # array and compare exact strings.
  local merged=0 _ref
  while IFS= read -r _ref; do
    [ "$_ref" = "$br" ] && { merged=1; break; }
  done < <(git -C "$main" branch --merged "$trunk" --format='%(refname:short)' 2>/dev/null)
  if [ "$merged" = 0 ]; then
    if [ "$force" = 0 ]; then
      printf 'reap: %s not merged into %s\n' "$br" "$trunk"
      git -C "$main" --no-pager diff --stat "$trunk...$br" 2>/dev/null || true
      printf 'reap: re-run with --force to override\n'
      return 1
    else
      printf 'reap: WARN %s not merged into %s — --force override\n' "$br" "$trunk"
    fi
  fi

  # Dirty gate
  if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
    if [ "$force" = 0 ]; then
      printf 'reap: %s has uncommitted changes — commit/stash or use --force\n' "$wt"
      return 1
    else
      printf 'reap: WARN uncommitted changes in %s — --force override\n' "$wt"
    fi
  fi

  # Confirm prompt (skip with --force or WT_ASSUME_YES=1)
  if [ "$force" = 0 ] && [ "${WT_ASSUME_YES:-}" != "1" ]; then
    printf 'reap: ticket merged + work finalized? proceed to promote+delete? [y/N] '
    local ans; read -r ans
    case "$ans" in y|Y) ;; *) printf 'reap: aborted\n'; return 1 ;; esac
  fi

  wt_reap_promote "$wt" "$main"
  # Preserve manifest outside the worktree before removal (it lives inside $wt, which we delete).
  local manifest_dst="$main/.worktrees/_reaped/$br.reap-manifest.md"
  mkdir -p "$(dirname "$manifest_dst")"
  if [ -f "$wt/.reap-manifest.md" ]; then
    cp "$wt/.reap-manifest.md" "$manifest_dst"
  fi
  local _rm_rc=0
  wt_remove "$main" "$wt"; _rm_rc=$?
  # fix1: purge serena project ONLY if wt_remove succeeded; on failure keep memories so they survive.
  if [ "$_rm_rc" = 0 ]; then
    wt_serena_deregister "$wt" --purge
    printf 'reap: done — branch %s reaped from %s\n' "$br" "$wt"
  else
    wt_serena_deregister "$wt"    # deregister (no --purge) so memories survive the failed removal
    printf 'reap: ERROR wt_remove failed (rc=%s) — serena memories preserved for recovery\n' "$_rm_rc" >&2
  fi
  if [ -f "$manifest_dst" ]; then
    printf 'reap: manifest preserved at %s\n' "$manifest_dst"
  fi
  # Explicit return — never let a trailing test-expression leak as the function's exit status.
  return "$_rm_rc"
}

# wt_remove <main-clone> <worktree>: safely remove a worktree + its per-wt key dir.
# If non-user-owned dirs (Docker root/nobody uid) block deletion, prints the exact sudo recovery
# command and exits with rc=1 rather than leaving a half-removed worktree.
wt_remove() {
  local main; main="$(cd "$1" 2>/dev/null && pwd)" \
    || { printf 'wt_remove: ERROR: main "%s" not accessible\n' "$1" >&2; return 1; }
  local wt="$2"
  if git -C "$main" worktree remove --force "$wt" 2>/dev/null; then
    local key_dir="$HOME/.claude/projects/$(wt_key "$wt")"
    rm -rf "$key_dir"
    printf 'wt_remove: removed %s + key dir %s\n' "$wt" "$key_dir"
    return 0
  fi
  printf 'wt_remove: blocked — non-user-owned dirs inside %s:\n' "$wt" >&2
  # -printf is GNU-only (macOS find has no -printf) — use stat with the per-platform format.
  # -maxdepth placed before the -user test: same results, and silences GNU find's option-order warning.
  if [ "$(uname -s)" = Darwin ]; then
    find "$wt" -maxdepth 3 ! -user "$(id -un)" -exec stat -f '  %Su:%Sg  %N' {} + 2>/dev/null >&2
  else
    find "$wt" -maxdepth 3 ! -user "$(id -un)" -exec stat -c '  %U:%G  %n' {} + 2>/dev/null >&2
  fi
  printf 'wt_remove: run the following, then re-run wt_remove:\n' >&2
  printf '  sudo rm -rf %q\n  git -C %q worktree prune\n' "$wt" "$main" >&2
  return 1
}

# wt_preflight_mounts: probe all /mnt/* mounts for reachability (timeout 3s each).
# A stale hard-mounted NAS makes `stat` hang and later bricks the bwrap sandbox
# (all Bash fails with "remount ... No such device"). Call before sandbox-dependent ops.
# rc=0 all mounts OK; rc=1 at least one stale mount (see stderr for which ones).
# Linux-only concern: bwrap and /proc/mounts don't exist on macOS (its Bash sandbox is
# seatbelt-based, and `timeout` isn't in the BSD userland) — no-op cleanly on Darwin.
# The .claude-must-be-real-dir rule is separate and enforced everywhere (wt_wire/wt_check).
wt_preflight_mounts() {
  if [ "$(uname -s)" = Darwin ]; then
    printf 'wt_preflight: Darwin — no bwrap//proc/mounts to probe (seatbelt sandbox); OK\n'
    return 0
  fi
  local m bad=0
  for m in $(awk '$2 ~ "^/mnt/" {print $2}' /proc/mounts 2>/dev/null); do
    if ! timeout 3 stat "$m" >/dev/null 2>&1; then
      printf 'wt_preflight: STALE mount %s — bwrap sandbox will fail here. Unmount or use dangerouslyDisableSandbox.\n' "$m" >&2
      bad=1
    fi
  done
  [ "$bad" = 0 ] && printf 'wt_preflight: all /mnt mounts reachable\n'
  return "$bad"
}
