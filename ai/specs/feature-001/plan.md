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
| `.github/workflows/deploy.yml` | modify | low — added new jobs, did not modify old jobs |
| `tests/llm/` | new | low — new test files, does not affect production |
| `tests/llm/fixtures/` | new | low — golden data files |
| `scripts/run_evals.py` | new | low — script to run eval |
| `scripts/store_eval_baseline.py` | new | low — script to update baseline |
| `requirements-dev.txt` | modify | low — added deps for eval (tiktoken) |

## 2. Data Flow

### Prompt Lint (CI — every PR):
```
PR push
  → GitHub Actions: prompt-lint job
  → pytest tests/llm/test_prompt_lint.py
      → load prompt JSON files from app/llm/
      → validate JSON schema
      → render prompt with mock context
      → count tokens using tiktoken
      → assert token_count < 0.8 * model_limit
  → pass / fail
```

### Prompt Diff Alert (CI — every PR):
```
PR push
  → GitHub Actions: prompt-diff-alert job
  → git diff origin/main...HEAD --name-only
  → filter: files in app/llm/ or tests/llm/fixtures/
  → if there are changes → gh pr comment (list files changed + warning)
```

### LLM Eval (CI — push to main only):
```
push to main → docker-build pass
  → GitHub Actions: llm-eval job
  → python scripts/run_evals.py
      → load golden cases from tests/llm/fixtures/
      → for each case:
          → call LLMPipelineService.generate() (real API)
          → call judge_output() with GPT-4o-mini
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
| `.github/workflows/deploy.yml` | modify | Add 3 jobs: `prompt-lint`, `prompt-diff-alert`, `llm-eval` |
| `tests/llm/__init__.py` | create | Python package marker |
| `tests/llm/conftest.py` | create | Fixtures: mock LLM client, sample contexts |
| `tests/llm/test_prompt_lint.py` | create | Prompt structural validation tests (no real API) |
| `tests/llm/fixtures/sop_golden_cases.json` | create | 5 golden input/criteria pairs for SOP |
| `tests/llm/fixtures/cover_letter_golden.json` | create | 3 golden input/criteria pairs for cover letter |
| `scripts/run_evals.py` | create | Entry point: run eval, compute score, compare baseline |
| `scripts/store_eval_baseline.py` | create | Update GitHub repo variable with new score |
| `requirements-dev.txt` | modify | Add `tiktoken>=0.7` for token counting |

## 4. Dependencies

| Dependency | Version | Justification |
|---|---|---|
| `tiktoken` | `>=0.7` | Token counting for OpenAI models, necessary for prompt-lint |
| `PyGithub` | `>=2.0` (optional) | If using Python to post PR comment instead of gh CLI |

> Only `tiktoken` is mandatory. PR comment can use `gh` CLI (already available in GitHub Actions).

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM-as-judge for unstable (flaky) results | medium | medium | Use threshold 0.5 buffer, do not hardcode; run 2 times to take average |
| API costs exceed budget | low | low | Limit: 5 SOP + 3 cover letter = ~8 API calls/run ≈ $0.50-$1 |
| `llm-eval` slow, blocks pipeline | low | medium | Timeout 10 minutes; job runs parallel with trivy-scan |
| Baseline drift (score gradually increases so threshold too loose) | low | low | Baseline only updates when CI passes; manual review each sprint |
| `OPENAI_API_KEY` not set → llm-eval fails entire job | medium | medium | Job `if: env.OPENAI_API_KEY != ''`; does not block deploy if key is missing |

## 6. Test Plan Summary

- **Unit tests (prompt-lint):** Validate 100% of existing prompt files pass; add test case for JSON malformed, missing placeholder, token overflow — run without API key
- **Integration tests (llm-eval):** Run with real API only on main; golden cases have clear rubric, do not depend on exact match
- **Edge cases:**
  - New prompt file added but no golden case → warn, do not fail
  - LLM returns invalid JSON → retry once, log error, score = 0
  - Both providers (OpenAI + Anthropic) fail → eval job fails with clear reason

## 7. Rollback Strategy

- New jobs (`prompt-lint`, `prompt-diff-alert`, `llm-eval`) are completely independent of existing jobs
- If rollback is needed: remove 3 new jobs from `deploy.yml` and delete `tests/llm/` + `scripts/run_evals.py`
- No DB migration, no changes to production code → zero-risk rollback
- `llm-eval` only runs after `docker-build` passes so does not block deploy if skipped

---

## Checklist before approval
- [ ] All affected components have been identified
- [ ] No forbidden actions
- [ ] Dependencies have been justified
- [ ] Risk assessment is complete
- [ ] Rollback strategy is clear
- [ ] Reviewed by human gate owner