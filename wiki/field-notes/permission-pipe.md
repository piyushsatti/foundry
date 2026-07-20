---
title: Permission Pipe Limitation
category: field-notes
status: stable
summary: Any deny rule containing a pipe, &&, ;, or || is dead config — the matcher splits composite commands — so pipe-based RCE must be blocked in PreToolUse hooks.
sources:
  - docs/permission-pipe-limitation.md
related: [Design Philosophy, Clipboard / OSC 52, Worktree Context Loading]
updated: 2026-07-20
---

# Permission Pipe Limitation

> **Status:** stable · **Consolidated from** `docs/permission-pipe-limitation.md`. Feeds Design Philosophy §3.2.

## Overview

<TODO: the load-bearing finding — deny rules with |, &&, ;, || are dead config
because the matcher splits composite commands.>

## Consequence

<TODO: pipe-based RCE must be blocked in PreToolUse hooks, not deny rules.>

## See also

- [Design philosophy](../architecture/design-philosophy.md)
