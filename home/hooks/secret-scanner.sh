#!/usr/bin/env bash
# PreToolUse Write|Edit|Bash — block writes/commands containing secrets
source ~/.claude/hooks/stats.sh
INPUT=$(cat)
CONTENT=$(echo "$INPUT" | jq -r '(.tool_input.content // "") + (.tool_input.new_string // "") + (.tool_input.command // "")')

# URI patterns split across quotes so this script doesn't trigger itself
_PG='postgres'"://"'[^:]+:[^@]+@'
_MG='mongodb'"://"'[^:]+:[^@]+@'

# Single combined grep for the no-secret fast path (avoids 9 subprocess forks per call)
COMBINED='sk-ant-[a-zA-Z0-9]{10,}|sk-proj-[a-zA-Z0-9]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|ghp_[a-zA-Z0-9]{36}|ghs_[a-zA-Z0-9]{36}|xoxb-[a-zA-Z0-9-]+|xoxp-[a-zA-Z0-9-]+|SG\.[a-zA-Z0-9_-]{22,}\.[a-zA-Z0-9_-]{22,}'
COMBINED="${COMBINED}|${_MG}|${_PG}"

if echo "$CONTENT" | grep -qiE "$COMBINED"; then
  # Identify type (only runs on match — rare; granularity used for stats ctx)
  SECRET_TYPE="unknown"
  if   echo "$CONTENT" | grep -qiE 'sk-ant-[a-zA-Z0-9]{10,}';                        then SECRET_TYPE="anthropic-key"
  elif echo "$CONTENT" | grep -qiE 'sk-proj-[a-zA-Z0-9]{10,}';                       then SECRET_TYPE="openai-key"
  elif echo "$CONTENT" | grep -qiE 'AKIA[0-9A-Z]{16}';                               then SECRET_TYPE="aws-key"
  elif echo "$CONTENT" | grep -qiE '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY';     then SECRET_TYPE="private-key"
  elif echo "$CONTENT" | grep -qiE 'ghp_[a-zA-Z0-9]{36}|ghs_[a-zA-Z0-9]{36}';      then SECRET_TYPE="github-token"
  elif echo "$CONTENT" | grep -qiE 'xoxb-[a-zA-Z0-9-]+|xoxp-[a-zA-Z0-9-]+';        then SECRET_TYPE="slack-token"
  elif echo "$CONTENT" | grep -qiE 'SG\.[a-zA-Z0-9_-]{22,}\.[a-zA-Z0-9_-]{22,}';   then SECRET_TYPE="sendgrid-key"
  elif echo "$CONTENT" | grep -qiE "$_MG";                                            then SECRET_TYPE="mongodb-uri"
  elif echo "$CONTENT" | grep -qiE "$_PG";                                            then SECRET_TYPE="postgres-uri"
  fi
  log_stat "secret-scanner" "PreToolUse" "deny" "$SECRET_TYPE"
  deny_hook "Possible secret or credential detected. Review before proceeding."
fi
