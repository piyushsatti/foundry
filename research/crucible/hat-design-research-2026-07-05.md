# Hat-File & Output-Contract Design: Evidence Review

**Scope:** persona-file design and output contracts for LLM artifact-review agents. Protocol-layer questions (debate, panel size, sycophancy, adjudication) are explicitly out of scope — already covered by prior research.
**Method:** 5 parallel literature sweeps (persona effectiveness, persona attributes/drift, format constraints, LLM-judge rubrics, persona evals), primary sources fetched directly (arXiv / ACL Anthology). Every claim carries: source, quote or tight paraphrase, confidence, refutation condition. Claims marked **[DEFAULT]** are engineering judgments with no direct study — do not cite them as evidence.
**Citation hygiene note:** several exact table numbers below were extracted via automated fetch of arXiv HTML rather than a character-level read of the PDF. Direction and rough magnitude are reliable; spot-check exact digits against the linked PDF before quoting any specific percentage in an external document. Flagged inline as *(verify digits)*.

---

## TL;DR

1. "You are a security engineer" alone is close to decorative: across 162 roles × 9 models, personas did not improve accuracy on average and sometimes hurt (Zheng et al., EMNLP Findings 2024).
2. What does carry effect: task-coupled role framing (what to *do*, not who to *be*), domain-relevant content, and explicit procedural checklists — the hat's power lives in its failure-class list and questions, not its identity line.
3. Irrelevant persona detail is actively harmful, not neutral: drops of up to ~30pp from irrelevant details (Principled Personas, 2025); demographic attributes cause systematic bias (ICLR 2024). Strip names, backstories, demographics.
4. Structured output does not hurt reasoning per se; **answer-before-reasoning ordering** hurts. Both camps of the "Let Me Speak Freely" dispute converge on: free reasoning first, structure last.
5. Anchored rubrics beat bare numeric scales (Prometheus ablation); binary-checkable criteria beat holistic Likert by a large margin (CheckEval: agreement α 0.05–0.09 → 0.45–0.67).
6. Evidence-before-verdict is the single best-quantified judge mitigation (math-grading failure 70% → 15% with reference-grounding; +10–14pt accuracy from evidence-first calibration).
7. Persona *distinctness* is a live empirical risk, not a given: personas on the same base model often collapse toward one voice (Chameleon's Limit); cross-model diversity is better evidenced than persona diversity for catching correlated errors.
8. Persona drift is real (~8 turns, attention decay) — hats need re-injection for long sessions; CoT makes persona *consistency* worse, not better (PERSIST).
9. A hat "works" only if probed: the seeded-defect ablation design (inject one known defect, measure per-class recall + FP on clean artifact) is published and directly adaptable; persona-vs-persona defect coverage has **no** published study — our eval fills a real gap.
10. Net: write hats as *checklist-and-contract documents with a thin domain-framing header*, not character sheets.

---

## 1. Persona effectiveness findings

### 1.1 The null result: identity personas don't buy accuracy

- **CLAIM:** Adding a persona to the system prompt does not improve factual-task accuracy vs. no-persona control, on average; some personas actively hurt.
  **SOURCE:** Zheng et al., "When 'A Helpful Assistant' Is Not Really Helpful" — https://arxiv.org/abs/2311.10054 (Findings of EMNLP 2024; https://aclanthology.org/2024.findings-emnlp.888/). 162 roles × 2,410 MMLU-derived questions × 9 models / 4 families, mixed-effects regression.
  **QUOTE:** "adding personas in system prompts does not improve model performance across a range of questions compared to the control setting where no persona is added." Also: "Most of the personas have no or negative impact on LLM's performance."
  **CONFIDENCE:** high. **REFUTED BY:** a replication on frontier models showing a consistent positive main effect on the same task set.

- **CLAIM:** Per-question persona effects exist but are unexploitable — picking the best persona in advance performs no better than random.
  **SOURCE:** same. **QUOTE:** "automatically identifying the best persona is challenging, with predictions often performing no better than random selection."
  **CONFIDENCE:** high. **REFUTED BY:** a method that predicts the best persona per question above chance on held-out data.
  **Implication for hats:** do not expect the *identity* of the hat to do work; expect the *content* to.

- **CLAIM:** Domain-matched expertise framing has a real but small positive effect on factual tasks (coefficient 0.004, p<0.01), and a much larger effect on tasks requiring generation of domain-specific detail.
  **SOURCES:** Zheng et al. (above) for the small effect; Salewski et al., "In-Context Impersonation Reveals LLMs' Strengths and Biases" — https://arxiv.org/abs/2305.14930 (NeurIPS 2023 spotlight) for the larger, domain-specific effect: "an LLM prompted to be a bird expert describes birds better than one prompted to be a car expert" (χ² p<0.001), effects directionally consistent across two models.
  **CONFIDENCE:** high (both primary). **REFUTED BY:** the expert advantage vanishing when output length/verbosity is controlled.
  **Reconciliation (our synthesis):** effect size is task-dependent — near-zero on closed-form recall, material on open-ended generation of domain-specific content. Artifact review is the latter type, so a one-line domain framing is worth keeping — but it is the cheapest, weakest ingredient, not the core.

### 1.2 What actually moves behavior: task-coupled role framing

- **CLAIM:** Role-play prompting tightly coupled to task execution ("you are an excellent math teacher and always teach your students math problems correctly") produces large zero-shot reasoning gains (AQuA 53.5→63.8; Last Letter 23.8→84.2 on ChatGPT), functioning as an implicit chain-of-thought trigger.
  **SOURCE:** Kong et al., "Better Zero-Shot Reasoning with Role-Play Prompting" — https://arxiv.org/abs/2308.07702 (NAACL 2024). **QUOTE:** "role-play prompting consistently surpasses the standard zero-shot approach across most datasets."
  **CONFIDENCE:** high for the numbers; medium for the CoT-trigger mechanism (authors' interpretation, not directly measured).
  **REFUTED BY:** inspection showing role-play answers contain no more intermediate reasoning than baseline.
  **CONTESTED:** "Persona is a Double-edged Sword" (https://arxiv.org/abs/2408.08631) finds role-play prompts *degrade* reasoning in 4 of 12 datasets even on GPT-4 (medium confidence — full text not independently fetched). The reasoning literature genuinely disagrees; the effect depends on prompt construction, not persona presence.

- **CLAIM:** Per-instruction *customized* expert descriptions (ExpertPrompting) win LLM-judged preference 48.5% vs 23% over vanilla answers — but on open-ended quality judged by GPT-4, with no ablation isolating specificity from mere expertise claims, and no objective benchmark.
  **SOURCE:** https://arxiv.org/abs/2305.14688. **CONFIDENCE:** medium-high on the result *(verify digits)*; medium on the mechanism. **REFUTED BY:** judge-blind or human-rater replication; or evidence the judge rewards persona-conditioned verbosity.
  **Implication:** specificity plausibly matters, but this paper cannot separate "detailed expert description" from "longer prompt." Treat "more customized = better" as suggestive, not established.

### 1.3 The strongest single result for hat design

- **CLAIM:** Expert personas produce positive-or-null changes; **irrelevant persona details produce performance drops of up to ~30 percentage points**; education/specialization/domain-relatedness effects are "often inconsistent or negligible across tasks"; robustness mitigations only work for the largest models.
  **SOURCE:** Araujo, Röttger, Hovy, Roth, "Principled Personas: Defining and Measuring the Intended Effects of Persona Prompting on Task Performance" — https://arxiv.org/abs/2508.19764 (2025; 9 SOTA LLMs × 27 tasks).
  **QUOTE (verbatim abstract):** "We find that expert personas usually lead to positive or non-significant performance changes. Surprisingly, models are highly sensitive to irrelevant persona details, with performance drops of almost 30 percentage points."
  **CONFIDENCE:** high — most recent, largest-scale, most on-point study found.
  **REFUTED BY:** irrelevant-detail sensitivity disappearing across model sizes.
  **Implication:** every word in a hat file that isn't task-relevant is not just wasted — it is measurable downside risk. This is the direct evidentiary basis for banning names, backstories, and flavor text.

- **CLAIM:** Socio-demographic persona attributes cause large, systematic reasoning degradation and stereotyped abstentions (80% of personas showed bias; drops of 70%+ on some datasets), even when the model overtly rejects the stereotype if asked directly.
  **SOURCE:** Gupta et al., "Bias Runs Deep: Implicit Reasoning Biases in Persona-Assigned LLMs" — https://arxiv.org/abs/2311.04892 (ICLR 2024).
  **CONFIDENCE:** high for the tested (2023-era) models; currency on 2025-26 models unverified — flagged as a gap. *(verify digits)*
  **Corroborated by:** Zheng et al. (gender-neutral roles outperform gendered, p<0.05) and Salewski et al. (systematic race/gender description biases).
  **Implication:** demographic attributes are not "noise with zero effect" — they are effect *in the wrong direction*. Professional hats must be demographically unmarked.

### 1.4 Persona drift and stability

- **CLAIM:** Models drift from system-prompt instructions within ~8 conversation rounds, driven by attention decay over the growing context; system-prompt re-injection is the most robust fix at long horizons (split-softmax matches it without context cost at short horizons).
  **SOURCE:** Li et al., "Measuring and Controlling Instruction (In)Stability in Language Model Dialogs" (originally circulated as the persona-drift paper) — https://arxiv.org/abs/2402.10962.
  **QUOTE:** "we reveal a significant instruction drift within eight rounds of conversations... the transformer attention mechanism plays a role, due to attention decay over long exchanges."
  **CONFIDENCE:** high, with a scope caveat: tested on LLaMA2-70B/GPT-3.5. **REFUTED BY:** no meaningful drift within 8 turns on current long-context models.

- **CLAIM:** Scaling gives only modest stability gains; **chain-of-thought reasoning increases persona/personality response variability rather than reducing it**; conversation history destabilizes small models most.
  **SOURCE:** PERSIST benchmark — https://arxiv.org/html/2508.04826v1 (25 models 1B–685B, 2M+ responses).
  **QUOTE:** "Chain-of-thought reasoning... in most cases increases response variability. Models generate different justifications across runs, leading to divergent conclusions for identical questions."
  **CONFIDENCE:** high. **REFUTED BY:** replication showing CoT stabilizes trait expression.
  **Implication:** don't rely on "the model will reason its way back into character." For fresh-subagent review protocols (our case) drift matters less than for chat, but any hat used in a long interactive session (the brainstorm partner) should be re-injected periodically. **[DEFAULT: re-inject every ~6–8 turns, derived from the 8-round finding but not directly tested as a schedule.]**

### 1.5 Signal vs. noise summary table

| Persona attribute | Effect | Evidence grade |
|---|---|---|
| Task-coupled role framing ("reviews X and always checks Y") | Large positive on reasoning-type tasks, but contested (helps most datasets, hurts some) | Evidence, mixed |
| Domain-expertise framing matched to artifact domain | Small positive (factual) to moderate positive (generative/descriptive) | Evidence |
| Explicit concern/failure-class lists | Not studied as a *persona attribute*; strongly supported as checklist decomposition (see §4) and self-verification (CoVe, https://arxiv.org/abs/2309.11495) | Evidence by bridge — flag as inference |
| Customization/specificity of expert description | Suggestive positive (ExpertPrompting), unablated | Weak evidence |
| Names, backstories, flavor | Up to ~30pp *harm* (irrelevant-detail sensitivity) | Evidence of harm |
| Demographic markers (gender, race, age, class) | Systematic bias/harm | Evidence of harm |
| Expertise *claims* alone ("you are a distinguished expert") | Null on average, unpredictable per-instance | Evidence of null |

**The honest framing for the methodology doc:** no published study directly A/B-tests "concern-list" against "identity/backstory" attributes in one factorial design. The recommendation to build hats around failure-class checklists rests on (a) persona-literature evidence that identity alone is null-to-harmful, plus (b) judge-literature evidence that explicit decomposed criteria drive consistency (§4), plus (c) defect-detection evidence that specialized checks massively out-recall generic review (§5). That is a strong triangulated case, but it is a bridge across literatures, not a single controlled result.

---

## 2. Recommended hat-file template (field by field)

Design principle from §1: **a hat is a review contract wearing a thin domain-framing header — not a character.** Every field must be task-relevant; task-irrelevant content is evidenced downside.

### Fields, with justification

**1. `role` — one-sentence, task-coupled, demographically unmarked.**
Format: "You are a [domain] reviewer. You review [artifact type] for [failure family] and always [core procedure]."
Justified by: small-but-real domain-matching effect (Zheng et al.; Salewski et al.); the task-coupled construction is the form that produced gains in Kong et al. (role bound to correct task execution, not identity). Bans on names/backstory/demographics justified by Araujo et al. (irrelevant-detail harm) and Gupta et al. (demographic bias). *Framing note (medium confidence, single source): Zheng et al. found audience-framing ("you are talking to X") outperformed speaker-framing ("you are X") — worth an internal A/B, not worth asserting.*

**2. `failure_classes` (was: failure-classes-uniquely-caught) — the load-bearing field. VALIDATED, with a rename.**
An enumerated list of defect classes this hat is responsible for catching, each with a one-line operational definition.
Justified by: CheckEval — explicitly defined, atomic criteria dramatically improve evaluator agreement (§4); the seeded-defect gates study — specialized detectors hit 100% recall where a generic LLM reviewer hit 41% (§5); CoVe — explicit enumeration of what to verify reduces hallucinated conclusions.
**Rename rationale:** "uniquely caught" is an empirical claim you cannot assert at authoring time — persona distinctness frequently fails in practice (Chameleon's Limit, §5). Declare *responsibility*, then *measure* uniqueness with the overlap eval (§5). **[The uniqueness guarantee is a DEFAULT aspiration; the responsibility list is evidence-backed.]**

**3. `always_ask` — a binary-checkable question list. VALIDATED, with a format constraint.**
Justified by: CheckEval's mechanism — "Are all words in the sentence spelled correctly?" (checkable) beats "How well does the sentence adhere to grammar rules?" (ambiguous); binary decomposition raised inter-evaluator agreement by ~0.4 α and cut score variance ~80% *(verify digits)*.
**Constraint:** each question must be answerable yes/no/n-a against the artifact. Open-ended "consider the architecture" prompts forfeit the measured consistency gain.

**4. `evidence_demands` — what counts as proof for a finding. VALIDATED.**
Per failure class: what the hat must cite (file/line/section quote) before a finding is valid, and what severity cap applies to unevidenced findings.
Justified by: Wang et al. — evidence-before-verdict calibration (+9.8–14.3pt judge accuracy; "conclusions generated by the model are not supported by the explanation generated afterward" when verdict comes first); Zheng et al. (MT-Bench) — reference-guided grading cut failure 70%→15%; Rulers (2026 preprint, emerging) — mechanical score-capping when evidence count is insufficient. The cap-severity-without-evidence rule is directly modeled on Rulers but that source is unreplicated — **[cap rule: reasonable default anchored to an emerging paper]**.

**5. `blind_spots` — declared out-of-scope failure families. KEEP, as a default.**
No published study tests whether declaring blind spots changes review behavior. **[DEFAULT]**, motivated by: (a) routing — the synthesizer/adjudicator needs to know what no hat covered; (b) Chameleon's Limit shows hats will drift toward a generic voice, and an explicit "do not report on X; the [other] hat owns it" instruction is the cheapest available counterpressure (untested); (c) it operationalizes the overlap eval in §5. Keep it short — this field is also exposure to the irrelevant-detail penalty.

**6. `overlaps` (was: overlaps-with-other-personas) — KEEP, demoted to registry metadata.**
No study validates this field's effect on behavior. Its real value is for the *panel composer and the eval harness*, not the model: pairs of hats with declared overlap are the ones to run the distinctness test on (§5). **[DEFAULT]** Recommendation: keep it out of the prompt payload entirely (avoid irrelevant-detail cost); store it in front-matter the protocol reads.

**7. `severity_rubric` (NEW — add) — anchored severity definitions, shared across hats, with per-hat exemplars.**
Justified by: Prometheus ablation — removing per-level rubric descriptions degrades human-alignment; 0–5-ish granularity best evidenced (§4). One shared taxonomy across hats (so the adjudicator can merge), with 1–2 hat-specific anchor examples per level ("a SQL injection reachable from unauthenticated input = critical"). Few-shot exemplars improve judge consistency (Zheng et al., MT-Bench, +12–40pt at ~4× cost — for a hat file the cost is a few hundred tokens).

**8. `output_contract` (NEW — add) — reference to the shared output format, reasoning-first.**
See §3. Keep the contract in one shared file referenced by all hats, so a contract fix doesn't require editing N hats. **[DEFAULT for the sharing mechanism; the reasoning-first ordering is evidence-backed.]**

### Fields to exclude, on evidence

- Names, personalities, career histories, "you have 20 years of experience at Google": null-to-harmful (Zheng et al.; Araujo et al.).
- Demographic markers: harmful (Gupta et al.; Salewski et al.; Zheng et al. gender finding).
- Flattery/"world-class"/"distinguished" intensifiers: no evidence they add beyond plain domain framing (ExpertPrompting can't isolate them; Zheng et al. suggests null). **[Exclusion is a default; direct study of intensifiers alone not found.]**

---

## 3. Output contract recommendation

### The structure-vs-reasoning dispute, resolved head-on

**The claim "format restrictions degrade reasoning" (Tam et al., "Let Me Speak Freely?", https://arxiv.org/abs/2408.02442, EMNLP 2024 Industry) is real but was over-broad, and its own data locates the mechanism.**

- **CLAIM (mechanism, uncontested):** JSON mode forced answer-before-reasoning — "100% of GPT 3.5 Turbo JSON-mode responses placed the 'answer' key before the 'reason' key, resulting in zero-shot direct answering instead of zero-shot chain-of-thought reasoning."
  **SOURCE:** https://arxiv.org/html/2408.02442v1. **CONFIDENCE:** high. Corroborated by the schema-key-wording paper (https://arxiv.org/abs/2604.14862: schema keys "enter the autoregressive context and may guide generation"; changing only key wording substantially affects accuracy) and by CRANE's theory (https://arxiv.org/abs/2502.09061, ICML 2025: restrictive output grammars provably cap expressible computation; leaving reasoning spans unconstrained recovers and exceeds both baselines).

- **CLAIM (headline, contested):** big accuracy drops under JSON (e.g., Claude-3-Haiku GSM8K 86.5→23.4 *(verify digits)*).
  **CONTESTED BY:** dottxt, "Say What You Mean" (https://blog.dottxt.ai/say-what-you-mean.html — engineering blog, not peer-reviewed): "The prompts used for unstructured (NL) generation are markedly different than the ones used for structured generation, so the comparisons are not apples-to-apples to begin with." Their matched-prompt re-runs show structured ≥ unstructured (GSM8K 78 vs 77; Last Letter 77 vs 73). JSONSchemaBench (https://arxiv.org/abs/2501.10868) also finds constrained decoding can *improve* accuracy done properly (note: aligned with the dottxt camp; verify baseline-prompt matching before treating as neutral arbitration).
  **CONFIDENCE in the resolution:** high, because **both camps independently endorse the same fix** — Tam et al.'s own two-step NL-to-Format condition ("nearly identical performance" to free natural language), dottxt's reasoning-field-before-answer-field schema, and CRANE's unconstrained-reasoning-then-constrained-answer grammar are three implementations of one principle.

### The contract (evidence-backed)

For hat reviews (markdown-emitting agents, no constrained decoding):

```
## Analysis            <- free prose. No format requirements. The hat reasons,
                          quotes the artifact, explores. (NL-first: Tam et al.
                          NL-to-Format; CRANE; dottxt — all three converge here.)

## Findings            <- fixed structure, one block per finding:
- id, failure_class    (from the hat's declared classes)
- severity             (shared anchored taxonomy, §4)
- evidence             (verbatim quote + location; findings without evidence
                        are capped at the lowest severity band)
- claim                (one sentence)
- suggested_probe      (how the adjudicator/author could verify it)

## Not-found           <- explicit "checked X, found nothing" per always_ask item
                          (binary-checklist completeness; CheckEval rationale)

## Blind-spot flags    <- anything observed outside this hat's declared classes,
                          routed, not scored. [DEFAULT — no direct study]
```

Rules, each tied to its source:
1. **Analysis before Findings, always** — the one point of full consensus across the format literature.
2. **Never require severity/verdict in the first N tokens** of any section (Wang et al.: verdict-first reasoning is post-hoc rationalization).
3. **Structure only what downstream consumers parse** (Tam et al.'s own practitioner recommendation: "looser format restrictions... while still maintaining some level of structure to facilitate downstream processing").
4. **Schema/section names are instructions** — name fields with task-relevant words ("evidence", "failure_class"), since key wording measurably steers generation (2604.14862).
5. If you ever move to constrained decoding: constrain only the Findings block, never the Analysis span (CRANE).
6. Well-formed ≠ correct: schema compliance can be near-perfect while content accuracy lags badly (https://arxiv.org/abs/2604.25359) — parse-rate is not a quality metric for hats.

---

## 4. Severity / rubric design

### What the evidence says

- **Decomposition improves consistency, and the effect scales with atomicity.**
  FLASK (https://arxiv.org/abs/2307.10928): skill-decomposed scoring beats holistic (Pearson 0.732 vs 0.673 — real but modest *(verify digits)*).
  CheckEval (https://arxiv.org/abs/2403.18771): binary yes/no checklists vs G-Eval-style holistic Likert — agreement α 0.05–0.09 → 0.45–0.67, score variance down ~80%, correlation with humans +0.10 *(verify digits)*. Mechanism: "adjacent Likert scale scores lack clear distinctions (e.g., 3 vs 4)"; binary items constrain the answer space.
  DeCE (https://arxiv.org/abs/2509.16093, legal QA): precision/recall-decomposed criteria r=0.78 vs 0.35–0.48 for pointwise/G-Eval *(verify digits; single domain, small n)*.
  **CONFIDENCE:** high on direction, three independent groups converge.

- **Anchored rubrics beat bare numeric scales.**
  Prometheus (https://arxiv.org/abs/2310.08491) defines a rubric as criteria + "a description of each scoring decision (1 to 5)"; its ablation shows removing the rubric text degrades correlation, and removing the reference answer degrades it most *(verify Table 6 digits)*. No single paper A/B-tests bare-1-to-10 vs anchored-1-to-10 head-to-head — the anchoring claim rests on the Prometheus ablation plus CheckEval's ambiguity mechanism. **CONFIDENCE:** medium-high.

- **~5 levels is the best-evidenced granularity.** Grading-scale study (https://arxiv.org/html/2601.03444v1, Jan 2026 preprint): "the grading scale of 0-5 yields the strongest human-LLM alignment" (ICC 0.853 vs 0.805 for 0–10) — task-dependent, weaker on subjective tasks, unreplicated. **CONFIDENCE:** medium.

- **Evidence-before-verdict is the strongest quantified mitigation.**
  Wang et al., "LLMs are not Fair Evaluators" (https://arxiv.org/abs/2305.17926, ACL 2024): explanation-first + position-balanced calibration: ChatGPT 44.4→58.7, GPT-4 52.7→62.5.
  Zheng et al., MT-Bench (https://arxiv.org/abs/2306.05685, NeurIPS 2023): reference-guided grading cut math-judging failure 70%→30% (CoT) →15% (reference-guided).
  **CONFIDENCE:** high.

- **Known judge biases to design against:** position bias (robust, can flip up to ~80% of verdicts for weak judges — mostly a protocol-layer concern, already handled); verbosity bias (weak judges fooled 91% by padded answers, GPT-4 8.7% — magnitudes dated to 2023-era models); self-preference (Zheng et al.: "our study cannot determine whether the models exhibit a self-enhancement bias" — inconclusive; G-Eval reports a hedged same-family preference).

### Recommended severity design

1. **One shared taxonomy across all hats**, 4–5 discrete named levels (e.g., blocker / major / minor / nit / observation), each with (a) an anchored one-sentence definition written as a *decision rule* with binary-checkable conditions ("blocker = causes incorrect behavior or data loss on a reachable path, evidence quoted"), and (b) 1–2 per-hat exemplar findings per level. [Anchoring: Prometheus. Binary conditions: CheckEval. ~5 levels: 2601.03444, medium. Exemplars: MT-Bench few-shot consistency.]
2. **Severity is assigned only after the evidence field is filled**, and is mechanically capped one band down if evidence is missing. [Evidence-first: Wang et al., high. Mechanical cap: Rulers (https://arxiv.org/html/2601.08654v1), Jan 2026 preprint, unreplicated — emerging.]
3. **Expect internal consistency to overstate calibration:** LLM panels agree with each other (ICC ~0.94) more than with humans (~0.80–0.85) — periodically spot-check severity calls against human judgment rather than trusting cross-hat agreement. [2601.03444, medium.]
4. **Plan for criteria drift:** "users need criteria to grade outputs, but grading outputs helps users define criteria" (Shankar et al., "Who Validates the Validators", https://arxiv.org/abs/2404.12272, UIST 2024). The severity rubric and failure-class definitions should be versioned and expected to be revised after real review batches — a locked-forever rubric contradicts the best HCI evidence. **CONFIDENCE:** high.

---

## 5. How to eval a hat

Three tests, in ascending order of published support for the *specific* application:

### (a) Adherence probe — "does the hat change behavior at all?" — mature methods exist
Administer a fixed battery of probe prompts; score with an LLM judge against an anchored rubric; validate the judge against human ratings once. Published precedents: InCharacter (https://arxiv.org/abs/2310.17976, ACL 2024 — isolated-context interview probes scored against ground truth; judge-human κ≈0.61); PersonaGym (https://arxiv.org/html/2407.18416v5, preprint — 5 behavioral tasks, judge-human Spearman ρ=0.751, Fleiss κ=0.71); RoleLLM (https://arxiv.org/abs/2310.00746, ACL Findings 2024 — decomposes adherence into orthogonal sub-metrics).
**For hats:** the probe set = the hat's `always_ask` list run against a small fixed artifact; pass = the hat addresses its declared classes and stays out of declared blind spots. **[Adaptation is ours; the measurement pattern is published.]**
**Caveat:** anonymize hat names in any judge-scored eval — judges score differently when they recognize the character name (https://arxiv.org/abs/2603.03915, preprint, medium confidence).

### (b) Distinctness test — "are two hats actually different?" — published evidence is mixed-to-NEGATIVE; treat as a real risk
- Chameleon's Limit (https://arxiv.org/abs/2604.24698, preprint, high-detail): personas on one base model frequently collapse — in one model "83% of variation is stochastic," i.e., persona signal below sampling noise; models that hit target traits caricature everything else.
- "Stable Behavior, Limited Variation" (https://arxiv.org/pdf/2604.28048, preprint): high within-persona stability, weak cross-persona differentiation.
- The classifier-attribution method (train a cheap classifier to identify which condition produced a text; F1 0.98–0.99 distinguishing *models*, https://arxiv.org/abs/2606.09854) is precedented as a method but **no published study applies it to same-model different-persona outputs** — running it hat-vs-hat is a sound, novel-in-application eval. **[Method: published. Application to hats: our design.]**
- **Cheaper operational proxy [DEFAULT]:** run 2 hats on the same artifact N times; compute finding-overlap (matched findings / total). High overlap on classes both hats declare = fine; high overlap on classes only one declares = the hats have collapsed; also compare against a *no-persona* control reviewer — a hat must beat the control on its own classes to justify existing (this control condition is directly motivated by Zheng et al.'s null result).
- **Note for the panel protocol:** the best-evidenced diversity lever in adversarial review is *cross-model* diversity, not persona diversity — the CVE-pipeline case study (https://arxiv.org/abs/2604.19049, preprint) needed a different model family to catch "correlated training-data errors that same-family review tends to miss," and states "adversarial framing alone is insufficient." If the blind panel can vary the model per hat, that is better supported than varying persona text alone.

### (c) Seeded-defect probe — "does the hat catch its declared classes?" — the published design to copy
Deterministic Integrity Gates (https://arxiv.org/abs/2606.09500, preprint): inject exactly one known, class-labeled defect at a time into a clean artifact; run the detector; record per-class recall; run on the clean artifact to measure false positives. Their numbers are the cautionary tale: specialized detectors 27/27 (100% recall, 0 FP) vs. a generic LLM reviewer 11/27 (41%), with entire failure families missed.
**For hats:** maintain per-hat defect corpora — for each declared failure class, ≥3 planted defects in otherwise-clean artifacts, plus defects belonging to *other* hats' classes (to measure lane discipline), plus clean artifacts (FP rate). A hat passes if per-class recall on its own classes clears a threshold and FP rate stays low. **No published study compares persona-vs-persona on planted defects — this eval fills a genuine gap; say so in the doc rather than citing it as established practice.**

### (d) Regression on edit — engineering practice, honestly labeled
- Direct evidence prompt edits regress silently: adding a "helpful assistant" wrapper improved instruction-following +13% while degrading extraction accuracy −10% and RAG compliance −13% on Llama-3-8B ("When 'Better' Prompts Hurt", https://arxiv.org/html/2601.22025v1, preprint — single model, treat as existence proof).
- Therefore: after any hat edit, re-run (a) + (c) and diff against the stored baseline; a gain on the edited dimension does not clear the change — all dimensions must hold. Baseline-diff workflow per promptfoo docs (https://www.promptfoo.dev/docs/intro/) — **tooling documentation, not science; no study measures how often such suites catch persona regressions.**
- Expect the criteria themselves to drift (Shankar et al., UIST 2024): schedule rubric/failure-class revision after real usage batches, and re-baseline evals when definitions change.

---

## 6. Contested / refuted claims

| Claim | Status | Detail |
|---|---|---|
| "Adding an expert persona improves LLM accuracy" | **Refuted as a general claim** for factual tasks (Zheng et al. 2311.10054); holds only as task-dependent, small-to-moderate for domain-matched generative/review-type work | Do not cite ExpertPrompting as generic support — it measures LLM-judged preference on open-ended answers, unablated |
| "Role-play prompting improves reasoning" | **Contested** | Large gains (Kong et al., NAACL 2024) vs. degradation on 4/12 datasets incl. GPT-4 (2408.08631). Depends on construction; not a reliable free lunch |
| "Format restrictions degrade reasoning" | **Contested; consensus narrows to the mechanism** | Tam et al. headline vs. dottxt matched-prompt rebuttal + JSONSchemaBench. Uncontested core: answer-before-reasoning ordering hurts; reasoning-first recovers (all camps) |
| "Decorative persona details are harmless noise" | **Refuted** | They are actively harmful: ~30pp drops (Araujo et al.), demographic bias (Gupta et al.) |
| "Distinct persona prompts yield distinct behavior" | **Contested, lean negative** | Chameleon's Limit + Stable-Behavior show frequent collapse; the one positive study confounds persona with temperature (2510.26490) |
| "CoT stabilizes persona consistency" | **Refuted** (as tested) | PERSIST: CoT *increases* response variability across runs |
| Judge self-preference bias | **Inconclusive** | Zheng et al. explicitly: "cannot determine"; G-Eval reports a hedged same-family effect. Don't state as established |
| "Best persona can be selected per task" | **Refuted** | Zheng et al.: automatic selection no better than random |
| Verbosity-bias magnitudes (91% vs 8.7%) | Dated | 2023-era judges; direction robust, numbers stale |
| Rulers evidence-capping, 0–5-scale optimality, "Better Prompts Hurt" numbers | Emerging | Jan 2026 preprints, unreplicated — cite as "early evidence," never as consensus |

---

## 7. Sources table

| # | Source | Venue / status | URL | Used for | Confidence |
|---|---|---|---|---|---|
| 1 | Zheng et al., "When 'A Helpful Assistant' Is Not Really Helpful" | EMNLP Findings 2024 | https://arxiv.org/abs/2311.10054 | Persona null result; domain coef; gender-neutral; selection≈random | High |
| 2 | Xu et al., ExpertPrompting | arXiv preprint | https://arxiv.org/abs/2305.14688 | Customized expert descriptions (LLM-judged) | Medium |
| 3 | Kong et al., Role-Play Prompting | NAACL 2024 | https://arxiv.org/abs/2308.07702 | Task-coupled role gains; ceiling effects | High |
| 4 | Salewski et al., In-Context Impersonation | NeurIPS 2023 spotlight | https://arxiv.org/abs/2305.14930 | Domain-expert effect; demographic bias | High |
| 5 | Gupta et al., Bias Runs Deep | ICLR 2024 | https://arxiv.org/abs/2311.04892 | Demographic personas harm reasoning | High (2023-era models) |
| 6 | Araujo et al., Principled Personas | arXiv 2025 | https://arxiv.org/abs/2508.19764 | Irrelevant-detail harm (~30pp); expert≈null-to-positive | High |
| 7 | "Persona is a Double-edged Sword" | arXiv preprint | https://arxiv.org/abs/2408.08631 | Role-play hurts 4/12 datasets | Medium |
| 8 | Li et al., Instruction (In)Stability | arXiv | https://arxiv.org/abs/2402.10962 | Drift in ~8 rounds; re-injection | High |
| 9 | PERSIST | arXiv 2025 | https://arxiv.org/html/2508.04826v1 | Scale doesn't fix instability; CoT worsens it | High |
| 10 | Prompt Makes the Person(a) | arXiv preprint | https://arxiv.org/abs/2507.16076 | Surface form affects stereotyping fidelity | Medium-high |
| 11 | Tam et al., Let Me Speak Freely? | EMNLP 2024 Industry | https://arxiv.org/abs/2408.02442 | Format-restriction drops; key-order mechanism; NL-to-Format fix | High |
| 12 | dottxt, Say What You Mean | Blog (not peer-reviewed) | https://blog.dottxt.ai/say-what-you-mean.html | Prompt-confound rebuttal; reasoning-first schema | Medium (direction) |
| 13 | JSONSchemaBench | arXiv preprint | https://arxiv.org/abs/2501.10868 | Constrained decoding can help | Medium-high |
| 14 | CRANE | ICML 2025 | https://arxiv.org/abs/2502.09061 | Theory; constrain answers not reasoning | Medium-high |
| 15 | Schema-key wording | arXiv 2026 preprint | https://arxiv.org/abs/2604.14862 | Keys are instructions | High (abstract verbatim) |
| 16 | Structured Output Benchmark | arXiv 2026 preprint | https://arxiv.org/abs/2604.25359 | Compliance ≠ correctness | High |
| 17 | G-Eval | arXiv (widely cited) | https://arxiv.org/abs/2303.16634 | Auto-CoT rubric; prob-weighted scores; same-family bias | High |
| 18 | Prometheus | arXiv | https://arxiv.org/abs/2310.08491 | Anchored rubric ablation | High (direction) |
| 19 | FLASK | arXiv | https://arxiv.org/abs/2307.10928 | Skill decomposition, modest gain | Medium-high |
| 20 | CheckEval | arXiv | https://arxiv.org/abs/2403.18771 | Binary checklists ≫ holistic Likert | Medium-high |
| 21 | DeCE | arXiv preprint | https://arxiv.org/abs/2509.16093 | Decomposed criteria r=0.78 (legal domain) | Medium |
| 22 | Rulers | arXiv Jan 2026 preprint | https://arxiv.org/html/2601.08654v1 | Locked rubric; evidence-capped scores | Low-medium (unreplicated) |
| 23 | Grading Scale Impact | arXiv Jan 2026 preprint | https://arxiv.org/html/2601.03444v1 | 0–5 scale best; panel-vs-human gap | Medium |
| 24 | Wang et al., Not Fair Evaluators | ACL 2024 | https://arxiv.org/abs/2305.17926 | Position bias; evidence-first calibration | High |
| 25 | Zheng et al., MT-Bench / LLM-as-judge | NeurIPS 2023 | https://arxiv.org/abs/2306.05685 | Verbosity bias; reference-guided grading; 85% agreement | High |
| 26 | Shankar et al., Who Validates the Validators | UIST 2024 | https://arxiv.org/abs/2404.12272 | Criteria drift; EvalGen | High |
| 27 | InCharacter | ACL 2024 | https://arxiv.org/abs/2310.17976 | Interview-probe adherence eval | High |
| 28 | RoleLLM / RoleBench | ACL Findings 2024 | https://arxiv.org/abs/2310.00746 | Decomposed adherence metrics | High |
| 29 | PersonaGym | arXiv preprint | https://arxiv.org/html/2407.18416v5 | Behavioral-task adherence rubric | Medium-high |
| 30 | Chameleon's Limit | arXiv 2026 preprint | https://arxiv.org/abs/2604.24698 | Persona collapse / distinctness diagnostics | High-detail, unreviewed |
| 31 | Stable Behavior, Limited Variation | arXiv 2026 preprint | https://arxiv.org/pdf/2604.28048 | Weak cross-persona differentiation | Medium (thesis-level) |
| 32 | Stylometric fingerprinting | arXiv 2026 preprint | https://arxiv.org/abs/2606.09854 | Classifier-attribution distinctness method | High (method), medium (relevance) |
| 33 | Adversarial CVE pipeline | arXiv 2026 preprint | https://arxiv.org/abs/2604.19049 | Cross-model diversity > persona diversity | High (case study, no ablation) |
| 34 | Deterministic Integrity Gates | arXiv 2026 preprint | https://arxiv.org/abs/2606.09500 | Seeded-defect eval design; generic reviewer 41% recall | High |
| 35 | When 'Better' Prompts Hurt | arXiv 2026 preprint | https://arxiv.org/html/2601.22025v1 | Silent regression from prompt edits | Medium (single model) |
| 36 | Chain-of-Verification (CoVe) | arXiv | https://arxiv.org/abs/2309.11495 | Explicit verification-question enumeration | High (bridge evidence) |
| 37 | Rethinking Role-Playing Eval (anonymization) | arXiv 2026 preprint | https://arxiv.org/abs/2603.03915 | Judge name-recognition confound | Medium |
| 38 | promptfoo docs | Tooling docs (not science) | https://www.promptfoo.dev/docs/intro/ | Baseline-diff regression workflow | High (as documentation) |
| 39 | Divergent/Convergent Personas | arXiv preprint | https://arxiv.org/html/2510.26490 | One positive distinctness result (temp-confounded) | Medium |
| 40 | Two Tales of Persona (survey) | arXiv | https://arxiv.org/abs/2406.01171 | No attribute-impact taxonomy exists (gap) | Medium |

### Explicit evidence gaps (state these in the methodology doc)
1. No factorial study of concern-lists vs. identity attributes as persona components — our checklist-centric hat design is a triangulated inference, not a single result.
2. No persona-vs-persona seeded-defect study — our hat eval (§5c) is a novel application of a published design.
3. No same-model persona-distinctness classifier study — §5b method is precedented, application is ours.
4. Persona-file regression testing has zero academic backing — it is tooling practice plus one silent-regression existence proof.
5. Demographic-bias findings (Gupta et al.) are unreplicated on 2025-26 frontier models.
