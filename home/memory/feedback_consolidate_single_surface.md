---
name: feedback_consolidate_single_surface
description: Prefer consolidating related reference info into ONE master doc over creating new parallel surfaces; too many overlapping docs drift apart and go stale
metadata: 
  node_type: memory
  last_updated: 2026-06-17
  type: feedback
  originSessionId: b5512805-6c83-4854-aa5f-61523baac9e6
---

When capturing or documenting reference info (host inventories, runbooks, network maps, etc.), **fold it into a single existing master document rather than spinning up a new parallel surface.** If several docs already overlap, consolidate them into one and replace the merged originals with one-line "Moved → [[master]]" pointer stubs (don't hard-delete — old links still resolve).

**Why:** the user's words — "we don't want too many surfaces, otherwise things drift apart and become useless." Proven in practice: two overlapping reference docs went stale (a host ended up listed at the wrong IP in one of them) precisely because the same facts lived in multiple places.

**How to apply:**
- Before writing a new reference doc, check whether an existing one should absorb it instead.
- Keep deep specialized docs separate but cross-linked (e.g. NAS mounts, DB schema) rather than bloating the master.
- Claude memory should be a compact *pointer* to the human master doc (source of truth), not a duplicate copy of it — e.g. a memory that just points at a project's master `infrastructure.md` rather than duplicating its contents.
- Aligns with [[feedback_promoting_memory_to_docs]].
