# Tree vs DAG Across Four Formal Traditions: A Decision Brief for the *manifold* Framework

## TL;DR
- **Three of the four traditions (refinement calculus, goal‑oriented RE, AND‑OR graphs/HTN) explicitly model decomposition as a DAG; only proof theory's *formal* natural‑deduction definition is strictly a tree, and even there real proof assistants (Coq, Lean 4, ACL2) internally share subproofs as DAGs.** Relaxing *manifold*'s across‑layer structure from tree to DAG is mathematically defensible and aligns with three of four primary literatures.
- **The closest formal match to *manifold*'s primitive (AND‑decomposition over satisfaction predicates with layered abstraction) is KAOS goal refinement**, which Darimont & van Lamsweerde (FSE‑4, 1996, §2) define verbatim as an "AND/OR directed acyclic graph," followed by Martelli & Montanari's (IJCAI 1973) additive AND/OR graphs.
- **Recommended adoption**: a strict DAG across layers, using the KAOS / iStar 2.0 vocabulary of *AND‑refinement* with multi‑parent children, optionally supplemented by separate "contribution" / "supports" edges drawn from the NFR Softgoal Interdependency Graph tradition (Chung et al. 2000, Ch. 3) for non‑decompositional dependencies.

---

## Key Findings

For each of the 20 sub‑questions: the formal definition (verbatim where it matters), the primary‑text citation, and one sentence on what it means for *manifold*'s tree‑vs‑DAG choice.

### Tradition 1 — Generative grammar / Chomsky hierarchy

**1.1  A single derivation in CFG / CSG is a tree.**
Hopcroft & Ullman, *Introduction to Automata Theory, Languages, and Computation* (Addison‑Wesley, 1979), §4.3 "Derivation Trees", defines a derivation/parse tree as an ordered rooted labelled tree whose interior nodes are nonterminals, leaves are terminals or ε, and whose direct descendants of any interior node A spell, left‑to‑right, the right‑hand side of some production A → α. Each non‑root node has exactly one parent by construction.
*For manifold:* the single‑derivation primitive of formal language theory is strictly tree‑shaped; any claim of direct affinity to "derivation" inherits a tree constraint.

**1.2  When multiple derivations exist, the parse forest is canonically a DAG ("shared packed parse forest").**
Scott & Johnstone, "GLL parse‑tree generation," *Science of Computer Programming* 78 (2013), pp. 1828–1844, §2: *"GLR parsers represent the complete set of derivation trees for a string using a shared packed parse forest (SPPF) which is designed to reduce the space required to represent multiple derivation trees. In an SPPF, nodes which have the same tree below them are shared and nodes which correspond to different derivations of the same substring from the same nonterminal are combined by creating a packed node for each family of children."* Tomita, *Efficient Parsing for Natural Language: A Fast Algorithm for Practical Systems* (Kluwer Academic Publishers, 1986), Ch. 4–5, is the original construction; the Earley‑style cubic SPPF (Scott 2008) is a successor.
*For manifold:* the moment alternative or shared sub‑derivations are admitted, the field's own data structure is a DAG, not a forest of disjoint trees.

**1.3  Dependency grammars enforce a strict single‑head (= single‑parent) tree.**
Tesnière, *Éléments de syntaxe structurale* (Klincksieck, 1959), Ch. 2 §1.3, defines syntactic connection as a binary asymmetric relation between governor and subordinate; the stemma is consequently a rooted tree. Mel'čuk, *Dependency Syntax: Theory and Practice* (SUNY Press, 1988), pp. 23–35 ("Three Basic Properties of Dependency Relations"), articulates the *single‑head principle*: each non‑root word has exactly one governor. Robinson (1970) Axiom 1 ("one and only one head") formalises this.
*For manifold:* dependency grammar is the tradition most hostile to multi‑parent edges; it explicitly *prohibits* DAGs.

**1.4  Classical Chomsky 1995 MERGE produces trees; Internal Merge keeps it a tree under copy theory; Parallel Merge (Citko 2005) yields *multidominance* — i.e. a DAG.**
Chomsky, *The Minimalist Program* (MIT Press, 1995), Ch. 4, defines Merge(α,β) = {α,β} as binary set formation, generating a binary‑branching tree. The copy theory of movement (ibid., §4.7) treats moved items as multiple copies — still tree‑formally. Citko, "On the Nature of Merge: External Merge, Internal Merge, and Parallel Merge," *Linguistic Inquiry* 36(4), 2005, pp. 475–497: *"This article argues in favor of a new type of Merge, Parallel Merge, which combines the properties of External Merge and Internal Merge. Parallel Merge creates symmetric, multidominant structures…"* — a node with two parents.
*For manifold:* mainstream Minimalism is tree‑only; the multidominance branch (Citko 2005, 2011; de Vries 2009) is precisely the literature that argues DAGs are sometimes empirically necessary.

**1.5  Compositional reuse across multiple parent contexts = multidominance.**
Citko, *Symmetry in Syntax: Merge, Move and Labels* (Cambridge UP, 2011), Ch. 2–3, and Citko & Gračanin‑Yüksek, *Merge* (MIT Press, 2021), give the systematic theory: across‑the‑board wh‑questions, right‑node raising, free relatives, parasitic gaps. Chomsky's "On Phases" (in *Foundational Issues in Linguistic Theory*, MIT Press, 2008) does not adopt multidominance; he treats sharing via copy/agreement instead.
*For manifold:* the linguistic literature has an explicit, named, well‑developed formal vocabulary — *multidominance* — for exactly the structure *manifold* is considering.

### Tradition 2 — Refinement calculus / predicate transformers

**2.1  ⊑ is a complete‑lattice partial order; its Hasse diagram is a DAG.**
Back & von Wright, *Refinement Calculus: A Systematic Introduction* (Springer GTCS, 1998), Ch. 2 "Posets, Lattices, and Categories", and Ch. 13 "Statements", state that the refinement relation on monotonic predicate transformers forms a complete lattice (and *a fortiori* a partial order). The Hasse diagram of any partial order with incomparable pairs is a DAG, not a tree.
*For manifold:* the refinement *relation* itself is set up from the outset as a partial‑order/DAG — never a tree.

**2.2  A shared sub‑specification reused as a component of multiple parents is a DAG by construction.**
Back & von Wright (1998), Ch. 13 §13.5 ("Specifications and Procedures") and Ch. 17 ("Procedures and Recursion"), formalise procedural abstraction so that a procedure body refined once may be invoked from multiple calling contexts. Morgan, *Programming from Specifications*, 2nd ed. (Prentice‑Hall, 1994), Ch. 12 "Procedures and Parameters" and Ch. 14 "Modules", explicitly treats a module's exported operations as components that *several* outer programs may import; the call‑graph is a DAG. Parallel composition (∥) in Back & von Wright Ch. 28 also produces shared‑state structures rather than tree‑structures.
*For manifold:* refinement calculus is silent‑bordering‑supportive on multi‑parent — procedure reuse is the standard idiom and gives a DAG.

**2.3  Dijkstra's wp‑calculus handles sharing via syntactic procedure substitution, not via a tree structure.**
Dijkstra, *A Discipline of Programming* (Prentice‑Hall, 1976), Ch. 7 ("Euclid's algorithm revisited") and Ch. 11 ("Array Manipulation"), defines wp(S,R) compositionally over program syntax; procedures and named statements are treated by macro‑expansion / substitution rather than via a named decomposition graph. The book does not draw a tree or graph of refinements explicitly.
*For manifold:* Dijkstra's framework is silent on the tree‑vs‑DAG question because sharing is dissolved at the syntax/wp level.

**2.4  Wirth 1971 worked the 8‑queens example as a single linear chain of refinements; he did not address shared sub‑problems.**
Wirth, "Program Development by Stepwise Refinement," *CACM* 14(4), 1971, pp. 221–227. Each refinement step replaces one abstract statement by a more concrete decomposition; reuse of `testsquare` across columns is achieved by procedural abstraction, not by a graph diagram of refinements. The paper's five concluding remarks discuss modularity but do not formalise a tree or DAG of refinement steps.
*For manifold:* Wirth is silent. Honest accounting: there is no Wirth citation that supports or prohibits multi‑parent.

**2.5  Modern refinement‑calculus literature treats shared components as a DAG via modules and parallel composition.**
Hoare & He, *Unifying Theories of Programming* (Prentice‑Hall International, 1998), Ch. 7 "Concurrency", model parallel composition P ∥ Q as a least upper bound in a lattice; shared subcomponents project naturally as DAG nodes. Back & von Wright (1998), Ch. 28 "Action Systems and Parallelism", §28.4 ("Refinement of Action Systems"), and Morgan (1994), Ch. 17 "Recursion", both give explicit examples where a single refined sub‑specification appears under multiple parents.
*For manifold:* the modern refinement‑calculus answer is **DAG via shared module / procedure**; the formal vocabulary is *procedure call* or *imported component*.

### Tradition 3 — Goal‑oriented requirements engineering

**3.1  In i* / iStar 2.0, refinement is a 1‑parent‑to‑many‑children n‑ary relation, and the integrity rules explicitly allow a child to appear under multiple parents.**
Dalpiaz, Franch & Horkoff, *iStar 2.0 Language Guide* (arXiv:1605.07767v3, 2016), §6.1 "Refinement": *"Refinement is an n‑ary relationship relating one parent to one or more children. An intentional element can be the parent in at most one refinement relationship… AND: the fulfillment of all the n children (n ≥ 2) makes the parent fulfilled; Inclusive OR: the fulfillment of at least one child makes the parent fulfilled… A parent can only be AND‑refined or OR‑refined, not both simultaneously."* The §8 metamodel integrity rules forbid refinement *cycles* but place no restriction on a child being the child in multiple refinements.
*For manifold:* iStar 2.0 explicitly **permits multi‑parent children** as a first‑class structural feature.

**3.2  KAOS defines goal refinement formally as an AND/OR directed acyclic graph.**
Darimont & van Lamsweerde, "Formal Refinement Patterns for Goal‑Driven Requirements Elaboration," *FSE‑4* (ACM, 1996), §2: *"The goal refinement structure for a given system can be represented by an AND/OR directed acyclic graph."* The same definition is preserved verbatim in van Lamsweerde, "Goal‑Oriented Requirements Engineering: A Guided Tour," *RE'01* (IEEE, 2001), §3 ("Directly borrowed from problem reduction methods in Artificial Intelligence … AND/OR graphs may be used to capture goal refinement links"), and reused in van Lamsweerde, *Requirements Engineering: From System Goals to UML Models to Software Specifications* (Wiley, 2009), Ch. 8 "Goal Orientation in RE".
*For manifold:* KAOS is **the** closest match — it explicitly names the structure a DAG and gives AND/OR semantics matching *manifold*'s AND‑decomposition primitive.

**3.3  The NFR framework's Softgoal Interdependency Graph (SIG) is, by definition and by its name, a graph; softgoals may receive contributions from and to multiple parents.**
Chung, Nixon, Yu & Mylopoulos, *Non‑Functional Requirements in Software Engineering* (Kluwer, 2000), Ch. 3 "Softgoal Interdependency Graphs". The chapter title is itself definitional. Contribution links {Make, Help, Hurt, Break, +, −, ++, −−} propagate qualitative labels through a *graph* — not a tree — using the label‑propagation procedure of Ch. 3 §3.4 and Ch. 4.
*For manifold:* SIG is a DAG plus extra contribution edges; it directly anticipates the "tree of decomposition + DAG of supports" hybrid proposed below.

**3.4  All three formalisms support subgoals/softgoals contributing to multiple parent goals, with different propagation semantics.**
KAOS uses pattern‑based refinement (Darimont & vL 1996, Tables 2–4) where satisfaction of *all* AND‑subgoals entails the parent — i.e. classical AND‑decomposition over a DAG. i* / iStar 2.0 distinguishes the *decomposition* link (AND/OR refinement; Dalpiaz et al. 2016, §6.1) from the *contribution* link with Make/Help/Hurt/Break labels (§6.2). NFR/SIG propagates {Satisficed, Denied, Conflict, Undetermined, Weakly Satisficed, Weakly Denied} labels through the SIG (Chung et al. 2000, Ch. 4 "The Evaluation Procedure").
*For manifold:* the closest semantic match to *manifold*'s "parent satisfied iff all children satisfied" is **KAOS AND‑refinement**, which is two‑valued and Boolean; i* and NFR add qualitative labels you don't need.

**3.5  KAOS maps cleanly onto AND‑decomposition over Boolean satisfaction predicates; i* and NFR require extra qualitative machinery.**
van Lamsweerde (2009), Ch. 7 "Goals", §7.1.2 specifies KAOS goal satisfaction in linear temporal logic (Achieve, Maintain, Avoid, Cease patterns), with AND‑refinement proven *sound* when ⋀ᵢ subgoalᵢ ⊨ parent. This matches *manifold*'s primitive exactly. NFR softgoals are *satisficed* (Simon's term) rather than satisfied; SIG label propagation uses a 6‑value lattice (Chung et al. 2000, §4.3), which is strictly more machinery than AND.
*For manifold:* if you want minimal added machinery, use KAOS; if your "contracts" become quality attributes (performance, security) needing partial satisfaction, lift in NFR.

### Tradition 4 — AND‑OR graphs / proof theory / HTN

**4.1  AND‑OR graphs are formally DAGs; Martelli & Montanari 1973 explicitly defines them as "folded AND/OR trees."**
Martelli & Montanari, "Additive AND/OR Graphs," *IJCAI* (1973), pp. 1–11, §1: *"Additive AND/OR graphs are defined as AND/OR graphs without circuits, which can be considered as folded AND/OR trees; i.e. the cost of a common subproblem is added to the cost as many times as the subproblem occurs, but it is computed only once."* Nilsson, *Principles of Artificial Intelligence* (Tioga, 1980), Ch. 3 §3.3 "AND/OR Graph Search Procedures", defines the AO* algorithm over the same graph structure. Russell & Norvig, *Artificial Intelligence: A Modern Approach*, 4th ed. (Pearson, 2020), Ch. 4 §4.3 ("And‑Or Search Trees") regrettably uses the word "tree" in the heading, but the algorithm itself memoises and operates over a graph.
*For manifold:* AND‑OR graph theory has, since 1973, formally been a DAG with shared subproblems; AO* is the search algorithm for this DAG.

**4.2  Natural‑deduction derivations are *formally* trees, but real proof assistants (Coq, Lean 4, ACL2) internally represent shared sub‑proofs as DAGs via hash‑consing.**
Prawitz, *Natural Deduction: A Proof‑Theoretical Study* (Almqvist & Wiksell, 1965), Ch. I §1 defines a derivation as a finite tree of formula‑occurrences with assumption‑classes labelled by markers at the leaves; sharing is *only* at the level of assumption‑marker identity. Troelstra & Schwichtenberg, *Basic Proof Theory*, 2nd ed. (Cambridge UP, 2000), Ch. 1 §1.1.8 defines finite trees, and Ch. 2 §2.1 introduces N‑systems with *"proofs in the form of deduction trees, assumptions appearing at top nodes."* Negri & von Plato, *Structural Proof Theory* (Cambridge UP, 2001), Ch. 1 §1.2, present derivations in the same tree format.

At the implementation level, however, hash‑consing collapses redundant proof subterms into shared DAG nodes. Boyer & Hunt, "Function Memoization and Unique Object Representation for ACL2 Functions," *Sixth International Workshop on the ACL2 Theorem Prover and Its Applications* (ACM, 2006), and ACL2 v6.2 official documentation: *"A record of ACL2 HONS objects is kept, and when an ACL2 function calls hons ACL2 searches for an existing identical pair before allocating a new pair; this operation has been called 'hash consing'."* HONS became the default release of ACL2 v7.0 in January 2015 (Moore et al., "Industrial Hardware and Software Verification with ACL2," *Philosophical Transactions of the Royal Society A* 375:20150399, 2017). Wernhard, "Generating Compressed Combinatory Proof Structures" (arXiv:2209.12592, 2022), §1: *"In a DAG representation of the combinator term these straightforwardly factor into shared subgraphs… DAGs permit to share duplicated subtrees where the conventional handling of variables as rigid… is not sufficient, because, in general, each use of a lemma takes it in a fresh copy."*
*For manifold:* the *mathematical object* is a tree, but the *engineering artefact* is universally a DAG. Lemma reuse is the standard, named idiom; if *manifold* nodes correspond to lemmas, DAG is implementation‑normal.

**4.3  HTN task decompositions are formally DAGs because the same task can appear in multiple methods.**
Erol, Hendler & Nau, "HTN Planning: Complexity and Expressivity," *AAAI* (1994), and Erol, Hendler & Nau, "Semantics for Hierarchical Task‑Network Planning," UMD Tech Report CS‑TR‑3239 (1994), §3, formalise an HTN domain as a tuple where methods decompose a compound task into a partially‑ordered set of subtasks; a single task type may appear in multiple methods' right‑hand sides. Höller, Behnke, Bercher & Biundo, "A Generic Method to Guide HTN Progression Search with Classical Heuristics," *ICAPS 2018*, AAAI Press, pp. 114–122, define the Task Decomposition Graph (TDG) as *"an AND/OR graph that compactly represents the reachability information imposed by the decomposition methods."* Ghallab, Nau & Traverso, *Automated Planning: Theory and Practice* (Morgan Kaufmann, 2004), Ch. 11 "Hierarchical Task Network Planning," and Nau et al., "SHOP2: An HTN Planning System," *JAIR* 20 (2003), pp. 379–404, operationalise this DAG semantics.
*For manifold:* HTN is a direct precedent for a layered DAG of decomposition where the same subtask is reused across multiple parent tasks/methods.

**4.4  AND‑OR graphs and minimax game trees are related but distinct formalisms.**
Knuth & Moore, "An Analysis of Alpha‑Beta Pruning," *Artificial Intelligence* 6(4), 1975, pp. 293–326, analyse minimax as a search over a game *tree* with alternating MAX (≈ OR) and MIN (≈ AND‑of‑best‑response) levels. Pearl, *Heuristics: Intelligent Search Strategies for Computer Problem Solving* (Addison‑Wesley, 1984), Ch. 3 §3.1 and Ch. 9, formally distinguishes problem‑reduction AND‑OR graphs (where AND nodes mean "all subgoals must be solved") from game trees (where MIN nodes model adversarial choice). Both fields cross‑pollinate (AO* ≈ proof‑number search ≈ minimax variant; see Pearl Ch. 9 §9.4 on the duality), but the AND semantics differs: problem reduction is conjunction; minimax is "worst‑case opponent choice."
*For manifold:* minimax is the wrong analogy because *manifold* is not adversarial; AND‑OR graphs (Martelli & Montanari, AO*) is the right one.

**4.5  Memoisation of shared subproblems is precisely what Martelli & Montanari's "additive" construction formalises; HTN shared subgoals are formal first‑class structure; proof‑term sharing is engineering practice rather than formal theory.**
Martelli & Montanari (1973), §1: *"the cost of a common subproblem is added to the cost as many times as the subproblem occurs, but it is computed only once."* HTN literature treats shared subtasks as the standard reason TDGs are DAGs (Höller et al., ICAPS 2018, defining the TDG as an AND/OR graph). Proof‑term sharing (Coq, Lean 4, ACL2 HONS per Boyer & Hunt 2006) is universally used at the engineering level but is *not* part of Prawitz's, Troelstra–Schwichtenberg's, or Gentzen's formal definition of a derivation.
*For manifold:* every tradition except dependency grammar formally addresses shared substructure; in three of the four it is the standard treatment.

---

## Synthesis Question Answers

**S.1  Classification.**

| Tradition | Support multi‑parent? |
|---|---|
| Generative grammar — single CFG derivation | **Prohibit** (tree by definition); dependency grammar **strongly prohibits** |
| Generative grammar — parse forest / Minimalism multidominance | **Support** (SPPF DAG; Citko Parallel Merge) |
| Refinement calculus | **Support** (lattice ⊑ is DAG; procedure / module reuse is DAG; multi‑parent is the standard idiom) |
| Goal‑oriented RE (KAOS, i*, NFR) | **Support explicitly** (KAOS = "AND/OR DAG"; iStar 2.0 §6.1 allows multi‑parent children; SIG is a graph) |
| AND‑OR graphs / HTN | **Support explicitly** (additive AND/OR DAG; HTN task decomposition graph is an AND/OR graph) |
| Proof theory (formal definition) | **Prohibit** at the level of Prawitz / T&S tree definitions; but **support** in Coq/Lean/ACL2 engineering practice |

**S.2  Closest formal match to *manifold*'s primitive (AND‑decomposition over satisfaction predicates with layered abstraction).** KAOS is the clearest match: AND‑refinement in KAOS is formally "satisfaction of all subgoals is sufficient for satisfaction of the parent" (Darimont & vL 1996; vL 2009 Ch. 8), exactly *manifold*'s contract rule, and the structure is by definition a DAG. Additive AND/OR graphs (Martelli & Montanari 1973) is a close second — formally identical AND semantics, just without the layered‑abstraction interpretation.

**S.3  Effect of relaxing strict‑tree across layers to DAG across layers.**

- **Generative grammar (CFG single derivation, dependency grammar):** *less* consistent.
- **Generative grammar (SPPF, Minimalism with multidominance):** *more* consistent.
- **Refinement calculus:** *more* consistent — the field's central object is a partial order whose Hasse diagram is a DAG.
- **Goal‑oriented RE (KAOS, i*, NFR):** *more* consistent — these are DAGs by primary‑text definition.
- **AND‑OR graphs / HTN:** *more* consistent — DAG is the primary structure.
- **Proof theory (Prawitz tree definition):** *less* consistent at the formal level, but *more* consistent with proof‑assistant practice.

Net: five of seven sub‑traditions become **more** consistent under DAG; the two that become less consistent are the most distant from *manifold*'s problem domain (CFG derivations, dependency syntax).

**S.4  Established vocabulary for "node with multiple parents."**

| Tradition | Term | Recommended for adoption? |
|---|---|---|
| Generative grammar | *multidominance* (Citko 2005, 2011) | Strong term, but linguistic; risks confusing audiences |
| Refinement calculus | *shared component* / *imported module* / *procedural abstraction* (Back & von Wright Ch. 17; Morgan Ch. 12, 14) | Software‑familiar; good if *manifold* targets engineers |
| Goal‑oriented RE | *AND‑refinement with multi‑parent child*; *contribution link* (Chung et al. 2000); KAOS *AND/OR DAG* (Darimont & vL 1996) | **Best primary‑text match for *manifold*'s domain.** |
| AND‑OR graphs | *shared subproblem* / *folded AND/OR tree* (Martelli & Montanari 1973); *task decomposition graph* (Höller et al., ICAPS 2018) | Excellent if *manifold* frames decomposition algorithmically |
| Proof theory | *lemma reuse* / *proof‑term sharing* (Boyer & Hunt 2006; Wernhard 2022) | Domain‑appropriate if *manifold* nodes are theorems |

Recommended primary citation: KAOS "AND/OR directed acyclic graph" (Darimont & vL 1996; vL 2009). Secondary: AND‑OR graph + additive AND/OR graphs (Martelli & Montanari 1973; Nilsson 1980).

**S.5  What each tradition gives up under tree / DAG / hybrid.**

- **Strict tree** — gives up:
  - in refinement calculus: procedural abstraction / module reuse (a fundamental concept; *expensive* loss);
  - in GORE: the named formal structure ("AND/OR DAG") of KAOS (*expensive*);
  - in HTN / AND‑OR: the entire "shared subproblem / memoisation" line of work, including AO* (*very expensive*);
  - in proof theory: nothing formal, but loses the engineering pattern of lemma reuse (*cheap*);
  - in linguistics: gains alignment with classical CFG and dependency grammar (*gain*).

- **Strict DAG** — gives up:
  - the single‑derivation parse‑tree intuition (*moderate*);
  - the dependency‑grammar single‑head principle (*moderate*; but irrelevant if *manifold* is not modelling syntax);
  - Prawitz‑style formal tree definitions of natural deduction (*moderate*; but engineering practice already uses DAGs).

- **Hybrid (tree of decomposition + separate DAG of "supports" edges)** — this is the *NFR Softgoal Interdependency Graph* pattern (Chung et al. 2000, Ch. 3): mandatory AND/OR refinement is one edge type; auxiliary *contribution* links are another. Cost: more vocabulary to maintain; benefit: cleanest separation of "what *must* hold for the parent" from "what *helps/hurts*."

---

## Recommendations

Adopt a strict DAG across layers, with KAOS AND/OR refinement as the formal substrate.

1. **Default to strict DAG.** Three of four primary traditions define their structure as a DAG; the fourth (proof theory) is a tree only at the Prawitz/T&S formal level, while every working proof assistant (Coq, Lean 4, ACL2 since v7.0) shares subproofs as DAGs. The cost of strict tree is high in the three closest traditions; the cost of strict DAG is low in the one tradition that strictly prefers trees.

2. **Cite KAOS as the primary lineage.** Use Darimont & van Lamsweerde 1996 §2 ("AND/OR directed acyclic graph") and van Lamsweerde 2009 Ch. 8 as your conceptual anchor. The semantics — parent satisfied iff conjunction of children is sufficient — is exactly *manifold*'s contract rule.

3. **Cite additive AND/OR graphs as the algorithmic lineage.** Martelli & Montanari 1973's *"folded AND/OR trees … the cost of a common subproblem is added to the cost as many times as the subproblem occurs, but it is computed only once"* is the canonical pre‑exists‑Wikipedia source for shared subproblems, and Nilsson 1980 Ch. 3 §3.3 defines AO* as the search procedure for it.

4. **Consider the hybrid only if you have non‑decompositional dependencies.** If your "contracts" begin to include qualitative attributes (security, performance, usability) where the parent should *not* require Boolean satisfaction of every child but rather aggregation of contributions, layer the SIG model on top: keep KAOS AND‑refinement as the spine and add NFR contribution links as a second edge type.

5. **Benchmarks that would change the recommendation.**
   - If *manifold* turns out to be modelling syntax or proof *objects* (rather than goals/specs), revert to tree to align with CFG/dependency grammar / Prawitz.
   - If aggregation becomes non‑Boolean (partial satisfaction, quantitative scores), shift from KAOS to the NFR SIG with explicit label‑propagation semantics.
   - If recursion is needed (cycles), neither KAOS nor iStar 2.0 supports cycles (iStar §8 explicitly forbids them); consider lifting to fixed‑point semantics in the refinement‑calculus style (Back & von Wright Ch. 19 "Fixed Points").

---

## Caveats

- For Chung et al. 2000, Ch. 3, I verified the chapter title ("Softgoal Interdependency Graphs") and the published abstract identifying SIG as a graph, but could not retrieve a verbatim definitional sentence from the chapter body online.
- For van Lamsweerde 2009 (Wiley book), the verbatim "AND/OR directed acyclic graph" formulation is traced through his 1996 (Darimont & vL, FSE‑4) and 2001 (RE'01 Guided Tour) papers, which the 2009 book consolidates; I could not retrieve a page‑numbered quote from the printed book directly.
- For Prawitz 1965, the tree formalisation is confirmed via secondary literature (Internet Encyclopedia of Philosophy; Martins & Martins 2006); the monograph itself is not freely available online.
- Wirth 1971 does not explicitly address shared sub‑problems; I have stated this rather than fabricating a position.
- Russell & Norvig's 4th ed. uses the heading "And‑Or Search Trees" (§4.3), which is terminologically misleading; the actual algorithmic treatment is over a graph with memoisation.
- The Hopcroft & Ullman §4.3 citation refers to the 1979 first edition; the 2007 Hopcroft–Motwani–Ullman 3rd edition restructures the material but preserves the same tree definition.
- Where two traditions disagree (e.g. Chomsky 1995 tree vs. Citko 2005 DAG), I have flagged the historical evolution rather than picking one position.