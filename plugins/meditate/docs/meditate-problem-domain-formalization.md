> **Vendored into the meditate plugin 2026-07-05** from
> `pslap:~/Documents/personal/notes/infrastructure/meditate-problem-domain-formalization.md`.
> This copy is canonical from now on; the pslap original is historical. Plugin prose
> (`agents/curator.md`, `skills/*`) still cites the old path — repointing is a pending repair item.

---
title: "meditate — Problem-Domain Formalization (model + research record)"
date: 2026-06-29
status: model COMPLETE; implementation designed + built 2026-07-03 (see §10 → implementation plan)
related:
  - mem-arch-interface-contract.md            # the WHAT / build-boundary (shape)
  - meditate-decisions-and-findings.md         # the chronological decision log
  - 2026-06-24-memory-architecture-spec.md     # the original spec
---

# meditate — Problem-Domain Formalization

## 1. Context & purpose

meditate began as **vertical promotion**: moving one item between stores (memory ⇄ rule) or up/down scope, driven by per-item usage signals. This session reframed it as a full **operation algebra** over a knowledge grid, adding the **horizontal** axis (restructuring the corpus: merge / split) — what we call **cross-pollination**.

Critical stance: **the current memory store has NO authority.** It is accreted debt (duplication, conflation, a dead-enum still in one memory). So `normalize` re-derives structure from the **content's meaning**, treating existing file boundaries as noise — not as a reference to preserve.

This doc is the **theory / why** surface. Companions: `mem-arch-interface-contract.md` = the *what / shape* (frozen build boundary); `meditate-decisions-and-findings.md` = the *chronological* decision log.

The model below is complete and every fork is decided (this session); the **implementation** (building it into the curator + apply skills) is designed and built as of 2026-07-03 — see §10.

---

## 2. The operation space

**Cell.** Every knowledge item occupies one **cell** = (store × scope × genericity × type):

- store ∈ {M = memory (recalled facts), R = rule (always-on CLAUDE.md/.local)} — extensible: K = serena/code.
- scope = `{depth, role}` mapping (depth = hops below $HOME; role ∈ home|repo|worktree|sub|dir) — the v2 frontmatter.
- genericity ∈ {generic, specific} — the export fence.
- type ∈ {user, feedback, project, reference, decision}.

**Atoms / items / layers.** An **atom** = an indivisible proposition (the conserved quantity — operations rearrange atoms, never destroy meaning; this is why archive-not-destroy). An **item** = a set of atoms (one memory file / one rule block). A **layer** = all items in one cell.

**Generators** (every operation is one of these or a composite):

| class | generators | axis |
|---|---|---|
| horizontal | `split` (1→N, refine), `combine` (N→1, coarsen) | grain (within a cell) |
| vertical · store | `promote-to-rule` (M→R), `demote-rule` (R→M) | store |
| vertical · scope | `promote` / `demote` | scope (broader⇄narrower) |
| vertical · fence | `generalize` (spec→gen) / `specialize` | genericity |
| lifecycle | `create`, `deprecate`, `retire` | atom birth/death (non-conservative) |

Note: "moving an atom between items" = `combine ∘ split` (derived, not a primitive).

**Enumeration table** (the named operations → generators):

| named op | generator(s) | class · axis |
|---|---|---|
| split memory / split rule | `split` @ M / @ R | horizontal · refine |
| combine memory / combine rule | `combine` @ M / @ R | horizontal · coarsen |
| promote-memory-to-rule | store-lift (M→R) | vertical · store |
| demote-rule-to-memory | store-lower (R→M) | vertical · store |
| promote-memory / demote-memory | scope lift/lower @ M | vertical · scope |
| promote-rule / demote-rule (scope) | scope lift/lower @ R | vertical · scope |
| generalize / specialize | fence flip | vertical · fence |
| create / deprecate / retire | lifecycle | atom birth/death |

**Naming-ambiguity finding:** "**demote-rule**" is overloaded — it can mean (a) R→M store demotion, or (b) rule-scope-down. Current meditate binds `demote-rule` = R→M (store axis). The enumeration forces disambiguation before more verbs are added (e.g., reserve `demote-rule` for store; name the scope move `narrow-rule`).

---

## 3. Cohesion & normal form

**Cohesion relation `~`.** `a ~ b` = "atoms a, b belong in the same item." It is a **tolerance relation**: reflexive + symmetric, but **NOT transitive**.

**Demonstration:** consider three atoms `fact-A`, `fact-B`, `fact-C` where `fact-A ~ fact-B` (share topic T1) and `fact-B ~ fact-C` (share topic T2) but `fact-A ≁ fact-C` (no shared topic). Cohesion *chains* but does not *close*. Forcing transitivity (single-linkage) collapses fact-A, fact-B, fact-C into one blob — **over-merge**. (Note: a knowledge store kept as several deliberately-separate-but-pairwise-related items — say `host-X` facts and `map-Y` facts linked through a bridge — is itself evidence that cohesion is treated as non-transitive; but the current store has no authority, so this is an illustration of the principle, not a proof from our data.)

**Consequence.** A tolerance relation does not induce a partition (quotient). Its **tolerance blocks** (maximal cliques of `~`) can **overlap** → a **cover**, not a partition → the "normal form" is **not unique**. To keep the verb `normalize` well-defined we must choose a recovery principle.

**The recovery — C + D (decided):**

- **C · extract-and-link:** when a "bridge" atom causes the chaining (it coheres with two otherwise-unrelated clusters), **extract it into its own item and `[[link]]`** to it. This breaks the chain; the residual relation becomes a partition. A `[[link]]` is the recorded image of a cohesion edge that crosses an item boundary.
- **D · human-gated local fixpoint:** with no trusted reference (not the store, not a mechanical quotient), the human is the only cohesion oracle. `normalize` = the **human-ratified local fixpoint** — the curator proposes, a human ratifies. **"normalized" = low churn** (additions ≫ splits/merges); there is no provable global "done."

**Rejected / absorbed:**

- **A · force-transitive (transitive closure / single-linkage): KILLED.** The entity-resolution literature is explicit — *never take the transitive closure of pairwise similarities*; single-linkage chaining is the canonical failure.
- **B · objective-optimum (modularity-γ / MDL / correlation-clustering): ABSORBED** — these are the curator's *internal reasoning aids* (how it reasons about a good cut), not a separate mechanism.

**Vocabulary (locked):** the noun for a complete/cohesive layer = **normal form**; the verb = **normalize**; the law phrasing = *"promote only between normalized layers."*

---

## 4. The stratification law

**Statement.** Let `Canon` = layer states that are fixpoints of {split, combine}. A vertical step `e : c → c′` is **enabled only if `c ∈ Canon ∧ c′ ∈ Canon`**. Firing may knock `c′` out of `Canon`; the system must re-normalize `c′` (horizontal closure) before any further vertical step touches it.

**Dynamics.** A forced alternation: `(→H)* ; →V ; (→H)* ; →V ; …` — normalize to fixpoint, take one vertical step, re-normalize. **Rest state (global equilibrium)** = every layer normalized.

**Two readings:** (rewriting) `→V` is a relation defined only between normal forms; (categorical analogy) objects = normalized layers, morphisms = promotions — a morphism is only defined on objects, never on a half-reduced state.

**Why (not arbitrary).** Normalizing first makes (a) the **unit of promotion** well-defined (you never promote half an atom or one of a duplicate pair) and (b) destination reconciliation **deterministic** (incoming item either matches an existing clique → combine, or is new → add). This is the same instinct as the locked **F1 "no copy-down / no merge against a stale base"** decision: reconcile only against a settled reference.

**A deliberate departure.** The field consolidates **incrementally / automatically** (per-write LLM judge). We choose **batch + stabilize + human-gate** instead — more conservative — justified by the over-merge evidence and the HITL gap (see §9). This is a designed choice, not an oversight.

---

## 5. MERGE design (the combine direction)

- **Conservative default** — empirically, conservative-merge beats aggressive (RMM ablations; Mem0 biases to NOOP). Between merge and keep-separate when unsure → keep separate.
- **Information-content gate** (Mem0): merge only if the result is **richer** than either input — never degrade a detailed item to a vague one.
- **Confidence-band** (Neo4j 3-zone): auto-merge above a high threshold · emit a provisional **`[[link]]` proposal** in the mid band (defer to human) · reject below a floor. Reversible.
- **Cluster-size cap** as a chaining backstop; **never** take the transitive closure.

---

## 6. SPLIT design (the refine direction) — the novel primitive

`split` is **absent from every surveyed agent-memory system** (all consolidation is many→one). We port it from **database normalization** (decomposition theory) + **LLM claim decomposition** (mechanism). Five parts:

### 6.1 Detect

An item must be **one cell × one cohesion-clique**. Triggers:

- **HARD (forced — no judgment):** the item spans ≥2 values on an axis → mixed **genericity** (one file can't be both generic and specific — the fence forbids it), mixed **scope**, mixed **store** (a fact + a rule together), or mixed **type**.
- **SOFT (cohesion):** the item's atom-graph has **≥2 disconnected components** (analogous to **LCOM4 ≥ 2**, the most-reliable software-cohesion split signal) → a clean split; or it is connected **only through a weak bridge atom** → the hard case (handle by extract-and-link).
- LLM-executable detector cues: coordinated independent claims · multiple subjects with distinct lifecycles · vocabulary-valley between halves · mixed types.

### 6.2 Cut

Order: **hard axis-cuts first** (forced), then the cohesion cut via **3NF *synthesis*** (the DB algorithm that guarantees BOTH lossless join AND dependency preservation — NOT BCNF decomposition). For a weak bridge → **extract the bridge atom into its own `[[linked]]` piece**. Mechanism = claim-decomposition rules: split compound→simple, separate appositives, **resolve pronouns / decontextualize** so each piece stands alone.

### 6.3 Lossless gate (all three before ratify)

- **structural (superkey / lossless-join):** the overlap (shared "bridge" atoms) between two pieces must be a **superkey** of at least one piece — i.e. must *uniquely determine* that piece's full content; else the split is **lossy**. **Extract-and-link satisfies this automatically** — the extracted bridge is the key of its own piece.
- **semantic (conservative extension / locality):** no child may introduce inferences about concepts it doesn't own ("a memory must not silently constrain concepts outside its signature").
- **link-fidelity (dependency preservation):** a dependency (cohesion edge) that crosses the cut cannot be enforced locally → **reify it as an explicit `[[link]]`** + a one-line invariant in each child. Each child carries the minimum context to stand alone; the **union of children must entail the original** (nothing dropped).

### 6.4 Floor (don't shred)

Stop when each piece is **one clique** (LCOM4 = 1) with a complete predicate + independent truth-value. Reject a child that is a bare modifier/label (no independent truth value) or is semantically equivalent to its sibling (dedup). If the smallest valid piece is still compound → **escalate to human**. Over-fragmentation's real cost = **recall-time join overhead** (reasoning needs many tiny items rejoined) — the DB "over-normalization" harm.

### 6.5 Gate + execute

The curator **proposes** {N children + each child's cell + the `[[links]]` + the *named* severed dependency}; a human ratifies; the applier writes the N files + links and **archives the original** (tombstone, reversible). Mid-confidence → an `inspect-manually` flag, not an auto-split.

**LOCKED decision — severed-dependency default = SPLIT + LINK** (the 3NF move): when a clean split would sever a dependency that can't be enforced locally, extract the bridge into its own linked piece. This **simultaneously** satisfies lossless (bridge = key of its own piece) AND preserves the dependency (as links); residual cost = recall-time join overhead, capped by the floor. (The alternatives — refuse-split/stay-bundled, or split-clean/co-retrieve — were considered and not chosen.)

**The duality.** `combine` coarsens until each item is one clique; `split` refines until each item is one clique-in-one-cell. **Same fixpoint, opposite directions.** And `split` is exactly what makes an item **promotable** — a single-cell item is "well-typed" for a vertical move (the mechanism behind the stratification law, §4).

**⚠ The irreducible warning (from DB theory):** you cannot *always* guarantee both maximum cohesion (clean split) AND full dependency preservation. The split contract must **name** the sacrificed/linked dependency explicitly — never silently overpromise both. (DB's `TEACH` relation is the canonical counterexample.)

---

## 7. Vertical-axis economics (the cost asymmetry)

- The **store axis** (`promote-to-rule`) carries a **capacity cost** the scope/fence axes do NOT: an always-on rule consumes context every session, and instruction-following **degrades with rule count** (IFScale: ~linear decay, a cliff near ~150 instructions; "Lost in the Middle": mid-file rules are under-weighted; practitioner ceiling ≈ 15 hard rules). So every promotion **dilutes adherence to all other rules** — promotion is conservative by **economics**, not just taste.
- **Promote-to-rule gate** (promote iff ALL): (1) **universality** (fires every session, no exception) · (2) **prevention-value** (its absence causes a real, specific mistake) · (3) **not-already-enforced** (no linter/CI does it) · (4) **not-auto-recorded** (the model doesn't already self-capture it) · (5) **recurrence** ≥3 separate sessions.
- **Demote triggers:** a linter/CI now enforces it · the model self-records it · not violated in >12 months · it reads generically (→ extract to global memory) · rule-budget pressure (~15).
- **Corroborator:** "Governance Decay" — context compaction raises constraint-violation rates sharply, validating the rules/memory durability premise and the P0 durable-memory hook.

---

## 8. Locked decisions (chronological)

- Cross-pollination = the untargeted axis: horizontal corpus restructuring (merge/split/re-home), distinct from vertical per-item promotion.
- Noun for a complete layer = **normal form**; verb = **normalize**.
- Cohesion `~` = a **tolerance relation** (non-transitive) — proven semantically (chaining).
- Recovery = **C + D** (extract-and-link + human-gated local fixpoint); **A** (force-transitive) killed by ER literature; **B** (objective-optimum) absorbed as the curator's reasoning aid.
- "normalized" = **low churn** (no provable global done).
- The grid = (store × scope × genericity × type); a normalized item = one clique in one cell.
- The **stratification law** (normalize before promote) — a deliberate, conservative departure from the field's incremental auto-consolidation.
- `split` is **novel** (no agent-memory prior art) → ported from DB normalization (theory) + LLM claim decomposition (mechanism).
- Severed-dependency default = **split + link** (the 3NF move).
- `demote-rule` naming ambiguity flagged (store vs scope) — disambiguate before adding verbs.

---

## 9. Research appendix — the links + insights

*Six Sonnet research agents (2026-06-29) grounded this model. Sources as surfaced by the agents; canonical papers verified, some practitioner/recent URLs not independently re-verified.*

### Stream 1 — Agent-memory architectures

**Focus:** Survey of production agent-memory systems: consolidation strategies, tier structures, and the HITL gap.

**Key findings:**

- Every production system consolidates automatically (per-write LLM judge, background "sleep-time" idle compute, or graph entity resolution). **No system gates consolidation behind a human** — this is the gap our batch + human-gate design fills.
- Tier structures (episode/semantic/community; working/episodic/semantic/procedural; hot-path vs background) map cleanly onto our rules-vs-facts separation. The store axis is not novel, but the explicit lift/lower algebra is.
- MemGAS names the single-linkage chaining problem in an agent-memory context explicitly; its GMM + entropy router is a clustering approach to granularity that parallels our tolerance-block analysis.
- Zep's temporal validity windows and community summaries, and Graphiti's equivalent, show that consolidation without a time/recurrence axis overpromotes stale items — corroborating the recurrence gate.
- Reflection-based periodic consolidation (Generative Agents) and idle-period consolidation (Letta) both treat consolidation as a background rewriting pass, not a gated promotion — the architectural difference from meditate is maximal.

**Sources:**
- Zep: A Temporal Knowledge Graph Architecture for Agent Memory — https://arxiv.org/abs/2501.13956 — episode/semantic/community tiers + entity dedup
- A-MEM: Agentic Memory for LLM Agents — https://arxiv.org/abs/2502.12110 — Zettelkasten-atomic + LINK-primary; best non-transitive-cohesion treatment
- Letta Sleep-time Compute — https://www.letta.com/blog/sleep-time-compute/ — idle-period background consolidation
- MemGAS: From Single to Multi-Granularity — https://arxiv.org/abs/2505.19549 — names the single-linkage chaining problem for agent memory; GMM + entropy router
- LangMem Conceptual Guide — https://langchain-ai.github.io/langmem/concepts/conceptual_guide/ — semantic/episodic/procedural taxonomy; hot-path vs background
- Generative Agents: Interactive Simulacra of Human Behavior (Park et al. 2023) — https://arxiv.org/abs/2304.03442 — reflection-based periodic consolidation
- State of AI Agent Memory 2026 (Mem0) — https://mem0.ai/blog/state-of-ai-agent-memory-2026 — practitioner benchmark; atomic-triplet approach
- Claude Code Auto Dream — https://antoniocortes.com/en/2026/03/30/auto-memory-and-auto-dream-how-claude-code-learns-and-consolidates-its-memory/ — practitioner reverse-engineering of idle consolidation
- Graphiti (Neo4j) — https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/ — temporal validity + community summaries
- Memory Consolidation & Summarization (APXML) — https://apxml.com/courses/agentic-llm-memory-architectures/chapter-3-designing-memory-systems/memory-consolidation-summarization — local vs global consolidation tradeoffs

### Stream 2 — Consolidation operations & entity resolution

**Focus:** The vocabulary and decision logic for merge/link/consolidate operations; the canonical failure modes in entity resolution.

**Key findings:**

- The dominant vocabulary is ADD/UPDATE/MERGE/LINK/CONSOLIDATE/NOOP (Mem0, RMM). **`split` (1→N) is absent everywhere** — all consolidation is many→one. This makes split a genuinely novel primitive in the agent-memory context.
- **Conservative-merge beats aggressive** in ablation studies (RMM). Mem0 biases toward NOOP when confidence is low — the same instinct as our "keep separate when unsure" default.
- The definitive entity-resolution survey is explicit: **never take the transitive closure of pairwise similarities**. Single-linkage chaining is the named canonical failure; the fix is clustering approaches that avoid it (complete/average linkage, community detection).
- Neo4j's three-zone confidence model (auto-merge / SAME\_AS provisional link / reject) provides the operational template for our mid-band `[[link]]` proposal: link-then-confirm preserves reversibility while avoiding the all-or-nothing merge decision.
- ByteRover is the only surveyed coding-agent tool with an explicit human approve/reject gate on memory operations — validating our HITL design as intentional, not absent from the field by accident.

**Sources:**
- Mem0: Production-Ready AI Agents with Scalable Long-Term Memory — https://arxiv.org/html/2504.19413v1 — ADD/UPDATE/DELETE/NOOP; information-content gate
- (Almost) All of Entity Resolution — https://pmc.ncbi.nlm.nih.gov/articles/PMC11636688/ — definitive ER survey; transitive-closure failure + clustering fixes
- Are We Ready For An Agent-Native Memory System? — https://arxiv.org/html/2606.24775v1 — conservative-merge ablation; CRUD + CONSOLIDATE + EVICT
- Memory for Autonomous LLM Agents (Write–Manage–Read) — https://arxiv.org/html/2603.07670v1 — taxonomy; notes SPLIT/LINK absent
- Neo4j Agent Memory — Entity Resolution & Deduplication — https://neo4j.com/labs/agent-memory/explanation/resolution-deduplication/ — three-zone confidence (auto / SAME\_AS link / reject)
- Reflective Memory Management (RMM) — https://aclanthology.org/2025.acl-long.413.pdf — conservative-merge ablation evidence
- ByteRover CLI memory layer — https://www.converter.brightcoding.dev/blog/byterover-cli-the-memory-layer-ai-coding-agents-desperately-need — only coding-agent tool with explicit human approve/reject gate
- Governance Decay: Context Compaction Silently Erases Safety Constraints — https://arxiv.org/html/2606.22528 — compaction → constraint-violation spike
- 5 Failure Modes in Agent Memory Compression — https://www.indium.tech/blog/agent-memory-compression-failure-modes/ — over-compression, hallucination amplification

### Stream 3 — Clustering granularity & atomicity

**Focus:** The formal and practical treatment of cohesion, granularity choice, and the tolerance-block / cover structure.

**Key findings:**

- **Single-linkage chaining is the named failure** across IR, NLP, and knowledge-management literature. Complete-linkage, average-linkage, HDBSCAN (mutual-reachability distance), and modularity-γ (Leiden) are the established remedies — each avoids closing the transitive hull.
- **Extract-and-link for bridge items is field-supported:** Matuschak's "bridge note" is a first-class note type in Zettelkasten practice. The tolerance-block = cover (not partition) result is the formal statement of the same observation.
- Granularity is **resolution-dependent** (the γ parameter in Leiden/Louvain; no single "correct" grain). "Settled" = low churn, not a provable global optimum — which is exactly how we define `normalize`.
- MDL-based cluster validity provides a parameter-free granularity selection principle (prefer the encoding that is shortest), offering a theoretical grounding for the "one clique per item" floor.
- Correlation clustering (Bansal et al.) — minimize agreement/disagreement on a signed graph — is the formal framework closest to our cohesion-edge model; it does not require a target number of clusters and handles negative edges (items that should NOT be merged).

**Sources:**
- Single-link & Complete-link Clustering (Manning, Raghavan, Schütze) — https://nlp.stanford.edu/IR-book/html/htmledition/single-link-and-complete-link-clustering-1.html — the chaining problem + complete-linkage remedy
- Evergreen notes should be atomic (Matuschak) — https://notes.andymatuschak.org/Evergreen_notes_should_be_atomic — atomic notes; split/link/merge tradeoff
- Taxonomy of note types (bridge notes) (Matuschak) — https://notes.andymatuschak.org/Taxonomy_of_note_types — "bridge note" as a first-class type
- The Principle of Atomicity (zettelkasten.de) — https://zettelkasten.de/posts/principle-of-atomicity-difference-between-principle-and-implementation/ — atomicity as emergent; the "only relationally meaningful" exception
- Correlation Clustering (Bansal, Blum & Chawla) — https://pages.cs.wisc.edu/~shuchi/papers/corrclusteringFOCS.pdf — signed-graph agreement/disagreement minimization
- From Louvain to Leiden (Traag et al. 2019) — https://www.nature.com/articles/s41598-019-41695-z — resolution parameter γ; connected-community guarantee
- Understanding HDBSCAN (Berba) — https://pberba.github.io/stats/2020/01/17/hdbscan/ — mutual-reachability distance as anti-chaining
- MDL-based Cluster Validity — https://link.springer.com/chapter/10.1007/978-3-642-23851-2_9 — parameter-free granularity selection

### Stream 4 — Rules vs retrieved memory

**Focus:** The capacity economics of the rule store; when to promote, when to demote.

**Key findings:**

- Rule-bloat **degrades instruction-following**: IFScale shows ~linear decay with instruction count, with a cliff near ~150 instructions; Lost in the Middle (Liu et al.) demonstrates primary-recency bias with mid-file rules systematically under-weighted. The practitioner ceiling of ~15 hard rules is empirically grounded, not arbitrary.
- Every promotion **dilutes adherence to all other rules** — the economics make promotion conservative by default, not just by taste.
- Tier-to-tier promotion is **understudied** in the formal literature (CoALA identifies the gap explicitly); practitioner consensus fills in with recurrence-count as the de-facto trigger (ReMe; Cursor forum).
- The 5-test promote gate (universality, prevention-value, not-already-enforced, not-auto-recorded, recurrence ≥3) synthesizes the practitioner evidence into a unified gate.
- Governance Decay corroborates the durability premise: context compaction raises constraint-violation rates sharply. This validates the P0 durable-memory hook and confirms that rules must be both few and durable to be effective.

**Sources:**
- IFScale: How Many Instructions Can LLMs Follow at Once? — https://arxiv.org/abs/2507.11538 — degradation curves; ~150 ceiling
- Lost in the Middle (Liu et al., TACL 2024) — https://aclanthology.org/2024.tacl-1.9/ — primary-recency bias; mid-context under-weighting
- Cognitive Architectures for Language Agents (CoALA) — https://arxiv.org/abs/2309.02427 — working/episodic/semantic/procedural; promotion "understudied"
- LangMem SDK launch — https://www.langchain.com/blog/langmem-sdk-launch — procedural-memory update pipeline
- ReMe (Remember Me, Refine Me) — https://arxiv.org/pdf/2512.10696 — recurrence-count promotion trigger
- The Complete Guide to CLAUDE.md (Ghosh) — https://medium.com/@bijit211987/the-complete-guide-to-claude-md-memory-rules-loading-and-cross-tool-compression-97cc12ed037b — concrete thresholds (≤15 rules, 80–120 lines)
- Cursor Forum: Rules vs Memories — https://forum.cursor.com/t/best-way-to-provide-context-rules-vs-memories/132960 — practitioner consensus
- Memory Bank (Tweag Agentic Coding Handbook) — https://tweag.github.io/agentic-coding-handbook/WORKFLOW_MEMORY_BANK/ — demotion-on-bloat pattern
- The Impact of Prompt Bloat on LLM Output Quality (MLOps) — https://home.mlops.community/public/blogs/the-impact-of-prompt-bloat-on-llm-output-quality — ~3000-token degradation onset
- Governance Decay: Context Compaction Silently Erases Safety Constraints — https://arxiv.org/html/2606.22528 — compaction → constraint-violation spike (cross-cited from Stream 2)

### Stream 5 — Decomposition theory (split · part 1)

**Focus:** Database normalization as the formal theory of split; the lossless-join and dependency-preservation conditions.

**Key findings:**

- **Lossless-join condition = the superkey condition**: a decomposition of R into R1, R2 is lossless iff (R1 ∩ R2) is a superkey of R1 or R2. Applied to knowledge items: the bridge atoms shared between two pieces must uniquely determine at least one piece's full content. Extract-and-link satisfies this automatically — the extracted bridge is the key of its own piece.
- **Dependency-preservation = links**: a functional dependency (cohesion edge) that crosses the cut cannot be enforced locally in either child. The fix is to reify it as an explicit cross-reference — the `[[link]]` + one-line invariant pattern. Formally: `(F1 ∪ … ∪ Fn)+ = F+` (the closure of each child's dependencies must equal the original's closure).
- **3NF synthesis is the cut algorithm** that guarantees BOTH lossless join AND dependency preservation. BCNF decomposition can violate dependency preservation; this is why we use 3NF synthesis, not BCNF, as the cut procedure.
- **The BCNF-vs-dependency-preservation tradeoff is irreducible**: the `TEACH(teacher, subject, hour)` relation is the canonical DB example of a relation that cannot be decomposed into BCNF while preserving all dependencies. The split contract must name the dependency being linked rather than locally preserved — never silently overpromise both.
- **Over-normalization = join-overhead harm**: the "myth of over-normalization" literature documents real performance costs from excessive fragmentation — the DB grounding for the LCOM4 = 1 floor and the escalate-to-human backstop.
- **Conservative extension / locality**: no child may introduce inferences about concepts it doesn't own — the semantic analog of functional-dependency scope.

**Sources:**
- Lossless join decomposition (Wikipedia) — https://en.wikipedia.org/wiki/Lossless_join_decomposition — the if-and-only-if superkey condition
- Chase algorithm (Wikipedia) — https://en.wikipedia.org/wiki/Chase_(algorithm) — tableau test for k-relation lossless
- Dependency-Preserving Decomposition (GeeksforGeeks) — https://www.geeksforgeeks.org/dbms/data-base-dependency-preserving-decomposition/ — (F1∪…∪Fn)+ = F+
- 3NF Synthesis Algorithm (Emory CS377) — https://www.cs.emory.edu/~cheung/Courses/377/Syllabus/9-NormalForms/FD-preserve-howto.html — the dependency-preserving + lossless synthesis procedure
- Using BCNF and 3NF (SFU) — https://www2.cs.sfu.ca/CourseCentral/354/jpei/slides/UsingBCNF-3NF.pdf — the BCNF-vs-dependency-preservation tradeoff (TEACH)
- Database normalization (Wikipedia) — https://en.wikipedia.org/wiki/Database_normalization — normal-form hierarchy + stopping
- The Myth of Over-Normalization (Red Gate) — https://www.red-gate.com/simple-talk/blogs/the-myth-of-over-normalization/ — fragmentation/join-overhead harm
- Survey of Modular Ontology Techniques — https://pmc.ncbi.nlm.nih.gov/articles/PMC3113511/ — conservative extension + locality

### Stream 6 — Decomposition mechanism (split · part 2)

**Focus:** LLM claim decomposition as the execution mechanism for split; software cohesion metrics as the split signal and stopping criterion.

**Key findings:**

- LLM atomic-claim decomposition (FActScore, Dense-X, Molecular-Facts, VeriScore, DnDScore) establishes the desiderata for a valid child: **minimal + distinct + self-contained**, with **pronoun resolution / decontextualization** so each piece stands alone without its parent's context. These are the LLM-executable form of the lossless gate.
- VeriScore argues against **forced atomicity** — pragmatic granularity floor, not maximum fragmentation. DnDScore's `Core` dedup step is the anti-fragmentation mechanism. Both corroborate the LCOM4 = 1 floor (stop when each piece is one clique, not when each piece is one sentence).
- **LCOM4 ≥ 2 = split signal; LCOM4 = 1 = stop criterion.** The connected-components interpretation makes LCOM4 directly applicable to atom-graphs: ≥2 disconnected components → clean split available; exactly 1 component → item is cohesive, do not split.
- TextTiling's lexical-cohesion valley detection provides an unsupervised boundary finder for the split-detect phase — the vocabulary-valley cue in §6.1 is the LLM-executable version of the same signal.
- HITL + reversibility patterns: the archive-not-destroy + tombstone design, the mid-confidence `inspect-manually` flag, and the propose-then-ratify gate are all supported by the surveyed HITL literature as the responsible pattern for irreversible corpus restructuring.

**Sources:**
- FActScore — https://aclanthology.org/2023.emnlp-main.741/ — atomic-fact decomposition via prompt
- Dense X Retrieval (Propositionizer) — https://arxiv.org/abs/2312.06648 — propositions: minimal + distinct + self-contained; pronoun-resolution decontextualization
- Molecular Facts: Desiderata for Decontextualization — https://arxiv.org/pdf/2406.20079 — failure modes of under-decontextualized pieces
- VeriScore — https://arxiv.org/html/2406.19276v1 — argues against forced atomicity; pragmatic granularity floor
- DnDScore — https://arxiv.org/html/2412.13175 — joint decompose+decontextualize; Core dedup as anti-fragmentation
- LCOM4 metric — https://objectscriptquality.com/docs/metrics/lack-cohesion-methods-lcom4 — connected-components; ≥2 = split, =1 = stop
- A Semantic-Based Approach for Detecting and Decomposing God Classes — https://arxiv.org/pdf/1204.1967 — LCOM + semantic clustering; cut = component membership
- TextTiling (Hearst 1997) — https://aclanthology.org/J97-1003/ — lexical-cohesion valley boundary detection
- Text Segmentation: Approaches, Datasets, Metrics (AssemblyAI) — https://www.assemblyai.com/blog/text-segmentation-approaches-datasets-and-evaluation-metrics — TextTiling/C99/BERT survey

---

## 10. Open / next

The model is complete. The horizontal-layer **implementation is now designed** — see
`2026-07-03-meditate-horizontal-implementation-plan.md` (v1.1, APPROVED FOR BUILD). Status below
updated per that plan; genuinely open items remain open.

- The curator's **relational/clustering pass** — **designed**: sweep-mode batch pass,
  cluster-sharded (implementation plan §5 task A2). Was: today's sweep audits each memory alone;
  cross-pollination needs a corpus-level pass that clusters + finds overlap-sets and over-broad
  bundles.
- The `split` / `combine` / `link` / `amend` verbs in the **curator** + **apply** skills —
  **designed, being built** (implementation plan §2.4, §5 task groups A/B). `amend` (in-place
  content correction) is a novel verb surfaced during live-fire, with no theory prior — see plan
  §2.4.
- **Manifest fields** for split-children + the links + the named severed-dependency — **designed**:
  contract v3 (`mem-arch-interface-contract.md` §3), full delta in the implementation plan §4.
- The **rule-budget guard**: enforce the promote-to-rule capacity ceiling — **designed**: ≤15
  markers per rulebook file, implementation plan §2.3 law 7 / §5 task A4.

Genuinely open (not in this build): the **resolve stage** (verdict-verification between curate and
review) and **auto-apply confidence bands** — both **stubbed** in the implementation plan §9,
deferred until after the horizontal layer lands.
