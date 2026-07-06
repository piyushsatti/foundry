#!/usr/bin/env bash
# UserPromptSubmit — nudge to consult context7 for external library/API docs
# before answering from training memory. Reinforces the "context7" tool-routing
# rule in the global CLAUDE.md. Minimal, non-blocking; replace with your own if
# you want conditional/keyword-gated behavior.
jq -n --arg ctx "Reminder: for any question about an external library, framework, SDK, API, CLI tool, or cloud service, call context7 (resolve-library-id -> query-docs) BEFORE answering from memory — training knowledge may be stale or version-wrong. Skip only for the user's own code/business logic, general programming concepts, or when explicitly told to answer from memory." \
  '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":$ctx}}'
