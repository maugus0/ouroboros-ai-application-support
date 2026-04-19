# Tasks: feature-001 — LLMOps CI/CD Pipeline

## Plan Reference
`ai/specs/feature-001/plan.md`

## Date
2026-04-18

---

## Task Breakdown

| ID | Title | Depends On | Effort | Status |
|---|---|---|---|---|
| T01 | Prompt Lint Tests — `tests/llm/test_prompt_lint.py` + fixtures + conftest | — | M | `done` |
| T02 | Golden Eval Fixtures — `tests/llm/fixtures/*.json` | T01 | S | `done` |
| T03 | Eval Runner Script — `scripts/run_evals.py` + LLM-as-judge | T02 | M | `done` |
| T04 | CI/CD Jobs — add 3 jobs to `deploy.yml` | T01, T03 | S | `done` |
| T05 | Baseline Script — `scripts/store_eval_baseline.py` + docs | T04 | S | `done` |

## Status Legend
- `todo` — Not started
- `in-progress` — In progress
- `review` — Code completed, waiting for review
- `done` — Reviewed and merged
- `blocked` — Waiting for dependency or decision

## Notes
- Each task must have a corresponding task pack in `task-packs/Txx.md`
- T01 and T02 do not require a real API key — can run locally with mock
- T03 requires `OPENAI_API_KEY` for real testing; can be mocked with `USE_MOCK_LLM=true`
- T04 depends on T01 and T03 — cannot merge CI jobs before test files exist
- T05 is necessary for automation but can be done manually first (update GitHub var manually)