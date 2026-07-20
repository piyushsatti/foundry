# Docs Context Retrieval

**As the rulebook and the wiki grow, loading all of it into Claude's context every time is wasteful and will eventually overflow — but shrinking the guides to fit is the wrong fix.** The right answer is retrieval: pull only what's relevant, when it's relevant.

> **Status:** draft — documented now, built later.

## The problem

Style, writing, and conventions guidance keeps expanding as we add decisions. So does the wiki. If Claude must read all of it to author or check a page, cost grows with the corpus and eventually breaks the context budget. Trimming the guides to stay small would trade correctness for convenience — exactly backwards.

## The approach

A tool — an **MCP server or an agent** — sits between Claude and the wiki:

1. Claude Code raises a documentation question ("how do I format a diagram that's too big?").
2. The tool searches the wiki and extracts the specific decided methodology.
3. That section is injected back as context.

Claude always has the latest relevant guidance; the guides stay as big as they need to be.

## Limits

Retrieval quality depends on the wiki being well-structured and the query being specific — the same discipline the rulebook already enforces. A vague question returns vague context.

## Open questions

- MCP server vs agent — which fits the Claude Code loop better?
- Index/retrieval mechanism (full-text, embeddings, or the frontmatter `summary`/`sources` as a lightweight index?).
- Does the same tool also power a publish transform (see [publishing](../meta/publishing))?

## See also

- [Roadmap](overview) · [Meta / writing](../meta/writing)
