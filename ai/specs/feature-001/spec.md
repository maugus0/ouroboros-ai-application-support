# Spec: feature-001 — LLMOps CI/CD Pipeline

## Status
`approved`

## Author
Antigravity (AI Engineer)

## Date
2026-04-18

---

## 1. User
- Persona: Backend engineer / ML engineer working on `application-support`
- Role: Developer pushes code to GitHub and needs to know immediately when prompt changes cause regression

## 2. Problem

Currently, `application-support` has a complete CI/CD pipeline (format → lint → tests → docker → trivy),
but **there are no steps to control the quality of LLM output**.

Specifically:
- When someone edits the prompt JSON file (`sop_outline_v1.json`, `cover_letter_generation_v1.json`, etc.)
  the CI pipeline **does not detect** that the LLM output may change for the worse.
- There are no tests to check: does the prompt render correctly? Are any placeholders missing?
  Does the token count exceed the model limit?
- There is no baseline to compare the quality of output between commits.
- `mysql_llm_call_log_repo` has logged `tokens, latency, success` but does not log **quality score**.

## 3. Goal

Add an **LLMOps stage** to the CI/CD pipeline of `application-support` consisting of 3 layers:

1. **Prompt Lint** (runs on every PR, free, < 30s): validate prompt structure, token count, placeholders
2. **Prompt Diff Alert** (runs on every PR, free): automatically comment on the PR when the prompt file changes
3. **LLM Eval / Quality Gate** (runs only when pushing to `main`, using real API): run golden test cases,
   use LLM-as-judge to score, compare with baseline, fail if regression

## 4. Expected Behavior

### PR flow:
1. Developer opens a PR that modifies `app/llm/` or any prompt file
2. Job `prompt-lint` runs: checks for valid JSON, all placeholders are injected, estimated token count < 80% limit
3. Job `prompt-diff-alert` runs: detects prompt file changes → comments on the PR listing which files changed and warns
4. If prompt-lint fails → PR is blocked from merging

### Push to main flow:
1. After a successful docker-build, job `llm-eval` runs
2. Script `scripts/run_evals.py` loads golden test cases from `tests/llm/fixtures/`
3. For each test case: call the real LLM → receive output → use LLM-as-judge (GPT-4o-mini) to score
4. Compare average score with `EVAL_BASELINE_SCORE` (GitHub repo variable)
5. If the score decreases by > 0.5 points compared to the baseline → pipeline fails
6. If pass → update the new baseline into the repo variable

## 5. Acceptance Criteria

- [ ] `prompt-lint` job runs successfully on PRs without prompt changes
- [ ] `prompt-lint` job fails when there is an invalid prompt JSON file
- [ ] `prompt-lint` job fails when the estimated token count exceeds 80% of the model limit
- [ ] `prompt-diff-alert` creates a comment on the PR when there are changes to files in `app/llm/`
- [ ] `llm-eval` job runs only when pushing to `main`
- [ ] `llm-eval` job fails when the average score decreases by > 0.5 compared to the baseline
- [ ] `llm-eval` uploads artifact `eval_results.json` after each run
- [ ] All new jobs follow the same Python version and caching pattern as the current CI
- [ ] `tests/llm/test_prompt_lint.py` can run locally without needing an API key
- [ ] There are at least 3 golden test cases for SOP and 2 for cover letter

## 6. Non-Goals

- Do not implement streaming evaluation (only single request/response)
- Do not integrate LangSmith, Promptfoo, or any external LLMOps platform
- Do not add eval for `checklist_service` or `deadline_service` in this feature
- Do not change the business logic of any existing services
- Do not add new database migrations

## 7. Open Questions

- [ ] Is GPT-4o-mini used as a judge reliable enough, or should we use GPT-4o?
- [ ] Should the baseline score be stored in a GitHub repo variable or committed to the repo as a file?
- [ ] If `OPENAI_API_KEY` is not set in CI → should llm-eval skip or fail?
- [ ] Cost budget for each eval run (estimated ~$0.50-$1.00/run)?

---

## Checklist before approval
- [ ] User and problem have been clearly defined
- [ ] Acceptance criteria are verifiable
- [ ] Non-goals have been listed
- [ ] There are no architectural assumptions that have not been approved
- [ ] Reviewed by human gate owner