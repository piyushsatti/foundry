---
title: Session Message Bus
category: roadmap
status: shelved
summary: Cross-session message passing between running Claude Code sessions — 3 delivery classes (interrupt/normal/passive), with an injection-surface security model. Shelved 2026-07-18.
sources: []
related: [Roadmap, Plan Orchestrator]
updated: 2026-07-20
---

# Idea: Session Message Bus

> **Status:** shelved (2026-07-18) · Captured for cold pickup, not scheduled.
> Existing writeup lives on the GitHub wiki page `Idea-Session-Message-Bus`; migrate it here.

## Overview

<TODO: message passing between running sessions (orchestrators/builders/meta);
three delivery classes — interrupt (mid-turn), normal (next boundary), passive
state-change (notification only).>

## Requirements

<TODO: message classes, addressing (stable names surviving resume/fork),
delivery guarantees, ordering, ack/read receipts, security (untrusted input!),
human oversight.>

## Architecture options

<TODO: (a) mailbox + hooks, (b) PTY/tmux proxy for true interrupts, (c) daemon/bus.>

## Open questions

<TODO: is a true mid-turn interrupt required; trust model; build-now vs wait.>

## See also

- [Roadmap](roadmap.md)
