---
name: onboard
description: Interactive machine onboarding — walks through shell, editor, git, Claude, and theme customization
user_invocable: true
---

# Machine Onboarding

You are running interactive onboarding for a new machine. The bash setup script (Phase 1) has already installed packages, linked dotfiles, and deployed Claude Code hooks. Your job is Phase 2: walk the user through **personalizing** their setup.

## Rules

1. **One question at a time.** Never batch 4+ choices. Use AskUserQuestion for every decision.
2. **Show impact.** Don't just list options — explain what each choice does and why someone would pick it.
3. **Mark recommended options.** Read `defaults.yml` and mark the default choice with "(Recommended)".
4. **Don't skip questions.** Even if someone picked "Default" in Phase 1, show every question here. They already installed the tools — now they're fine-tuning.
5. **Read before writing.** Before modifying any config, read the current version first.
6. **Back up before overwriting.** If you're about to overwrite a file, copy the original to `.bak` first.

## Setup

Before asking questions:

1. Read `infrastructure/defaults.yml` to load recommended values
2. Read `infrastructure/preferences/` files for context on why things are recommended
3. Check what's currently installed (`command -v` for tools, `ls -la` for symlinks)
4. Announce: "Welcome to machine customization! I'll walk you through 4 categories. Each question has a recommended option — press enter to accept or pick your own."

## Category 1: Shell & Terminal

Announce: "First up — your shell experience. This covers your prompt, aliases, terminal multiplexer, and autocompletion."

### Q1.1: Starship Prompt Preset

Read the current `~/.config/starship.toml` and describe what it does. Then ask:

- **Plain Nerd (Recommended)** — Minimal: directory + git branch/status + active language + command duration. Current config.
- **Bracketed Segments** — Each module wrapped in [brackets]. More structured, slightly busier.
- **Pastel Powerline** — Colored segments with arrow separators. Flashy, needs Nerd Font (already installed).
- **Keep current** — Don't change anything.

If user picks a preset other than current, run `starship preset <name> > ~/.config/starship.toml`.

### Q1.2: Shell Aliases

Read `~/.bash_aliases` and show the current aliases. Then ask:

- **eza-based (Recommended)** — `ls=eza --icons`, `ll=eza -la`, `lt=eza --tree`. Current config.
- **lsd-based** — Similar icons/colors but uses lsd instead of eza.
- **Plain coreutils** — No replacements. `ls`, `ll=ls -la`.
- **Keep current + add custom** — Keep what's there. Free text: "What aliases do you want to add?"

### Q1.3: Tmux Configuration

Read `~/.tmux.conf` and summarize the current setup. Then ask three sub-questions:

**Prefix key:**
- **Ctrl+Space (Recommended)** — Ergonomic, doesn't conflict with most apps. Current config.
- **Ctrl+a** — Screen-style classic. Conflicts with "go to beginning of line" in bash.
- **Ctrl+b** — tmux default. Harder to reach but universal in tutorials.

**Mouse mode:**
- **Enabled (Recommended)** — Click to select panes, scroll with mousewheel. Current config.
- **Disabled** — Keyboard only. Better for SSH-heavy workflows.

**Session persistence (resurrect + continuum):**
- **Enabled (Recommended)** — Auto-save every 10 min, auto-restore on start. Survives reboots. Current config.
- **Disabled** — Fresh sessions every time.

### Q1.4: ble.sh Autosuggestions

- **Enabled (Recommended)** — Fish-like autosuggestions as you type. 100ms delay. Current config.
- **Disabled** — Vanilla bash completion only. Faster shell startup.
- **Customize delay** — Ask for delay in ms (default: 100).

### Q1.5: fzf Integration

Read `~/.bashrc` for fzf configuration. Then ask:

- **Full integration (Recommended)** — Ctrl+R history search, Ctrl+T file finder with bat preview, Alt+C directory jump with eza preview. Current config.
- **Basic** — Ctrl+R history search only. No file previews.
- **Disabled** — Don't configure fzf keybindings.

### Q1.6: bat Theme

- **Catppuccin Mocha (Recommended)** — Matches your terminal theme. Current config.
- **Dracula** — Purple-heavy dark theme.
- **gruvbox-dark** — Warm retro dark theme.
- **ansi** — Uses your terminal's ANSI colors. Most compatible.

Write choice to `~/.config/bat/config`.

---

## Category 2: Editor & Git

Announce: "Next — your code editor and git workflow."

### Q2.1: Default Editor

This sets `$EDITOR` and `$VISUAL` in your bashrc and git's `core.editor`.

- **VS Code (Recommended)** — `code --wait`. Opens files in VS Code, waits for close. Current config.
- **Neovim** — `nvim`. Terminal-based, powerful. Needs separate configuration.
- **Vim** — `vim`. Available everywhere.
- **Nano** — `nano`. Simplest. Good for beginners.

If changed: update `~/.bashrc` EDITOR/VISUAL vars and `git config --global core.editor`.

### Q2.2: VS Code Extensions

Read `infrastructure/system/dotfiles/vscode/extensions.txt`. Show the full list grouped by category:
- **AI**: Claude Code
- **Theme**: Catppuccin theme + icons
- **Python**: Python, Pylance, Ruff, Debugpy, envs
- **JavaScript**: ESLint, Prettier
- **Containers**: Docker, Kubernetes, Remote SSH/Containers
- **Git**: GitLens, Git Graph, GitHub Actions
- **Languages**: C++, CMake, Makefile, YAML
- **Other**: Markdown lint, PDF viewer, Jupyter suite

Then ask:
- **Install all 37 (Recommended)** — Full development environment.
- **Let me pick** — Show multi-select grouped by category.
- **Skip** — Don't install any extensions.

### Q2.3: Git Identity

This is required — git won't let you commit without it.

Ask for (using free text input):
- **Name**: "What name should appear in your git commits?"
- **Email**: "What email should appear in your git commits?"

Run:
```bash
git config --global user.name "Their Name"
git config --global user.email "their@email.com"
```

### Q2.4: Git Commit Signing

- **No signing (Recommended)** — Simplest. Good for personal projects and most teams.
- **GPG signing** — Ask for GPG key ID. Configures `commit.gpgsign = true`.
- **SSH signing** — Ask for SSH key path. Uses SSH keys for commit verification.

### Q2.5: Git Diff Tool

Read `~/.gitconfig` for current delta config. Then ask:

- **delta side-by-side (Recommended)** — Beautiful colored diffs with line numbers. Current config.
- **delta unified** — Same colors, single-pane view. Better for narrow terminals.
- **diff-so-fancy** — Colorful but simpler. Good fallback if delta is too heavy.
- **Plain git diff** — No pager enhancements.

### Q2.6: Pull Strategy

- **Merge (Recommended)** — `git pull` creates merge commits. Preserves history. Current config.
- **Rebase** — `git pull --rebase`. Linear history. Can cause issues with shared branches.

---

## Category 3: Claude Code

Announce: "Now let's configure Claude Code — your AI pair programmer. This is where the real customization happens."

### Q3.1: Hooks

Read `infrastructure/defaults.yml` for the hook list. Show them in three groups:

**Safety Hooks** (protect against mistakes):
| Hook | What it does |
|------|-------------|
| secret-scanner | Blocks writes containing API keys, tokens, credentials |
| sensitive-file-guard | Blocks edits to .pem, .key, credential files |
| main-branch-guard | Blocks commits/pushes directly to main/master |
| destructive-sql-guard | Blocks DROP TABLE, TRUNCATE in psql commands |

**Quality Hooks** (enforce standards):
| Hook | What it does |
|------|-------------|
| conventional-commit | Enforces feat:/fix:/chore: commit format |
| test-file-guard | Asks before modifying test files |
| ai-artifact-guard | Prevents AI docs from landing in project trees |
| docker-compose-validator | Validates docker-compose after edits |
| python-formatter | Auto-formats Python with ruff after edits |
| python-linter | Lints Python with ruff after edits |

**Observability Hooks** (track activity):
| Hook | What it does |
|------|-------------|
| audit-log | Logs all bash commands to ~/.claude/audit.log |
| session-log | Records session summaries at stop |
| todo-detector | Surfaces TODO/FIXME at session start |
| pending-cleanup-check | Reminds about pending cleanup tasks |
| project-bootstrap-check | Detects missing project infrastructure |

For each group, ask with multi-select (all pre-selected as recommended):
- "Which safety hooks do you want enabled?"
- "Which quality hooks do you want enabled?"
- "Which observability hooks do you want enabled?"

Then modify `~/.claude/settings.json` — for disabled hooks, remove their entries from the hooks configuration.

### Q3.2: Statusline

Show a description: "The statusline shows your current folder, git branch, active model, and API rate limit in the Claude Code UI."

- **Enabled (Recommended)** — Catppuccin-colored status bar. Current config.
- **Disabled** — Clean UI with no status bar.

### Q3.3: Plugins

Read the plugin list from defaults.yml. Show each with a one-line description:

| Plugin | Purpose |
|--------|---------|
| superpowers | Enhanced skills and workflows |
| context7 | Library documentation lookup |
| feature-dev | Feature development agents |
| serena | Semantic code navigation |
| commit-commands | Git commit workflows |
| claude-md-management | Project context management |
| skill-creator | Build custom skills |
| pyright-lsp | Python type checking |
| hookify | Create hooks from conversation |
| playwright | Browser testing |
| frontend-design | UI design assistance |
| playground | Experimental features |
| data | Data analysis tools |

Ask:
- **All recommended (Recommended)** — Enable everything above.
- **Let me pick** — Multi-select from the list.
- **Minimal** — Just superpowers + commit-commands.

### Q3.4: Sandbox Settings

Explain: "The sandbox controls which files and network hosts Claude can access. This prevents accidental writes to sensitive locations."

- **Default (Recommended)** — Write to ~/projects + ~/.claude. Block reading ~/.ssh, ~/.aws/credentials, ~/.gnupg. Allow github.com, pypi.org, npmjs.org.
- **Customize** — Ask which directories to allow/block.
- **Disable** — No sandbox. Full access. (Not recommended for security.)

### Q3.5: Permission Presets

Explain: "Permissions control which commands Claude can run without asking. The recommended set auto-allows read-only commands (git status, ls, find) and blocks destructive ones (rm -rf, git push --force)."

- **Recommended (Recommended)** — 100+ read-only allows, 30+ destructive denies. Current config.
- **More permissive** — Also auto-allow git commit, git push, npm install.
- **More restrictive** — Only auto-allow git status, ls, cat. Ask for everything else.
- **Review manually** — Show the full allow/deny lists and let the user edit.

---

## Category 4: Theme & Aesthetics

Announce: "Final category — making everything look consistent and beautiful."

### Q4.1: Color Theme

- **Catppuccin Mocha (Recommended)** — Warm dark theme. Pastel colors on dark background. Current config across all tools.
- **Catppuccin Latte** — Light variant. Same colors, white background.
- **Gruvbox Dark** — Warm retro palette. Orange/yellow/green.
- **Dracula** — Cool dark theme. Purple/cyan/green.
- **Tokyo Night** — Blue-tinted dark theme. Calm.
- **Nord** — Arctic blue palette. Muted.

If changed from Catppuccin Mocha: note which config files need updating (the user can do this manually or you can offer to help with the ones you know how to change — bat config, VS Code settings).

### Q4.2: Apply Theme To

Multi-select (all pre-selected as recommended):
- Alacritty (terminal colors)
- tmux (status bar)
- bat (syntax highlighting)
- VS Code (editor theme)
- fzf (finder colors)

### Q4.3: Terminal Font

- **JetBrainsMono Nerd Font (Recommended)** — Programming ligatures + Nerd Font icons. Already installed.
- **FiraCode Nerd Font** — Popular ligature font. Rounder characters.
- **CascadiaCode Nerd Font** — Microsoft's monospace font. Clean.
- **Hack Nerd Font** — No ligatures. Very readable at small sizes.

If changed: update alacritty.toml `font.normal.family` and VS Code `editor.fontFamily`.

### Q4.4: Terminal Opacity

- **0.95 (Recommended)** — Slight transparency. Can see desktop wallpaper through terminal. Current config.
- **1.0** — Fully opaque. No transparency.
- **0.90** — More transparent. Nice with dark wallpapers.
- **Custom** — Ask for value between 0.5 and 1.0.

If changed: update alacritty.toml `window.opacity`.

---

## After All Questions

1. Summarize all choices made across all 4 categories
2. Show which files were modified
3. Print a "Setup Complete" message with:
   - Reminder to restart shell for bash changes
   - Reminder to restart VS Code for extension/theme changes
   - Reminder to restart tmux for tmux config changes
4. Offer: "Want me to explain any of these tools in more detail?"
