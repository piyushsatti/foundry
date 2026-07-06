---
name: feedback_long_output_to_file
description: "Write long runbooks/instructions/reference output to a markdown FILE the user can open, not only into the TUI chat — repaint-TUI scrollback garbles long messages on scroll-up"
metadata:
  node_type: memory
  last_updated: 2026-06-01
  type: feedback
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

When producing substantial reference material the user will re-read — runbooks, multi-step instructions, long plans/reports — write it to a markdown FILE the user can open in their editor, in addition to (or instead of) dumping the whole thing into the TUI chat. Keep the chat message to a short summary + the file path.

**Why:** On 2026-06-01 a long "finish runbook" emitted only into chat became unreadable when the user scrolled up in Claude Code's TUI (Alacritty, no tmux): the in-place-repaint renderer fills the terminal's scrollback with overlapping partial frames (a palimpsest), so scrolled-back long messages garble — duplicated lines, ghost text bleeding through. No data is lost (the session transcript persists the bytes), but the user could not re-read it in place. tmux does NOT fix this — the repaint-into-scrollback cause is identical under tmux, and the extra emulation layer tends to *add* redraw-fidelity problems, not remove them. The user never saw this on **kitty** (0.32.2) but does on **Alacritty** (0.16.0-dev): both support synchronized output (mode 2026), so it is NOT a feature gap — it is a frame-coalescing maturity difference. kitty's older render/scrollback engine collapses the intermediate repaint frames before committing to scrollback; Alacritty's leaner, lower-latency pipeline lets the in-flight frames through (a secondary factor: `TERM=xterm-kitty` advertises a richer capability set than `TERM=alacritty`, so the app may negotiate a more atomic render path under kitty).

**How to apply:** For any long/reference deliverable, offer to write it to a markdown file (and do so once authorized). Location: `/tmp/<name>.md` for ephemeral (survives across sessions but not a reboot); a durable notes path (e.g. `~/Documents/notes/infrastructure/<date>-<name>.md`) when it must outlive a reboot or seed a fresh session. Short content and live one-step-at-a-time walkthroughs stay in chat (see [[feedback_incremental_walkthroughs]]). On-screen recovery for an already-garbled view: Ctrl+L (repaint) or scroll back to the live region.

**Resolution (2026-06-01):** user accepts the file-habit as the fix and is staying on Alacritty — do NOT re-propose terminal-level remedies for this (Alacritty config tweaks, switching back to kitty, or tmux). The write-long-content-to-a-file habit is the agreed close-out.
