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
| T04 | CI/CD Jobs — thêm 3 jobs vào `deploy.yml` | T01, T03 | S | `done` |
| T05 | Baseline Script — `scripts/store_eval_baseline.py` + docs | T04 | S | `done` |

## Status Legend
- `todo` — Chưa bắt đầu
- `in-progress` — Đang làm
- `review` — Code xong, chờ review
- `done` — Reviewed và merged
- `blocked` — Chờ dependency hoặc decision

## Notes
- Mỗi task phải có task pack tương ứng trong `task-packs/Txx.md`
- T01 và T02 không cần API key thật — chạy được local với mock
- T03 cần `OPENAI_API_KEY` để test thật; có thể mock với `USE_MOCK_LLM=true`
- T04 phụ thuộc T01 và T03 — không thể merge CI jobs trước khi test files tồn tại
- T05 cần thiết cho automation nhưng có thể làm manual trước (update GitHub var bằng tay)
