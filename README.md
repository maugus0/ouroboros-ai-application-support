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
- [Security](#security)
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

- **Input sanitization** — Length limits, whitespace normalisation, control character detection
- **Prompt injection detection** — Pattern matching for common injection attempts
- **Prompt guardrails** — Clear DATA/INSTRUCTION boundaries in prompts
- **Output validation** — Prompt leakage detection, generic phrase detection, quality scoring

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
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
| `LOG_LEVEL` | No | `INFO` | `DEBUG\|INFO\|WARNING\|ERROR\|CRITICAL` |
| `USE_MOCK_DATA` | No | `false` | Use in-memory repos (tests only) |
| `ALLOW_DB_FAILURE` | No | `false` | Continue if DB unavailable (tests only) |

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
└── 006_create_llm_call_logs.sql
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
| GET | `/checklists/{user_id}` | Get all checklists for user |
| PUT | `/checklists/{id}/items/{item_id}` | Update checklist item |

### Deadlines

| Method | Path | Description |
|--------|------|-------------|
| GET | `/deadlines/{user_id}` | Get all deadlines for user |
| POST | `/deadlines/` | Create deadline entry |
| PUT | `/deadlines/{id}` | Update deadline entry |

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

## Security

This service handles user-provided text that feeds directly into LLM prompts, making it the **most vulnerable to prompt injection** in the Ouroboros platform.

### Security Layers

1. **Input Sanitization** (`app/security/input_sanitizer.py`)
   - Length limits (configurable via `MAX_INPUT_LENGTH`)
   - Whitespace normalisation
   - Control pattern detection (system overrides, assistant tags)

2. **Prompt Guardrails** (`app/security/prompt_guardrails.py`)
   - Clear DATA/INSTRUCTION boundaries in prompts
   - User data wrapped in clearly marked sections
   - System instructions protected from data override

3. **Output Validation** (`app/security/output_validator.py`)
   - Prompt leakage detection (AI self-references, system markers)
   - Generic phrase detection (quality signal)
   - Quality scoring (0.0-1.0)

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
│   ├── test_prompt_utils.py        # Prompt template loading & context merge
│   └── test_llm_prompts.py         # Prompt generation (JSON + text formats)
└── integration/
    └── (future E2E tests)
```

---

## CI/CD Pipeline

**Workflow**: `.github/workflows/deploy.yml`

**Trigger**: Pull requests to `main` or `develop`

### Pipeline Stages

| Stage | Description |
|-------|-------------|
| **Format** | Black + isort validation |
| **Lint** | flake8 + pylint (both blocking) |
| **Unit Tests** | `pytest tests/unit/` with JUnit XML artifact |
| **Type Check** | mypy — blocking (after format + lint) |
| **Tests + Coverage** | Full `pytest tests/` with HTML + Cobertura XML |
| **Security Audit** | Bandit (JSON artifact) |
| **Docker Build** | Verify image builds — no push |
| **Summary** | Markdown table of all job results |

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
│   │   └── mysql_retrieval_repo.py  # SOP reference retrieval
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
│   │   └── docx_generator.py        # python-docx wrapper
│   ├── config.py                    # Pydantic settings
│   └── main.py                      # FastAPI app with lifespan
├── prompts/                         # Version-controlled LLM prompt templates
│   ├── sop_outline_v1.json
│   ├── sop_expansion_v1.json
│   ├── sop_quality_review_v1.json
│   ├── cover_letter_generation_v1.json
│   └── cv_improvement_v1.json
├── migrations/                      # SQL migration files (001-006)
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
