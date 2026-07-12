# mocks — mock session maps

Three mock **session maps** built from real situations (sanitized). These are the data that Claude Design renders into design directions in Phase 1 — real structure, real text, no lorem ipsum.

**The schema below is PROVISIONAL.** It exists so the three mocks are consistent and so designs have something concrete to render. It is NOT the Phase 3 map-schema decision — hold it loosely; it will be reworked.

Each mock ships two files:
- `mock-X.json` — the session map data
- `mock-X.md` — the situation, what a correct render must show, and which design demonstrables this mock stresses

## Provisional schema

```jsonc
{
  "session": {
    "surface": "claude.ai | claude-code",
    "title": "...",
    "date": "YYYY-MM-DD",
    "compaction_events": [ { "after_node": "n07", "note": "context compacted here" } ]
  },
  "nodes": [
    {
      "id": "n01",                     // stable identity — annotations will reference node@version
      "version": 2,                    // bumps on every in-place update
      "type": "topic | move | decision | open-question",
      "title": "short spine label",
      "summary": "current consolidated reading — must scan clean top-to-bottom",
      "status": "done | active | open | false-alarm | dead-end",
      "parent": "n00 or null",         // tree; topics at top level
      "residuals": [                   // wrong turns / detours — folded behind the node, never in the spine
        { "label": "...", "detail": "...", "provenance": [ { "transcript": "...", "lines": [10, 42] } ] }
      ],
      "history": [                     // superseded versions, oldest first
        { "version": 1, "summary": "what this node said before", "superseded_because": "..." }
      ],
      "provenance": [ { "transcript": "path-or-session-id", "lines": [120, 188] } ],
      "quote": { "text": "verbatim transcript quote", "lines": [150, 152] }   // decision nodes ONLY; never paraphrase
    }
  ]
}
```

Rules baked in from the brief: rework UPDATES nodes (version bump + history entry) instead of appending; dead ends fold into residuals; decisions anchor to verbatim quotes; every node carries provenance pointers; the spine must read as "what we did and how we approached it" with corrections demoted behind interaction.

Sanitization: no work credentials, hostnames, IPs, or proprietary identifiers in any mock.
