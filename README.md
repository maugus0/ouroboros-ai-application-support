# Ouroboros Application Support Agent

Microservice for the **Ouroboros AI** scholarship discovery platform. The Application Support Agent generates Statements of Purpose (SOPs), cover letters, CV improvement suggestions, application checklists, and tracks deadlines using a multi-step LLM pipeline (LangChain + LangGraph), with MySQL storage using raw SQL and the repository pattern (NO SQLAlchemy).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Prompt System](#prompt-system)
- [LLM Integration](#llm-integration)
- [Prompt Engineering](#prompt-engineering)
- [Version Control](#version-control)
- [Security](#security)
- [AI Governance & MLSecOps](#ai-governance--mlsecops)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Attribution](#attribution)

---

## Overview

The Application Support Agent is a critical microservice in the Ouroboros AI platform that:

1. **Generates SOPs** via a multi-step LLM pipeline (outline → expand → quality review)
2. **Generates cover letters** tailored to target programs/scholarships
3. **Suggests CV improvements** based on target program requirements
4. **Creates application checklists** with dynamic JSON-based items and progress tracking
5. **Tracks deadlines** with separate queryable entries and reminder flags
6. **Supports iterative refinement** with version control for all generated content

**Key Design Principles:**

- No direct frontend access — only the orchestrator calls this service via `X-Service-Token`
- No ORM overhead — raw SQL with `aiomysql` async connection pool
- Multi-step LLM pipeline via LangChain + LangGraph
- Retrieval-assisted generation (NOT full RAG) — style reference only
- CRITICAL security focus — most vulnerable to prompt injection
- LLM resilience — OpenAI primary, Anthropic fallback with retry logic
- JSON prompt templates — version-controlled in `prompts/` with runtime context injection

---

## Architecture

```
┌─────────────────────────────────────┐
│    Orchestrator Service (8000)      │
│    (Single Entry Point)             │
└──────────────┬──────────────────────┘
               │
               │ X-Service-Token
               ▼
┌──────────────────────────────────────────────────────┐
│       Application Support Agent (8005)               │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │  API Layer (FastAPI)                        │     │
│  │  POST /sop/generate                         │     │
│  │  GET  /sop/{id}                             │     │
│  │  POST /cover-letters/generate               │     │
│  │  POST /checklists                           │     │
│  │  GET  /checklists/{user_id}                 │     │
│  │  POST /deadlines                            │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Security Layer                             │     │
│  │  InputSanitizer  (injection detection)      │     │
│  │  PromptGuardrails (data boundary enforcement)│    │
│  │  OutputValidator  (leakage + quality check) │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Service Layer                              │     │
│  │  SOPService      (3-step LLM pipeline)      │     │
│  │  CoverLetterService                         │     │
│  │  ChecklistService                           │     │
│  │  DeadlineService                            │     │
│  │  RetrievalService (style reference)         │     │
│  │  LLMPipelineService (OpenAI → Anthropic)    │     │
│  └─────────────────────┬───────────────────────┘     │
│                        │                             │
│  ┌─────────────────────▼───────────────────────┐     │
│  │  Repository Layer (Raw SQL)                 │     │
│  │  SOPRepository                              │     │
│  │  CoverLetterRepository                      │     │
│  │  ChecklistRepository                        │     │
│  │  DeadlineRepository                         │     │
│  │  RetrievalRepository                        │     │
│  │  LLMCallLogRepository                       │     │
│  └─────────────────────────────────────────────┘     │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
      ┌─────────────────┐
      │   MySQL 8.0     │
      │   (aiomysql)    │
      └─────────────────┘
```

---

## Features

### SOP Generation (Multi-Step Pipeline)

- **Step 1: Outline** — Generate structured SOP outline from student profile
- **Step 2: Expansion** — Expand outline into full 500-800 word prose
- **Step 3: Quality Review** — LLM-assisted quality scoring and refinement
- **Example output** — With real keys and data, the pipeline produces a structured outline (JSON), a 500–800 word draft, then a revised draft with `quality_score` and feedback strings stored on the row.
- **Version control** — Track iterations with parent_sop_id chain
- **Retrieval-assisted** — Reference 1-2 example SOPs for style guidance

### Cover Letter Generation

- Tailored to program, scholarship, professor, or other target types
- Version control for iterative refinement

### Application Checklists

- Dynamic JSON-based items with status tracking
- Automatic completion percentage calculation
- Per-item category and priority

### Deadline Tracking

- Separate queryable table for deadline entries
- Upcoming deadline queries with configurable windows
- Reminder flag support

### Security (Critical)

- **Input sanitization** — Max **10,000** chars per string (`MAX_INPUT_LENGTH`), Unicode **Cc** stripped, whitespace normalised
- **Prompt injection detection** — Regex for template tags, instruction overrides, and obvious markup
- **Prompt guardrails** — User JSON wrapped as **DATA** blocks so profile text cannot masquerade as system rules
- **Output validation** — Leakage / echoed jailbreak patterns, cliché regex + list, **program relevance** check, quality score
- **Threat model** — Mitigations vs out-of-scope assumptions are summarized under [Security / Threat Model](#threat-model)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Runtime |
| MySQL | 8.0+ | Database |
| OpenAI API Key | — | Primary LLM provider |
| Anthropic API Key | — | Fallback LLM provider (optional but recommended) |
| Docker | 24.0+ | Containerised deployment (optional) |

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/maugus0/ouroboros-ai-application-support.git
cd ouroboros-ai-application-support

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
DB_HOST=localhost
DB_NAME=ouroboros_application_db
DB_USERNAME=root
DB_PASSWORD=your_mysql_password

X_SERVICE_TOKEN=your-secret-service-token-change-this

OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### 3. Database Setup

**Option A: Docker (Recommended)**

```bash
docker compose up mysql -d
docker compose logs -f mysql   # wait for "ready for connections"
```

**Option B: Local MySQL**

```bash
mysql -u root -p -e "CREATE DATABASE ouroboros_application_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 4. Run Migrations

```bash
python scripts/run_migrations.py
```

### 5. Seed Reference Data (Optional)

```bash
python scripts/seed_sop_references.py
```

### 6. Start the Service

```bash
./start.sh
# or: uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### 7. Verify Health

```bash
curl http://localhost:8005/health
# {"status":"healthy","version":"0.1.0","database":"not_connected"}
```

Swagger docs are available at `http://localhost:8005/docs`.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| **Database** ||||
| `DB_HOST` | No | `localhost` | MySQL host |
| `DB_PORT` | No | `3306` | MySQL port |
| `DB_NAME` | No | `ouroboros_application_db` | Database name |
| `DB_USERNAME` | No | `root` | MySQL user |
| `DB_PASSWORD` | Yes | — | MySQL password |
| `DB_POOL_SIZE` | No | `10` | Max connections in pool |
| **Service Auth** ||||
| `X_SERVICE_TOKEN` | Yes | — | Inter-service auth token (shared with orchestrator) |
| **LLM — OpenAI** ||||
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model identifier |
| `OPENAI_MAX_TOKENS` | No | `2000` | Max output tokens |
| `OPENAI_TEMPERATURE` | No | `0.2` | Sampling temperature (slightly creative for SOP) |
| **LLM — Anthropic** ||||
| `ANTHROPIC_API_KEY` | Recommended | — | Anthropic API key (fallback) |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-20250514` | Model identifier |
| `ANTHROPIC_MAX_TOKENS` | No | `2000` | Max output tokens |
| **SOP Generation** ||||
| `SOP_MIN_WORDS` | No | `500` | Minimum SOP word count |
| `SOP_MAX_WORDS` | No | `800` | Maximum SOP word count |
| `SOP_QUALITY_THRESHOLD` | No | `0.7` | Minimum quality score (0.0-1.0) |
| **Retrieval** ||||
| `RETRIEVAL_TOP_K` | No | `2` | Max reference SOPs to retrieve |
| `RETRIEVAL_ENABLED` | No | `true` | Enable style reference retrieval |
| **Security** ||||
| `MAX_INPUT_LENGTH` | No | `10000` | Max input characters |
| `ENABLE_PROMPT_INJECTION_DETECTION` | No | `true` | Enable injection detection |
| `ENABLE_OUTPUT_VALIDATION` | No | `true` | Enable output validation |
| **Application** ||||
| `ENVIRONMENT` | No | `development` | `development` (console logs) or `production` (JSON logs) |
| `LOG_LEVEL` | No | `INFO` | `DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL` |
| `USE_MOCK_DATA` | No | `false` | Skip real LLM calls; return canned SOP/cover letter (tests / local) |
| `ALLOW_DB_FAILURE` | No | `false` | Skip DB pool startup; API reads/writes that need MySQL will error (tests / CI) |
| **File uploads** ||||
| `MAX_FILE_SIZE_MB` | No | `10` | Max upload size for future DOCX flows |
| `ALLOWED_EXTENSIONS` | No | `.pdf,.docx,...` | Allowed extensions (see `app/utils/file_utils.py`) |
| `TEMP_UPLOAD_DIR` | No | `/tmp/uploads` | Temp directory for uploads |

### Docker / CI Prefix Compatibility

The service also reads `MYSQL_*` variables for Docker/CI environments. Resolution logic lives in the `settings.get_db_*()` helpers in `app/config.py`.

---

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `generated_sops` | Generated SOPs with versioning, quality metadata, and pipeline tracking |
| `generated_cover_letters` | Cover letters with target type and version control |
| `application_checklists` | JSON-based checklists with completion tracking |
| `deadline_entries` | Queryable deadline entries with reminder support |
| `sop_references` | Reference SOPs for retrieval-assisted style guidance |
| `llm_call_logs` | Audit trail for all LLM invocations |

### Migrations

Run in order via `python scripts/run_migrations.py`:

```
migrations/
├── 001_create_generated_sops.sql
├── 002_create_generated_cover_letters.sql
├── 003_create_application_checklists.sql
├── 004_create_deadline_entries.sql
├── 005_create_sop_references.sql
├── 006_create_llm_call_logs.sql
├── 007_deadline_source_fields.sql
└── 008_match_attribution_snapshot_if_missing.sql
```

---

## API Endpoints

**Base URL**: `http://localhost:8005`

All endpoints (except health) require the `X-Service-Token` header.

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Root health check |
| GET | `/health` | No | Detailed health status |

### SOP

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sop/generate` | Generate SOP via 3-step pipeline |
| GET | `/sop/{id}` | Retrieve single SOP |
| GET | `/sop/versions/{sop_id}` | List all SOP versions |

### Cover Letters

| Method | Path | Description |
|--------|------|-------------|
| POST | `/cover-letters/generate` | Generate tailored cover letter |
| GET | `/cover-letters/{id}` | Retrieve cover letter |

### Checklists

| Method | Path | Description |
|--------|------|-------------|
| POST | `/checklists` | Create checklist with items |
| GET | `/checklists/{user_id}` | Get all checklists for user |
| PUT | `/checklists/{id}/items/{item_id}` | Update checklist item |

### Deadlines

| Method | Path | Description |
|--------|------|-------------|
| POST | `/deadlines` | Create deadline entry |
| GET | `/deadlines/{user_id}` | Get all deadlines for user |
| PUT | `/deadlines/{id}` | Update deadline entry |

### Example `curl` calls

Replace `YOUR_TOKEN` with the same value as `X_SERVICE_TOKEN` in `.env`.

**Generate SOP (or mock SOP when `USE_MOCK_DATA=true`):**

```bash
curl -s -X POST http://localhost:8005/sop/generate \
  -H "X-Service-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "program_id": "prog-456",
    "user_profile": {"full_name": "Jane Doe"},
    "target_program": {"field_of_study": "Computer Science"},
    "user_preferences": {}
  }'
```

**Get SOP by id:**

```bash
curl -s http://localhost:8005/sop/SOP_UUID \
  -H "X-Service-Token: YOUR_TOKEN"
```

**List SOP version chain:**

```bash
curl -s http://localhost:8005/sop/versions/SOP_UUID \
  -H "X-Service-Token: YOUR_TOKEN"
```

**Generate cover letter:**

```bash
curl -s -X POST http://localhost:8005/cover-letters/generate \
  -H "X-Service-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "target_type": "program",
    "target_id": "prog-456",
    "user_profile": {"full_name": "Jane Doe"},
    "target_details": {"program_name": "MS CS"}
  }'
```

**Create checklist:**

```bash
curl -s -X POST http://localhost:8005/checklists \
  -H "X-Service-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "program_id": "prog-456",
    "items": [
      {"description": "Submit transcripts", "status": "pending"},
      {"description": "Request recommendations", "status": "pending"}
    ]
  }'
```

**Update checklist item:**

```bash
curl -s -X PUT http://localhost:8005/checklists/CHECKLIST_UUID/items/ITEM_UUID \
  -H "X-Service-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

**Create deadline:**

```bash
curl -s -X POST http://localhost:8005/deadlines \
  -H "X-Service-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "deadline_date": "2026-12-01",
    "item_description": "Application due"
  }'
```

**List deadlines for user:**

```bash
curl -s http://localhost:8005/deadlines/user-123 \
  -H "X-Service-Token: YOUR_TOKEN"
```

---

## Prompt System

Prompts are stored as **JSON templates** in `prompts/` and loaded at runtime with optional context injection.

### Available Prompts

| File | Purpose |
|------|---------|
| `sop_outline_v1.json` | SOP outline generation (pipeline step 1) |
| `sop_expansion_v1.json` | SOP prose expansion (pipeline step 2) |
| `sop_quality_review_v1.json` | Quality review and refinement (pipeline step 3) |
| `cover_letter_generation_v1.json` | Cover letter generation |
| `cv_improvement_v1.json` | CV improvement suggestions |

### Prompt Utilities

The `app/utils/prompt_utils.py` module provides:

- `load_prompt_template(filename)` — load raw JSON from disk
- `merge_runtime_context(template, context)` — inject runtime data
- `build_prompt_json(filename, context)` — full pipeline, returns JSON string
- `build_prompt_text(filename, context)` — full pipeline, returns formatted text

---

## LLM Integration

Calls flow through `LLMPipelineService` (`app/services/llm_pipeline_service.py`):

1. **Primary** — `call_openai` (`app/llm/openai_client.py`) with optional `response_format=json` for structured steps.
2. **Fallback** — On any OpenAI failure, `call_anthropic` (`app/llm/anthropic_client.py`) runs with an appended “JSON only” instruction when JSON output is required.
3. **Retries** — Both clients use `tenacity` (3 attempts, exponential backoff).
4. **Audit** — Each attempt can be written to `llm_call_logs` via `LLMCallLogRepository` when the DB pool is active (`ALLOW_DB_FAILURE=false`).

The production SOP flow uses **three sequential** `generate()` calls (outline → expand → review). `app/llm/pipeline/sop_pipeline.py` remains the place to introduce a LangGraph `StateGraph` if you want explicit graph semantics later.

```mermaid
flowchart LR
  A[API / Service] --> B[LLMPipelineService.generate]
  B --> C{OpenAI}
  C -->|success| D[Parse text or JSON]
  C -->|error| E{Anthropic}
  E -->|success| D
  E -->|error| F[LLMGenerationError 502]
  D --> G[(llm_call_logs optional)]
```

---

## Prompt Engineering

To add or version a new prompt:

1. Add a JSON file under `prompts/` following the existing `prompt_template.base` shape.
2. Expose a builder in `app/llm/prompts.py` (mirror `get_sop_outline_prompt`).
3. Inject runtime fields only through the `context` dict so templates stay static on disk.
4. For user-supplied text, always wrap with `app/security/prompt_guardrails.py` so profile data stays in a DATA section.

---

## Version Control

- **SOPs** — `generated_sops.version` increments when `parent_sop_id` points at a prior row. `GET /sop/versions/{id}` walks ancestors (via `parent_sop_id`) and descendants (children chains) to return the full version set for that lineage.
- **Cover letters** — Same pattern on `generated_cover_letters` with `parent_letter_id`.

---

## Security

This service handles user-provided text that feeds directly into LLM prompts, making it the **most vulnerable to prompt injection** in the Ouroboros platform.

### Security Layers

1. **Input Sanitization** (`app/security/input_sanitizer.py`)
   - **Length cap** — Each string field is capped at `MAX_INPUT_LENGTH` (default **10,000** characters); oversize input returns **422**.
   - **Control characters** — Unicode category **Cc** (NUL, bells, device controls, etc.) is stripped before checks; optional preservation of `\n` / `\t` for readability, then normalized to single spaces for LLM-bound text.
   - **Pattern detection** — When `ENABLE_PROMPT_INJECTION_DETECTION=true`, substrings resembling chat templates or overrides are rejected (e.g. `IGNORE PREVIOUS INSTRUCTIONS`, `<|im_start|>`, `[INST]`, `### SYSTEM`, `NEW INSTRUCTIONS:`, obvious `script` tags). Raises **422** (`PromptInjectionError`).
   - **Recursive structures** — `sanitize_dict` walks nested dicts and lists; **list elements that are dicts** are sanitized (e.g. `education[]` entries).

2. **Prompt Guardrails** (`app/security/prompt_guardrails.py`)
   - User JSON is wrapped in labeled **DATA** blocks (`wrap_user_data`, `build_safe_prompt`) so profile text is framed as data, not instructions.
   - SOP pipeline uses these wrappers on outline, expansion, and quality-review user messages.

3. **Output Validation** (`app/security/output_validator.py`) — runs when `ENABLE_OUTPUT_VALIDATION=true` after the quality-review step
   - **Length** — Word count vs `SOP_MIN_WORDS` / `SOP_MAX_WORDS`.
   - **Generic / template phrases** — Substring list plus **regex** clichés (e.g. “deeply passionate”, “transformative experience”); too many flags an issue and lowers score.
   - **Prompt leakage** — Output must not echo assistant/system tropes or internal markers (`as an AI`, `=====`, `STUDENT_CONTEXT`, pipe tags, etc.).
   - **Injected instruction echoes** — Patterns such as “ignore all instructions”, “developer mode”, `jailbreak`, repeated role tags.
   - **Program relevance** — Draft must mention at least one **meaningful** anchor from `target_program` (e.g. `university_name`, `program_name`, `field_of_study`; short acronyms like **CS** matched as whole words) or a non-UUID `program_id`, so generic unrelated essays are flagged.
   - **Quality score** — `compute_quality_score()` incorporates the above (and sentence-length heuristics) into a **0.0–1.0** signal; issues are appended to `quality_feedback` on the API response.

4. **Mock / CI path** — With `USE_MOCK_DATA=true`, `SOPService._generate_mock` still runs **the same input sanitization** as the live path so malicious payloads fail before any mock body is returned.

### Threat Model

**Mitigated in this service (design intent)**

- **Prompt injection and instruction smuggling** in user-supplied text — input pattern checks, DATA-block guardrails, and post-generation output checks reduce (but cannot mathematically eliminate) the risk of the model following attacker-controlled instructions.
- **Unbounded or malformed text** — length caps, control-character handling, and structured sanitization for nested payloads.
- **Low-quality or off-topic generations** — relevance heuristics and quality scoring catch some generic or unrelated drafts before they are treated as acceptable SOPs.
- **Casual unauthenticated API use** — protected routes expect a shared `X-Service-Token` aligned with deployment config (callers that lack the token should not reach business logic).

**Explicitly out of scope / not solely addressed here**

- **Compromise of upstream dependencies** — a broken or hostile LLM API, orchestrator, or dependency supply chain is a platform and vendor-trust problem, not fully solvable inside this microservice.
- **Network and infrastructure attacks** — DDoS, TLS misconfiguration, VPC breaches, and similar controls belong to hosting, API gateways, and platform security.
- **Full content policy / legal compliance** — jurisdiction-specific rules, hate speech, PII handling policies, and enterprise DLP are not exhaustively enforced by the validators described above.
- **Insider or token theft** — anyone with a valid service token can call the API; rotation, vaulting, and least-privilege deployment are operational concerns.
- **Data at rest / backup exposure** — MySQL hardening, encryption, and access control are deployment responsibilities.

### Configuration (env)

| Variable | Role |
|----------|------|
| `MAX_INPUT_LENGTH` | Max characters per sanitized string (default `10000`) |
| `ENABLE_PROMPT_INJECTION_DETECTION` | Reject suspicious input patterns (default `true`) |
| `ENABLE_OUTPUT_VALIDATION` | Post-generation SOP checks + relevance (default `true`) |

### Tests

- `tests/unit/test_input_sanitizer.py` — length, whitespace, patterns, control-byte stripping.
- `tests/unit/test_output_validator.py` — leakage, generics, relevance scoring.
- `tests/unit/test_sop_security_malicious.py` — adversarial strings and HTTP **422** on `/sop/generate` and `/api/v1/applications/generate-sop`.
- `tests/unit/test_deadline_reminder_scheduler.py` — optional deadline reminder scheduler start/skip behaviour.

---

## AI Governance & MLSecOps

This service implements a comprehensive **MLSecOps/LLMSecOps** framework aligned with responsible AI principles (e.g., IMDA's Model AI Governance Framework).

### Governance Principles

| Principle | Implementation in OuroborosAI |
|-----------|-------------------------------|
| **Transparency** | Evaluation reports log `model_id`, `prompt_version`, and `token_usage` for every run. |
| **Explainability** | Judge LLM providing natural language `reason` for quality scores in evaluation reports. |
| **Fairness** | Automated bias detection testing demographic variants (name/gender) with a strict `bias_gap` limit. |
| **Safety** | Multi-layer input sanitization, PII guardrails, and adversarial testing for prompt injection. |
| **Auditability** | Version-controlled evaluation history stored on a dedicated `eval-history` audit branch. |

### LLMSecOps Controls

1.  **Shift-Left Security**: Prompt linting and PII scanning run on every Pull Request.
2.  **Adversarial Defense**: Automated unit tests for prompt injection and malicious instruction smuggling.
3.  **Governance in CI**: CI/CD pipeline blocks merges if quality drops below baseline or if bias is detected.
4.  **Supply Chain Security**: Dependency scanning (Snyk) and container vulnerability scanning (Trivy).

---

## Development Workflow

### Code Quality Checks

```bash
black app/ tests/
isort app/ tests/
flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503,E501
pylint app/ tests/
mypy app/ --ignore-missing-imports --no-strict-optional
ALLOW_DB_FAILURE=true X_SERVICE_TOKEN=test-service-token pytest tests/ -v
```

### Pre-Commit Script

```bash
chmod +x pre-commit-check.sh
./pre-commit-check.sh
```

---

## Testing

### Run All Tests

```bash
ALLOW_DB_FAILURE=true X_SERVICE_TOKEN=test-service-token pytest tests/ -v
```

### Run with Coverage

```bash
ALLOW_DB_FAILURE=true X_SERVICE_TOKEN=test-service-token pytest tests/ --cov=app --cov-report=html -v
open htmlcov/index.html
```

### Test Structure

```
tests/
├── conftest.py                     # Shared fixtures
├── fake_repos.py                   # In-memory repository mocks
├── unit/
│   ├── test_config.py              # Configuration loading
│   ├── test_main.py                # Health endpoints
│   ├── test_security.py            # X-Service-Token validation
│   ├── test_input_sanitizer.py     # Input sanitization + injection detection
│   ├── test_output_validator.py    # Output validation + quality scoring
│   ├── test_sop_security_malicious.py  # Adversarial SOP inputs + API 422
│   ├── test_prompt_utils.py        # Prompt template loading & context merge
│   ├── test_llm_prompts.py         # Prompt generation (JSON + text formats)
│   ├── test_llm_pipeline_service.py # OpenAI → Anthropic fallback
│   ├── test_sop_service.py         # SOP orchestration (mock / LLM-mock)
│   ├── test_checklist_service.py   # Completion percentage rules
│   ├── test_deadline_service.py    # Deadline service + mocked repo
│   ├── test_retrieval_service.py   # Retrieval on/off and repo delegation
│   ├── test_db_rows.py             # Row → response helpers
│   └── test_file_utils.py          # Extension / MIME helpers
└── integration/
    └── test_sop_generation_flow.py # HTTP SOP generate + GET edge cases
```

---

## CI/CD Pipeline

**Workflow**: `.github/workflows/deploy.yml` (GitHub Actions name: **OuroborosAI Application Support CI/CD Pipeline**)

**Trigger**: Pull requests to `main` or `develop`

### Pipeline Stages

| Stage | Description | MLSecOps Role |
|-------|-------------|---------------|
| **Format & Lint** | Black, isort, flake8, pylint | Code Quality |
| **Unit Tests** | `pytest tests/unit/` | Functional Correctness |
| **Prompt Lint** | Validate prompt templates & tokens | **Prompt Governance** |
| **PII Guard** | Scan fixtures for sensitive data | **Data Protection** |
| **Type Check** | mypy static analysis | Code Reliability |
| **Security Audit** | Bandit & Snyk OSS | **SAST / SCA** |
| **Docker Build** | Verify container image | Supply Chain |
| **Trivy Scan** | Scan image for CVEs | **Infrastructure Security** |
| **LLM Eval** | Quality & Bias evaluation | **AI Governance** |
| **Summary** | Consolidated report bundle | Transparency |

### Automated Evaluations

The `llm-eval` stage runs `scripts/run_evals.py` which:
- Compares current output quality against a versioned **Baseline**.
- Performs **Bias Detection** by testing demographic variants.
- Stores results in `eval-history` branch for long-term auditability.

---

## Deployment

### Docker Compose (Full Stack)

```bash
docker compose up --build -d
docker compose logs -f
docker compose down
docker compose down -v    # remove volumes
```

### Docker (Service Only)

```bash
docker build -t application-support-agent .

docker run -p 8005:8005 \
  -e DB_HOST=mysql-host \
  -e DB_PASSWORD=secret \
  -e X_SERVICE_TOKEN=token \
  -e OPENAI_API_KEY=sk-... \
  application-support-agent
```

---

## Project Structure

```
ouroboros-ai-application-support/
├── app/
│   ├── api/                         # Route handlers (thin layer)
│   │   ├── health.py                # GET / and /health
│   │   ├── sop.py                   # SOP generation + retrieval
│   │   ├── cover_letter.py          # Cover letter generation + retrieval
│   │   ├── checklist.py             # Checklist retrieval + item updates
│   │   └── deadline.py              # Deadline CRUD
│   ├── core/                        # Infrastructure
│   │   ├── logging.py               # structlog configuration
│   │   └── security.py              # X-Service-Token validation
│   ├── llm/                         # LLM-specific logic
│   │   ├── prompts.py               # Prompt loading with context injection
│   │   ├── schemas.py               # Pydantic schemas for LLM output
│   │   ├── openai_client.py         # OpenAI client with retry
│   │   ├── anthropic_client.py      # Anthropic client with retry
│   │   └── pipeline/                # LangGraph pipeline definitions
│   │       ├── sop_pipeline.py      # 3-step SOP pipeline
│   │       ├── quality_review.py    # Quality scoring logic
│   │       └── state.py             # Pipeline state management
│   ├── middleware/                   # Middleware
│   │   ├── service_auth.py          # X-Service-Token dependency
│   │   └── logging_middleware.py    # Request/response logging with trace_id
│   ├── models/                      # Pydantic request/response schemas
│   │   ├── common_models.py         # StandardResponse, Pagination
│   │   ├── sop_models.py            # SOP schemas
│   │   ├── cover_letter_models.py   # Cover letter schemas
│   │   ├── checklist_models.py      # Checklist schemas
│   │   ├── deadline_models.py       # Deadline schemas
│   │   └── llm_models.py           # LLM pipeline metadata
│   ├── repositories/                # Raw SQL data access (aiomysql)
│   │   ├── db_pool.py               # Async MySQL connection pool
│   │   ├── mysql_base.py            # Base repository with helpers
│   │   ├── mysql_sop_repo.py        # SOP CRUD with versioning
│   │   ├── mysql_cover_letter_repo.py
│   │   ├── mysql_checklist_repo.py
│   │   ├── mysql_deadline_repo.py
│   │   ├── mysql_retrieval_repo.py  # SOP reference retrieval
│   │   └── mysql_llm_call_log_repo.py
│   ├── security/                    # Security validation (CRITICAL)
│   │   ├── input_sanitizer.py       # Input sanitization + injection detection
│   │   ├── prompt_guardrails.py     # DATA/INSTRUCTION boundary enforcement
│   │   └── output_validator.py      # Leakage detection + quality scoring
│   ├── services/                    # Business logic
│   │   ├── sop_service.py           # SOP generation orchestration
│   │   ├── cover_letter_service.py  # Cover letter generation
│   │   ├── checklist_service.py     # Checklist management
│   │   ├── deadline_service.py      # Deadline tracking
│   │   ├── llm_pipeline_service.py  # LLM call with provider fallback
│   │   └── retrieval_service.py     # Style reference retrieval
│   ├── utils/                       # Utilities
│   │   ├── exceptions.py            # Custom exception hierarchy
│   │   ├── trace_id.py              # UUID-v4 trace ID generation
│   │   ├── helpers.py               # generate_uuid, timestamps
│   │   ├── timezone.py              # UTC helpers
│   │   ├── prompt_utils.py          # JSON template loading & context merge
│   │   ├── file_utils.py            # Upload extension / MIME helpers
│   │   ├── db_rows.py               # MySQL row → Pydantic-friendly dicts
│   │   └── docx_generator.py        # python-docx wrapper
│   ├── config.py                    # Pydantic settings
│   └── main.py                      # FastAPI app with lifespan
├── prompts/                         # Version-controlled LLM prompt templates
│   ├── sop_outline_v1.json
│   ├── sop_expansion_v1.json
│   ├── sop_quality_review_v1.json
│   ├── cover_letter_generation_v1.json
│   └── cv_improvement_v1.json
├── migrations/                      # SQL migration files (001-008)
├── scripts/
│   ├── run_migrations.py
│   ├── seed_sop_references.py
│   └── generate_service_token.py
├── tests/                           # Test suite
├── .github/workflows/
│   └── deploy.yml                   # CI/CD pipeline
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── pytest.ini
├── .pylintrc
├── .flake8
├── .env.example
├── start.sh
├── pre-commit-check.sh
└── README.md
```

---

## Troubleshooting

### LLM Generation Failed

**Symptom**: HTTP 502 with `LLM generation failed` / logs show both providers exhausted.

```bash
grep -E 'OPENAI_API_KEY|ANTHROPIC_API_KEY' .env
```

- Ensure at least one provider key is set for real generation (`USE_MOCK_DATA=false`).
- For local smoke tests without keys, set `USE_MOCK_DATA=true` to exercise the API without outbound LLM calls.
- JSON steps (outline, quality review, cover letter) require parseable model output; if Anthropic returns prose, check prompts and temperature.

### Database Connection Failed

```bash
# Check MySQL is running
docker compose ps

# Test connection
mysql -h localhost -P 3308 -u root -p -e "SHOW DATABASES;"

# Verify credentials
grep DB_ .env
```

### LLM Generation Failed

```bash
# Verify API keys are set
grep API_KEY .env

# Test OpenAI connectivity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Import Errors

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Attribution

**Developed by**: OuroborosAI Developer Team

**Project**: Ouroboros AI Scholarship Discovery Platform
