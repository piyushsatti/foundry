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

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    per_hat: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          hat: { type: 'string' },
          in_class_findings: { type: 'integer' },
          out_of_class_findings: { type: 'integer' },
          beats_control: { type: 'boolean' },
          unique_catches: { type: 'array', items: { type: 'string' } },
        },
        required: ['hat', 'in_class_findings', 'out_of_class_findings', 'beats_control'],
      },
    },
    pairwise_overlap: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          pair: { type: 'string' },
          overlapping_findings: { type: 'integer' },
          note: { type: 'string' },
        },
        required: ['pair', 'overlapping_findings'],
      },
    },
    verdict: { type: 'string' },
  },
  required: ['per_hat', 'pairwise_overlap', 'verdict'],
}

// Review the shared artifact once per hat (in its lens) + once with no persona (control).
const reviewers = hats.map((h) => ({ name: h.name, isControl: false }))
reviewers.push({ name: 'no-persona-control', isControl: true })

const reviewed = await parallel(reviewers.map((r) => async () => {
  const prompt = r.isControl
    ? `You are a competent, generalist technical reviewer with no special lens. Read the artifact at ${artifactPath} and report any genuine defects you find. For each: failure_class (your own short label), severity (blocker/major/minor/nit), location, claim (one sentence). Report only real defects; return an empty array if none.`
    : `You are a PANELIST wearing the "${r.name}" lens. Read your lens at ${hatDir}/${r.name}.md and the artifact at ${artifactPath}. Review the artifact ONLY through this lens. For each finding: failure_class MUST be one of your hat's declared classes; severity (blocker/major/minor/nit); location; claim (one sentence). Report only genuine defects in your lane; return an empty array if none.`
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

const judgeInput = {
  hat_class_definitions: hats.reduce((acc, h) => { acc[h.name] = h.classes; return acc }, {}),
  hat_findings: hatReviews.reduce((acc, r) => { acc[r.reviewer] = r.findings; return acc }, {}),
  control_findings: control ? control.findings : [],
}

const verdict = await agent(
  `You are evaluating whether a set of professional-lens "hats" are genuinely DISTINCT reviewers, and whether each earns its existence vs a no-persona control. Same-model personas often collapse toward one voice — your job is to measure whether these did.

Input JSON:
${JSON.stringify(judgeInput, null, 1)}

For EACH hat compute:
- in_class_findings: how many of its findings fall within its own declared classes (hat_class_definitions).
- out_of_class_findings: findings outside its declared classes (lane discipline — lower is better).
- beats_control: true if the hat surfaced at least one in-class defect that the no-persona control did NOT raise (this is the "justifies existing" test — a hat that only finds what a generic reviewer finds adds nothing).
- unique_catches: short labels for defects this hat caught that no other hat and not the control caught.

Then pairwise_overlap: for each hat pair, how many findings are about the SAME underlying issue (semantic match, not wording). High overlap on classes BOTH hats declare is fine; high overlap on classes only one declares signals collapse.

Finally a one-paragraph verdict on whether the hats are acceptably distinct or show collapse, and which (if any) fail the beats_control test.`,
  {
    label: 'judge:distinctness',
    phase: 'Judge',
    model: 'opus',
    effort: 'high',
    agentType: 'general-purpose',
    schema: JUDGE_SCHEMA,
  }
)

return {
  artifact: artifactPath,
  hats_tested: hats.map((h) => h.name),
  control_finding_count: control ? control.findings.length : 0,
  per_hat_finding_counts: hatReviews.map((r) => ({ hat: r.reviewer, count: r.findings.length })),
  distinctness: verdict,
}
