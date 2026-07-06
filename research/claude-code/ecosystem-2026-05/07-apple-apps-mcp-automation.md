# Programmatic Access to Apple Apps for an LLM Capture/Management Surface on macOS

## TL;DR
- **Build a thin Swift CLI on top of EventKit for Reminders/Calendar, wrap Apple Mail and Notes via AppleScript/JXA, and expose them through a single Python `stdio` MCP server.** This is what every successful open-source project converges on, and it is the only way to reliably get the operations you actually want (recurrence, alarms, sublists, drafts, attachments, locations) from Claude Desktop.
- **You almost certainly do not have "official" Reminders/Calendar/Mail connectors on macOS — what's enabled is iOS-only or a third-party MCP server.** Anthropic ships first-party Apple-native connectors only for **Notes** and **iMessage** on macOS Desktop. The Reminders/Calendar/Mail Apple integrations Anthropic advertises are iOS-only (EventKit + Compose sheet). If they appear "enabled" in Claude Desktop on a Mac, a third-party MCP server is providing them.
- **Apple Notes write access is still the hard problem.** AppleScript can create/update text, but strips checklist state, can't add native attachments, mangles first-line formatting, and cannot round-trip rich content. macOS 26 Tahoe's new Markdown import is the only sanctioned way to land *formatted* notes — and one MCP server (`ailenshen/apple-notes-mcp`) already exploits it. The SQLite/protobuf path is read-only in practice; nobody has shipped a reliable writer.

## Key Findings

### 1. Native automation surfaces, ranked by what you should actually use

| Surface | Reminders | Calendar | Notes | Mail |
|---|---|---|---|---|
| **EventKit (Swift)** | ✅ Full CRUD: title, notes, URL, priority, due/start dates, alarms (relative/absolute/location-geofence), recurrence rules, subtasks (via `parentReminder`), tags via notes field | ✅ Full CRUD: events, calendars, attendees (read), `EKRecurrenceRule` (single rule per event), alarms, structured locations | ❌ No EventKit equivalent — Apple does not expose a public Notes framework | ❌ No public framework |
| **AppleScript / JXA via `osascript`** | ✅ Works, but slower and quirkier than EventKit | ✅ Works; recurrence is set as an RFC 5545 (RRULE) string — most third-party scripts get this wrong | ⚠️ Only path that exists. First line treated as `name` (unformatted); body is HTML in/out; checklist state lost on read; no programmatic attachments; no rich link previews | ✅ Send, draft, attach, mailbox manipulation. Reply/forward had a long-standing empty-body bug fixed in `sweetrb/apple-mail-mcp` v1.4.0 by switching from `with opening window` to `without opening window` |
| **`shortcuts` CLI** | Trigger-able from terminal; pass input via `-i`/`--input-path`; all flags besides `list` open the Shortcuts GUI app | Same | Same | Same — useful fallback for things AppleScript can't reach, but not a programming surface |
| **TCC permission model** | Now split into write-only vs. **Full Access**; `requestFullAccessToReminders` (macOS 14+) | Same; `requestFullAccessToEvents` | `kTCCServiceAppleEvents` for Notes — also requires Full Disk Access if you read `NoteStore.sqlite` | Mail Data Access entitlement in System Settings → Privacy & Security → Automation |

The community has converged on a clear hierarchy: **EventKit > AppleScript > Shortcuts CLI > raw SQLite**. EventKit gives you the only first-class API for recurrence rules (`EKRecurrenceRule` with `daysOfTheWeek`, `daysOfTheMonth`, `weeksOfTheYear`, etc.), alarms (`EKAlarm` with `EKAlarmProximity` enter/leave geofences via `EKStructuredLocation`), and the split full-access authorization on macOS 14+. Apple's docs explicitly note: *"The implementation only supports a single recurrence rule. Adding a recurrence rule replaces the single recurrence rule."* — this is the most-missed gotcha when porting from Google Calendar mental models.

### 2. Existing tools that actually work today (May 2026)

**Reminders / Calendar (EventKit-backed — recommended starting points):**
- **`keith/reminders-cli`** — pure Swift, ~746★ (per the GitHub releases page as of May 2026), actively maintained, JSON output, full CRUD including priorities and `--due-date` natural-language parsing. **Caveat:** when called from a parent process other than Terminal (e.g., a Claude Desktop subprocess), TCC permission inheritance breaks; the canonical workaround is to also fire a one-shot `osascript -e 'tell application "Reminders"…'` to trigger the prompt against the parent bundle ID (documented in `mcp-server-apple-events` and issue #68 on the `reminders-cli` repo).
- **`schappim/ekctl`** — newer pure-Swift CLI, JSON-only output, code-signed with entitlements for cleaner TCC handling. Designed explicitly to pair with Claude Code Skills.
- **`FradSer/mcp-server-apple-events`** — TypeScript MCP server with a bundled Swift EventKitCLI. Exposes service-scoped tools for full CRUD on reminders + calendar events, including `relativeOffset` / `absoluteDate` / `locationTrigger` alarms, multi-recurrence input, and subtasks. The repo is migrating to depend on a standalone `event` Swift CLI rather than embedding the binary — sign of long-term maintenance.
- **`PsychQuant/che-ical-mcp`** — 24-tool Swift EventKit MCP server with same-name disambiguation across iCloud/Google/Exchange calendars; supports idempotent writes and `delete_events_batch` dry-run mode.
- **`ai-mcp-garage/mcp-reminders`** — Python + PyObjC EventKit, with optional `PROJECT_NAME` scoping. Good reference if you prefer to stay in Python.

**Mail:**
- **`imdinu/apple-mail-mcp`** (Python, pipx) — **the one to start with.** Per the project's own documentation (imdinu.github.io/apple-mail-mcp), it achieves *"~3ms single email fetch via disk-first .emlx reading"* and *"~7ms subject search via FTS5 — competitive with native Rust on the same operation. Reliable across all 6 benchmarked operations on a real ~72K-message mailbox. Tested against 8 other Apple Mail MCP servers."* Read-only as of v1.x; write tools are roadmap. Requires Full Disk Access for Terminal. The project's batch-JXA approach is *"up to 87× faster"* than per-message AppleScript, and body search is *"~3500× faster"* than standard live-scan approaches.
- **`sweetrb/apple-mail-mcp`** (Node, AppleScript) — full read/write/draft/send/attach/move/bulk-delete with the v1.4.0 reply-body fix; documented attack-surface restrictions (`save-attachment` allowlists `~`, `/tmp`, `/private/tmp`, `/Volumes`).
- **`patrickfreyer/apple-mail-mcp`** (Python, FastMCP) — bundles a Claude Code Skill (`/email-management`) plus a `--read-only` flag and HTML draft composition.

**Notes:**
- **`ailenshen/apple-notes-mcp`** (Node, **requires macOS 26 Tahoe**) — uses the new `File → Import to Notes` Markdown import as the write path, so headings/bold/lists land as native rich text instead of literal markdown characters. Reads go through SQLite + turndown for HTML→Markdown. Update = delete + re-create.
- **`sweetrb/apple-notes-mcp`** — AppleScript-based create/search/update/delete; has a `get-checklist-state` tool that bypasses the AppleScript checklist-state stripping by reading `NoteStore.sqlite` directly (Full Disk Access required for that one tool only).
- **`disco-trooper/apple-notes-mcp`** — semantic + full-text + keyword search via local embeddings (~200 MB model download); chunked indexing; folder-scoped queries fast even on large vaults.
- **`RafalWilinski/mcp-apple-notes`** — read-only RAG with LanceDB + `all-MiniLM-L6-v2`. Good if you only want search.
- **`sirmews/apple-notes-mcp`** — Python, read-only direct SQLite reader; author explicitly notes AppleScript would be needed for writes.

**All-in-one bundles (use with caution):**
- **`supermemoryai/apple-mcp`** (formerly Dhravya Shah's `apple-mcp`) — Messages, Notes, Contacts, Mail, Reminders, Calendar, Maps via JXA+AppleScript. Wide-but-shallow: Notes is list/search/read only (no native create); Reminders is create/list/search but no priority or recurrence.
- **`more-io/claude-apple-bridges`** — Swift CLIs (`reminders-bridge`, `calendar-bridge`, `mail-bridge`, etc.) plus a Claude Code skill (`/apple-bridges`). Designed for Claude Code, not Claude Desktop.

**Avoid:** anything that requires installing a separate macOS .app for permissions (Claunnector, Macuse). These are commercial products in MCP clothing and conflict with your "no third-party native apps" constraint.

### 3. Anthropic's first-party connectors — what you already have, and what you don't

**Confirmed first-party macOS Desktop connectors as of May 2026:** **Apple Notes** and **iMessage** only. Both shipped as part of Anthropic's Connectors directory / Desktop Extensions push in **July 2025** (per a contemporaneous Medium overview by Daniel Ferrera, which stated *"As of July 2025, the directory has connectors for Gmail, PayPal, Slack, Stripe, Canva, Notion, Google Drive, Zapier, and dozens more,"* and listed *"manage Apple Notes, send iMessages"* among Desktop Extension capabilities). Both are AppleScript-backed (iMessage also reads `~/Library/Messages/chat.db` directly via SQLite for history).

**iOS-only native Apple integrations** (Calendar, Reminders, Mail compose sheet, Maps, Location): these use EventKit on iOS and live in the Claude iOS app, not Claude Desktop. Per Anthropic's own help center, *"Claude cannot create or edit reminder lists themselves, only items within existing lists"* on iOS, and *"Messages/Email: Claude does not read existing messages or emails, only creates new content."* MacStories' Federico Viticci, in *"Testing Claude's Native Integration with Reminders and Calendar on iOS and iPadOS"* (September 10, 2025), confirmed: *"Unfortunately, as is the case with other Reminders integrations in third-party iOS apps, Claude cannot access more modern app features like native rich links, tags, and subtasks."*

**Implication:** if you have "Reminders/Calendar/Mail" enabled in Claude Desktop on macOS, you are running a third-party MCP server (most likely `FradSer/mcp-server-apple-events`, `dbmcco/apple-reminders-mcp`, or one of the Mail servers). The first-party Notes connector is real, but it is **Create/Read/Update only — delete is not advertised**, markdown lands as literal text (not formatting) per GitHub issue #2290 on `modelcontextprotocol/servers`, rich link previews and file attachments are impossible, and it requires a **Pro or Team** plan.

### 4. The harder cases in detail

**Notes (write access):** Three approaches, all imperfect.
1. **AppleScript via `osascript`** — works from macOS 10.13 onward, but: first line of the note is treated as `name` and is *not* formatted, body is HTML in/out, formatting on the first line is silently lost, no native attachments, no rich link previews, no checklist state preservation, no native tags. This is what `sweetrb/apple-notes-mcp`, the upGrowth-documented Anthropic first-party connector, `apple-mcp`, and most others use.
2. **Markdown import (macOS 26 Tahoe / iOS 26 only)** — `File → Import to Notes`. AppleInsider and Apple's own release notes confirm headings, links, lists, bold/italic survive; tables, footnotes, diagrams do not. `ailenshen/apple-notes-mcp` automates this by writing a temp `.md`, calling `open -a Notes`, and auto-confirming the import dialog. **This is the highest-fidelity write path available today**, but it has a ~0.5 s GUI flash, requires Tahoe, and `update_note` = delete + recreate (round-trip is fundamentally lossy because `body of note` returns HTML, not Markdown).
3. **Direct SQLite writes to `NoteStore.sqlite`** — **don't.** Apple stores note content as zlib-gzipped protobuf with CRDT-flavored attribute runs (replicaID/clock substring metadata for sync). Jon Baumann's `threeplanetssoftware/apple_cloud_notes_parser` is the canonical *read* tool — it's been kept current with the format for years. There is no production-quality writer; you would corrupt iCloud sync. Forensic write workflows exist for cracking encrypted notes (Hashcat mode 16200, PBKDF2 → AES key unwrap → protobuf decode) but nobody is writing back.

**Mail:** Send, save-as-draft, attach files, move between mailboxes, set flags/labels (= mail rules in Apple's terms) all work via AppleScript. Two persistent gotchas: (a) `reply with opening window` followed immediately by `set content` silently drops the body when invoked from a non-GUI parent process — fix is `without opening window` (see `sweetrb/apple-mail-mcp` issue #7); (b) AppleScript-only servers timeout on large mailboxes — `imdinu/apple-mail-mcp` solved this with `.emlx` direct reads + FTS5, benchmarked at *"~3ms single email fetch"* and *"~7ms subject search"* on a ~72K-message mailbox.

**Calendar:** EventKit supports everything you'd want: multiple calendars per account, full RFC 5545 recurrence (`daysOfTheWeek`, `daysOfTheMonth`, `weeksOfTheYear`, `monthsOfTheYear`, plus `setPositions`), `EKAlarm` with absolute or relative offset, attendees (read-only — you cannot programmatically *invite* attendees from EventKit on macOS; the OS forces you through the Calendar UI for invitation send), structured locations, and virtual-conference descriptors. AppleScript exposes recurrence as an RFC 5545 RRULE string, which is fiddly. Span behavior on saves: pass `EKSpanFutureEvents` to apply changes to a recurring series.

**Reminders:** EventKit gives you priority (0=none, 1=high, 5=medium, 9=low — the Apple numeric scale, which is what `dbmcco/apple-reminders-mcp` exposes), `EKRecurrenceRule` (still single-rule), `EKAlarm` (time-based or location-based), and **subtasks** via the `parentReminder` relationship (added in iOS 17/macOS 14). Sublists do *not* exist as a first-class concept — what looks like sublists in the UI is the `parentReminder` hierarchy within a single list. Native **tags** (the `#tag` chips introduced in iOS 17) have **no public API**; the workaround is to write `#hashtag` into the notes field, which is what `che-ical-mcp` does explicitly ("tags are searchable via MCP but do not appear as native Reminders.app tags").

### 5. Architecture & permission gotchas

**Build vs. buy:** for your stated goals (CRUD across all four apps, codifiable, no native app dependency, no monthly subscription), build. The existing servers are good references but each makes different tradeoffs and none covers all four apps at the depth you'd want.

**Recommended minimal stack:**
1. **Swift CLI (one binary)** that does Reminders + Calendar via EventKit. Borrow structure from `keith/reminders-cli` or `schappim/ekctl`. Code-sign with entitlements (`codesign --force --sign - --entitlements yours.entitlements`) so TCC remembers the grant.
2. **AppleScript helpers** for Mail and Notes, invoked via `subprocess.run(["osascript", ...])` from Python. For Notes writes specifically, prefer the Markdown-import path if you're on Tahoe.
3. **Python MCP server (stdio)** using `mcp` (the official SDK) or FastMCP. Stdio is the right transport: Claude Desktop spawns it as a subprocess and the server inherits the right TCC context — *until* it doesn't.

**The TCC trap** (the single most-reported failure mode):
- macOS keys Automation permissions by the requesting binary's code-signing identifier. Claude Desktop spawns MCP servers through a helper at `/Applications/Claude.app/Contents/Helpers/disclaimer`, which has a generic non-reverse-DNS identifier; this prevents TCC from persisting Automation grants (`anthropics/claude-code` issues #36832 and #27557).
- **Workaround**: launch Claude from the terminal the first time so the prompt is attributed to your shell/Ghostty/iTerm parent (documented at `lenticular.zone/macos-tcc-claude-mcp/`). Once TCC has the grant, future invocations work. Or grant **Full Disk Access** to `Claude.app` itself, which suppresses launch-time prompts (but a second prompt may still fire on the first user message).
- For a daemon, sign your Swift CLI with a stable bundle ID (`com.yourdomain.appletools`) so TCC can persist the grant against *your* binary, not the helper.

**Stdio vs. SSE/HTTP:** Use **stdio**. Native macOS API calls need to inherit the desktop session's TCC context; a remote SSE server would run under a different user/launchd context and would re-prompt or silently fail. The only reason to use HTTP is to share the server across machines, which collides with the locality of EventKit/AppleScript permissions anyway.

## Details

### Conflicting or recently-changed claims worth flagging in any docs you write

- **The "Anthropic ships a Reminders/Calendar/Mail connector for macOS Desktop" claim that's floating around the web is wrong.** Anthropic's own help center documents these as iOS-only. The macOS Desktop first-party connectors today are Apple Notes and iMessage (both since July 2025). If your current setup uses these on macOS, you're running someone else's MCP server.
- **Markdown import in Notes is macOS 26 Tahoe only.** This is the biggest recent change in this entire space. If you're on Sequoia (15) or earlier, the Markdown-import write path doesn't exist.
- **EventKit "full access" vs. "write-only" is a macOS 14+ split.** Older code that calls `requestAccess(to: .reminder)` works but only gets write-only access on newer OSes. Use `requestFullAccessToReminders()` / `requestFullAccessToEvents()`.
- **Apple's Reminders tag API:** still no public API as of EventKit in macOS 15/Sequoia. Every MCP server claiming "tag support" is stuffing `#hashtag` into the notes field. `mcp-server-apple-events` and `che-ical-mcp` are explicit about this limitation.
- **Notes SQLite is reverse-engineered, not documented.** Apple has changed the protobuf format multiple times. Treat it as read-only for forensics/export only.

### Repos worth evaluating tonight (in priority order)

1. **`FradSer/mcp-server-apple-events`** — closest to your end-state architecture (TypeScript MCP + Swift EventKit CLI). Read its `EventKitCLI.swift` for the alarm/recurrence/location patterns.
2. **`schappim/ekctl`** — cleanest Swift+EventKit CLI with JSON output and proper entitlements signing. Best starting point if you want to roll your own CLI rather than fork.
3. **`keith/reminders-cli`** — battle-tested Swift CLI (~746★). Read its issues for the long tail of TCC edge cases.
4. **`imdinu/apple-mail-mcp`** — best Mail performance pattern (`.emlx` + FTS5). Read-only today; you'd add writes via AppleScript.
5. **`sweetrb/apple-notes-mcp`** — most complete AppleScript-based Notes server; read its `get-checklist-state` SQLite bypass and its v1.4.0 reply-body fix in the Mail sibling repo.
6. **`ailenshen/apple-notes-mcp`** — only server that produces natively-formatted Notes; Tahoe-only. Worth reading even if you're not on Tahoe yet.
7. **`threeplanetssoftware/apple_cloud_notes_parser`** — definitive read-only Notes parser. The README is the best documentation of the `NoteStore.sqlite`/protobuf format you'll find anywhere.

## Recommendations

**Stage 1 (this week — confirm what you already have):**
- Open Claude Desktop → Settings → Connectors. Anything labeled "Apple Notes" or "iMessage" with the Anthropic logo is first-party. Anything else (Reminders, Calendar, Mail) is third-party.
- Inspect `~/Library/Application Support/Claude/claude_desktop_config.json` — that's where third-party MCP servers register.
- Verify Notes capabilities with prompts: "Create a note titled 'Test' with a bulleted list." If bullets render as `* item` literally, you're on AppleScript (first-party or not); if they render as native bullets, you're on the Tahoe Markdown-import path. **If you're on Sequoia or earlier, you have no fully-faithful native-format Notes write path today.**

**Stage 2 (this weekend — minimal viable stack):**
- Install `keith/reminders-cli` or build `schappim/ekctl` from source. Grant Reminders + Calendar Full Access in System Settings. Smoke-test from terminal.
- `pipx install apple-mail-mcp` (`imdinu/apple-mail-mcp`) for fast Mail reads. Grant Mail Full Disk Access.
- Decide on a Notes server: `ailenshen/apple-notes-mcp` if you're on Tahoe (highest fidelity), `sweetrb/apple-notes-mcp` otherwise.
- Add all three to `claude_desktop_config.json`, restart Claude (Cmd-Q, not close), verify the hammer icon shows the tool count.

**Stage 3 (next sprint — your own MCP server):**
- Fork `FradSer/mcp-server-apple-events` if you want maximum coverage with TypeScript, **or** start fresh with FastMCP + a small Swift CLI you control. The Swift CLI should be a single binary with subcommands (`event create`, `event list`, `reminder add`, `reminder complete`, ...) that emit JSON.
- Code-sign the binary with a stable identifier so TCC remembers the Reminders/Calendar grants.
- Wrap Mail and Notes in AppleScript via `osascript`. Keep AppleScript strings in `.applescript` files in a `scripts/` directory, not inline in Python — easier to test in Script Editor.
- Use stdio transport. Add a `--debug` mode that logs to stderr (stdout is reserved for JSON-RPC).
- Add idempotency keys to writes so retries on timeout don't double-create reminders (this is what `che-ical-mcp` does; everyone eventually needs it).

**Benchmarks that should make you change strategy:**
- If Tahoe ships a public Notes framework or extends EventKit to cover Notes (watch **WWDC 2026, kicking off June 8** per Apple's newsroom press release of March 23, 2026: *"WWDC26 will kick off June 8 with the Keynote and Platforms State of the Union… taking place June 8–12"*) → drop AppleScript for Notes immediately.
- If Anthropic ships first-party macOS Desktop connectors for Reminders/Calendar/Mail (likely, given they exist on iOS) → re-evaluate whether your custom server still pays for itself. The current iOS connectors are EventKit-based and likely to port directly.
- If your `osascript` round-trip latency exceeds ~500 ms per call (it can on cold-start Mail.app), switch to direct `.emlx` + SQLite reads à la `imdinu/apple-mail-mcp`.

## Caveats

- macOS TCC behavior is *the* dominant pain point. Expect to spend more time on permissions than on code. The community has not converged on a clean answer; even Anthropic's own Claude Code has open bugs (#23550, #27557, #36832, #50735) about the helper-binary identifier problem.
- Anthropic's connector landscape changes rapidly — the iMessage and Apple Notes Desktop connectors landed in July 2025; Reminders/Calendar/Mail Desktop connectors are plausible additions. Anything in this report about which apps have first-party connectors should be re-checked at WWDC 2026 (June 8) and at the next Anthropic Desktop release.
- The Notes SQLite protobuf format is undocumented and Apple changes it. Treat `NoteStore.sqlite` as read-only for export/search only. Do not write back.
- EventKit "attendees" support on macOS is read-mostly: you can enumerate attendees on events you receive, but creating new invitations programmatically is restricted (the system routes through the Calendar UI for sending).
- Reminders tags, Notes rich link previews, Notes native attachments, and Mail's smart-mailbox synthesis all have **no public API**. Workarounds exist (hashtag in notes, plaintext URLs in note body, file references via `file://` links) but they are not equivalent to the native features.
- `keith/reminders-cli` is mature but small in scope (no recurrence input flags); for full feature parity you'll end up writing your own CLI anyway.