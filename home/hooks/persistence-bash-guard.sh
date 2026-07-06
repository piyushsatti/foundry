#!/usr/bin/env bash
# PreToolUse Bash — surface "ask" prompt for Bash commands that WRITE to
# persistence / lateral-movement paths via redirects, cp, mv, tee, dd, install, ln.
# Closes the indirect-write gap that persistence-guard.sh (Write/Edit) leaves open.

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

H="$HOME"

# Normalize redirect forms: insert spaces around >, >>, >|, &>, &>>, and after `cmd>path`
# so the tokenizer sees them as separate tokens. Done in a temp variable to avoid
# disturbing the original command stored in audit logs.
NORM=$(printf '%s' "$CMD" | sed -E '
  s/&>>/ \&>> /g
  s/&>/ \&> /g
  s/>\|/ >| /g
  s/>>/ >> /g
  s/([^>])>([^>|])/\1 > \2/g
  s/^>([^>|])/> \1/
')

# Match a path against the persistence path list. Returns 0 if match.
matches_persistence() {
  local p="$1"
  case "$p" in
    "$H"/.ssh/authorized_keys|"$H"/.ssh/authorized_keys2|"$H"/.ssh/config|"$H"/.ssh/known_hosts) return 0 ;;
    "$H"/.bashrc|"$H"/.bash_profile|"$H"/.bash_login|"$H"/.bash_logout|"$H"/.profile|"$H"/.inputrc) return 0 ;;
    "$H"/.zshrc|"$H"/.zshenv|"$H"/.zprofile|"$H"/.zlogin|"$H"/.zlogout) return 0 ;;
    "$H"/.kshrc|"$H"/.cshrc|"$H"/.tcshrc) return 0 ;;
    "$H"/.config/fish/config.fish|"$H"/.config/fish/conf.d/*|"$H"/.config/fish/functions/*) return 0 ;;
    "$H"/.gitconfig|"$H"/.config/git/config|"$H"/.config/git/attributes) return 0 ;;
    */.git/hooks/*) return 0 ;;
    */.git/config) return 0 ;;
    "$H"/.config/systemd/user/*|"$H"/.config/autostart/*|"$H"/.config/environment.d/*) return 0 ;;
    "$H"/.local/bin/*|"$H"/bin/*) return 0 ;;
    "$H"/.npmrc|"$H"/.yarnrc|"$H"/.yarnrc.yml|"$H"/.pypirc|"$H"/.pip/pip.conf|"$H"/.config/pip/pip.conf|"$H"/.gemrc|"$H"/.cargo/config|"$H"/.cargo/config.toml|"$H"/.docker/config.json) return 0 ;;
    "$H"/.netrc|"$H"/.pgpass|"$H"/.git-credentials) return 0 ;;
    "$H"/.vimrc|"$H"/.vim/vimrc|"$H"/.config/nvim/init.lua|"$H"/.config/nvim/init.vim|"$H"/.config/nvim/lua/*) return 0 ;;
    "$H"/.xinitrc|"$H"/.xsession|"$H"/.xprofile) return 0 ;;
    /etc/cron*|/etc/systemd/*|/etc/profile.d/*|/etc/init.d/*|/etc/rc.local|/etc/pam.d/*|/etc/sudoers*|/etc/passwd|/etc/shadow|/etc/group|/etc/hosts) return 0 ;;
  esac
  return 1
}

# Match a directory path (no trailing slash needed) against persistence directory roots
# used for -t / --target-directory parsing.
matches_persistence_dir() {
  local d="${1%/}"
  case "$d" in
    "$H"/.ssh|"$H"/.local/bin|"$H"/bin) return 0 ;;
    "$H"/.config/systemd/user|"$H"/.config/autostart|"$H"/.config/environment.d) return 0 ;;
    "$H"/.config/fish/conf.d|"$H"/.config/fish/functions) return 0 ;;
    "$H"/.config/nvim/lua) return 0 ;;
    "$H"/.vim) return 0 ;;
    "$H"/.pip|"$H"/.config/pip|"$H"/.cargo|"$H"/.docker) return 0 ;;
    */.git/hooks) return 0 ;;
    /etc|/etc/cron.d|/etc/cron.daily|/etc/cron.hourly|/etc/cron.weekly|/etc/cron.monthly) return 0 ;;
    /etc/systemd|/etc/systemd/system|/etc/systemd/user) return 0 ;;
    /etc/profile.d|/etc/init.d|/etc/pam.d) return 0 ;;
  esac
  return 1
}

# Normalize a token: strip shell metas, expand tilde
clean_tok() {
  local t="$1"
  t=$(printf '%s' "$t" | sed 's/^[`("\x27]*//; s/[;|&)`"\x27]*$//')
  case "$t" in
    "~/"*) t="$H${t#\~}" ;;
    "~") t="$H" ;;
  esac
  printf '%s' "$t"
}

# Tokenize the NORMALIZED command (best-effort; quoted paths with spaces still slip)
read -r -a TOKENS <<< "$NORM"

CANDIDATES=()

# Pass 1: redirect targets after > or >> or >| or &> or &>>; dd of=<path>
PREV=""
for tok in "${TOKENS[@]}"; do
  case "$PREV" in
    ">"|">>"|">|"|"&>"|"&>>") CANDIDATES+=("$(clean_tok "$tok")") ;;
  esac
  case "$tok" in
    of=*) CANDIDATES+=("$(clean_tok "${tok#of=}")") ;;
  esac
  PREV="$tok"
done

# Pass 2: for cp/mv/tee/install/ln, identify destination(s).
# - Default: last non-flag, non-meta arg is destination
# - With -t <DIR> or --target-directory=<DIR>: every non-flag positional arg ends up under DIR
case "$NORM" in
  cp\ *|mv\ *|tee\ *|install\ *|ln\ *|cp|mv|tee|install|ln)
    # Check for -t / --target-directory first
    TARGET_DIR=""
    i=0
    n=${#TOKENS[@]}
    while [ $i -lt $n ]; do
      case "${TOKENS[$i]}" in
        -t)
          j=$((i+1))
          [ $j -lt $n ] && TARGET_DIR=$(clean_tok "${TOKENS[$j]}")
          ;;
        --target-directory=*)
          TARGET_DIR=$(clean_tok "${TOKENS[$i]#--target-directory=}")
          ;;
        -t*)
          # GNU-style combined: -tDIR (rare but possible)
          TARGET_DIR=$(clean_tok "${TOKENS[$i]#-t}")
          ;;
      esac
      i=$((i+1))
    done
    if [ -n "$TARGET_DIR" ]; then
      CANDIDATES+=("$TARGET_DIR")
      # Also flag if the target directory itself is a persistence root
      :
    else
      # Last non-flag positional is destination
      LAST=""
      for tok in "${TOKENS[@]}"; do
        case "$tok" in
          -*|">"|">>"|">|"|"&>"|"&>>"|"<"|"|"|"&"|";"|"cp"|"mv"|"tee"|"install"|"ln") continue ;;
        esac
        LAST=$(clean_tok "$tok")
      done
      [ -n "$LAST" ] && CANDIDATES+=("$LAST")
    fi
    ;;
esac

# Check each candidate
for c in "${CANDIDATES[@]}"; do
  [ -z "$c" ] && continue
  if matches_persistence "$c" || matches_persistence_dir "$c"; then
    jq -nc --arg path "$c" \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":("Bash command writes to \($path) (persistence/lateral-movement vector). Approve only if you explicitly requested this in this session.")}}'
    exit 0
  fi
done

exit 0
