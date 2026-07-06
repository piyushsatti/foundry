export const meta = {
  name: 'crucible-hat-evals',
  description: 'Distinctness/overlap + adherence eval for crucible hats — do the lenses actually differ, and does each beat a no-persona control on its own classes',
  phases: [
    { title: 'Review' },
    { title: 'Judge' },
  ],
}

// args = { artifactPath, hatDir, hats: [{name, classes}] }
const A = typeof args === 'string' ? JSON.parse(args) : args
const { artifactPath, hatDir, hats } = A

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          failure_class: { type: 'string' },
          severity: { type: 'string' },
          location: { type: 'string' },
          claim: { type: 'string' },
        },
        required: ['failure_class', 'severity', 'location', 'claim'],
      },
    },
  },
  required: ['findings'],
}

// The judge independently re-classifies every finding — it never trusts the
// reviewer's self-reported failure_class (that would force in-class labels
// and make out-of-class structurally ~0). finding_classifications is the
// source of truth in/out-of-class counts are computed from below.
const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    finding_classifications: {
      type: 'array',
      description: 'One entry per finding, across ALL reviewers, independently classified by the judge — never trusts the reviewer\'s self-reported failure_class.',
      items: {
        type: 'object',
        properties: {
          reviewer_id: { type: 'string', description: 'Opaque id of the reviewer who raised this finding, e.g. "Reviewer-2"' },
          finding_index: { type: 'integer', description: 'Index of this finding within that reviewer\'s own findings array' },
          classified_as: { type: 'string', description: 'The opaque reviewer id whose declared classes this finding TRULY belongs to, or "none" if it fits no reviewer\'s declared classes' },
          rationale: { type: 'string' },
        },
        required: ['reviewer_id', 'finding_index', 'classified_as'],
      },
    },
    per_reviewer: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          reviewer_id: { type: 'string' },
          beats_control: { type: 'boolean' },
          unique_catches: { type: 'array', items: { type: 'string' } },
        },
        required: ['reviewer_id', 'beats_control'],
      },
    },
    pairwise_overlap: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          reviewer_a: { type: 'string' },
          reviewer_b: { type: 'string' },
          overlapping_findings: { type: 'integer' },
          note: { type: 'string' },
        },
        required: ['reviewer_a', 'reviewer_b', 'overlapping_findings'],
      },
    },
    verdict: { type: 'string' },
  },
  required: ['finding_classifications', 'per_reviewer', 'pairwise_overlap', 'verdict'],
}

// Review the shared artifact once per hat (in its lens) + once with no persona (control).
const reviewers = hats.map((h) => ({ name: h.name, isControl: false }))
reviewers.push({ name: 'no-persona-control', isControl: true })

const reviewed = await parallel(reviewers.map((r) => async () => {
  const prompt = r.isControl
    ? `You are a competent, generalist technical reviewer with no special lens. Read the artifact at ${artifactPath} and report any genuine defects you find. For each: failure_class (your own short label), severity (blocker/major/minor/nit), location, claim (one sentence). Report only real defects; return an empty array if none.`
    : `You are a PANELIST wearing the "${r.name}" lens. Read your lens at ${hatDir}/${r.name}.md and the artifact at ${artifactPath}. Review the artifact ONLY through this lens. For each finding, label it with the failure_class you believe it is — prefer your hat's declared classes, but if a defect you notice falls outside them, report it with your best-fit label rather than forcing it into your hat's taxonomy. Also report severity (blocker/major/minor/nit); location; claim (one sentence). Report only genuine defects in your lane; return an empty array if none.`
  const out = await agent(prompt, {
    label: `review:${r.name}`,
    phase: 'Review',
    model: 'opus',
    effort: 'high',
    agentType: 'general-purpose',
    schema: REVIEW_SCHEMA,
  })
  return { reviewer: r.name, isControl: r.isControl, findings: (out && out.findings) || [] }
}))

const clean = reviewed.filter(Boolean)
const control = clean.find((r) => r.isControl)
const hatReviews = clean.filter((r) => !r.isControl)

// Anonymize before the judge ever sees anything: opaque Reviewer-N ids only —
// a judge that recognizes "the security hat" can lean on name association
// instead of independently classifying the finding. Order is decorrelated from
// the caller's hats-array order by a deterministic name-sort (NOT Math.random —
// the workflow runtime forbids it, and randomness would break resume). Name-
// hiding is the actual bias protection; the reorder is just belt-and-suspenders.
const shuffled = [...hatReviews].sort((a, b) => (a.reviewer < b.reviewer ? -1 : a.reviewer > b.reviewer ? 1 : 0))

const idToName = new Map()
const nameToId = new Map()
shuffled.forEach((r, i) => {
  const id = `Reviewer-${i + 1}`
  idToName.set(id, r.reviewer)
  nameToId.set(r.reviewer, id)
})

const hatClassesByName = hats.reduce((acc, h) => { acc[h.name] = h.classes; return acc }, {})

const reviewer_class_definitions = {}
const reviewer_findings = {}
for (const r of hatReviews) {
  const id = nameToId.get(r.reviewer)
  reviewer_class_definitions[id] = hatClassesByName[r.reviewer]
  reviewer_findings[id] = r.findings
}

const judgeInput = {
  reviewer_class_definitions,
  reviewer_findings,
  control_findings: control ? control.findings : [],
}

const verdict = await agent(
  `You are evaluating whether a set of professional-lens "hats" are genuinely DISTINCT reviewers, and whether each earns its existence vs a no-persona control. Same-model personas often collapse toward one voice — your job is to measure whether these did.

Reviewers are presented to you as opaque ids (Reviewer-1..N) — you do not know which named hat each id really is. Judge each finding on its content, never on a name.

Input JSON:
${JSON.stringify(judgeInput, null, 1)}

For EACH finding from EACH reviewer, independently decide which reviewer's declared class list (reviewer_class_definitions) it TRULY belongs to — do NOT trust the finding's own "failure_class" label; reviewers were told they may report a best-fit label outside their own lane rather than force one. Output one entry per finding in finding_classifications: reviewer_id (who raised it), finding_index (its position in that reviewer's findings array), classified_as (the reviewer_id whose declared classes it truly fits, or "none" if it fits no reviewer's declared classes), and a short rationale. A finding is in-class for the reviewer that raised it only when classified_as equals that same reviewer_id; anything else (a different reviewer_id, or "none") is out-of-class for the raiser.

Then for EACH reviewer (per_reviewer) compute:
- beats_control: true if the reviewer surfaced at least one in-class defect (by YOUR classification above) that the no-persona control did NOT raise (the "justifies existing" test — a hat that only finds what a generic reviewer finds adds nothing).
- unique_catches: short labels for defects this reviewer caught that no other reviewer and not the control caught.

Then pairwise_overlap: for each reviewer pair (reviewer_a, reviewer_b — opaque ids), how many findings are about the SAME underlying issue (semantic match, not wording). High overlap on classes BOTH declare is fine; high overlap on classes only one declares signals collapse.

Finally a one-paragraph verdict on whether the reviewers are acceptably distinct or show collapse, and which (if any) fail the beats_control test. Refer to reviewers only by their opaque id in the verdict text.`,
  {
    label: 'judge:distinctness',
    phase: 'Judge',
    model: 'opus',
    effort: 'high',
    agentType: 'general-purpose',
    schema: JUDGE_SCHEMA,
  }
)

// in_class_findings / out_of_class_findings are computed here from the
// judge's independent per-finding classification — never from the
// reviewer's own self-label. This is what makes out-of-class measurable
// instead of structurally ~0.
const classifications = (verdict && verdict.finding_classifications) || []
const perHatCounts = {}
for (const id of idToName.keys()) perHatCounts[id] = { in_class_findings: 0, out_of_class_findings: 0 }
for (const c of classifications) {
  const bucket = perHatCounts[c.reviewer_id]
  if (!bucket) continue
  if (c.classified_as === c.reviewer_id) bucket.in_class_findings += 1
  else bucket.out_of_class_findings += 1
}

const perReviewerJudge = (verdict && verdict.per_reviewer) || []
const perReviewerById = perReviewerJudge.reduce((acc, p) => { acc[p.reviewer_id] = p; return acc }, {})

// De-anonymize: opaque ids are mapped back to real hat names only here, in
// the script's final return value — the judge itself never saw real names.
const per_hat = [...idToName.entries()].map(([id, name]) => {
  const j = perReviewerById[id] || {}
  const counts = perHatCounts[id] || { in_class_findings: 0, out_of_class_findings: 0 }
  return {
    hat: name,
    in_class_findings: counts.in_class_findings,
    out_of_class_findings: counts.out_of_class_findings,
    beats_control: !!j.beats_control,
    unique_catches: j.unique_catches || [],
  }
})

const pairwise_overlap = ((verdict && verdict.pairwise_overlap) || []).map((p) => ({
  pair: `${idToName.get(p.reviewer_a) || p.reviewer_a} vs ${idToName.get(p.reviewer_b) || p.reviewer_b}`,
  overlapping_findings: p.overlapping_findings,
  note: p.note,
}))

return {
  artifact: artifactPath,
  hats_tested: hats.map((h) => h.name),
  control_finding_count: control ? control.findings.length : 0,
  per_hat_finding_counts: hatReviews.map((r) => ({ hat: r.reviewer, count: r.findings.length })),
  per_hat,
  pairwise_overlap,
  distinctness: (verdict && verdict.verdict) || '',
}
