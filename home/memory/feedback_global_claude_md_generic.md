---
name: feedback_global_claude_md_generic
description: Global ~/.claude/CLAUDE.md holds only generic workflow discipline — no project/language/employer specifics
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b6b08d33-2215-4763-8a26-671e94e61686
last_updated: 2026-05-29
---

The global `~/.claude/CLAUDE.md` must contain only generic, cross-project workflow discipline. Keep OUT: project lists, languages/tech stacks, employer/domain descriptions, and output-style directives. Those belong in each project's own CLAUDE.md (or, for output style, the on-demand `/output-style` toggle).

**Why:** On 2026-05-29 Piyush asked three times in one session to strip specifics from the global file — first the stale project list, then the style directive, then "remove language or project specific things… that's for that project's specific claude.md." Revealed a firm preference: the global file is workflow rules only; specificity drifts stale and pollutes every session.

**How to apply:** When editing `~/.claude/CLAUDE.md`, reject additions that name a project, language, framework, or employer detail. If such context seems needed, put it in the relevant project's `.claude/CLAUDE.md`. Output style is controlled by `outputStyle` + the toggle, not by a CLAUDE.md line. See [[feedback_promoting_memory_to_docs]] and [[feedback_memory_criteria]].
