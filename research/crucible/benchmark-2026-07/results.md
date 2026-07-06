# Model×effort benchmark — results (2026-07-05)

**Workflow:** `scripts/workflows/role-benchmark.js` · **Corpus:** this dir (24 seeded variants + clean controls) · **Judge:** opus/high, config names anonymized to the scorer. · **72 agents, ~2.0M tokens.**

**Roles benchmarked:** red-attacker (security lens, 7 seeded security variants + 3 clean controls) and panelist (architect lens, 6 seeded architecture variants). **Adjudicator was NOT benchmarked** — it needs red+blue pairs (≈2× cost); deferred, so its pin still rests on the D-evidence prior, not data. This is a logged sample bound, not silent truncation.

## Raw results

**Red (security lens)** — recall = planted defects caught / total; FP = substantive defect claims raised on clean artifacts.

| Config | Recall | FP on clean | Total findings |
|---|---|---|---|
| sonnet / high | **7/7** | 7 | 23 |
| sonnet / max | **7/7** | **10** | 29 |
| opus / medium | **7/7** | 7 | 24 |
| opus / high | **7/7** | 7 | 22 |

**Panel (architect lens)** — 6 seeded variants, no clean controls in this slice.

| Config | Recall | FP | Total findings |
|---|---|---|---|
| sonnet / high | **6/6** | 0 | 19 |
| sonnet / max | **6/6** | 0 | 19 |
| opus / medium | **6/6** | 0 | 19 |
| opus / high | **6/6** | 0 | 22 |

Every config caught every planted defect at both roles, including the `subtle`-graded ones (architect ownership-ambiguity and painted-into-corner; security data-exposure and injection).

## What this does and does not tell us

**Primary finding — the benchmark did not discriminate the configs on detection.** Recall saturated at 100% across all four configs on both roles. On this corpus, capability tier (sonnet vs opus) and effort (high/max/medium) made **no difference to whether a planted defect was found.** That is a real result, but it means the corpus is **too easy to answer the "sonnet-high vs opus-medium" question** — the planted defects, even the subtle ones, were within reach of the cheapest config tested. To separate the tiers you need defects that require deeper reasoning to surface (multi-step, cross-section, or defects disguised as correct code).

**The one signal that did emerge — max effort inflates false positives on adversarial review.** sonnet/max raised 10 false-positive defect claims on clean artifacts vs 7 for every other config, with the most total findings (29). More adversarial "effort" produced more *unfounded* flags, not more real catches — recall was already maxed. This matches the methodology's precision-bias finding [D9]: cranking up an attacker's aggression trades precision for noise. **Actionable: do not use `max` effort for the red/attacker role.**

**Precision ordering (secondary, weak N=1 signal):** at equal 7/7 recall, opus/high was the leanest (22 findings) and sonnet/max the noisiest (29). opus/high and opus/medium and sonnet/high all tied on FP (7). So opus/high has a slight precision edge, but it is not decisive over sonnet/high on this corpus.

## Pin decisions

The provisional pins are **retained, not overturned** — the data neither refutes them nor strongly supports opus over sonnet, because recall saturated. Rationale:

| Agent | Pin | Basis after benchmark |
|---|---|---|
| red-attacker | opus / **high** | Retained on the D-evidence prior + slight precision edge (leanest at 7/7). **Not** max (max inflated FP). sonnet/high is a viable cost-saving alternative — it matched opus/high here. |
| adjudicator | opus / high | **Un-benchmarked** — stays on prior [D6/D10: severity calls are the expensive failure]. Benchmark this next (needs pairs). |
| blue-verifier | sonnet / high | Consistent with the panel result (sonnet matched opus at 0 FP). |
| panelist | sonnet / medium | **Validated directionally** — the architect panel hit 6/6 / 0 FP at sonnet; medium not directly tested but the easy-corpus recall saturation makes a lighter tier safe here. |

**No pin changed.** Changing pins to chase a non-discriminating result would be over-fitting to an easy corpus.

## Follow-ups (logged, not done)

1. **Harder corpus v2** — defects that need multi-step reasoning, so the benchmark can actually separate tiers. The current corpus proves the harness works but lacks discriminating power on recall.
2. **Benchmark the adjudicator** — the role whose pin most needs data (its severity calls are the expensive failure) is still un-benchmarked.
3. **FP-focused scoring** — since recall saturates, false-positive rate and precision are the discriminating axes on easy corpora; weight them in v2.
