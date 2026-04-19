# Spec: feature-002 — AI Governance Layer (Bias, Transparency, Auditability)

## Status
`draft`

## Author
Antigravity (AI Engineer)

## Date
2026-04-19

---

## 1. User

- **Persona:** ML Engineer / Product Owner managing the AI quality of `application-support`
- **Role:** The person responsible for ensuring that the AI system generates content that is fair, transparent, and auditable before delivering it to the end-user

---

## 2. Problem

Feature-001 has established a basic quality control pipeline (linting + LLM-as-judge scoring).
However, there are **4 major risks that have not been controlled** according to AI Governance standards:

### 2.1 Bias & Fairness
- The system generates SOPs and Cover Letters for various student demographics.
- Currently, there are **no tests** to check whether the AI treats different genders, nationalities, or socioeconomic backgrounds differently.
- For example: with the same profile, just changing the name from "David" → "Emma" or from "Wang" → "Smith" → does the AI give different scores/quality?

### 2.2 Transparency & Explainability
- The current `eval_results.json` only stores `score` and a short `reason`.
- There are no logs about: which model is running, which version of the prompt is used, or what the temperature setting is.
- When CI fails, the team does not have enough information to trace back the cause.

### 2.3 Auditability
- After 30 days, the artifact `eval_results.json` is automatically deleted by GitHub.
- There is no long-term history to compare quality trends over multiple sprints.
- When customers ask "Is your AI biased?", there is no evidence to answer.

### 2.4 Confidentiality of Golden Fixtures
- The files `tests/llm/fixtures/*.json` currently use fictional character names (Ada Lovelace, Alan Turing...) but there is **no policy** preventing developers from accidentally committing real customer data here.
- An automated check is needed to detect real PII (Personally Identifiable Information) mixed into test fixtures.

---

## 3. Goal

Build an **AI Governance Layer** to supplement the existing pipeline, consisting of 3 groups:

1. **Bias Detection Tests** — Automatically detect discrepancies in AI output scores when changing demographic attributes (gender, nationality) within the same profile
2. **Transparency Logging** — Enriching `eval_results.json` with complete metadata (model version, prompt version, temperature, latency percentiles) + long-term storage
3. **PII Guard in Fixtures** — Automated scan to ensure no real PII in golden test fixtures before committing

---

## 4. Expected Behavior

### Bias Detection (runs every time `llm-eval` is executed):
1. For each golden case SOP/Cover Letter, the system automatically creates **variants (demographic variants)** by swapping names and genders
2. Call LLM-as-judge to score each variant
3. Calculate **bias gap** = max(scores) - min(scores) between variants of the same profile
4. If bias gap > threshold (default: 1.5 points) → report in detail, do not block CI but mark as a warning
5. Results are saved in `eval_results.json` under the field `bias_report`

### Transparency Logging:
1. `eval_results.json` is enriched with:
   - `model_id`: actual model name (`gpt-4o`, `claude-3-5-sonnet`, etc.)
   - `prompt_version`: version hash of the prompt file being used (git SHA of the prompt file)
   - `temperature`: temperature setting at the time of the call
   - `latency_p50_ms`, `latency_p95_ms`: percentile latency
   - `token_usage`: prompt_tokens + completion_tokens
2. The artifact `eval_results.json` is pushed to a separate Git branch (`eval-history`) for long-term storage, independent of GitHub artifact expiry

### PII Guard:
1. A new job `pii-guard` runs on every PR that changes files in `tests/llm/fixtures/`
2. Uses regex patterns to detect: real phone numbers, ID cards, emails with real domains, real home addresses
3. If PII is detected → job fails, blocks PR merge

---

## 5. Acceptance Criteria

### Bias Detection:
- [ ] Each golden case has at least 2 demographic variants (gender swap: male/female name)
- [ ] `bias_report` field appears in `eval_results.json` after each eval run
- [ ] CI does not fail when bias gap < 1.5, but clearly prints a warning to the console
- [ ] CI clearly prints the bias gap report for each case when the threshold is exceeded

### Transparency Logging:
- [ ] `eval_results.json` contains all new fields: `model_id`, `prompt_version`, `temperature`, `token_usage`, `latency_p50_ms`, `latency_p95_ms`
- [ ] There is a script `scripts/push_eval_history.py` that commits `eval_results.json` to the `eval-history` branch
- [ ] The `eval-history` branch can be used to draw trend charts (by reading historical json files)

### PII Guard:
- [ ] Job `pii-guard` runs when there is a PR changing files in `tests/llm/fixtures/`
- [ ] Job fails when the fixture contains emails like `@gmail.com`, `@yahoo.com`, or phone numbers like `+84...`
- [ ] Job passes when character names are clearly fictional (no name checks)
- [ ] Script `scripts/check_pii.py` can run locally

---

## 6. Non-Goals

- Do not implement real-time bias monitoring in production (only in CI/CD)
- Do not integrate third-party fairness libraries (Fairlearn, AI Fairness 360) — keep it lightweight
- Do not change business logic in `app/`
- Do not implement a full GDPR audit trail — only CI-level safeguards
- Do not cover bias related to socioeconomic background or disability (too complex, to be addressed in the future roadmap)

---

## 7. Open Questions

- [ ] Is the bias gap threshold of 1.5 points reasonable, or should it be configurable via a GitHub variable?
- [ ] Does the `eval-history` branch need to be a protected branch, or should the workflow push automatically?
- [ ] Should we use pure regex or a library like `presidio-analyzer` (Microsoft) to detect PII?
- [ ] Should the bias test run in parallel with the regular eval, or as a separate job (incurring additional API costs)?

---

## 8. AI Governance Principles Covered

| Principle | Feature-001 | Feature-002 |
|---|---|---|
| **Measurability** | ✅ Score 1-10 per case | ✅ + percentile latency, token usage |
| **Bias & Fairness** | ❌ | ✅ Demographic variant testing |
| **Transparency** | ⚠️ Score + 1-line reason | ✅ Full metadata logging |
| **Explainability** | ⚠️ Basic reason | ✅ Per-case breakdown with model/prompt version |
| **Auditability** | ⚠️ 30-day artifact only | ✅ Long-term `eval-history` branch |
| **Reproducibility** | ✅ commit_sha logged | ✅ + prompt_version hash |
| **Confidentiality** | ❌ No PII check | ✅ PII Guard job |
| **AI Safeguards** | ❌ | ⚠️ PII guard only; prompt injection in roadmap |

---

## Checklist before approval
- [ ] User and problem have been clearly defined
- [ ] Acceptance criteria are verifiable
- [ ] Non-goals have been listed
- [ ] There are no architectural assumptions that have not been approved
- [ ] Reviewed by human gate owner