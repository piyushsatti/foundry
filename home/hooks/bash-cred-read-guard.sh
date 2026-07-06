#!/usr/bin/env bash
# PreToolUse Bash — deny Bash commands that reference known credential storage paths.
#
# Rationale: secret-scanner.sh checks for secrets in command TEXT (e.g. "AKIA..."
# embedded in args), not output. sensitive-file-guard.sh handles Write/Edit only.
# This hook closes the Bash read-side gap: `cat ~/.ssh/id_ed25519`, `head ~/.aws/credentials`,
# `jq .access_token ~/.config/gh/hosts.yml` all sail through the other layers.
#
# Sandbox `denyRead` rules would also catch this, but sandbox is currently disabled.
# When the sandbox is re-enabled this hook becomes belt-and-braces.

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')

[ -z "$CMD" ] && exit 0

# Sensitive path patterns — match anywhere in the command string.
# Word-boundaried for directory references (.ssh, .gnupg, etc.) so trailing space/end is caught;
# substring-matched for file-suffix patterns (credentials, hosts.yml).
# Patterns are deliberately broad — false positives prompt; false negatives leak.
SENSITIVE='(^|[~/[:space:]=])\.ssh($|/|[^[:alnum:]_])'
SENSITIVE="$SENSITIVE"'|(^|[~/[:space:]=])\.gnupg($|/|[^[:alnum:]_])'
SENSITIVE="$SENSITIVE"'|(^|[~/[:space:]=])\.aws($|/|[^[:alnum:]_])'
SENSITIVE="$SENSITIVE"'|(^|[~/[:space:]=])\.docker($|/|[^[:alnum:]_])'
SENSITIVE="$SENSITIVE"'|(^|[~/[:space:]=])\.kube($|/|[^[:alnum:]_])'
SENSITIVE="$SENSITIVE"'|\.netrc($|[^[:alnum:]_])|\.pgpass($|[^[:alnum:]_])'
SENSITIVE="$SENSITIVE"'|\.git-credentials|/credentials\.toml|\.npmrc|\.pypirc'
SENSITIVE="$SENSITIVE"'|/gh/hosts\.yml|/gh/config\.yml'
SENSITIVE="$SENSITIVE"'|password-store|/keyrings/'
SENSITIVE="$SENSITIVE"'|\.mozilla/firefox|\.config/google-chrome|\.config/chromium'
SENSITIVE="$SENSITIVE"'|/Login Data|/Cookies'

if printf '%s' "$CMD" | grep -qE "$SENSITIVE"; then
    # Try to extract the matching path for a more useful denial reason
    MATCH=$(printf '%s' "$CMD" | grep -oE "[^[:space:]]*($SENSITIVE)[^[:space:]]*" | head -1)
    jq -nc --arg match "$MATCH" \
       '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":("Bash command references a credential storage path (\($match)). Reading SSH keys, cloud credentials, GH tokens, or browser profiles is blocked. If this is intentional, run the command manually outside Claude.")}}'
    exit 0
fi

# CLI-tool credential exfil — these tools emit secrets to stdout without
# referencing any sensitive *path*. They sail past the SENSITIVE regex above.
CLI_TOOL=""
case "$CMD" in
    gh\ auth\ token*|*\ gh\ auth\ token*)              CLI_TOOL="gh auth token" ;;
    *gh\ auth\ status*-t*|*gh\ auth\ status*--show-token*) CLI_TOOL="gh auth status -t/--show-token" ;;
    aws\ configure\ get*|*\ aws\ configure\ get*)      CLI_TOOL="aws configure get" ;;
    aws\ configure\ export-credentials*)               CLI_TOOL="aws configure export-credentials" ;;
    op\ read*|*\ op\ read*)                            CLI_TOOL="op read (1Password)" ;;
    op\ item\ get*|*\ op\ item\ get*)                  CLI_TOOL="op item get (1Password)" ;;
    bw\ get*|*\ bw\ get*)                              CLI_TOOL="bw get (Bitwarden)" ;;
    pass\ show*|*\ pass\ show*)                        CLI_TOOL="pass show" ;;
    secret-tool\ lookup*|*\ secret-tool\ lookup*)      CLI_TOOL="secret-tool lookup" ;;
    keyring\ get*|*\ keyring\ get*)                    CLI_TOOL="keyring get" ;;
    security\ find-generic-password*|*\ security\ find-generic-password*) CLI_TOOL="security find-generic-password (macOS Keychain)" ;;
    security\ find-internet-password*|*\ security\ find-internet-password*) CLI_TOOL="security find-internet-password (macOS Keychain)" ;;
esac

if [ -n "$CLI_TOOL" ]; then
    jq -nc --arg tool "$CLI_TOOL" \
       '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":("Bash command invokes a credential-emitting CLI tool (\($tool)). The output would contain secrets that flow into Claude'\''s context. If you need these credentials, retrieve them manually outside Claude.")}}'
fi
