#!/usr/bin/env bash
set -u
HERE=$(cd "$(dirname "$0")/.." && pwd)
# Portability: on macOS the temp dir sits under /var → /private/var (a symlink), while git
# prints PHYSICAL paths in `worktree list --porcelain` — fixture greps against porcelain output
# would miss (macOS mktemp ignores $TMPDIR; it asks confstr for the Darwin user temp dir).
# Shadow mktemp so every fixture dir comes back already resolved; files pass through untouched.
mktemp() {
  local d; d=$(command mktemp "$@") || return 1
  (cd "$d" 2>/dev/null && pwd -P) || printf '%s\n' "$d"
}
source "$HERE/helpers.sh"
fail=0
assert_eq() { if [ "$2" != "$3" ]; then echo "FAIL $1: want [$3] got [$2]"; fail=1; else echo "ok $1"; fi; }

# wt_key: replace every '/', '.' and '_' with '-' (must match CC's project-key sanitization)
assert_eq wt_key_simple   "$(wt_key /home/u/Documents/projects/repo)"                 "-home-u-Documents-projects-repo"
assert_eq wt_key_worktree "$(wt_key /home/u/Documents/projects/.worktrees/repo/RE-1)" "-home-u-Documents-projects--worktrees-repo-RE-1"
assert_eq wt_key_slashed  "$(wt_key /home/u/Documents/projects/.worktrees/repo/hotfix/x)" "-home-u-Documents-projects--worktrees-repo-hotfix-x"
assert_eq wt_key_underscore "$(wt_key /home/u/Documents/projects/yubo_monorepo)"      "-home-u-Documents-projects-yubo-monorepo"


# canonical_dir: from ANY worktree, returns ~/.claude/projects/<key-of-main-clone>
# Fixture: fake a `git` that prints a worktree list with the main clone first.
PATH_BAK="$PATH"; TMPB=$(mktemp -d)
cat > "$TMPB/git" <<'G'
#!/usr/bin/env bash
# stub: only supports `git -C X worktree list --porcelain`
echo "worktree /home/u/Documents/projects/repo"
echo "worktree /home/u/Documents/projects/.worktrees/repo/RE-1"
G
chmod +x "$TMPB/git"; PATH="$TMPB:$PATH"
assert_eq canonical_dir "$(HOME=/home/u canonical_dir /any/path)" "/home/u/.claude/projects/-home-u-Documents-projects-repo"
PATH="$PATH_BAK"; rm -rf "$TMPB"

# detect_stack: marker file → stack label (ros2 before bare cmake)
FX=$(mktemp -d)
mkdir -p "$FX/py" && touch "$FX/py/pyproject.toml"
mkdir -p "$FX/node" && touch "$FX/node/package.json"
mkdir -p "$FX/ros" && touch "$FX/ros/package.xml" "$FX/ros/CMakeLists.txt"
mkdir -p "$FX/cpp" && touch "$FX/cpp/CMakeLists.txt"
mkdir -p "$FX/none"
assert_eq stack_py   "$(detect_stack "$FX/py")"   python
assert_eq stack_node "$(detect_stack "$FX/node")" node
assert_eq stack_ros  "$(detect_stack "$FX/ros")"  ros2
assert_eq stack_cpp  "$(detect_stack "$FX/cpp")"  cpp
assert_eq stack_none "$(detect_stack "$FX/none")" unknown
rm -rf "$FX"

# wt_env_cmd: returns "WEIGHT<TAB>COMMAND"; node manager picked by lockfile
ENVP=$(mktemp -d); touch "$ENVP/pnpm-lock.yaml"; ENVY=$(mktemp -d); touch "$ENVY/yarn.lock"
ENVN=$(mktemp -d)  # clean dir — no lockfile — for the bare npm-ci fallback case
assert_eq env_py    "$(wt_env_cmd python)"         "$(printf 'auto\tuv venv && uv pip install -e \".[dev]\"')"
assert_eq env_node  "$(wt_env_cmd node "$ENVN")"  "$(printf 'auto\tnpm ci 2>/dev/null || npm install')"
assert_eq env_pnpm  "$(wt_env_cmd node "$ENVP")"   "$(printf 'auto\tpnpm install')"
assert_eq env_yarn  "$(wt_env_cmd node "$ENVY")"   "$(printf 'auto\tyarn install')"
assert_eq env_ros   "$(wt_env_cmd ros2)"           "$(printf 'propose\tcolcon build')"
assert_eq env_cpp   "$(wt_env_cmd cpp)"            "$(printf 'none\t# C++: build dir is regenerated on demand')"
assert_eq env_unk   "$(wt_env_cmd unknown)"        "$(printf 'none\t# unknown stack: set up env manually')"
rm -rf "$ENVP" "$ENVY" "$ENVN"

# wt_wire: brain stub + .claude REAL dir (copied from main) + memory OWN BUCKET + artifact links (real temp FS)
W=$(mktemp -d); HOME_BAK="$HOME"
MAIN="$W/projects/repo"; WT="$W/projects/.worktrees/repo/RE-1"
CANON="$W/claude/projects/-x-repo"
mkdir -p "$MAIN/.claude" "$CANON/memory" "$WT" "$W/projects/artifacts/repo/sdkA"
echo '{"x":1}' > "$MAIN/.claude/settings.local.json"
HOME="$W/claude_home"; mkdir -p "$HOME"
wt_wire "$WT" "$MAIN" "$CANON"
[ -f "$WT/CLAUDE.local.md" ] && ! grep -q '^@' "$WT/CLAUDE.local.md" && echo "ok wire_stub_empty" || { echo "FAIL wire_stub_empty (CLAUDE.local.md missing or contains @import)"; fail=1; }
[ -f "$MAIN/CLAUDE.md" ] && echo "ok wire_project_claudemd" || { echo "FAIL wire_project_claudemd"; fail=1; }
[ -f "$MAIN/CLAUDE.local.md" ] && echo "ok wire_project_claudelocal" || { echo "FAIL wire_project_claudelocal"; fail=1; }
{ [ -d "$WT/.claude" ] && [ ! -L "$WT/.claude" ]; } && echo "ok wire_claude" || { echo "FAIL wire_claude"; fail=1; }
[ -L "$WT/artifacts/sdkA" ] && [ -e "$WT/artifacts/sdkA" ] && echo "ok wire_artifact" || { echo "FAIL wire_artifact"; fail=1; }
# G1: memory is a real dir (own bucket), NOT a symlink to canon
_wtkey_wire="$HOME/.claude/projects/$(wt_key "$WT")"
{ [ -d "$_wtkey_wire/memory" ] && [ ! -L "$_wtkey_wire/memory" ]; } && echo "ok wire_memory_own_bucket" || { echo "FAIL wire_memory_own_bucket (memory/ should be real dir, not symlink)"; fail=1; }
# 4th-arg override: artifacts dir passed explicitly at a NON-derived location [Task 8]
mkdir -p "$W/elsewhere/sdkB"
wt_wire "$WT" "$MAIN" "$CANON" "$W/elsewhere"
[ -L "$WT/artifacts/sdkB" ] && [ -e "$WT/artifacts/sdkB" ] && echo "ok wire_artifact_4tharg" || { echo "FAIL wire_artifact_4tharg"; fail=1; }
HOME="$HOME_BAK"; rm -rf "$W"

# wt_check: real git repo fixture — nested .worktrees/ layout
W=$(mktemp -d); HOME_BAK="$HOME"; HOME="$W/ch"; mkdir -p "$HOME"
MAIN="$W/repo"
mkdir -p "$MAIN"; git -C "$MAIN" init -q
printf '/.worktrees/\n' > "$MAIN/.gitignore"
git -C "$MAIN" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN" -c user.email=t@t -c user.name=t commit -qm init
WT_CHK="$MAIN/.worktrees/RE-1"
git -C "$MAIN" worktree add -b RE-1 "$WT_CHK" HEAD -q 2>/dev/null
CANON_CHK=$(HOME="$W/ch" canonical_dir "$MAIN")
mkdir -p "$CANON_CHK/memory"
mkdir -p "$MAIN/.claude"; echo '{}' > "$MAIN/.claude/settings.local.json"
wt_wire "$WT_CHK" "$MAIN" "$CANON_CHK"
out=$(wt_check "$WT_CHK" "$CANON_CHK")
echo "$out" | grep -q 'brain.*OK'    && echo "ok check_brain"  || { echo "FAIL check_brain: $out";  fail=1; }
echo "$out" | grep -q 'bridge.*OK'   && echo "ok check_bridge" || { echo "FAIL check_bridge: $out"; fail=1; }
echo "$out" | grep -q 'nest.*OK'     && echo "ok check_nest"   || { echo "FAIL check_nest: $out";   fail=1; }
echo "$out" | grep -q 'settings.*OK' && echo "ok check_set"    || { echo "FAIL check_set: $out";    fail=1; }
# G1: wt_check must report memory: OK (own bucket) — real dir, not symlink
echo "$out" | grep -q 'memory.*OK.*own bucket' && echo "ok check_memory_own_bucket" || { echo "FAIL check_memory_own_bucket: $out"; fail=1; }
# regression: a symlinked .claude must report FAIL — it breaks the bwrap sandbox (EISDIR)
rm -rf "$WT_CHK/.claude"; ln -s "$MAIN/.claude" "$WT_CHK/.claude"
wt_check "$WT_CHK" "$CANON_CHK" | grep -q 'settings.*FAIL' && echo "ok check_set_symlink" || { echo FAIL check_set_symlink; fail=1; }
HOME="$HOME_BAK"; rm -rf "$W"

# wt_add: nested path test — worktree lands at <main>/.worktrees/<branch>, status clean
W=$(mktemp -d); HOME_BAK="$HOME"; HOME="$W/ch"; mkdir -p "$HOME"
ADDMAIN="$W/addrepo"
mkdir -p "$ADDMAIN"; git -C "$ADDMAIN" init -q
printf '/.worktrees/\nCLAUDE.md\nCLAUDE.local.md\n' > "$ADDMAIN/.gitignore"
git -C "$ADDMAIN" -c user.email=t@t -c user.name=t add .gitignore
git -C "$ADDMAIN" -c user.email=t@t -c user.name=t commit -qm init
wt_add "$ADDMAIN" addtest HEAD >/dev/null 2>&1
EXPECTED_WT="$ADDMAIN/.worktrees/addtest"
[ -d "$EXPECTED_WT" ] && echo "ok wt_add_nested_path" || { echo "FAIL wt_add_nested_path (dir $EXPECTED_WT missing)"; fail=1; }
STATUS=$(git -C "$ADDMAIN" status --porcelain 2>/dev/null)
[ -z "$STATUS" ] && echo "ok wt_add_clean_status" || { echo "FAIL wt_add_clean_status: $STATUS"; fail=1; }
HOME="$HOME_BAK"; rm -rf "$W"

# wt_setup_env: auto weight runs the command; propose just prints; none just prints
FX=$(mktemp -d); mkdir -p "$FX/py" && touch "$FX/py/pyproject.toml"
out=$(wt_setup_env "$FX/py" 2>&1); echo "$out" | grep -q 'weight=auto' && echo "ok setup_env_auto_weight" || { echo FAIL setup_env_auto_weight; fail=1; }
echo "$out" | grep -q 'running:' && echo "ok setup_env_auto_runs" || { echo FAIL setup_env_auto_runs; fail=1; }
FX2=$(mktemp -d); mkdir -p "$FX2/ros" && touch "$FX2/ros/package.xml"
out2=$(wt_setup_env "$FX2/ros" 2>&1); echo "$out2" | grep -q 'PROPOSE' && echo "ok setup_env_propose" || { echo FAIL setup_env_propose; fail=1; }
out3=$(wt_setup_env "$FX/py" 2>&1)   # same python dir — check idempotent re-run still shows auto
echo "$out3" | grep -q 'weight=auto' && echo "ok setup_env_idempotent" || { echo FAIL setup_env_idempotent; fail=1; }
rm -rf "$FX" "$FX2"

# wt_remove: clean-path case removes the worktree and key dir
# (Uses a real git repo fixture so git worktree add/remove work correctly.)
W=$(mktemp -d); HOME_BAK="$HOME"
git -C "$W" init -q; git -C "$W" commit --allow-empty -q -m init
WT_R="$W/.worktrees/test-remove-br"
git -C "$W" worktree add -b test-remove-br "$WT_R" HEAD -q 2>/dev/null || true
HOME="$W/ch"; mkdir -p "$HOME"
source "$HERE/helpers.sh"   # reload with new functions — use $HERE (absolute), not ~, since HOME is overridden
wt_remove "$W" "$WT_R" >/dev/null 2>&1
[ ! -d "$WT_R" ] && echo "ok wt_remove_dir_gone" || { echo FAIL wt_remove_dir_gone; fail=1; }
HOME="$HOME_BAK"; rm -rf "$W"

# wt_preflight_mounts: rc=0 when /proc/mounts has no unreachable /mnt entries
# (In CI / test environment there may be no /mnt mounts — function should still exit 0.)
wt_preflight_mounts >/dev/null 2>&1 && echo "ok preflight_rc0" || { echo FAIL preflight_rc0; fail=1; }

# wt_serena_prestage: F1 serena pre-staging tests
# Fixture: fake HOME with serena dirs; fake git that returns a main clone path.
PATH_BAK2="$PATH"; W_SER=$(mktemp -d)
FAKE_GIT_DIR="$W_SER/fakebin"
mkdir -p "$FAKE_GIT_DIR"
cat > "$FAKE_GIT_DIR/git" <<'G'
#!/usr/bin/env bash
# minimal stub for wt_serena_prestage: wt_wire calls wt_check which calls git
# Just pass through to real git for non-worktree commands
exec /usr/bin/git "$@"
G
chmod +x "$FAKE_GIT_DIR/git"

HOME_SER="$W_SER/home"
MAIN_SER="$W_SER/main_repo"
WT_SER="$W_SER/main_repo/.worktrees/feat-x"
mkdir -p "$MAIN_SER" "$WT_SER"
mkdir -p "$HOME_SER/.serena/projects/main_repo/memories"
echo 'project_name: "main_repo"' > "$HOME_SER/.serena/projects/main_repo/project.yml"
echo 'languages: [python]' >> "$HOME_SER/.serena/projects/main_repo/project.yml"
echo "main memory content" > "$HOME_SER/.serena/projects/main_repo/memories/notes.md"
# Create a minimal serena_config.yml
cat > "$HOME_SER/.serena/serena_config.yml" <<'YAML'
language_backend: LSP
projects:
- /some/other/project
YAML

# serena_prestage_folder: project.yml created with correct project_name
(HOME="$HOME_SER" wt_serena_prestage "$WT_SER" "$MAIN_SER")
pname=$(grep "^project_name:" "$HOME_SER/.serena/projects/feat-x/project.yml" 2>/dev/null | sed 's/project_name: *//;s/"//g')
[ "$pname" = "feat-x" ] && echo "ok serena_prestage_folder" || { echo "FAIL serena_prestage_folder: project_name='$pname'"; fail=1; }

# D1: serena_prestage_memories_empty: worktree serena memories/ starts EMPTY (no copy from parent)
[ ! -f "$HOME_SER/.serena/projects/feat-x/memories/notes.md" ] && \
  echo "ok serena_prestage_memories_empty" || { echo "FAIL serena_prestage_memories_empty (notes.md was copied but should not be)"; fail=1; }

# serena_prestage_skip: if proj dir already exists, skip (revive case — memories preserved)
SENTINEL="$HOME_SER/.serena/projects/feat-x/memories/sentinel.md"
mkdir -p "$HOME_SER/.serena/projects/feat-x/memories"
echo "sentinel" > "$SENTINEL"
echo "extra mem" > "$HOME_SER/.serena/projects/main_repo/memories/extra.md"
(HOME="$HOME_SER" wt_serena_prestage "$WT_SER" "$MAIN_SER")
# sentinel still there (pre-existing memories preserved)
[ -f "$SENTINEL" ] && grep -q "sentinel" "$SENTINEL" && echo "ok serena_prestage_skip_sentinel" || { echo "FAIL serena_prestage_skip_sentinel"; fail=1; }
# extra.md NOT copied (skip logic — proj dir already exists)
[ ! -f "$HOME_SER/.serena/projects/feat-x/memories/extra.md" ] && echo "ok serena_prestage_skip_no_extra" || { echo "FAIL serena_prestage_skip_no_extra (extra was copied on revive)"; fail=1; }

# serena_register_idempotent: run prestage twice; path appears exactly once
(HOME="$HOME_SER" wt_serena_prestage "$WT_SER" "$MAIN_SER")
(HOME="$HOME_SER" wt_serena_prestage "$WT_SER" "$MAIN_SER")
count=$(grep -c "^- $WT_SER$" "$HOME_SER/.serena/serena_config.yml" 2>/dev/null || echo 0)
[ "$count" = "1" ] && echo "ok serena_register_idempotent" || { echo "FAIL serena_register_idempotent: count=$count"; fail=1; }

PATH="$PATH_BAK2"; rm -rf "$W_SER"

# wire_artifacts_dir: wt_wire links into artifacts/ (not .gitignored/) + info/exclude updated
W_ART=$(mktemp -d); HOME_BAK3="$HOME"; HOME="$W_ART/ch"; mkdir -p "$HOME"
MAIN_ART="$W_ART/repo"
mkdir -p "$MAIN_ART"; git -C "$MAIN_ART" init -q
printf '/.worktrees/\n' > "$MAIN_ART/.gitignore"
git -C "$MAIN_ART" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_ART" -c user.email=t@t -c user.name=t commit -qm init
WT_ART="$MAIN_ART/.worktrees/art-test"
git -C "$MAIN_ART" worktree add -b art-test "$WT_ART" HEAD -q 2>/dev/null
CANON_ART="$W_ART/ch/.claude/projects/$(wt_key "$MAIN_ART")"
mkdir -p "$CANON_ART/memory"
mkdir -p "$MAIN_ART/.claude"
# Provide an artifacts dir with content
mkdir -p "$(dirname "$MAIN_ART")/artifacts/$(basename "$MAIN_ART")/sdkZ"
wt_wire "$WT_ART" "$MAIN_ART" "$CANON_ART" >/dev/null 2>&1
# Check links in artifacts/ not .gitignored/
[ -L "$WT_ART/artifacts/sdkZ" ] && [ -e "$WT_ART/artifacts/sdkZ" ] && echo "ok wire_artifacts_dir" || { echo "FAIL wire_artifacts_dir (link not in artifacts/)"; fail=1; }
# Check info/exclude contains /artifacts/
EXCLUDE_FILE="$(git -C "$WT_ART" rev-parse --git-common-dir 2>/dev/null)/info/exclude"
grep -qF '/artifacts/' "$EXCLUDE_FILE" 2>/dev/null && echo "ok wire_artifacts_exclude" || { echo "FAIL wire_artifacts_exclude"; fail=1; }
HOME="$HOME_BAK3"; rm -rf "$W_ART"

# wire_context_template: WT_TICKET set → CLAUDE.local.md contains Ticket: RE-1
W_CTX=$(mktemp -d); HOME_BAK4="$HOME"; HOME="$W_CTX/ch"; mkdir -p "$HOME"
MAIN_CTX="$W_CTX/repo"
mkdir -p "$MAIN_CTX"; git -C "$MAIN_CTX" init -q
printf '/.worktrees/\n' > "$MAIN_CTX/.gitignore"
git -C "$MAIN_CTX" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_CTX" -c user.email=t@t -c user.name=t commit -qm init
WT_CTX="$MAIN_CTX/.worktrees/ctx-test"
git -C "$MAIN_CTX" worktree add -b ctx-test "$WT_CTX" HEAD -q 2>/dev/null
CANON_CTX="$W_CTX/ch/.claude/projects/$(wt_key "$MAIN_CTX")"
mkdir -p "$CANON_CTX/memory"
mkdir -p "$MAIN_CTX/.claude"
WT_TICKET="RE-1" WT_PURPOSE="test purpose" WT_HANDOFF="" wt_wire "$WT_CTX" "$MAIN_CTX" "$CANON_CTX" >/dev/null 2>&1
grep -q "Ticket: RE-1" "$WT_CTX/CLAUDE.local.md" && echo "ok wire_context_template" || { echo "FAIL wire_context_template: $(cat "$WT_CTX/CLAUDE.local.md")"; fail=1; }

# wire_context_empty: no env vars → CLAUDE.local.md is empty
W_EMP=$(mktemp -d); HOME_BAK5="$HOME"; HOME="$W_EMP/ch"; mkdir -p "$HOME"
MAIN_EMP="$W_EMP/repo"
mkdir -p "$MAIN_EMP"; git -C "$MAIN_EMP" init -q
printf '/.worktrees/\n' > "$MAIN_EMP/.gitignore"
git -C "$MAIN_EMP" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_EMP" -c user.email=t@t -c user.name=t commit -qm init
WT_EMP="$MAIN_EMP/.worktrees/emp-test"
git -C "$MAIN_EMP" worktree add -b emp-test "$WT_EMP" HEAD -q 2>/dev/null
CANON_EMP="$W_EMP/ch/.claude/projects/$(wt_key "$MAIN_EMP")"
mkdir -p "$CANON_EMP/memory"
mkdir -p "$MAIN_EMP/.claude"
unset WT_TICKET WT_PURPOSE WT_HANDOFF
wt_wire "$WT_EMP" "$MAIN_EMP" "$CANON_EMP" >/dev/null 2>&1
[ ! -s "$WT_EMP/CLAUDE.local.md" ] && echo "ok wire_context_empty" || { echo "FAIL wire_context_empty: $(cat "$WT_EMP/CLAUDE.local.md")"; fail=1; }
HOME="$HOME_BAK5"; rm -rf "$W_EMP"

# ── Task 2: lifecycle modes ──────────────────────────────────────────────────

# Helper: make a minimal fake HOME with a serena_config.yml
_make_ser_home() {
  local h="$1" wt_path="${2:-}"
  mkdir -p "$h/.serena/projects"
  {
    printf 'language_backend: LSP\n'
    printf 'projects:\n'
    [ -n "$wt_path" ] && printf -- '- %s\n' "$wt_path"
  } > "$h/.serena/serena_config.yml"
}

# ── deregister_idempotent ────────────────────────────────────────────────────
W_D=$(mktemp -d); HOME_BAK_D="$HOME"; HOME="$W_D/h"; mkdir -p "$HOME"
_make_ser_home "$HOME" "$W_D/repos/main/.worktrees/feat-d"
# Run deregister twice — no error, path absent both times
(HOME="$HOME" wt_serena_deregister "$W_D/repos/main/.worktrees/feat-d") >/dev/null 2>&1
count_d1=$(grep -c "^- $W_D/repos/main/.worktrees/feat-d$" "$HOME/.serena/serena_config.yml" 2>/dev/null); count_d1=${count_d1:-0}
(HOME="$HOME" wt_serena_deregister "$W_D/repos/main/.worktrees/feat-d") >/dev/null 2>&1
count_d2=$(grep -c "^- $W_D/repos/main/.worktrees/feat-d$" "$HOME/.serena/serena_config.yml" 2>/dev/null); count_d2=${count_d2:-0}
[ "$count_d1" = "0" ] && [ "$count_d2" = "0" ] && echo "ok deregister_idempotent" || { echo "FAIL deregister_idempotent: counts=$count_d1,$count_d2"; fail=1; }
HOME="$HOME_BAK_D"; rm -rf "$W_D"

# ── archive_revive_roundtrip ─────────────────────────────────────────────────
W_AR=$(mktemp -d); HOME_BAK_AR="$HOME"; HOME="$W_AR/h"; mkdir -p "$HOME"
MAIN_AR="$W_AR/repo"
mkdir -p "$MAIN_AR"; git -C "$MAIN_AR" init -q
printf '/.worktrees/\n' > "$MAIN_AR/.gitignore"
git -C "$MAIN_AR" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_AR" -c user.email=t@t -c user.name=t commit -qm init
WT_AR="$MAIN_AR/.worktrees/arc-test"
git -C "$MAIN_AR" worktree add -b arc-test "$WT_AR" HEAD -q 2>/dev/null
# Put an uncommitted file in the worktree
echo "uncommitted" > "$WT_AR/dirty.txt"
# Set up fake HOME serena with wt_path registered
_make_ser_home "$HOME" "$WT_AR"
mkdir -p "$HOME/.serena/projects/arc-test"

# wt_archive → dir at _archive/<br>
(HOME="$HOME" wt_archive "$MAIN_AR" "$WT_AR") >/dev/null 2>&1
arch_path="$MAIN_AR/.worktrees/_archive/arc-test"
[ -d "$arch_path" ] && echo "ok archive_dir_moved" || { echo "FAIL archive_dir_moved: $arch_path missing"; fail=1; }
# git worktree list shows it locked
lock_out=$(git -C "$MAIN_AR" worktree list --porcelain 2>/dev/null)
echo "$lock_out" | grep -A5 "worktree $arch_path" | grep -q "locked" \
  && echo "ok archive_locked" || { echo "FAIL archive_locked"; fail=1; }
# original wt path gone
[ ! -d "$WT_AR" ] && echo "ok archive_orig_gone" || { echo "FAIL archive_orig_gone: $WT_AR still exists"; fail=1; }
# uncommitted file preserved in archive
[ -f "$arch_path/dirty.txt" ] && echo "ok archive_uncommitted_preserved" || { echo "FAIL archive_uncommitted_preserved"; fail=1; }
# wt path NOT in serena_config projects:
count_ar=$(grep -c "^- $WT_AR$" "$HOME/.serena/serena_config.yml" 2>/dev/null); count_ar=${count_ar:-0}
[ "$count_ar" = "0" ] && echo "ok archive_serena_deregistered" || { echo "FAIL archive_serena_deregistered: count=$count_ar"; fail=1; }

# wt_revive → dir back at .worktrees/<br>, not locked, file present, path back in projects:
(HOME="$HOME" wt_revive "$MAIN_AR" "arc-test") >/dev/null 2>&1
[ -d "$WT_AR" ] && echo "ok revive_dir_back" || { echo "FAIL revive_dir_back: $WT_AR missing"; fail=1; }
# not locked (lock attribute absent from porcelain for this entry)
revive_lock=$(git -C "$MAIN_AR" worktree list --porcelain 2>/dev/null | grep -A5 "worktree $WT_AR" | grep "locked" || echo "")
[ -z "$revive_lock" ] && echo "ok revive_not_locked" || { echo "FAIL revive_not_locked: $revive_lock"; fail=1; }
[ -f "$WT_AR/dirty.txt" ] && echo "ok revive_file_preserved" || { echo "FAIL revive_file_preserved"; fail=1; }
count_rv=$(grep -c "^- $WT_AR$" "$HOME/.serena/serena_config.yml" 2>/dev/null); count_rv=${count_rv:-0}
[ "$count_rv" = "1" ] && echo "ok revive_serena_registered" || { echo "FAIL revive_serena_registered: count=$count_rv"; fail=1; }
HOME="$HOME_BAK_AR"; rm -rf "$W_AR"

# ── archive_refuses_existing_target ─────────────────────────────────────────
W_AE=$(mktemp -d); HOME_BAK_AE="$HOME"; HOME="$W_AE/h"; mkdir -p "$HOME"
MAIN_AE="$W_AE/repo"
mkdir -p "$MAIN_AE"; git -C "$MAIN_AE" init -q
printf '/.worktrees/\n' > "$MAIN_AE/.gitignore"
git -C "$MAIN_AE" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_AE" -c user.email=t@t -c user.name=t commit -qm init
WT_AE="$MAIN_AE/.worktrees/arc-exist"
git -C "$MAIN_AE" worktree add -b arc-exist "$WT_AE" HEAD -q 2>/dev/null
# Pre-create the archive target
mkdir -p "$MAIN_AE/.worktrees/_archive/arc-exist"
_make_ser_home "$HOME"
(HOME="$HOME" wt_archive "$MAIN_AE" "$WT_AE") >/dev/null 2>&1; rc_ae=$?
[ "$rc_ae" != "0" ] && echo "ok archive_refuses_existing" || { echo "FAIL archive_refuses_existing: should have returned non-zero"; fail=1; }
HOME="$HOME_BAK_AE"; rm -rf "$W_AE"

# ── reap_merged ──────────────────────────────────────────────────────────────
W_RM=$(mktemp -d); HOME_BAK_RM="$HOME"; HOME="$W_RM/h"; mkdir -p "$HOME"
MAIN_RM="$W_RM/repo"
mkdir -p "$MAIN_RM"; git -C "$MAIN_RM" init -q
printf '/.worktrees/\n' > "$MAIN_RM/.gitignore"
git -C "$MAIN_RM" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RM" -c user.email=t@t -c user.name=t commit -qm init
WT_RM="$MAIN_RM/.worktrees/reap-merged"
git -C "$MAIN_RM" worktree add -b reap-merged "$WT_RM" HEAD -q 2>/dev/null
# Make a commit on the branch, then merge it into main
echo "feature" > "$WT_RM/feat.txt"
git -C "$WT_RM" add feat.txt
git -C "$WT_RM" -c user.email=t@t -c user.name=t commit -qm "feat: add feature"
git -C "$MAIN_RM" merge --no-edit reap-merged -q 2>/dev/null
_make_ser_home "$HOME" "$WT_RM"
mkdir -p "$HOME/.serena/projects/reap-merged"
mkdir -p "$HOME/.serena/projects/$(basename "$MAIN_RM")"
# Run reap with WT_ASSUME_YES=1 to skip interactive prompt
(HOME="$HOME" WT_ASSUME_YES=1 wt_reap "$MAIN_RM" "$WT_RM") >/dev/null 2>&1; rc_rm=$?
[ "$rc_rm" = "0" ] && echo "ok reap_merged_rc0" || { echo "FAIL reap_merged_rc0: rc=$rc_rm"; fail=1; }
# wt dir gone
[ ! -d "$WT_RM" ] && echo "ok reap_merged_dir_gone" || { echo "FAIL reap_merged_dir_gone"; fail=1; }
# serena project folder purged
[ ! -d "$HOME/.serena/projects/reap-merged" ] && echo "ok reap_merged_serena_purged" || { echo "FAIL reap_merged_serena_purged"; fail=1; }
# path gone from projects:
count_rm=$(grep -c "^- $WT_RM$" "$HOME/.serena/serena_config.yml" 2>/dev/null); count_rm=${count_rm:-0}
[ "$count_rm" = "0" ] && echo "ok reap_merged_serena_dereg" || { echo "FAIL reap_merged_serena_dereg: count=$count_rm"; fail=1; }
# manifest preserved at _reaped/<branch>.reap-manifest.md with branch content
manifest_rm="$MAIN_RM/.worktrees/_reaped/reap-merged.reap-manifest.md"
[ -f "$manifest_rm" ] && echo "ok reap_merged_manifest_exists" || { echo "FAIL reap_merged_manifest_exists: $manifest_rm not found"; fail=1; }
[ -f "$manifest_rm" ] && grep -q "^branch: reap-merged" "$manifest_rm" && echo "ok reap_merged_manifest_branch" || { echo "FAIL reap_merged_manifest_branch"; fail=1; }
# D2: manifest contains candidates: YAML block (may be empty list if no memories written)
[ -f "$manifest_rm" ] && grep -q '^candidates:' "$manifest_rm" && echo "ok reap_merged_manifest_candidates" || { echo "FAIL reap_merged_manifest_candidates (no candidates: key in manifest)"; fail=1; }
HOME="$HOME_BAK_RM"; rm -rf "$W_RM"

# ── reap_unmerged_aborts ─────────────────────────────────────────────────────
W_RU=$(mktemp -d); HOME_BAK_RU="$HOME"; HOME="$W_RU/h"; mkdir -p "$HOME"
MAIN_RU="$W_RU/repo"
mkdir -p "$MAIN_RU"; git -C "$MAIN_RU" init -q
printf '/.worktrees/\n' > "$MAIN_RU/.gitignore"
git -C "$MAIN_RU" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RU" -c user.email=t@t -c user.name=t commit -qm init
WT_RU="$MAIN_RU/.worktrees/reap-unmerged"
git -C "$MAIN_RU" worktree add -b reap-unmerged "$WT_RU" HEAD -q 2>/dev/null
# A commit on the branch NOT merged
echo "unmerged" > "$WT_RU/new.txt"
git -C "$WT_RU" add new.txt
git -C "$WT_RU" -c user.email=t@t -c user.name=t commit -qm "feat: unmerged"
_make_ser_home "$HOME" "$WT_RU"
(HOME="$HOME" wt_reap "$MAIN_RU" "$WT_RU") >/dev/null 2>&1; rc_ru=$?
[ "$rc_ru" != "0" ] && echo "ok reap_unmerged_aborts" || { echo "FAIL reap_unmerged_aborts: should have returned non-zero"; fail=1; }
[ -d "$WT_RU" ] && echo "ok reap_unmerged_wt_present" || { echo "FAIL reap_unmerged_wt_present: wt was removed"; fail=1; }
HOME="$HOME_BAK_RU"; rm -rf "$W_RU"

# ── reap_force_overrides ─────────────────────────────────────────────────────
W_RF=$(mktemp -d); HOME_BAK_RF="$HOME"; HOME="$W_RF/h"; mkdir -p "$HOME"
MAIN_RF="$W_RF/repo"
mkdir -p "$MAIN_RF"; git -C "$MAIN_RF" init -q
printf '/.worktrees/\n' > "$MAIN_RF/.gitignore"
git -C "$MAIN_RF" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RF" -c user.email=t@t -c user.name=t commit -qm init
WT_RF="$MAIN_RF/.worktrees/reap-force"
git -C "$MAIN_RF" worktree add -b reap-force "$WT_RF" HEAD -q 2>/dev/null
echo "unmerged" > "$WT_RF/new.txt"
git -C "$WT_RF" add new.txt
git -C "$WT_RF" -c user.email=t@t -c user.name=t commit -qm "feat: unmerged"
_make_ser_home "$HOME" "$WT_RF"
mkdir -p "$HOME/.serena/projects/reap-force"
mkdir -p "$HOME/.serena/projects/$(basename "$MAIN_RF")"
(HOME="$HOME" WT_ASSUME_YES=1 wt_reap "$MAIN_RF" "$WT_RF" --force) >/dev/null 2>&1; rc_rf=$?
[ "$rc_rf" = "0" ] && echo "ok reap_force_rc0" || { echo "FAIL reap_force_rc0: rc=$rc_rf"; fail=1; }
[ ! -d "$WT_RF" ] && echo "ok reap_force_wt_gone" || { echo "FAIL reap_force_wt_gone"; fail=1; }
HOME="$HOME_BAK_RF"; rm -rf "$W_RF"

# ── reap_dirty_aborts ────────────────────────────────────────────────────────
W_RD=$(mktemp -d); HOME_BAK_RD="$HOME"; HOME="$W_RD/h"; mkdir -p "$HOME"
MAIN_RD="$W_RD/repo"
mkdir -p "$MAIN_RD"; git -C "$MAIN_RD" init -q
printf '/.worktrees/\n' > "$MAIN_RD/.gitignore"
git -C "$MAIN_RD" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RD" -c user.email=t@t -c user.name=t commit -qm init
WT_RD="$MAIN_RD/.worktrees/reap-dirty"
git -C "$MAIN_RD" worktree add -b reap-dirty "$WT_RD" HEAD -q 2>/dev/null
# Merge the branch first so merge gate passes
git -C "$MAIN_RD" merge --no-edit reap-dirty -q 2>/dev/null
# Now add an uncommitted file
echo "dirty" > "$WT_RD/dirty.txt"
_make_ser_home "$HOME" "$WT_RD"
(HOME="$HOME" wt_reap "$MAIN_RD" "$WT_RD") >/dev/null 2>&1; rc_rd=$?
[ "$rc_rd" != "0" ] && echo "ok reap_dirty_aborts" || { echo "FAIL reap_dirty_aborts: should have returned non-zero"; fail=1; }
[ -d "$WT_RD" ] && echo "ok reap_dirty_wt_present" || { echo "FAIL reap_dirty_wt_present: wt was removed"; fail=1; }
HOME="$HOME_BAK_RD"; rm -rf "$W_RD"

# ── fix2: wt_add with slashed branch feat/x ─────────────────────────────────
W_SL=$(mktemp -d); HOME_BAK_SL="$HOME"; HOME="$W_SL/h"; mkdir -p "$HOME"
MAIN_SL="$W_SL/repo"
mkdir -p "$MAIN_SL"; git -C "$MAIN_SL" init -q
printf '/.worktrees/\nCLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_SL/.gitignore"
git -C "$MAIN_SL" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_SL" -c user.email=t@t -c user.name=t commit -qm init
(HOME="$HOME" wt_add "$MAIN_SL" "feat/x" HEAD) >/dev/null 2>&1
EXPECTED_SL="$MAIN_SL/.worktrees/feat/x"
[ -d "$EXPECTED_SL" ] && echo "ok wt_add_slashed_branch" || { echo "FAIL wt_add_slashed_branch (dir $EXPECTED_SL missing)"; fail=1; }
HOME="$HOME_BAK_SL"; rm -rf "$W_SL"

# ── fix3: wt_reap refuses main clone (wt == main) ────────────────────────────
W_F3=$(mktemp -d); HOME_BAK_F3="$HOME"; HOME="$W_F3/h"; mkdir -p "$HOME"
MAIN_F3="$W_F3/repo"
mkdir -p "$MAIN_F3"; git -C "$MAIN_F3" init -q
printf '/.worktrees/\n' > "$MAIN_F3/.gitignore"
git -C "$MAIN_F3" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_F3" -c user.email=t@t -c user.name=t commit -qm init
_make_ser_home "$HOME"
(HOME="$HOME" wt_reap "$MAIN_F3" "$MAIN_F3") >/dev/null 2>&1; rc_f3=$?
[ "$rc_f3" != "0" ] && echo "ok reap_refuses_main_clone" || { echo "FAIL reap_refuses_main_clone: should return non-zero when wt==main"; fail=1; }
[ -d "$MAIN_F3" ] && echo "ok reap_refuses_main_not_deleted" || { echo "FAIL reap_refuses_main_not_deleted"; fail=1; }
HOME="$HOME_BAK_F3"; rm -rf "$W_F3"

# ── fix5: info/exclude partial match still appends /artifacts/ ───────────────
W_F5=$(mktemp -d); HOME_BAK_F5="$HOME"; HOME="$W_F5/h"; mkdir -p "$HOME"
MAIN_F5="$W_F5/repo"
mkdir -p "$MAIN_F5"; git -C "$MAIN_F5" init -q
printf '/.worktrees/\n' > "$MAIN_F5/.gitignore"
git -C "$MAIN_F5" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_F5" -c user.email=t@t -c user.name=t commit -qm init
WT_F5="$MAIN_F5/.worktrees/fix5-test"
git -C "$MAIN_F5" worktree add -b fix5-test "$WT_F5" HEAD -q 2>/dev/null
# Pre-seed info/exclude with a partial/superset line (not an exact /artifacts/ match)
EXCL_F5="$(git -C "$WT_F5" rev-parse --git-common-dir 2>/dev/null)/info/exclude"
printf 'node_modules/artifacts/\n' >> "$EXCL_F5"
# Provide artifacts dir so wt_wire reaches the exclude logic
mkdir -p "$(dirname "$MAIN_F5")/artifacts/$(basename "$MAIN_F5")/sdkX"
CANON_F5="$W_F5/h/.claude/projects/$(wt_key "$MAIN_F5")"
mkdir -p "$CANON_F5/memory" "$MAIN_F5/.claude"
(HOME="$HOME" wt_wire "$WT_F5" "$MAIN_F5" "$CANON_F5") >/dev/null 2>&1
# Exact /artifacts/ line must now be present (partial match is not exact)
_art_exact=0
while IFS= read -r _el; do [ "$_el" = '/artifacts/' ] && _art_exact=1; done < "$EXCL_F5"
[ "$_art_exact" = "1" ] && echo "ok fix5_exclude_exact_appended" || { echo "FAIL fix5_exclude_exact_appended (exact /artifacts/ not in exclude file)"; fail=1; }
HOME="$HOME_BAK_F5"; rm -rf "$W_F5"

# ── fix1: wt_reap purge-only-on-success + serena preserved on failure ────────
# We test the happy path (clean merged reap) already purges serena (reap_merged_serena_purged above).
# For failure gate: simulate wt_remove failure by making the worktree non-removable, then assert
# the serena project dir survives.
W_F1=$(mktemp -d); HOME_BAK_F1="$HOME"; HOME="$W_F1/h"; mkdir -p "$HOME"
MAIN_F1="$W_F1/repo"
mkdir -p "$MAIN_F1"; git -C "$MAIN_F1" init -q
printf '/.worktrees/\n' > "$MAIN_F1/.gitignore"
git -C "$MAIN_F1" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_F1" -c user.email=t@t -c user.name=t commit -qm init
WT_F1="$MAIN_F1/.worktrees/fix1-test"
git -C "$MAIN_F1" worktree add -b fix1-test "$WT_F1" HEAD -q 2>/dev/null
git -C "$MAIN_F1" merge --no-edit fix1-test -q 2>/dev/null
_make_ser_home "$HOME" "$WT_F1"
mkdir -p "$HOME/.serena/projects/fix1-test/memories"
echo "precious memory" > "$HOME/.serena/projects/fix1-test/memories/precious.md"
# Make wt non-removable by planting a root-owned file stub: instead inject a fake wt_remove
# that always fails, by shadowing it with a function in a subshell
(
  HOME="$HOME"
  wt_remove() { printf 'wt_remove: SIMULATED FAILURE\n' >&2; return 1; }
  export -f wt_remove
  WT_ASSUME_YES=1 wt_reap "$MAIN_F1" "$WT_F1"
) >/dev/null 2>&1; rc_f1=$?
# wt_reap should return non-zero (wt_remove failed)
[ "$rc_f1" != "0" ] && echo "ok fix1_reap_rc_nonzero_on_remove_fail" || { echo "FAIL fix1_reap_rc_nonzero_on_remove_fail: expected non-zero"; fail=1; }
# serena project dir should SURVIVE (not purged) because wt_remove failed
[ -d "$HOME/.serena/projects/fix1-test" ] && echo "ok fix1_serena_preserved_on_remove_fail" || { echo "FAIL fix1_serena_preserved_on_remove_fail: serena project was purged despite wt_remove failure"; fail=1; }
HOME="$HOME_BAK_F1"; rm -rf "$W_F1"

# ── D2: wt_reap_promote YAML manifest with candidates ─────────────────────────
W_D2=$(mktemp -d); HOME_BAK_D2="$HOME"; HOME="$W_D2/h"; mkdir -p "$HOME"
MAIN_D2="$W_D2/repo"
mkdir -p "$MAIN_D2"; git -C "$MAIN_D2" init -q
printf '/.worktrees/\n' > "$MAIN_D2/.gitignore"
git -C "$MAIN_D2" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_D2" -c user.email=t@t -c user.name=t commit -qm init
WT_D2="$MAIN_D2/.worktrees/d2-test"
git -C "$MAIN_D2" worktree add -b d2-test "$WT_D2" HEAD -q 2>/dev/null
# Seed serena memory
_make_ser_home "$HOME"
mkdir -p "$HOME/.serena/projects/d2-test/memories"
printf '%s\n' '---' 'type: reference' '---' 'serena content' > "$HOME/.serena/projects/d2-test/memories/ser_note.md"
# Seed claude bucket memory
_wt_key_d2="$HOME/.claude/projects/$(wt_key "$WT_D2")/memory"
mkdir -p "$_wt_key_d2"
printf '%s\n' '---' 'type: feedback' '---' 'claude content' > "$_wt_key_d2/cl_note.md"
# Seed parent dest (claude) with same filename to trigger collision
mkdir -p "$HOME/.claude/projects/$(wt_key "$MAIN_D2")/memory"
printf 'parent content\n' > "$HOME/.claude/projects/$(wt_key "$MAIN_D2")/memory/cl_note.md"
# Serena parent dest — no collision for ser_note.md
mkdir -p "$HOME/.serena/projects/$(basename "$MAIN_D2")/memories"
# Run wt_reap_promote directly
(HOME="$HOME" wt_reap_promote "$WT_D2" "$MAIN_D2") >/dev/null 2>&1
mf_d2="$WT_D2/.reap-manifest.md"
[ -f "$mf_d2" ] && echo "ok d2_manifest_exists" || { echo "FAIL d2_manifest_exists"; fail=1; }
# Must have candidates: key
grep -q '^candidates:' "$mf_d2" && echo "ok d2_candidates_key" || { echo "FAIL d2_candidates_key"; fail=1; }
# Must have both entries (serena + claude)
grep -q 'store: serena' "$mf_d2" && echo "ok d2_serena_entry" || { echo "FAIL d2_serena_entry"; fail=1; }
grep -q 'store: claude' "$mf_d2" && echo "ok d2_claude_entry" || { echo "FAIL d2_claude_entry"; fail=1; }
# cl_note (claude) collision must point at a real path (not 'none') — check in the full file
# The collision line for cl_note contains the parent dest path (ends in cl_note.md)
grep -q 'collision:.*cl_note' "$mf_d2" && echo "ok d2_collision_detected" || { echo "FAIL d2_collision_detected (no collision line containing cl_note)"; fail=1; }
# ser_note (serena) collision must be 'none' — ser_note is not in parent serena dest
grep -q 'collision: none' "$mf_d2" && echo "ok d2_no_collision_serena" || { echo "FAIL d2_no_collision_serena (no collision: none line found)"; fail=1; }
# proposed: {} must be present for each candidate
count_proposed=$(grep -c '^    proposed: {}' "$mf_d2" 2>/dev/null || echo 0)
[ "$count_proposed" = "2" ] && echo "ok d2_proposed_empty" || { echo "FAIL d2_proposed_empty: count=$count_proposed (expected 2)"; fail=1; }
# Must NOT contain 'base:' anywhere
grep -q '^base:' "$mf_d2" && { echo "FAIL d2_no_base_field (base: found in manifest)"; fail=1; } || echo "ok d2_no_base_field"
HOME="$HOME_BAK_D2"; rm -rf "$W_D2"

# ── fix7: wt_check artifacts OK on empty artifacts dir ───────────────────────
W_F7=$(mktemp -d); HOME_BAK_F7="$HOME"; HOME="$W_F7/h"; mkdir -p "$HOME"
MAIN_F7="$W_F7/repo"
mkdir -p "$MAIN_F7"; git -C "$MAIN_F7" init -q
printf '/.worktrees/\n' > "$MAIN_F7/.gitignore"
git -C "$MAIN_F7" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_F7" -c user.email=t@t -c user.name=t commit -qm init
WT_F7="$MAIN_F7/.worktrees/f7-test"
git -C "$MAIN_F7" worktree add -b f7-test "$WT_F7" HEAD -q 2>/dev/null
CANON_F7="$W_F7/h/.claude/projects/$(wt_key "$MAIN_F7")"
mkdir -p "$CANON_F7/memory" "$MAIN_F7/.claude" "$WT_F7/.claude"
touch "$MAIN_F7/CLAUDE.md" "$MAIN_F7/CLAUDE.local.md"
mkdir -p "$HOME/.claude/projects/$(wt_key "$WT_F7")/memory"
# Create empty artifacts dir (no entries)
mkdir -p "$WT_F7/artifacts"
out_f7=$(wt_check "$WT_F7" "$CANON_F7" 2>/dev/null)
echo "$out_f7" | grep -q 'artifacts.*OK' && echo "ok fix7_empty_artifacts_ok" || { echo "FAIL fix7_empty_artifacts_ok: $out_f7"; fail=1; }
HOME="$HOME_BAK_F7"; rm -rf "$W_F7"

# ── portability: wt_check flags a broken artifacts symlink (find-based probe, no read -d '') ──
W_BS=$(mktemp -d); HOME_BAK_BS="$HOME"; HOME="$W_BS/h"; mkdir -p "$HOME"
MAIN_BS="$W_BS/repo"
mkdir -p "$MAIN_BS"; git -C "$MAIN_BS" init -q
printf '/.worktrees/\n' > "$MAIN_BS/.gitignore"
git -C "$MAIN_BS" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_BS" -c user.email=t@t -c user.name=t commit -qm init
WT_BS="$MAIN_BS/.worktrees/bs-test"
git -C "$MAIN_BS" worktree add -b bs-test "$WT_BS" HEAD -q 2>/dev/null
CANON_BS="$W_BS/h/.claude/projects/$(wt_key "$MAIN_BS")"
mkdir -p "$CANON_BS/memory" "$MAIN_BS/.claude" "$WT_BS/.claude"
touch "$MAIN_BS/CLAUDE.md" "$MAIN_BS/CLAUDE.local.md"
mkdir -p "$HOME/.claude/projects/$(wt_key "$WT_BS")/memory"
mkdir -p "$WT_BS/artifacts"
ln -s "$W_BS/nonexistent-target" "$WT_BS/artifacts/deadlink"
out_bs=$(wt_check "$WT_BS" "$CANON_BS" 2>/dev/null)
echo "$out_bs" | grep -q 'artifacts: FAIL' && echo "ok broken_artifact_flagged" || { echo "FAIL broken_artifact_flagged: $out_bs"; fail=1; }
HOME="$HOME_BAK_BS"; rm -rf "$W_BS"

# ── portability: wt_remove blocked path — owner listing must not rely on GNU find -printf ──
# (Blocked branch is reached whenever `git worktree remove` fails; the listing itself is empty
# here because everything is user-owned, but the branch must run cleanly and print the recovery.)
W_PB=$(mktemp -d)
git -C "$W_PB" init -q; git -C "$W_PB" commit --allow-empty -qm init
mkdir -p "$W_PB/notawt"
out_pb=$(wt_remove "$W_PB" "$W_PB/notawt" 2>&1); rc_pb=$?
[ "$rc_pb" != "0" ] && echo "ok remove_blocked_rc_nonzero" || { echo "FAIL remove_blocked_rc_nonzero"; fail=1; }
echo "$out_pb" | grep -q 'sudo rm -rf' && echo "ok remove_blocked_recovery_msg" || { echo "FAIL remove_blocked_recovery_msg: $out_pb"; fail=1; }
rm -rf "$W_PB"

# ── portability: helpers must be sourceable + functional in zsh ──────────────
# zsh indexes arrays from 1 (bash from 0) — wt_add's positional parsing regressed there before
# it was rewritten to scalars. Also exercises zsh's stricter nomatch globbing via wt_wire.
if command -v zsh >/dev/null 2>&1; then
  zsh -f -c "source '$HERE/helpers.sh' && [ \"\$(wt_key /home/u/a_b.c)\" = '-home-u-a-b-c' ]" \
    && echo "ok zsh_source_wt_key" || { echo "FAIL zsh_source_wt_key"; fail=1; }
  W_Z=$(mktemp -d); HOME_BAK_Z="$HOME"; HOME="$W_Z/h"; mkdir -p "$HOME"
  MAIN_Z="$W_Z/repo"
  mkdir -p "$MAIN_Z"; git -C "$MAIN_Z" init -q
  printf '/.worktrees/\nCLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_Z/.gitignore"
  git -C "$MAIN_Z" -c user.email=t@t -c user.name=t add .gitignore
  git -C "$MAIN_Z" -c user.email=t@t -c user.name=t commit -qm init
  zsh -f -c "source '$HERE/helpers.sh' && wt_add --ticket Z-9 '$MAIN_Z' ztest HEAD" >/dev/null 2>&1
  [ -d "$MAIN_Z/.worktrees/ztest" ] && echo "ok zsh_wt_add_positionals" || { echo "FAIL zsh_wt_add_positionals"; fail=1; }
  grep -q 'Ticket: Z-9' "$MAIN_Z/.worktrees/ztest/CLAUDE.local.md" 2>/dev/null && echo "ok zsh_wt_add_ticket_flag" || { echo "FAIL zsh_wt_add_ticket_flag"; fail=1; }
  HOME="$HOME_BAK_Z"; rm -rf "$W_Z"
else
  echo "skip zsh portability tests (zsh not found)"
fi

exit $fail
