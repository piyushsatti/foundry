---
title: Clipboard / OSC 52
category: field-notes
status: stable
summary: Why Claude Code's fullscreen TUI writes selections only to CLIPBOARD (never PRIMARY) via hardcoded OSC 52, and the tui;default fix.
sources:
  - docs/clipboard-model.md
related: [Permission Pipe Limitation, Worktree Context Loading]
updated: 2026-07-20
---

# Clipboard / OSC 52

> **Status:** stable · **Consolidated from** `docs/clipboard-model.md` (verified v2.1.141).

## Overview

<TODO: the fullscreen TUI writes selections only to the CLIPBOARD selection via
hardcoded OSC 52, never to PRIMARY — the root-cause mechanism.>

## The fix

<TODO: `tui: default`.>

## Reusable diagnostic

<TODO: the "is it the terminal or the app?" diagnostic chain.>

## See also

- [Permission pipe limitation](permission-pipe.md)
- [Worktree context loading](worktree-context.md)
