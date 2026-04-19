# LLMOps CI/CD Pipeline

This feature introduces an automated LLMOps pipeline to the `application-support` service to ensure the quality of LLM-generated content (like SOPs and Cover Letters) does not regress when prompts or models are updated.

## 1. Purpose

- **Prompt Linting**: Validates prompt JSON syntax, ensures no missing placeholders, and checks that prompt token sizes are within safe limits. This runs on every PR and is free/fast.
- **Prompt Diff Alert**: Automatically comments on PRs when prompt files are changed, warning reviewers to pay attention to potential regressions.
- **LLM Evaluation (Quality Gate)**: Runs only on pushes to `main`. It uses a set of "golden fixtures" to generate outputs using the real LLM APIs, and then uses GPT-4o-mini as a "judge" to score the output from 1-10. If the average score drops by more than 0.5 below the baseline, the CI pipeline fails.

## 2. How to run Prompt Lint local

You can run the prompt linting tests locally without an API key:

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install dev dependencies (if not already done)
pip install -r requirements-dev.txt

# Run the tests
ALLOW_DB_FAILURE=true pytest tests/llm/test_prompt_lint.py -v
```

## 3. How to run LLM Eval local

You can run the evaluation script locally to test the LLM judge.

**Dry run (Mock LLM, no cost, fast):**
```bash
ALLOW_DB_FAILURE=true python scripts/run_evals.py --dry-run
```

**Real Evaluation (Costs money, calls OpenAI API):**
```bash
export OPENAI_API_KEY="sk-..."
ALLOW_DB_FAILURE=true python scripts/run_evals.py
```
This will create an `eval_results.json` file in the current directory.

## 4. Resetting the Baseline Manually

When you intentionally make a change that you expect to alter the baseline (e.g., significantly improving a prompt or switching to a new model), you might need to manually update the baseline if the CI fails because the new score is vastly different, or you just want to set a new high-water mark.

You can use the GitHub CLI (`gh`) to update it manually:

```bash
# Make sure you are authenticated with gh CLI
gh variable set EVAL_BASELINE_SCORE --body "8.5"
```
Or you can go to the GitHub Repository Settings -> Secrets and variables -> Actions -> Variables and edit `EVAL_BASELINE_SCORE`.

## 5. Troubleshooting

- **`llm-eval` job was skipped on main:** Ensure that the `OPENAI_API_KEY` secret is set in the repository secrets. The job has a condition `if: env.OPENAI_API_KEY != ''`.
- **Baseline Drift:** Over time, if scores slightly improve, the baseline will automatically update. However, if a prompt change is intended to be a complete rewrite, you might want to manually set a lower baseline temporarily.
- **Flaky Judge:** If GPT-4o-mini is giving inconsistent scores, consider increasing the retries in `scripts/run_evals.py` or updating the `tests/llm/fixtures/judge_rubric.json` to be more explicit and rigid in its grading criteria.