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

# Layout under test (sibling worktrees, no symlinks):
#   <project>/<repo>/             the git repo
#   <project>/worktrees/<branch>  worktrees BESIDE the repo
#   <project>/worktrees/_archive/ archived (locked) worktrees
#   <project>/artifacts/          shared store, reached by plain relative path
#   <project>/history/reaped/     reap manifests
# Fixtures use MAIN=$W/repo, so <project> == $W.

# wt_key: replace every '/', '.' and '_' with '-' (must match CC's project-key sanitization)
assert_eq wt_key_simple   "$(wt_key /home/u/Studio/Developer/projects/repo/repo)" \
  "-home-u-Studio-Developer-projects-repo-repo"
assert_eq wt_key_worktree "$(wt_key /home/u/Studio/Developer/projects/repo/worktrees/RE-1)" \
  "-home-u-Studio-Developer-projects-repo-worktrees-RE-1"
assert_eq wt_key_slashed  "$(wt_key /home/u/Studio/Developer/projects/repo/worktrees/hotfix/x)" \
  "-home-u-Studio-Developer-projects-repo-worktrees-hotfix-x"
assert_eq wt_key_underscore "$(wt_key /home/u/Studio/Developer/projects/yubo_monorepo/yubo_monorepo)" \
  "-home-u-Studio-Developer-projects-yubo-monorepo-yubo-monorepo"


# canonical_dir: from ANY worktree, returns ~/.claude/projects/<key-of-main-clone>
# Fixture: fake a `git` that prints a worktree list with the main clone first.
PATH_BAK="$PATH"; TMPB=$(mktemp -d)
cat > "$TMPB/git" <<'G'
#!/usr/bin/env bash
# stub: only supports `git -C X worktree list --porcelain`
echo "worktree /home/u/Studio/Developer/projects/repo/repo"
echo "worktree /home/u/Studio/Developer/projects/repo/worktrees/RE-1"
G
chmod +x "$TMPB/git"; PATH="$TMPB:$PATH"
assert_eq canonical_dir "$(HOME=/home/u canonical_dir /any/path)" \
  "/home/u/.claude/projects/-home-u-Studio-Developer-projects-repo-repo"
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

# wt_wire: brain stub + .claude REAL dir (copied from main) + memory OWN BUCKET + artifacts
# reported by relative path (real temp FS). Sibling layout: WT is beside the repo, not inside it.
W=$(mktemp -d); HOME_BAK="$HOME"
MAIN="$W/projects/repo"; WT="$W/projects/worktrees/RE-1"
CANON="$W/claude/projects/-x-repo"
mkdir -p "$MAIN/.claude" "$CANON/memory" "$WT" "$W/projects/artifacts/sdkA"
echo '{"x":1}' > "$MAIN/.claude/settings.local.json"
HOME="$W/claude_home"; mkdir -p "$HOME"
wire_out=$(wt_wire "$WT" "$MAIN" "$CANON" 2>&1)
[ -f "$WT/CLAUDE.local.md" ] && ! grep -q '^@' "$WT/CLAUDE.local.md" && echo "ok wire_stub_empty" || { echo "FAIL wire_stub_empty (CLAUDE.local.md missing or contains @import)"; fail=1; }
[ -f "$MAIN/CLAUDE.md" ] && echo "ok wire_project_claudemd" || { echo "FAIL wire_project_claudemd"; fail=1; }
[ -f "$MAIN/CLAUDE.local.md" ] && echo "ok wire_project_claudelocal" || { echo "FAIL wire_project_claudelocal"; fail=1; }
{ [ -d "$WT/.claude" ] && [ ! -L "$WT/.claude" ]; } && echo "ok wire_claude" || { echo "FAIL wire_claude"; fail=1; }
# artifacts: derived as <project>/artifacts (ONE dirname off main), reported as reachable
echo "$wire_out" | grep -qF "artifacts reachable at $W/projects/artifacts" \
  && echo "ok wire_artifacts_derived" || { echo "FAIL wire_artifacts_derived: $wire_out"; fail=1; }
# regression: NOTHING is created inside the worktree — no symlink farm, no artifacts/ dir
[ ! -e "$WT/artifacts" ] && echo "ok wire_no_artifacts_dir_created" || { echo "FAIL wire_no_artifacts_dir_created (wt/artifacts was created)"; fail=1; }
[ ! -e "$WT/.gitignored" ] && echo "ok wire_no_gitignored_fallback" || { echo "FAIL wire_no_gitignored_fallback"; fail=1; }
# the relative path really does resolve from the worktree to the store
[ "$(cd "$WT/../../artifacts" && pwd -P)" = "$(cd "$W/projects/artifacts" && pwd -P)" ] \
  && echo "ok wire_artifacts_relative_resolves" || { echo "FAIL wire_artifacts_relative_resolves"; fail=1; }
# G1: memory is a real dir (own bucket), NOT a symlink to canon
_wtkey_wire="$HOME/.claude/projects/$(wt_key "$WT")"
{ [ -d "$_wtkey_wire/memory" ] && [ ! -L "$_wtkey_wire/memory" ]; } && echo "ok wire_memory_own_bucket" || { echo "FAIL wire_memory_own_bucket (memory/ should be real dir, not symlink)"; fail=1; }
# 4th-arg override: artifacts store passed explicitly at a NON-derived location
mkdir -p "$W/elsewhere"
wire_out4=$(wt_wire "$WT" "$MAIN" "$CANON" "$W/elsewhere" 2>&1)
echo "$wire_out4" | grep -qF "artifacts reachable at $W/elsewhere" \
  && echo "ok wire_artifacts_4tharg" || { echo "FAIL wire_artifacts_4tharg: $wire_out4"; fail=1; }
# absent store → reported as none, still nothing created
wire_out5=$(wt_wire "$WT" "$MAIN" "$CANON" "$W/nope" 2>&1)
echo "$wire_out5" | grep -q 'artifacts: none' && echo "ok wire_artifacts_absent" || { echo "FAIL wire_artifacts_absent: $wire_out5"; fail=1; }
HOME="$HOME_BAK"; rm -rf "$W"

# wt_check: real git repo fixture — sibling worktrees/ layout
W=$(mktemp -d); HOME_BAK="$HOME"; HOME="$W/ch"; mkdir -p "$HOME"
MAIN="$W/repo"
mkdir -p "$MAIN"; git -C "$MAIN" init -q
# .claude/ ignored so the fixture's own scaffolding does not confound the status assertion below
printf 'CLAUDE.md\nCLAUDE.local.md\n.claude/\n' > "$MAIN/.gitignore"
git -C "$MAIN" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN" -c user.email=t@t -c user.name=t commit -qm init
WT_CHK="$W/worktrees/RE-1"
git -C "$MAIN" worktree add -b RE-1 "$WT_CHK" HEAD -q 2>/dev/null
mkdir -p "$W/artifacts/sdkA"
CANON_CHK=$(HOME="$W/ch" canonical_dir "$MAIN")
mkdir -p "$CANON_CHK/memory"
mkdir -p "$MAIN/.claude"; echo '{}' > "$MAIN/.claude/settings.local.json"
wt_wire "$WT_CHK" "$MAIN" "$CANON_CHK"
out=$(wt_check "$WT_CHK" "$CANON_CHK")
echo "$out" | grep -q 'brain.*OK'    && echo "ok check_brain"  || { echo "FAIL check_brain: $out";  fail=1; }
echo "$out" | grep -q 'bridge.*OK'   && echo "ok check_bridge" || { echo "FAIL check_bridge: $out"; fail=1; }
echo "$out" | grep -q 'nest.*OK'     && echo "ok check_nest"   || { echo "FAIL check_nest: $out";   fail=1; }
echo "$out" | grep -q 'settings.*OK' && echo "ok check_set"    || { echo "FAIL check_set: $out";    fail=1; }
echo "$out" | grep -q 'artifacts: OK' && echo "ok check_artifacts" || { echo "FAIL check_artifacts: $out"; fail=1; }
# serena is gone from the skill — wt_check must not emit a serena line at all
echo "$out" | grep -qi 'serena' && { echo "FAIL check_no_serena_line: $out"; fail=1; } || echo "ok check_no_serena_line"
# G1: wt_check must report memory: OK (own bucket) — real dir, not symlink
echo "$out" | grep -q 'memory.*OK.*own bucket' && echo "ok check_memory_own_bucket" || { echo "FAIL check_memory_own_bucket: $out"; fail=1; }
# a worktree beside the repo must never dirty the main clone's git status (no ignore rule needed)
CHK_STATUS=$(git -C "$MAIN" status --porcelain 2>/dev/null)
[ -z "$CHK_STATUS" ] && echo "ok check_main_status_clean" || { echo "FAIL check_main_status_clean: $CHK_STATUS"; fail=1; }
# regression: a symlinked .claude must report FAIL — it breaks the bwrap sandbox (EISDIR)
rm -rf "$WT_CHK/.claude"; ln -s "$MAIN/.claude" "$WT_CHK/.claude"
wt_check "$WT_CHK" "$CANON_CHK" | grep -q 'settings.*FAIL' && echo "ok check_set_symlink" || { echo FAIL check_set_symlink; fail=1; }
HOME="$HOME_BAK"; rm -rf "$W"

# wt_check nest: the LEGACY in-repo path <repo>/.worktrees/<branch> must now FAIL
W_LG=$(mktemp -d); HOME_BAK_LG="$HOME"; HOME="$W_LG/h"; mkdir -p "$HOME"
MAIN_LG="$W_LG/repo"
mkdir -p "$MAIN_LG"; git -C "$MAIN_LG" init -q
printf '/.worktrees/\nCLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_LG/.gitignore"
git -C "$MAIN_LG" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_LG" -c user.email=t@t -c user.name=t commit -qm init
WT_LG="$MAIN_LG/.worktrees/legacy"
git -C "$MAIN_LG" worktree add -b legacy "$WT_LG" HEAD -q 2>/dev/null
CANON_LG="$W_LG/h/.claude/projects/$(wt_key "$MAIN_LG")"
mkdir -p "$CANON_LG/memory" "$MAIN_LG/.claude" "$WT_LG/.claude"
touch "$MAIN_LG/CLAUDE.md" "$MAIN_LG/CLAUDE.local.md"
mkdir -p "$HOME/.claude/projects/$(wt_key "$WT_LG")/memory"
out_lg=$(wt_check "$WT_LG" "$CANON_LG" 2>/dev/null)
echo "$out_lg" | grep -q 'nest: FAIL' && echo "ok check_legacy_nest_fails" || { echo "FAIL check_legacy_nest_fails: $out_lg"; fail=1; }
HOME="$HOME_BAK_LG"; rm -rf "$W_LG"

# wt_add: sibling path test — worktree lands at <project>/worktrees/<branch>, status clean
W=$(mktemp -d); HOME_BAK="$HOME"; HOME="$W/ch"; mkdir -p "$HOME"
ADDMAIN="$W/addrepo"
mkdir -p "$ADDMAIN"; git -C "$ADDMAIN" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$ADDMAIN/.gitignore"
git -C "$ADDMAIN" -c user.email=t@t -c user.name=t add .gitignore
git -C "$ADDMAIN" -c user.email=t@t -c user.name=t commit -qm init
wt_add "$ADDMAIN" addtest HEAD >/dev/null 2>&1
EXPECTED_WT="$W/worktrees/addtest"
[ -d "$EXPECTED_WT" ] && echo "ok wt_add_sibling_path" || { echo "FAIL wt_add_sibling_path (dir $EXPECTED_WT missing)"; fail=1; }
[ ! -e "$ADDMAIN/.worktrees" ] && echo "ok wt_add_nothing_inside_repo" || { echo "FAIL wt_add_nothing_inside_repo (.worktrees created inside the repo)"; fail=1; }
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
mkdir -p "$W/repo"; git -C "$W/repo" init -q; git -C "$W/repo" commit --allow-empty -q -m init
WT_R="$W/worktrees/test-remove-br"
git -C "$W/repo" worktree add -b test-remove-br "$WT_R" HEAD -q 2>/dev/null
HOME="$W/ch"; mkdir -p "$HOME"
source "$HERE/helpers.sh"   # reload with new functions — use $HERE (absolute), not ~, since HOME is overridden
wt_remove "$W/repo" "$WT_R" >/dev/null 2>&1
[ ! -d "$WT_R" ] && echo "ok wt_remove_dir_gone" || { echo FAIL wt_remove_dir_gone; fail=1; }
HOME="$HOME_BAK"; rm -rf "$W"

# wt_preflight_mounts: rc=0 when /proc/mounts has no unreachable /mnt entries
# (In CI / test environment there may be no /mnt mounts — function should still exit 0.)
wt_preflight_mounts >/dev/null 2>&1 && echo "ok preflight_rc0" || { echo FAIL preflight_rc0; fail=1; }

# serena removal: neither serena helper may exist, and the file must not mention serena at all
for _fn in wt_serena_prestage wt_serena_deregister; do
  if command -v "$_fn" >/dev/null 2>&1; then echo "FAIL serena_helper_removed_$_fn (still defined)"; fail=1
  else echo "ok serena_helper_removed_$_fn"; fi
done
grep -qi 'serena' "$HERE/helpers.sh" && { echo "FAIL helpers_no_serena_mentions"; fail=1; } || echo "ok helpers_no_serena_mentions"

# wire_context_template: WT_TICKET set → CLAUDE.local.md contains Ticket: RE-1
W_CTX=$(mktemp -d); HOME_BAK4="$HOME"; HOME="$W_CTX/ch"; mkdir -p "$HOME"
MAIN_CTX="$W_CTX/repo"
mkdir -p "$MAIN_CTX"; git -C "$MAIN_CTX" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_CTX/.gitignore"
git -C "$MAIN_CTX" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_CTX" -c user.email=t@t -c user.name=t commit -qm init
WT_CTX="$W_CTX/worktrees/ctx-test"
git -C "$MAIN_CTX" worktree add -b ctx-test "$WT_CTX" HEAD -q 2>/dev/null
CANON_CTX="$W_CTX/ch/.claude/projects/$(wt_key "$MAIN_CTX")"
mkdir -p "$CANON_CTX/memory"
mkdir -p "$MAIN_CTX/.claude"
WT_TICKET="RE-1" WT_PURPOSE="test purpose" WT_HANDOFF="" wt_wire "$WT_CTX" "$MAIN_CTX" "$CANON_CTX" >/dev/null 2>&1
grep -q "Ticket: RE-1" "$WT_CTX/CLAUDE.local.md" && echo "ok wire_context_template" || { echo "FAIL wire_context_template: $(cat "$WT_CTX/CLAUDE.local.md")"; fail=1; }
HOME="$HOME_BAK4"; rm -rf "$W_CTX"

# wire_context_empty: no env vars → CLAUDE.local.md is empty
W_EMP=$(mktemp -d); HOME_BAK5="$HOME"; HOME="$W_EMP/ch"; mkdir -p "$HOME"
MAIN_EMP="$W_EMP/repo"
mkdir -p "$MAIN_EMP"; git -C "$MAIN_EMP" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_EMP/.gitignore"
git -C "$MAIN_EMP" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_EMP" -c user.email=t@t -c user.name=t commit -qm init
WT_EMP="$W_EMP/worktrees/emp-test"
git -C "$MAIN_EMP" worktree add -b emp-test "$WT_EMP" HEAD -q 2>/dev/null
CANON_EMP="$W_EMP/ch/.claude/projects/$(wt_key "$MAIN_EMP")"
mkdir -p "$CANON_EMP/memory"
mkdir -p "$MAIN_EMP/.claude"
unset WT_TICKET WT_PURPOSE WT_HANDOFF
wt_wire "$WT_EMP" "$MAIN_EMP" "$CANON_EMP" >/dev/null 2>&1
[ ! -s "$WT_EMP/CLAUDE.local.md" ] && echo "ok wire_context_empty" || { echo "FAIL wire_context_empty: $(cat "$WT_EMP/CLAUDE.local.md")"; fail=1; }
HOME="$HOME_BAK5"; rm -rf "$W_EMP"

# ── Task 2: lifecycle modes ──────────────────────────────────────────────────

# ── archive_revive_roundtrip ─────────────────────────────────────────────────
W_AR=$(mktemp -d); HOME_BAK_AR="$HOME"; HOME="$W_AR/h"; mkdir -p "$HOME"
MAIN_AR="$W_AR/repo"
mkdir -p "$MAIN_AR"; git -C "$MAIN_AR" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_AR/.gitignore"
git -C "$MAIN_AR" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_AR" -c user.email=t@t -c user.name=t commit -qm init
WT_AR="$W_AR/worktrees/arc-test"
git -C "$MAIN_AR" worktree add -b arc-test "$WT_AR" HEAD -q 2>/dev/null
# Put an uncommitted file in the worktree
echo "uncommitted" > "$WT_AR/dirty.txt"

# wt_archive → dir at <project>/worktrees/_archive/<br>
(HOME="$HOME" wt_archive "$MAIN_AR" "$WT_AR") >/dev/null 2>&1
arch_path="$W_AR/worktrees/_archive/arc-test"
[ -d "$arch_path" ] && echo "ok archive_dir_moved" || { echo "FAIL archive_dir_moved: $arch_path missing"; fail=1; }
# git worktree list shows it locked
lock_out=$(git -C "$MAIN_AR" worktree list --porcelain 2>/dev/null)
echo "$lock_out" | grep -A5 "worktree $arch_path" | grep -q "locked" \
  && echo "ok archive_locked" || { echo "FAIL archive_locked"; fail=1; }
# original wt path gone
[ ! -d "$WT_AR" ] && echo "ok archive_orig_gone" || { echo "FAIL archive_orig_gone: $WT_AR still exists"; fail=1; }
# uncommitted file preserved in archive
[ -f "$arch_path/dirty.txt" ] && echo "ok archive_uncommitted_preserved" || { echo "FAIL archive_uncommitted_preserved"; fail=1; }
# index.tsv lives under the worktrees root, beside _archive
[ -f "$W_AR/worktrees/_archive/index.tsv" ] && echo "ok archive_index_location" || { echo "FAIL archive_index_location"; fail=1; }
# nothing was written inside the repo
[ ! -e "$MAIN_AR/.worktrees" ] && echo "ok archive_nothing_in_repo" || { echo "FAIL archive_nothing_in_repo"; fail=1; }

# wt_revive → dir back at <project>/worktrees/<br>, not locked, file present
(HOME="$HOME" wt_revive "$MAIN_AR" "arc-test") >/dev/null 2>&1
[ -d "$WT_AR" ] && echo "ok revive_dir_back" || { echo "FAIL revive_dir_back: $WT_AR missing"; fail=1; }
# not locked (lock attribute absent from porcelain for this entry)
revive_lock=$(git -C "$MAIN_AR" worktree list --porcelain 2>/dev/null | grep -A5 "worktree $WT_AR" | grep "locked" || echo "")
[ -z "$revive_lock" ] && echo "ok revive_not_locked" || { echo "FAIL revive_not_locked: $revive_lock"; fail=1; }
[ -f "$WT_AR/dirty.txt" ] && echo "ok revive_file_preserved" || { echo "FAIL revive_file_preserved"; fail=1; }
# index row removed (header survives)
if grep -q '^arc-test	' "$W_AR/worktrees/_archive/index.tsv"; then echo "FAIL revive_index_row_removed"; fail=1; else echo "ok revive_index_row_removed"; fi
HOME="$HOME_BAK_AR"; rm -rf "$W_AR"

# ── archive_refuses_existing_target ─────────────────────────────────────────
W_AE=$(mktemp -d); HOME_BAK_AE="$HOME"; HOME="$W_AE/h"; mkdir -p "$HOME"
MAIN_AE="$W_AE/repo"
mkdir -p "$MAIN_AE"; git -C "$MAIN_AE" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_AE/.gitignore"
git -C "$MAIN_AE" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_AE" -c user.email=t@t -c user.name=t commit -qm init
WT_AE="$W_AE/worktrees/arc-exist"
git -C "$MAIN_AE" worktree add -b arc-exist "$WT_AE" HEAD -q 2>/dev/null
# Pre-create the archive target
mkdir -p "$W_AE/worktrees/_archive/arc-exist"
(HOME="$HOME" wt_archive "$MAIN_AE" "$WT_AE") >/dev/null 2>&1; rc_ae=$?
[ "$rc_ae" != "0" ] && echo "ok archive_refuses_existing" || { echo "FAIL archive_refuses_existing: should have returned non-zero"; fail=1; }
HOME="$HOME_BAK_AE"; rm -rf "$W_AE"

# ── reap_merged ──────────────────────────────────────────────────────────────
W_RM=$(mktemp -d); HOME_BAK_RM="$HOME"; HOME="$W_RM/h"; mkdir -p "$HOME"
MAIN_RM="$W_RM/repo"
mkdir -p "$MAIN_RM"; git -C "$MAIN_RM" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_RM/.gitignore"
git -C "$MAIN_RM" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RM" -c user.email=t@t -c user.name=t commit -qm init
WT_RM="$W_RM/worktrees/reap-merged"
git -C "$MAIN_RM" worktree add -b reap-merged "$WT_RM" HEAD -q 2>/dev/null
# Make a commit on the branch, then merge it into main
echo "feature" > "$WT_RM/feat.txt"
git -C "$WT_RM" add feat.txt
git -C "$WT_RM" -c user.email=t@t -c user.name=t commit -qm "feat: add feature"
git -C "$MAIN_RM" merge --no-edit reap-merged -q 2>/dev/null
# Run reap with WT_ASSUME_YES=1 to skip interactive prompt
(HOME="$HOME" WT_ASSUME_YES=1 wt_reap "$MAIN_RM" "$WT_RM") >/dev/null 2>&1; rc_rm=$?
[ "$rc_rm" = "0" ] && echo "ok reap_merged_rc0" || { echo "FAIL reap_merged_rc0: rc=$rc_rm"; fail=1; }
# wt dir gone
[ ! -d "$WT_RM" ] && echo "ok reap_merged_dir_gone" || { echo "FAIL reap_merged_dir_gone"; fail=1; }
# manifest preserved at <project>/history/reaped/<branch>.reap-manifest.md
manifest_rm="$W_RM/history/reaped/reap-merged.reap-manifest.md"
[ -f "$manifest_rm" ] && echo "ok reap_merged_manifest_in_history" || { echo "FAIL reap_merged_manifest_in_history: $manifest_rm not found"; fail=1; }
[ -f "$manifest_rm" ] && grep -q "^branch: reap-merged" "$manifest_rm" && echo "ok reap_merged_manifest_branch" || { echo "FAIL reap_merged_manifest_branch"; fail=1; }
# D2: manifest contains candidates: YAML block (may be empty list if no memories written)
[ -f "$manifest_rm" ] && grep -q '^candidates:' "$manifest_rm" && echo "ok reap_merged_manifest_candidates" || { echo "FAIL reap_merged_manifest_candidates (no candidates: key in manifest)"; fail=1; }
# nothing written inside the repo
[ ! -e "$MAIN_RM/.worktrees" ] && echo "ok reap_merged_nothing_in_repo" || { echo "FAIL reap_merged_nothing_in_repo"; fail=1; }
HOME="$HOME_BAK_RM"; rm -rf "$W_RM"

# ── reap_unmerged_aborts ─────────────────────────────────────────────────────
W_RU=$(mktemp -d); HOME_BAK_RU="$HOME"; HOME="$W_RU/h"; mkdir -p "$HOME"
MAIN_RU="$W_RU/repo"
mkdir -p "$MAIN_RU"; git -C "$MAIN_RU" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_RU/.gitignore"
git -C "$MAIN_RU" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RU" -c user.email=t@t -c user.name=t commit -qm init
WT_RU="$W_RU/worktrees/reap-unmerged"
git -C "$MAIN_RU" worktree add -b reap-unmerged "$WT_RU" HEAD -q 2>/dev/null
# A commit on the branch NOT merged
echo "unmerged" > "$WT_RU/new.txt"
git -C "$WT_RU" add new.txt
git -C "$WT_RU" -c user.email=t@t -c user.name=t commit -qm "feat: unmerged"
(HOME="$HOME" wt_reap "$MAIN_RU" "$WT_RU") >/dev/null 2>&1; rc_ru=$?
[ "$rc_ru" != "0" ] && echo "ok reap_unmerged_aborts" || { echo "FAIL reap_unmerged_aborts: should have returned non-zero"; fail=1; }
[ -d "$WT_RU" ] && echo "ok reap_unmerged_wt_present" || { echo "FAIL reap_unmerged_wt_present: wt was removed"; fail=1; }
HOME="$HOME_BAK_RU"; rm -rf "$W_RU"

# ── reap_force_overrides ─────────────────────────────────────────────────────
W_RF=$(mktemp -d); HOME_BAK_RF="$HOME"; HOME="$W_RF/h"; mkdir -p "$HOME"
MAIN_RF="$W_RF/repo"
mkdir -p "$MAIN_RF"; git -C "$MAIN_RF" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_RF/.gitignore"
git -C "$MAIN_RF" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RF" -c user.email=t@t -c user.name=t commit -qm init
WT_RF="$W_RF/worktrees/reap-force"
git -C "$MAIN_RF" worktree add -b reap-force "$WT_RF" HEAD -q 2>/dev/null
echo "unmerged" > "$WT_RF/new.txt"
git -C "$WT_RF" add new.txt
git -C "$WT_RF" -c user.email=t@t -c user.name=t commit -qm "feat: unmerged"
(HOME="$HOME" WT_ASSUME_YES=1 wt_reap "$MAIN_RF" "$WT_RF" --force) >/dev/null 2>&1; rc_rf=$?
[ "$rc_rf" = "0" ] && echo "ok reap_force_rc0" || { echo "FAIL reap_force_rc0: rc=$rc_rf"; fail=1; }
[ ! -d "$WT_RF" ] && echo "ok reap_force_wt_gone" || { echo "FAIL reap_force_wt_gone"; fail=1; }
HOME="$HOME_BAK_RF"; rm -rf "$W_RF"

# ── reap_dirty_aborts ────────────────────────────────────────────────────────
W_RD=$(mktemp -d); HOME_BAK_RD="$HOME"; HOME="$W_RD/h"; mkdir -p "$HOME"
MAIN_RD="$W_RD/repo"
mkdir -p "$MAIN_RD"; git -C "$MAIN_RD" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_RD/.gitignore"
git -C "$MAIN_RD" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_RD" -c user.email=t@t -c user.name=t commit -qm init
WT_RD="$W_RD/worktrees/reap-dirty"
git -C "$MAIN_RD" worktree add -b reap-dirty "$WT_RD" HEAD -q 2>/dev/null
# Merge the branch first so merge gate passes
git -C "$MAIN_RD" merge --no-edit reap-dirty -q 2>/dev/null
# Now add an uncommitted file
echo "dirty" > "$WT_RD/dirty.txt"
(HOME="$HOME" wt_reap "$MAIN_RD" "$WT_RD") >/dev/null 2>&1; rc_rd=$?
[ "$rc_rd" != "0" ] && echo "ok reap_dirty_aborts" || { echo "FAIL reap_dirty_aborts: should have returned non-zero"; fail=1; }
[ -d "$WT_RD" ] && echo "ok reap_dirty_wt_present" || { echo "FAIL reap_dirty_wt_present: wt was removed"; fail=1; }
HOME="$HOME_BAK_RD"; rm -rf "$W_RD"

# ── fix2: wt_add with slashed branch feat/x ─────────────────────────────────
W_SL=$(mktemp -d); HOME_BAK_SL="$HOME"; HOME="$W_SL/h"; mkdir -p "$HOME"
MAIN_SL="$W_SL/repo"
mkdir -p "$MAIN_SL"; git -C "$MAIN_SL" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_SL/.gitignore"
git -C "$MAIN_SL" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_SL" -c user.email=t@t -c user.name=t commit -qm init
# artifacts store present so the deeper (../../../) relative walk-up is exercised
mkdir -p "$W_SL/artifacts/sdkS"
(HOME="$HOME" wt_add "$MAIN_SL" "feat/x" HEAD) >/dev/null 2>&1
EXPECTED_SL="$W_SL/worktrees/feat/x"
[ -d "$EXPECTED_SL" ] && echo "ok wt_add_slashed_branch" || { echo "FAIL wt_add_slashed_branch (dir $EXPECTED_SL missing)"; fail=1; }
# a slashed branch sits one level deeper — the relative walk-up must still reach artifacts
CANON_SL="$W_SL/h/.claude/projects/$(wt_key "$MAIN_SL")"
out_sl=$(HOME="$HOME" wt_check "$EXPECTED_SL" "$CANON_SL" 2>/dev/null)
echo "$out_sl" | grep -q 'artifacts: OK' && echo "ok slashed_artifacts_reachable" || { echo "FAIL slashed_artifacts_reachable: $out_sl"; fail=1; }
echo "$out_sl" | grep -q 'nest: OK' && echo "ok slashed_nest_ok" || { echo "FAIL slashed_nest_ok: $out_sl"; fail=1; }
HOME="$HOME_BAK_SL"; rm -rf "$W_SL"

# ── fix3: wt_reap refuses main clone (wt == main) ────────────────────────────
W_F3=$(mktemp -d); HOME_BAK_F3="$HOME"; HOME="$W_F3/h"; mkdir -p "$HOME"
MAIN_F3="$W_F3/repo"
mkdir -p "$MAIN_F3"; git -C "$MAIN_F3" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_F3/.gitignore"
git -C "$MAIN_F3" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_F3" -c user.email=t@t -c user.name=t commit -qm init
(HOME="$HOME" wt_reap "$MAIN_F3" "$MAIN_F3") >/dev/null 2>&1; rc_f3=$?
[ "$rc_f3" != "0" ] && echo "ok reap_refuses_main_clone" || { echo "FAIL reap_refuses_main_clone: should return non-zero when wt==main"; fail=1; }
[ -d "$MAIN_F3" ] && echo "ok reap_refuses_main_not_deleted" || { echo "FAIL reap_refuses_main_not_deleted"; fail=1; }
HOME="$HOME_BAK_F3"; rm -rf "$W_F3"

# ── no-symlink regression: wt_wire must not touch git's info/exclude at all ──
# (The old implementation appended '/artifacts/' there to hide the symlink farm. With a plain
#  relative path nothing lands inside the worktree, so exclude must stay byte-identical.)
W_EX=$(mktemp -d); HOME_BAK_EX="$HOME"; HOME="$W_EX/h"; mkdir -p "$HOME"
MAIN_EX="$W_EX/repo"
mkdir -p "$MAIN_EX"; git -C "$MAIN_EX" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_EX/.gitignore"
git -C "$MAIN_EX" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_EX" -c user.email=t@t -c user.name=t commit -qm init
WT_EX="$W_EX/worktrees/ex-test"
git -C "$MAIN_EX" worktree add -b ex-test "$WT_EX" HEAD -q 2>/dev/null
EXCL_EX="$(git -C "$WT_EX" rev-parse --git-common-dir 2>/dev/null)/info/exclude"
mkdir -p "$(dirname "$EXCL_EX")"; printf 'node_modules/\n' > "$EXCL_EX"
excl_before=$(cat "$EXCL_EX")
mkdir -p "$W_EX/artifacts/sdkX"
CANON_EX="$W_EX/h/.claude/projects/$(wt_key "$MAIN_EX")"
mkdir -p "$CANON_EX/memory" "$MAIN_EX/.claude"
(HOME="$HOME" wt_wire "$WT_EX" "$MAIN_EX" "$CANON_EX") >/dev/null 2>&1
[ "$(cat "$EXCL_EX")" = "$excl_before" ] && echo "ok wire_leaves_exclude_untouched" || { echo "FAIL wire_leaves_exclude_untouched: $(cat "$EXCL_EX")"; fail=1; }
if grep -qF '/artifacts/' "$EXCL_EX"; then echo "FAIL wire_no_artifacts_exclude_entry"; fail=1; else echo "ok wire_no_artifacts_exclude_entry"; fi
HOME="$HOME_BAK_EX"; rm -rf "$W_EX"

# ── fix1: wt_reap returns non-zero when wt_remove fails ──────────────────────
W_F1=$(mktemp -d); HOME_BAK_F1="$HOME"; HOME="$W_F1/h"; mkdir -p "$HOME"
MAIN_F1="$W_F1/repo"
mkdir -p "$MAIN_F1"; git -C "$MAIN_F1" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_F1/.gitignore"
git -C "$MAIN_F1" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_F1" -c user.email=t@t -c user.name=t commit -qm init
WT_F1="$W_F1/worktrees/fix1-test"
git -C "$MAIN_F1" worktree add -b fix1-test "$WT_F1" HEAD -q 2>/dev/null
git -C "$MAIN_F1" merge --no-edit fix1-test -q 2>/dev/null
mkdir -p "$HOME/.claude/projects/$(wt_key "$WT_F1")/memory"
# Shadow wt_remove with an always-failing stub inside a subshell
(
  HOME="$HOME"
  wt_remove() { printf 'wt_remove: SIMULATED FAILURE\n' >&2; return 1; }
  WT_ASSUME_YES=1 wt_reap "$MAIN_F1" "$WT_F1"
) >/dev/null 2>&1; rc_f1=$?
[ "$rc_f1" != "0" ] && echo "ok fix1_reap_rc_nonzero_on_remove_fail" || { echo "FAIL fix1_reap_rc_nonzero_on_remove_fail: expected non-zero"; fail=1; }
# the worktree's memory bucket must survive a failed removal
[ -d "$HOME/.claude/projects/$(wt_key "$WT_F1")" ] && echo "ok fix1_memory_preserved_on_remove_fail" || { echo "FAIL fix1_memory_preserved_on_remove_fail"; fail=1; }
HOME="$HOME_BAK_F1"; rm -rf "$W_F1"

# ── D2: wt_reap_promote YAML manifest with candidates (claude store only) ─────
W_D2=$(mktemp -d); HOME_BAK_D2="$HOME"; HOME="$W_D2/h"; mkdir -p "$HOME"
MAIN_D2="$W_D2/repo"
mkdir -p "$MAIN_D2"; git -C "$MAIN_D2" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_D2/.gitignore"
git -C "$MAIN_D2" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_D2" -c user.email=t@t -c user.name=t commit -qm init
WT_D2="$W_D2/worktrees/d2-test"
git -C "$MAIN_D2" worktree add -b d2-test "$WT_D2" HEAD -q 2>/dev/null
# Seed the worktree's claude bucket: one colliding note, one fresh note
_wt_key_d2="$HOME/.claude/projects/$(wt_key "$WT_D2")/memory"
mkdir -p "$_wt_key_d2"
printf '%s\n' '---' 'type: feedback' '---' 'claude content' > "$_wt_key_d2/cl_note.md"
printf '%s\n' '---' 'type: reference' '---' 'fresh content' > "$_wt_key_d2/fresh_note.md"
# Seed parent dest with cl_note.md only → collision for cl_note, none for fresh_note
mkdir -p "$HOME/.claude/projects/$(wt_key "$MAIN_D2")/memory"
printf 'parent content\n' > "$HOME/.claude/projects/$(wt_key "$MAIN_D2")/memory/cl_note.md"
(HOME="$HOME" wt_reap_promote "$WT_D2" "$MAIN_D2") >/dev/null 2>&1
mf_d2="$WT_D2/.reap-manifest.md"
[ -f "$mf_d2" ] && echo "ok d2_manifest_exists" || { echo "FAIL d2_manifest_exists"; fail=1; }
grep -q '^candidates:' "$mf_d2" && echo "ok d2_candidates_key" || { echo "FAIL d2_candidates_key"; fail=1; }
grep -q 'store: claude' "$mf_d2" && echo "ok d2_claude_entry" || { echo "FAIL d2_claude_entry"; fail=1; }
# serena is gone — no serena-store candidate may ever appear
if grep -q 'store: serena' "$mf_d2"; then echo "FAIL d2_no_serena_entry"; fail=1; else echo "ok d2_no_serena_entry"; fi
# cl_note collision must point at a real path (not 'none')
grep -q 'collision:.*cl_note' "$mf_d2" && echo "ok d2_collision_detected" || { echo "FAIL d2_collision_detected (no collision line containing cl_note)"; fail=1; }
# fresh_note has no parent counterpart → collision: none
grep -q 'collision: none' "$mf_d2" && echo "ok d2_no_collision_fresh" || { echo "FAIL d2_no_collision_fresh (no collision: none line found)"; fail=1; }
# proposed: {} must be present for each candidate
count_proposed=$(grep -c '^    proposed: {}' "$mf_d2" 2>/dev/null || echo 0)
[ "$count_proposed" = "2" ] && echo "ok d2_proposed_empty" || { echo "FAIL d2_proposed_empty: count=$count_proposed (expected 2)"; fail=1; }
# Must NOT contain 'base:' anywhere
if grep -q '^base:' "$mf_d2"; then echo "FAIL d2_no_base_field (base: found in manifest)"; fail=1; else echo "ok d2_no_base_field"; fi
HOME="$HOME_BAK_D2"; rm -rf "$W_D2"

# ── wt_check artifacts: empty store dir is still OK; absent store is NA ──────
W_F7=$(mktemp -d); HOME_BAK_F7="$HOME"; HOME="$W_F7/h"; mkdir -p "$HOME"
MAIN_F7="$W_F7/repo"
mkdir -p "$MAIN_F7"; git -C "$MAIN_F7" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_F7/.gitignore"
git -C "$MAIN_F7" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_F7" -c user.email=t@t -c user.name=t commit -qm init
WT_F7="$W_F7/worktrees/f7-test"
git -C "$MAIN_F7" worktree add -b f7-test "$WT_F7" HEAD -q 2>/dev/null
CANON_F7="$W_F7/h/.claude/projects/$(wt_key "$MAIN_F7")"
mkdir -p "$CANON_F7/memory" "$MAIN_F7/.claude" "$WT_F7/.claude"
touch "$MAIN_F7/CLAUDE.md" "$MAIN_F7/CLAUDE.local.md"
mkdir -p "$HOME/.claude/projects/$(wt_key "$WT_F7")/memory"
# store dir exists but is empty
mkdir -p "$W_F7/artifacts"
out_f7=$(wt_check "$WT_F7" "$CANON_F7" 2>/dev/null)
echo "$out_f7" | grep -q 'artifacts: OK' && echo "ok empty_artifacts_ok" || { echo "FAIL empty_artifacts_ok: $out_f7"; fail=1; }
# remove the store → NA, not FAIL (artifacts are optional)
rmdir "$W_F7/artifacts"
out_f7b=$(wt_check "$WT_F7" "$CANON_F7" 2>/dev/null)
echo "$out_f7b" | grep -q 'artifacts: NA' && echo "ok absent_artifacts_na" || { echo "FAIL absent_artifacts_na: $out_f7b"; fail=1; }
HOME="$HOME_BAK_F7"; rm -rf "$W_F7"

# ── wt_check artifacts: store exists but worktree cannot reach it relatively ──
# (Replaces the old broken-symlink probe: with no symlinks, the only artifacts failure mode
#  is a worktree parked outside the project tree.)
W_UR=$(mktemp -d); W_STRAY=$(mktemp -d); HOME_BAK_UR="$HOME"; HOME="$W_UR/h"; mkdir -p "$HOME"
MAIN_UR="$W_UR/repo"
mkdir -p "$MAIN_UR"; git -C "$MAIN_UR" init -q
printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_UR/.gitignore"
git -C "$MAIN_UR" -c user.email=t@t -c user.name=t add .gitignore
git -C "$MAIN_UR" -c user.email=t@t -c user.name=t commit -qm init
mkdir -p "$W_UR/artifacts/sdkA"
WT_UR="$W_STRAY/worktrees/stray"
git -C "$MAIN_UR" worktree add -b stray "$WT_UR" HEAD -q 2>/dev/null
CANON_UR="$W_UR/h/.claude/projects/$(wt_key "$MAIN_UR")"
mkdir -p "$CANON_UR/memory" "$MAIN_UR/.claude" "$WT_UR/.claude"
touch "$MAIN_UR/CLAUDE.md" "$MAIN_UR/CLAUDE.local.md"
mkdir -p "$HOME/.claude/projects/$(wt_key "$WT_UR")/memory"
out_ur=$(wt_check "$WT_UR" "$CANON_UR" 2>/dev/null)
echo "$out_ur" | grep -q 'artifacts: FAIL' && echo "ok unreachable_artifacts_flagged" || { echo "FAIL unreachable_artifacts_flagged: $out_ur"; fail=1; }
HOME="$HOME_BAK_UR"; rm -rf "$W_UR" "$W_STRAY"

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
  printf 'CLAUDE.md\nCLAUDE.local.md\n' > "$MAIN_Z/.gitignore"
  git -C "$MAIN_Z" -c user.email=t@t -c user.name=t add .gitignore
  git -C "$MAIN_Z" -c user.email=t@t -c user.name=t commit -qm init
  mkdir -p "$W_Z/artifacts/sdkZ"
  zsh -f -c "source '$HERE/helpers.sh' && wt_add --ticket Z-9 '$MAIN_Z' ztest HEAD" >/dev/null 2>&1
  [ -d "$W_Z/worktrees/ztest" ] && echo "ok zsh_wt_add_positionals" || { echo "FAIL zsh_wt_add_positionals"; fail=1; }
  grep -q 'Ticket: Z-9' "$W_Z/worktrees/ztest/CLAUDE.local.md" 2>/dev/null && echo "ok zsh_wt_add_ticket_flag" || { echo "FAIL zsh_wt_add_ticket_flag"; fail=1; }
  HOME="$HOME_BAK_Z"; rm -rf "$W_Z"
else
  echo "skip zsh portability tests (zsh not found)"
fi

exit $fail
