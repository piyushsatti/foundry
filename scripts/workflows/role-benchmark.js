export const meta = {
  name: 'crucible-role-benchmark',
  description: 'Model×effort benchmark for crucible review roles (red-attacker + panelist) against the seeded-defect corpus',
  phases: [
    { title: 'Review' },
    { title: 'Score' },
  ],
}

// args = {
//   corpusDir, hatDir,
//   configs: [{id, model, effort}],
//   redTasks:   [{variant_file, is_clean, failure_class, defect_id, location, subtlety}],
//   panelTasks: [{variant_file, is_clean, failure_class, defect_id, location, subtlety}],
// }
const A = typeof args === 'string' ? JSON.parse(args) : args
const { corpusDir, hatDir, configs, redTasks, panelTasks } = A

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
    per_task: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          defect_id: { type: 'string' },
          caught: { type: 'boolean' },
          subtlety: { type: 'string' },
          note: { type: 'string' },
        },
        required: ['defect_id', 'caught'],
      },
    },
    planted_caught: { type: 'integer' },
    planted_total: { type: 'integer' },
    false_positive_findings_on_clean: { type: 'integer' },
  },
  required: ['per_task', 'planted_caught', 'planted_total', 'false_positive_findings_on_clean'],
}

const RED_CLASSES = 'trust-boundary-violation, authz-gap, data-exposure, injection, supply-chain, missing-abuse-controls'
const ARCH_CLASSES = 'implicit-coupling, wrong-seam, single-point-of-failure, painted-into-corner, ownership-ambiguity, sync/async-mismatch'

function reviewPrompt(role, task) {
  const hatFile = role === 'red' ? `${hatDir}/security.md` : `${hatDir}/architect.md`
  const classes = role === 'red' ? RED_CLASSES : ARCH_CLASSES
  const stance = role === 'red'
    ? 'You are RED — an adversarial security reviewer. Assume the artifact fails in production and find how.'
    : 'You are a PANELIST wearing the architect lens — a neutral systems-architecture reviewer.'
  return `${stance}
Read the lens definition at ${hatFile} and the artifact at ${corpusDir}/${task.variant_file}.
Review the artifact ONLY through this lens. Report genuine defects only — do NOT invent problems to seem thorough; a clean artifact should yield few or no findings.
For every finding: failure_class MUST be one of {${classes}}; severity ∈ {blocker,major,minor,nit}; location = the section/step where it occurs; claim = one sentence on what is wrong. Assign severity only after you can point at the evidence.
Return the findings array (empty if you find nothing real).`
}

function judgePrompt(role, scored) {
  const classes = role === 'red' ? RED_CLASSES : ARCH_CLASSES
  return `You are scoring a reviewer's findings against ground truth. Failure-class vocabulary: {${classes}}.
For each task below you get: defect_id, whether the artifact is CLEAN (no planted defect) or has a planted defect (with its failure_class + location), and the reviewer's findings.
Scoring rules:
- A planted defect is CAUGHT if any reviewer finding is semantically about that defect: its failure_class matches or is equivalent to the planted class AND its location points at approximately the planted location. Be strict about semantic match but tolerant of wording/section-label differences.
- planted_caught = number of non-clean tasks caught; planted_total = number of non-clean tasks.
- false_positive_findings_on_clean = total count of substantive defect findings the reviewer raised on CLEAN artifacts (nit-level style notes don't count; real claimed defects do).
Return per_task (defect_id, caught bool, subtlety, short note), and the three totals.

TASKS (JSON):
${JSON.stringify(scored, null, 1)}`
}

async function runRole(role, tasks) {
  // For each config: review every task at that config, then judge the batch.
  const results = await pipeline(
    configs,
    async (cfg) => {
      const reviews = await parallel(tasks.map((task) => async () => {
        const out = await agent(reviewPrompt(role, task), {
          label: `${role}:${cfg.id}:${task.defect_id}`,
          phase: 'Review',
          model: cfg.model,
          effort: cfg.effort,
          agentType: 'general-purpose',
          schema: REVIEW_SCHEMA,
        })
        return { task, findings: (out && out.findings) || [] }
      }))
      return { cfg, reviews: reviews.filter(Boolean) }
    },
    async ({ cfg, reviews }) => {
      const scored = reviews.map(({ task, findings }) => ({
        defect_id: task.defect_id,
        clean: task.is_clean,
        planted_failure_class: task.is_clean ? null : task.failure_class,
        planted_location: task.is_clean ? null : task.location,
        subtlety: task.subtlety,
        reviewer_findings: findings,
      }))
      const verdict = await agent(judgePrompt(role, scored), {
        label: `judge:${role}:${cfg.id}`,
        phase: 'Score',
        model: 'opus',
        effort: 'high',
        agentType: 'general-purpose',
        schema: JUDGE_SCHEMA,
      })
      const findingCounts = reviews.map((r) => r.findings.length)
      return {
        role,
        config: cfg.id,
        model: cfg.model,
        effort: cfg.effort,
        recall: verdict ? `${verdict.planted_caught}/${verdict.planted_total}` : 'n/a',
        planted_caught: verdict ? verdict.planted_caught : null,
        planted_total: verdict ? verdict.planted_total : null,
        false_positives_on_clean: verdict ? verdict.false_positive_findings_on_clean : null,
        total_findings_raised: findingCounts.reduce((a, b) => a + b, 0),
        per_task: verdict ? verdict.per_task : [],
      }
    }
  )
  return results.filter(Boolean)
}

log(`Benchmark: ${configs.length} configs × (${redTasks.length} red + ${panelTasks.length} panel) tasks`)
const redResults = await runRole('red', redTasks)
const panelResults = await runRole('panel', panelTasks)

return { red: redResults, panel: panelResults, configs }
