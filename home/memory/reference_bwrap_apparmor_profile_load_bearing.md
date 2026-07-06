---
name: reference-bwrap-apparmor-profile-load-bearing
description: "/etc/apparmor.d/bwrap is NOT junk — it grants bwrap userns and keeps Claude's sandbox working; don't delete it"
metadata:
  node_type: memory
  type: reference
  last_updated: 2026-06-20
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

`/etc/apparmor.d/bwrap` is the **canonical profile that grants `/usr/bin/bwrap` the `userns` capability**:

```
profile bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,
  include if exists <local/bwrap>
}
```

Under `kernel.apparmor_restrict_unprivileged_userns=1` (default on 24.04 AND 26.04), this profile is **load-bearing for Claude Code's bwrap sandbox** — without it (or the stock `bwrap-userns-restrict`), bwrap can't create user namespaces and the Bash tool dies.

**Do NOT delete it** as "unknown-provenance cruft" — a migration plan mislabeled it that way; reading it before deleting (correctly) reversed the call. On 26.04 both this profile AND stock `bwrap-userns-restrict` coexist; the sandbox works. Read-before-delete saved the sandbox here.

Related sandbox gotchas: [[reference-worktree-claude-symlink-breaks-sandbox]], [[reference-claude-guard-coverage]].
