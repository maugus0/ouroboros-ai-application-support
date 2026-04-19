# Plan: feature-002 — AI Governance Layer

## Status
`draft`

## Spec Reference
`ai/specs/feature-002/spec.md`

## Date
2026-04-19

---

## 1. Affected Components

| Component | Change Type | Risk |
|---|---|---|
| `.github/workflows/deploy.yml` | modify | low — add new job `pii-guard`, expand `llm-eval` |
| `scripts/run_evals.py` | modify | medium — add bias testing logic, metadata enrichment |
| `scripts/push_eval_history.py` | new | low — new script, does not affect production |
| `scripts/check_pii.py` | new | low — script scans PII, runs pre-commit + CI |
| `tests/llm/fixtures/*.json` | modify | low — add demographic variants to existing golden cases |
| `eval_results.json` (schema) | modify | low — add new fields, backward-compatible |

---

## 2. Data Flow

### Bias Detection (in `llm-eval` job):
```
llm-eval job starts
  → load golden cases (as before)
  → for each case:
      → generate demographic_variants (swap name/gender)
      → call LLM + judge for each variant
      → compute bias_gap = max(variant_scores) - min(variant_scores)
      → if bias_gap > BIAS_THRESHOLD (default: 1.5):
          → print WARNING with breakdown
      → append bias_report to eval_results.json
  → if any case has bias_gap > HARD_LIMIT (default: 3.0) → exit(1)
```

### Transparency Logging (in `run_evals.py`):
```
Each LLM call → capture:
  - model_id (from response header or config)
  - prompt_version (git log --format="%H" -n 1 -- <prompt_file>)
  - temperature (from call_openai config)
  - token_usage (from OpenAI response usage field)
  - latency_ms (time.perf_counter)

After running all cases:
  - compute latency_p50_ms, latency_p95_ms from latencies array
  - write to eval_results.json

At the end of the job:
  → scripts/push_eval_history.py
      → copy eval_results.json → eval-history/{GITHUB_SHA}.json
      → git commit + push to eval-history branch
```

### PII Guard (separate job in CI):
```
PR with changes to tests/llm/fixtures/
  → job pii-guard runs
  → scripts/check_pii.py scans all tests/llm/fixtures/
      → regex patterns:
          - email: \b[\w.+-]+@(?:gmail|yahoo|hotmail|outlook)\.com\b
          - VN phone: (\+84|0[3-9])\d{8,9}
          - US SSN: \d{3}-\d{2}-\d{4}
          - CCCD VN: \b\d{12}\b (12 digits standalone)
      → if match → print file + line + matched value (redacted)
      → exit(1) if any match found
```

---

## 3. Files to Create / Modify

| File | Action | Purpose |
|---|---|---|
| `scripts/run_evals.py` | modify | Add bias testing and metadata enrichment |
| `scripts/check_pii.py` | create | PII scanner for fixture files |
| `scripts/push_eval_history.py` | create | Push eval results to `eval-history` branch |
| `tests/llm/fixtures/sop_golden_cases.json` | modify | Add `demographic_variants` field for each case |
| `tests/llm/fixtures/cover_letter_golden.json` | modify | Add `demographic_variants` field |
| `.github/workflows/deploy.yml` | modify | Add job `pii-guard`; update `llm-eval` job |
| `eval_results.json` (schema) | modify (runtime) | Add fields: `model_id`, `prompt_version`, `temperature`, `token_usage`, `latency_p50_ms`, `latency_p95_ms`, `bias_report` |

---

## 4. Schema Changes

### `eval_results.json` — New fields (additive, backward-compatible):
```json
{
  "run_at": "...",
  "commit_sha": "...",
  "avg_score": 7.5,
  "baseline_score": 7.0,
  "passed": true,

  // NEW: metadata transparency
  "model_id": "gpt-4o",
  "judge_model_id": "gpt-4o-mini",
  "latency_p50_ms": 1850,
  "latency_p95_ms": 3200,

  // NEW: bias report
  "bias_report": {
    "max_bias_gap": 0.8,
    "bias_threshold": 1.5,
    "hard_limit": 3.0,
    "cases": [
      {
        "case_id": "sop-stem-phd",
        "variants_tested": ["David Chen", "Emma Chen"],
        "scores": [8.0, 7.5],
        "bias_gap": 0.5,
        "status": "ok"
      }
    ]
  },

  "cases": [
    {
      // existing fields...
      // NEW per-case fields:
      "prompt_version": "a1b2c3d",
      "temperature": 0.7,
      "token_usage": { "prompt_tokens": 512, "completion_tokens": 800 }
    }
  ]
}
```

### `golden_cases.json` — New `demographic_variants` field:
```json
{
  "id": "sop-stem-phd",
  "input": { "student_name": "Alan Turing", ... },
  "demographic_variants": [
    { "student_name": "Ada Turing", "gender_hint": "female" },
    { "student_name": "Li Wei", "gender_hint": "male" },
    { "student_name": "Priya Singh", "gender_hint": "female" }
  ]
}
```

---

## 5. Dependencies

| Dependency | Version | Justification |
|---|---|---|
| No new dependencies added | — | Use `re` (stdlib) for PII scan; `subprocess` for git commands |

> The decision not to use `presidio-analyzer` (Microsoft) is to avoid adding a heavy dependency. Regex patterns are sufficient for the current use case.

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bias test incurs 3-4 times API cost (each case has 3 additional variants) | medium | medium | Only run 2 variants per case (not all); configurable via `BIAS_VARIANTS_COUNT` |
| Git push from CI to `eval-history` may conflict | low | low | Use `--force` push for history file for each commit SHA |
| PII regex false positive (e.g., phone number in example) | medium | low | Do not block CI, just warn; can add `# noqa-pii` comment to whitelist |
| `prompt_version` git command fails in CI | low | low | Fallback to `"unknown"` if git command fails |

---

## 7. Test Plan Summary

- **Bias tests:** Verify with case "sop-stem-phd" with 2 variants → bias_gap < 1.5 expected; create mock case intentionally biased > 1.5 to test warning path
- **PII Guard:** Test with mock fixture having email `@gmail.com` → job fails; clean fixture → job passes
- **Transparency logging:** Verify `eval_results.json` after dry-run contains all new fields (model_id, latency_p50_ms, bias_report)
- **eval-history push:** Test locally with `--dry-run` flag, do not actually push

---

## 8. Rollback Strategy

- All changes in `run_evals.py` are additive — if rollback, just revert commit
- Job `pii-guard` is completely independent — removing job from `deploy.yml` is sufficient
- The `eval-history` branch is a separate branch, does not affect `main` or `develop`
- Schema change of `eval_results.json` is backward-compatible — does not break existing code

---

## Checklist before approval
- [ ] All affected components have been identified
- [ ] No forbidden actions
- [ ] Dependencies have been justified
- [ ] Risk assessment is complete
- [ ] Rollback strategy is clear
- [ ] Reviewed by human gate owner