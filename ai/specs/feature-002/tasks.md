# Tasks: feature-002 — AI Governance Layer

## Plan Reference
`ai/specs/feature-002/plan.md`

## Date
2026-04-19

---

## Task Breakdown

| ID | Title | Depends On | Effort | Status |
|---|---|---|---|---|
| T01 | PII Guard Script — `scripts/check_pii.py` + CI job `pii-guard` | — | S | `done` |
| T02 | Demographic Variants — add `demographic_variants` to golden fixtures | — | S | `done` |
| T03 | Bias Detection Logic — extend `scripts/run_evals.py` with bias testing | T02 | M | `done` |
| T04 | Transparency Metadata — enrich `eval_results.json` with model/prompt/token metadata | — | M | `done` |
| T05 | Eval History Script — `scripts/push_eval_history.py` + branch `eval-history` | T03, T04 | S | `done` |
| T06 | CI Integration — update `deploy.yml` for all changes above | T01, T03, T04, T05 | S | `done` |

---

## Status Legend
- `todo` — Not started
- `in-progress` — In progress
- `review` — Code completed, waiting for review
- `done` — Reviewed and merged
- `blocked` — Waiting for dependency or decision

---

## Notes
- **T01** (PII Guard) is completely independent, so it should be done first to unblock the merge early.
- **T02** should be done in parallel with T01 — it's just data, no complex code.
- **T03** (Bias) will consume the most API calls — need to estimate cost before actual deployment.
- **T04** (Transparency) does not incur additional API calls — it just captures more metadata from existing calls.
- **T05** requires access to push into the `eval-history` branch — need to create the branch and set permissions first.
- **T06** should be the last task, consolidating everything into CI.
- The default bias threshold of `1.5` can be reviewed after the first trial run.