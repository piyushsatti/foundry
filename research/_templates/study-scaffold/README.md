# Study scaffold — copy this folder to start a new research study

```bash
cp -r research/_templates/study-scaffold research/<topic>/<study-name-YYYY-MM>
# Edit 00-MASTER-HANDOFF.md and session prompts
mkdir -p research/<topic>/<study-name-YYYY-MM>/results
```

Replace placeholders in all files:
- `[TOPIC]` — e.g. orchestrator, progress-tracker
- `[STUDY_NAME]` — e.g. landscape, competitive-pricing
- `[PROBLEM_CHARTER]` — 2–3 sentences on what question this study answers

Add a row to [`research/README.md`](../README.md) Active studies table.
