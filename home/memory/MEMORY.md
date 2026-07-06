---
name: ""
metadata: 
  node_type: memory
  last_updated: 2026-06-01
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

- [Proactive data quality](feedback_data_quality_proactive.md) — surface and prompt fixes for quality issues, don't silently work around them
- [Diagnose before fixing](feedback_diagnose_before_fixing.md) — verify assumptions with evidence (logs, reproductions) before writing fix code
- [Memory criteria](feedback_memory_criteria.md) — document everything worthwhile, remember only what repeats; propose saves with evaluation
- [Promoting memory to docs](feedback_promoting_memory_to_docs.md) — when moving content out of memory, capture active-use framing in the doc and cross-link from consumers, else the surfacing is lost
- [Dev machine problems log](reference_dev_machine_problems_log.md) — `~/Documents/notes/journal/dev-machine-problems.md` tracks dev-machine setup tasks/resolutions
- [Global CLAUDE.md stays generic](feedback_global_claude_md_generic.md) — no project/language/employer specifics in `~/.claude/CLAUDE.md`; those go in project CLAUDE.md
- [Incremental walkthroughs](feedback_incremental_walkthroughs.md) — one step at a time for interactive procedures; don't wall-of-text
- [Workflow schema placement](feedback_workflow_schema_placement.md) — don't schema a workflow's heavy file-writing stage; only the small verdict stages
- [Claude guard coverage](reference_claude_guard_coverage.md) — hooks guard the agent's Bash tool calls only; `!` bang-shell bypasses them, and verify the bwrap sandbox is actually live (it wasn't on 2026-06-01)
- [Long output to file](feedback_long_output_to_file.md) — write long runbooks/reference output to a markdown file, not just the TUI chat; repaint-TUI scrollback garbles long messages on scroll-up (tmux doesn't fix it)
- [Worktree .claude breaks sandbox](reference_worktree_claude_symlink_breaks_sandbox.md) — a symlinked `.claude` in a git worktree makes the bwrap sandbox fail to start (EISDIR → all Bash dead); fix = real `.claude` dir, not a symlink. Affects every `/worktree`-made worktree
- [Plan → red/blue → implement](feedback_plan_redblue_then_implement.md) — non-trivial work gets a durable dated plan doc + adversarial review before any code/config change
- [Plan blast radius](feedback_plan_blast_radius.md) — every plan file includes a brief blast-radius: what artifacts a change touches + at what scope (global/project/file), what's untouched, reversibility
- [Consolidate into one surface](feedback_consolidate_single_surface.md) — fold reference info into a single master doc + pointer stubs; don't spin up parallel surfaces that drift and go stale
- [Separate conflating topics](feedback_separate_conflating_topics.md) — when two related-but-distinct topics tangle, stop and ask to split them or take one at a time; reasoning about both at once produces conflated, wrong answers
- [Linux package manager strategy](reference_linux_package_manager_strategy.md) — no single "brew for Linux"; daemons→apt, GUI→flatpak (but VS Code/Chrome→vendor apt), CLI→universe/official-stable-repo/release-deb; avoid codename-pinned PPAs (break on dist-upgrade)
- [bwrap apparmor profile is load-bearing](reference_bwrap_apparmor_profile_load_bearing.md) — `/etc/apparmor.d/bwrap` grants bwrap `userns` and keeps Claude's sandbox alive under userns restriction; don't delete it as "cruft"
- [NVIDIA VGL device perms on Ubuntu](reference_nvidia_vgl_device_perms_ubuntu.md) — persist `/dev/nvidia*` group=vglusers ONLY via udev `RUN+=` on the PCI add event; `KERNEL==`/modprobe-GID/systemd-units all fail (ub-device-create hardcodes root:root)
