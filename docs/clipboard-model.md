---
title: "Claude Code clipboard model — fullscreen TUI captures the mouse and writes only to CLIPBOARD"
applies_to: Claude Code v2.1.x (verified 2.1.141, 2026-05-22)
created: 2026-05-22
last_updated: 2026-05-22
keywords: [claude-code, clipboard, osc52, primary-selection, x11, wayland, kitty, tui, fullscreen, mouse-tracking]
related:
  - "permission-pipe-limitation.md"
---

# Why this doc exists

If you ever hit the symptom **"highlighted text in Claude Code → middle-click in another app → nothing pastes (but Ctrl+Shift+V does)"**, read this before opening a kitty/Wayland/X11 investigation. The root cause is **inside Claude Code's TUI renderer**, not the terminal, not the display server, and not a configurable kitty setting. The fix is a one-line settings change.

# TL;DR fix

```bash
# In a Claude Code session:
/tui default

# Or directly in ~/.claude/settings.json:
"tui": "default"
```

Restart Claude. Selection in Claude Code now lands in PRIMARY (filled by your terminal's native selection mechanism), so middle-click paste works everywhere — browsers, file managers, other terminals, Slack, etc.

Cost: lose the `/focus` view feature (requires fullscreen renderer per Claude's own error message); the visual model changes from a fixed full-screen viewport to inline scrolling. If `/focus` matters to you, fall back to the kitty.conf workaround in the "Alternative" section below.

# Mechanism (what's actually happening)

**Claude Code has two TUI rendering modes**, set by `"tui"` in `~/.claude/settings.json` (default is `fullscreen` on modern installs):

| Mode | What it does |
|---|---|
| `fullscreen` | Enters alt-screen (`\e[?1049h`), enables mouse capture (modes `1000h` + `1002h` + `1003h` + `1006h`), builds its own selection in-process when you drag, writes selected text to system CLIPBOARD via OSC 52 (`\e]52;c;<base64>\e\\`). PRIMARY is **never** touched. |
| `default`   | Renders inline in the main screen buffer. No alt-screen. No mouse capture. The terminal owns the mouse, so dragging produces normal terminal selection, which fills PRIMARY exactly like `cat` or `git log` output would. |

In fullscreen mode the OSC 52 write is **the only clipboard mechanism Claude uses** — the binary contains `]52;c;` and nothing for selector `p` (PRIMARY) or `cp` (multi-selector). This is not configurable: there is no Claude Code setting, no flag, and no env var that makes Claude write to PRIMARY. The OSC 52 selector is hardcoded.

So in fullscreen mode:

```
mouse drag in Claude  →  Claude captures via modes 1000h/1002h/1003h
                      →  builds in-process selection
                      →  emits \e]52;c;<base64> on mouse-up
                      →  terminal writes CLIPBOARD only
                      →  PRIMARY remains empty
                      →  middle-click (which reads PRIMARY) pastes nothing
                      →  Ctrl+V / Ctrl+Shift+V (which read CLIPBOARD) work fine
```

And in default mode:

```
mouse drag in Claude  →  terminal sees the drag
                      →  terminal does its normal text selection
                      →  selected text → PRIMARY (always, on X11/Wayland)
                      →  middle-click works
                      →  Ctrl+V also works if your terminal also fills CLIPBOARD on select
                         (e.g., kitty's `copy_on_select clipboard`, or VS Code's
                         `terminal.integrated.copyOnSelection: true`)
```

# How to recognize this in the wild

Claude Code in fullscreen mode displays a **bottom-right status string** after each mouse selection:

```
sent N chars via OSC 52 · check terminal clipboard settings if paste fails
```

If you see this and middle-click paste isn't working, the diagnosis is confirmed. The "check terminal clipboard settings" hint refers to your terminal's OSC 52 write-permissions (e.g., kitty's `clipboard_control` setting — kitty's defaults already allow it). The hint is **not** suggesting a fix for the PRIMARY-vs-CLIPBOARD split — that split is structural, not a permission issue.

# Why no kitty/terminal setting can fix this in fullscreen mode

When you've ruled in Claude Code as the source of the asymmetry, it's tempting to look for a terminal-side mirror or remap. Don't burn time on it:

- **kitty `copy_on_select`** controls what happens when *kitty* does a selection. In fullscreen mode kitty never sees the selection — Claude captured it.
- **kitty `clipboard_control`** gates OSC 52 reads/writes. The default already allows `write-clipboard` and `write-primary`. The sender (Claude) chooses the selector; kitty cannot rewrite `c` to `cp` or `p`.
- **kitty `mouse_map`** can remap *what kitty does on mouse events*. In fullscreen mode kitty forwards mouse events to Claude, so this never fires for the drag itself. (It can be used to change kitty's own middle-click target — see "Alternative" below.)
- **No system-wide setting** on Linux remaps middle-click from PRIMARY→CLIPBOARD. The middle-click-paste-PRIMARY behavior is hardcoded into GTK and Qt widgets; some apps have per-app overrides (e.g., Firefox `middlemouse.paste`) but there is no global switch.

# Alternative (if you must stay in fullscreen mode)

If you use `/focus` view or strongly prefer the fullscreen visual feel and accept losing middle-click-into-non-terminal-apps for Claude-originated content, the workaround is to make middle-click *inside kitty* read CLIPBOARD (where Claude already writes) instead of PRIMARY:

```conf
# ~/.config/kitty/kitty.conf
copy_on_select clipboard
mouse_map middle release ungrabbed paste_from_clipboard
```

Effects:
- `copy_on_select clipboard` — kitty's own selections now fill both PRIMARY and CLIPBOARD
- `mouse_map middle release ungrabbed paste_from_clipboard` — middle-click in any kitty window pastes CLIPBOARD instead of PRIMARY

After this, highlight-in-Claude → middle-click-into-another-kitty-window works. The trade-off: highlight-in-browser → middle-click-into-kitty now fails (because kitty's middle-click no longer reads PRIMARY); use `Shift+Insert` to read PRIMARY explicitly. Middle-click into non-terminal GUI apps with Claude-originated content still fails because we can't change GTK/Qt.

The `tui: default` switch avoids all of this complexity. Prefer it unless `/focus` is non-negotiable.

# Diagnostic chain (re-usable for future "is it the terminal or the app?" investigations)

If you're hit by a similar "selection landed in the wrong clipboard" symptom in another TUI:

1. **Identify which clipboard has the text.** From a non-sandboxed shell: `xclip -o -sel primary` (X11) or `wl-paste --primary` (Wayland) for PRIMARY; `xclip -o -sel clip` or `wl-paste` for CLIPBOARD.
2. **Identify which mouse modes the app enables.** Run the app under `script -q /tmp/trace.log`, reproduce, exit, then `grep -oE $'\x1b\\[\\?[0-9]+[hl]' /tmp/trace.log | sort -u`. Mouse-mode codes are `1000` (X10 click) / `1002` (cell motion) / `1003` (any motion) / `1006` (SGR coords).
3. **Identify OSC 52 use.** `strings <binary> | grep -E ']52;[a-z]+;' | sort -u`. If the only selector is `c`, the app writes CLIPBOARD only; if you see `p` or `cp`, it can target PRIMARY.
4. **Check the terminal's permission gate.** For kitty: `grep clipboard_control /usr/lib/kitty/kitty/options/definition.py`. Defaults usually permit writes; reads are typically prompt-gated.
5. **If the app has a "non-TUI mode" toggle, try it first** — the cleanest fix is to let the terminal own the mouse, because the terminal's selection mechanism feeds PRIMARY by default on X11/Wayland.

# Provenance

Diagnosed 2026-05-22 over a multi-hour Claude Code session. The investigation walked through every terminal-side hypothesis (kitty `mouse_map`, `clipboard_control`, `copy_on_select`, modifier-release timing, X11-vs-Wayland session protocol, clipboard manager presence) before locating the root cause in Claude Code's TUI renderer via binary string inspection. The `tui: default` resolution was found because the user asked the right question — "can't I just set TUI to default?" — which prompted a check of Claude's slash commands that the earlier investigation had missed.

This doc lives in infrastructure/claude/ because it's portable Claude Code reference material that applies to any machine running Claude Code.
