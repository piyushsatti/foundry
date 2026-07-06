---
name: primer
description: Draft or update a scope primer for the current problem space. Use when you want to capture key decisions, context, and next steps so future sessions start informed.
allowed-tools: Read, Write, Bash(ls:*), Bash(cat:*), Bash(jq:*)
---

# Scope Primer Editor

You are drafting or updating a scope primer — a concise context document injected into new sessions via `--append-system-prompt-file`.

**Argument:** $ARGUMENTS (optional guidance for what the primer should focus on)

## Steps

### 1. Identify the current scope

Read `~/.cache/cc/session-scopes.json` and look up the current session by checking which session files were most recently modified in the current project's Claude data directory. The project dir is derived from the current working directory: replace `/` with `-` to get the encoded path, then look in `~/.claude/projects/<encoded>/`.

If no scope is assigned, ask the user which scope this session belongs to.

### 2. Read existing primer

Check `~/.claude/scopes/<project-name>/<scope>.md` (where project-name is the directory basename, e.g., `my-project-prod`). Also check for `.<scope>.staged.md` (a staged update from compaction).

If an existing primer exists, read it. If a staged update exists, incorporate it.

### 3. Draft the primer

Based on this session's context (decisions made, problems solved, current state), draft the primer. Structure:

```markdown
# Scope: <scope-name>

## Context
[2-3 sentences: what area of the project this covers and why]

## Key decisions
- [Decision 1 and reasoning]
- [Decision 2 and reasoning]

## Active threads
- [Current work item, ticket reference if known]
- [Open question that needs resolution]

## Patterns
- [Naming convention, approach, or constraint specific to this scope]
```

Rules:
- Keep under 40 lines total
- Be specific: reference file paths, function names, ticket numbers
- Never include secrets, credentials, or API keys
- Write in present tense, imperative mood
- Do not duplicate content from the project's CLAUDE.md
- Focus on knowledge that does NOT survive context compaction well

### 4. Present for review

Show the full draft. Ask the user to approve, edit, or reject. Do NOT write the file until the user explicitly approves.

### 5. Write the file

On approval:
1. Create the scope directory if needed: `~/.claude/scopes/<project-name>/`
2. Write to `~/.claude/scopes/<project-name>/<scope>.md`
3. Remove any staged update file (`.<scope>.staged.md`) if it exists
4. Confirm to the user that the primer was saved
