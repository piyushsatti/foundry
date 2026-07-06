#!/usr/bin/env bash
# PreToolUse Write|Edit|MultiEdit — surface "ask" prompt for writes to
# persistence / lateral-movement paths. You decide per-write: approve if you
# explicitly requested this in the session, deny if Claude went rogue.
#
# Companion: persistence-bash-guard.sh covers Bash-side writes (redirects, cp, mv, tee, dd).

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

# Normalize: resolve existing paths
if [ -e "$FILE" ]; then
  ABS=$(realpath "$FILE" 2>/dev/null || echo "$FILE")
else
  ABS="$FILE"
fi

# Manual tilde expansion if needed
case "$ABS" in
  "~/"*) ABS="$HOME${ABS#\~}" ;;
  "~") ABS="$HOME" ;;
esac

H="$HOME"
REASON=""

case "$ABS" in
  # SSH
  "$H"/.ssh/authorized_keys|"$H"/.ssh/authorized_keys2)
    REASON="modifies SSH authorized_keys (persistent backdoor risk)" ;;
  "$H"/.ssh/config|"$H"/.ssh/known_hosts)
    REASON="modifies SSH client config (could redirect connections)" ;;
  # Bash startup
  "$H"/.bashrc|"$H"/.bash_profile|"$H"/.bash_login|"$H"/.bash_logout|"$H"/.profile|"$H"/.inputrc)
    REASON="modifies bash startup file (code runs on every login)" ;;
  # Zsh startup
  "$H"/.zshrc|"$H"/.zshenv|"$H"/.zprofile|"$H"/.zlogin|"$H"/.zlogout)
    REASON="modifies zsh startup file (code runs on every login)" ;;
  # Other shells
  "$H"/.kshrc|"$H"/.cshrc|"$H"/.tcshrc)
    REASON="modifies shell startup file" ;;
  # Fish
  "$H"/.config/fish/config.fish|"$H"/.config/fish/conf.d/*|"$H"/.config/fish/functions/*)
    REASON="modifies fish shell config (code runs on every login)" ;;
  # Git (global + per-repo)
  "$H"/.gitconfig|"$H"/.config/git/config|"$H"/.config/git/attributes)
    REASON="modifies global git config (alias/hooksPath hijack risk)" ;;
  */.git/hooks/*)
    REASON="modifies per-repo git hook (code execution on next checkout/pull/commit)" ;;
  */.git/config)
    REASON="modifies per-repo git config (alias/hooksPath hijack risk)" ;;
  # Systemd / autostart
  "$H"/.config/systemd/user/*|"$H"/.config/autostart/*|"$H"/.config/environment.d/*)
    REASON="modifies user service/autostart (boot/login persistence)" ;;
  # PATH shadow
  "$H"/.local/bin/*|"$H"/bin/*)
    REASON="writes to PATH-shadowed directory (could hijack future command invocations)" ;;
  # Package manager registries
  "$H"/.npmrc|"$H"/.yarnrc|"$H"/.yarnrc.yml|"$H"/.pypirc|"$H"/.pip/pip.conf|"$H"/.config/pip/pip.conf|"$H"/.gemrc|"$H"/.cargo/config|"$H"/.cargo/config.toml|"$H"/.docker/config.json)
    REASON="modifies package-manager registry config (install hijack risk)" ;;
  # Credentials
  "$H"/.netrc|"$H"/.pgpass|"$H"/.git-credentials)
    REASON="modifies credentials file" ;;
  # Editor auto-exec
  "$H"/.vimrc|"$H"/.vim/vimrc|"$H"/.config/nvim/init.lua|"$H"/.config/nvim/init.vim|"$H"/.config/nvim/lua/*)
    REASON="modifies vim/nvim config (code runs on editor open)" ;;
  # X session
  "$H"/.xinitrc|"$H"/.xsession|"$H"/.xprofile)
    REASON="modifies X session startup" ;;
  # System
  /etc/cron*|/etc/systemd/*|/etc/profile.d/*|/etc/init.d/*|/etc/rc.local|/etc/pam.d/*|/etc/sudoers*|/etc/passwd|/etc/shadow|/etc/group|/etc/hosts)
    REASON="modifies system file (system-wide impact)" ;;
esac

[ -z "$REASON" ] && exit 0

jq -nc --arg path "$ABS" --arg reason "$REASON" \
  '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":("Write to \($path) flagged: \($reason). Approve only if you explicitly requested this in this session.")}}'

exit 0
