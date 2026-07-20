# Clipboard and OSC 52

**Claude Code's fullscreen TUI writes mouse selections only to CLIPBOARD via hardcoded OSC 52, never to PRIMARY — so middle-click paste fails everywhere.**

> **Status:** stable

## The symptom

**Highlight text in Claude Code → middle-click into another app → nothing pastes**, but `Ctrl+Shift+V` works. The root cause is Claude Code's TUI renderer — not the terminal, display server, or any kitty setting.

## The fix

```bash
/tui default            # in a session
# or ~/.claude/settings.json: "tui": "default"
```

Restart. Selections now land in PRIMARY (filled by the terminal's native selection), so middle-click works everywhere. **Cost:** you lose `/focus` view; the layout becomes inline scrolling instead of a fixed viewport.

## Mechanism

Claude Code has two render modes, set by `"tui"` (default `fullscreen`):

| Mode | Mouse owner | Selection lands in |
|---|---|---|
| `fullscreen` | Claude captures (mouse modes `1000h`/`1002h`/`1003h`/`1006h`), alt-screen | CLIPBOARD only, via `\e]52;c;<base64>` — PRIMARY never touched |
| `default` | Terminal owns the drag | PRIMARY, exactly like `cat` output |

In fullscreen the OSC 52 write is the **only** clipboard path, and the selector `c` (CLIPBOARD) is **hardcoded** — the binary has no `p` or `cp` selector. No Claude flag, setting, or env var can target PRIMARY.

**Recognize it in the wild:** fullscreen mode prints a bottom-right status after each selection: `sent N chars via OSC 52 · check terminal clipboard settings if paste fails`. That hint refers to OSC 52 write-permissions, not the PRIMARY/CLIPBOARD split — which is structural, not a permission issue.

## Why no terminal setting fixes it

In fullscreen mode kitty never sees the selection, so `copy_on_select`, `clipboard_control`, and `mouse_map` don't apply to the drag. The sender picks the selector; the terminal can't rewrite `c` to `p`. And no Linux global remaps middle-click PRIMARY→CLIPBOARD (it's baked into GTK/Qt widgets).

**If you must keep fullscreen** (e.g. for `/focus`), make kitty's own middle-click read CLIPBOARD where Claude writes:

```conf
copy_on_select clipboard
mouse_map middle release ungrabbed paste_from_clipboard
```

Trade-off: highlight-in-browser → middle-click-into-kitty now fails (use `Shift+Insert`), and non-terminal GUI apps still won't paste Claude content. Prefer `tui: default` unless `/focus` is non-negotiable.

## Reusable diagnostic: is it the terminal or the app?

For any "selection landed in the wrong clipboard" TUI symptom:

1. **Which clipboard has the text?** `xclip -o -sel primary` / `wl-paste --primary` (PRIMARY); `xclip -o -sel clip` / `wl-paste` (CLIPBOARD).
2. **Which mouse modes does the app enable?** Run under `script -q`, reproduce, then `grep -oE $'\x1b\\[\\?[0-9]+[hl]' trace.log | sort -u`. Codes: `1000`/`1002`/`1003`/`1006`.
3. **Which OSC 52 selector?** `strings <binary> | grep -E ']52;[a-z]+;' | sort -u`. Only `c` → CLIPBOARD-only; `p`/`cp` → can target PRIMARY.
4. **Check the terminal's permission gate** (kitty: `clipboard_control`).
5. **If the app has a non-TUI mode, try it first** — letting the terminal own the mouse feeds PRIMARY by default on X11/Wayland.
