# Plan: feature-001 — LLMOps CI/CD Pipeline

## Status
`approved`

## Spec Reference
`ai/specs/feature-001/spec.md`

## Date
2026-04-18

---

## 1. Affected Components

| Component | Change Type | Risk |
|---|---|---|
| `.github/workflows/deploy.yml` | modify | low — thêm jobs mới, không sửa jobs cũ |
| `tests/llm/` | new | low — test files mới, không ảnh hưởng production |
| `tests/llm/fixtures/` | new | low — golden data files |
| `scripts/run_evals.py` | new | low — script chạy eval |
| `scripts/store_eval_baseline.py` | new | low — script cập nhật baseline |
| `requirements-dev.txt` | modify | low — thêm deps cho eval (tiktoken) |

## 2. Data Flow

### Prompt Lint (CI — mọi PR):
```
PR push
  → GitHub Actions: prompt-lint job
  → pytest tests/llm/test_prompt_lint.py
      → load prompt JSON files từ app/llm/
      → validate JSON schema
      → render prompt với mock context
      → count tokens bằng tiktoken
      → assert token_count < 0.8 * model_limit
  → pass / fail
```

### Prompt Diff Alert (CI — mọi PR):
```
PR push
  → GitHub Actions: prompt-diff-alert job
  → git diff origin/main...HEAD --name-only
  → filter: files trong app/llm/ hoặc tests/llm/fixtures/
  → nếu có thay đổi → gh pr comment (list files changed + warning)
```

### LLM Eval (CI — push to main only):
```
push to main → docker-build pass
  → GitHub Actions: llm-eval job
  → python scripts/run_evals.py
      → load golden cases từ tests/llm/fixtures/
      → for each case:
          → call LLMPipelineService.generate() (real API)
          → call judge_output() với GPT-4o-mini
          → score: 1-10
      → compute avg_score
      → compare vs EVAL_BASELINE_SCORE (GitHub var)
      → if avg_score < baseline - 0.5 → exit(1)
      → upload eval_results.json artifact
  → if pass → store_eval_baseline.py (update GitHub var)
```

## 3. Files to Create / Modify

| File | Action | Purpose |
|---|---|---|
| `.github/workflows/deploy.yml` | modify | Thêm 3 jobs: `prompt-lint`, `prompt-diff-alert`, `llm-eval` |
| `tests/llm/__init__.py` | create | Python package marker |
| `tests/llm/conftest.py` | create | Fixtures: mock LLM client, sample contexts |
| `tests/llm/test_prompt_lint.py` | create | Prompt structural validation tests (no real API) |
| `tests/llm/fixtures/sop_golden_cases.json` | create | 5 golden input/criteria pairs cho SOP |
| `tests/llm/fixtures/cover_letter_golden.json` | create | 3 golden input/criteria pairs cho cover letter |
| `scripts/run_evals.py` | create | Entry point: chạy eval, compute score, compare baseline |
| `scripts/store_eval_baseline.py` | create | Update GitHub repo variable với score mới |
| `requirements-dev.txt` | modify | Thêm `tiktoken>=0.7` cho token counting |

## 4. Dependencies

| Dependency | Version | Justification |
|---|---|---|
| `tiktoken` | `>=0.7` | Token counting cho OpenAI models, cần thiết cho prompt-lint |
| `PyGithub` | `>=2.0` (optional) | Nếu dùng Python để post PR comment thay vì gh CLI |

> Chỉ `tiktoken` là bắt buộc. PR comment có thể dùng `gh` CLI (đã có sẵn trong GitHub Actions).

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM-as-judge cho kết quả không ổn định (flaky) | medium | medium | Dùng threshold 0.5 buffer, không hardcode; chạy 2 lần lấy trung bình |
| Chi phí API vượt budget | low | low | Limit: 5 SOP + 3 cover letter = ~8 API calls/run ≈ $0.50-$1 |
| `llm-eval` chậm, block pipeline | low | medium | Timeout 10 phút; job chạy parallel với trivy-scan |
| Baseline drift (score tăng dần nên threshold quá lỏng) | low | low | Baseline chỉ update khi CI pass; review manual mỗi sprint |
| `OPENAI_API_KEY` không set → llm-eval fail toàn bộ | medium | medium | Job `if: env.OPENAI_API_KEY != ''`; không block deploy nếu key không có |

## 6. Test Plan Summary

- **Unit tests (prompt-lint):** Validate 100% prompt files hiện có đều pass; thêm test case cho JSON malformed, missing placeholder, token overflow — chạy không cần API key
- **Integration tests (llm-eval):** Chạy với real API chỉ trên main; golden cases có rubric rõ ràng, không phụ thuộc exact match
- **Edge cases:**
  - Prompt file mới được thêm vào nhưng chưa có golden case → warn, không fail
  - LLM trả về JSON không valid → retry 1 lần, log error, score = 0
  - Cả 2 provider (OpenAI + Anthropic) fail → eval job fail rõ lý do

## 7. Rollback Strategy

- Jobs mới (`prompt-lint`, `prompt-diff-alert`, `llm-eval`) hoàn toàn độc lập với các jobs hiện có
- Nếu cần rollback: xoá 3 jobs mới khỏi `deploy.yml` và xoá `tests/llm/` + `scripts/run_evals.py`
- Không có migration DB, không có thay đổi production code → zero-risk rollback
- `llm-eval` chỉ chạy sau `docker-build` pass nên không block deploy nếu skip

---

## Checklist before approval
- [ ] Tất cả affected components đã được identify
- [ ] Không có forbidden actions
- [ ] Dependencies đã được justify
- [ ] Risk assessment đầy đủ
- [ ] Rollback strategy rõ ràng
- [ ] Reviewed by human gate owner
