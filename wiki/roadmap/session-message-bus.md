---
title: Session Message Bus
status: shelved
summary: Message passing between running Claude Code sessions — three delivery classes, with the mailbox as a prompt-injection surface. Shelved 2026-07-18.
sources: []
updated: 2026-07-20
---

# Session Message Bus

**Tooling to pass messages between running Claude Code sessions** (orchestrators, builders, meta-orchestrators, human relay), delivered by priority into the receiver's agentic lifecycle.

> **Status:** shelved (2026-07-18) — captured for cold pickup, not scheduled. A fuller writeup exists on the legacy GitHub wiki page `Idea-Session-Message-Bus`.

## Three message classes

| Class | Delivery | Analogy |
|-------|----------|---------|
| Interrupt | mid-turn, breaks current work | pager |
| Normal | next turn boundary | email |
| Passive state-change | notification only ("check X") | file-watcher event |

These need different transport, not one queue with a priority tag.

## The sharp edge: security

**A message is untrusted input to the receiver.** Any sender can write a mailbox file, so the mailbox is a prompt-injection surface. Consequences: never auto-execute message content as if it were the owner's; present it as quoted, attributed data; treat declared priority as a claim the receiver can downgrade; log every interrupt loudly.

## Architecture options

- **(a) Mailbox file + hooks** — buildable today; delivers normal/passive on next `UserPromptSubmit`; does **not** truly interrupt.
- **(b) PTY / tmux proxy** — the only path to real mid-turn interrupts, but races the human's keystrokes; "worth a spike," not v0.
- **(c) Daemon / bus** — best for fan-out + a single audit log; still needs (a) or (b) to actually land a message.

**Read:** (a) + (c) are complementary (delivery leg + storage/audit backbone); (b) is a separate, riskier bet. Smallest v0 = mailbox JSONL + hook + a `send` CLI + a shared traffic log.

## Open question

Is a genuine mid-turn interrupt actually required, or does "delivered at next touch, human nudged to touch soon" cover the real need? That decides whether (b) is worth pursuing at all.

## See also

- [Roadmap](overview.md) · [Plan Orchestrator](../plugins/plan-orchestrator/overview.md)
