---
name: reference-linux-package-manager-strategy
description: "verified package-install pattern for the Ubuntu dev box — which utility for daemons vs GUI vs CLI, and why"
metadata:
  node_type: memory
  type: reference
  last_updated: 2026-06-20
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

Verified (3 web-research passes, 2026-06) package-management pattern for the Ubuntu dev laptop. There is **no single "brew for Linux"** that handles everything — the honest tiering:

- **System daemons** (docker, tailscale, nvidia-container-toolkit, zabbix) → **native apt**. Hard architectural wall: Homebrew won't wire systemd units (tailscale closed-wontfix), Nix can't manage system services on non-NixOS. Prefer the vendor's OWN apt repo, not snap.
- **GUI apps** → **flatpak/Flathub** — EXCEPT where the vendor's apt repo is the official channel and sandboxing breaks things:
  - **VS Code → Microsoft apt repo** (`packages.microsoft.com/repos/code`). Flathub build is unofficial; sandbox breaks integrated terminal / host toolchains / `$PATH` / dev-containers. NOT flatpak.
  - **Chrome → Google apt repo** (`dl.google.com/linux/chrome/deb`). No official Chrome flatpak/snap exists at all (only Chromium / unofficial wrappers).
  - QGIS, Signal, etc. → flatpak is fine (QGIS 4.x via `org.qgis.qgis//stable`; note `//lts` branch is much older).
- **CLI / dev tools** → **apt universe** if well-packaged (jq, alacritty), **official `stable`-codename vendor repo** if one exists (gh = `cli.github.com/packages stable`), **GitHub-release `.deb`** for freshness without PPA risk (fastfetch). Homebrew is **overkill** for ~6 tools (adds a 2nd package manager + ~500MB) — only worth it for macOS parity or 10+ unpackaged tools.

**Golden rule (learned the hard way):** prefer repos whose suite is **codename-agnostic** (`stable`, or `stable/deb/$(ARCH) /`) — these survive `do-release-upgrade`. **Avoid codename-pinned PPAs** (`...noble.sources` with `Suites: noble`) — they ALL got disabled on the 24.04→26.04 upgrade and had to be repointed/dropped one-by-one.

Ties into [[project-portable-dev-machine-north-star]]. Full per-tool detail + sources: `~/Documents/notes/journal/2026-06-20-ubuntu-26.04-migration-runbook.md`.
