# Local Development Guide for AastraaHR

This document outlines the local development setup for the AastraaHR project on Windows.

## Required Runtime and Services

| Tool | Version hint | Purpose |
|------|----------------|---------|
| **Docker Desktop** | latest stable | Compose stack |
| **PostgreSQL** | 16+ | Primary DB (via compose) |
| **Redis** | 7+ | Cache, Celery broker, sessions |
| **MinIO** | latest | S3-compatible local object storage |
| **Python** | 3.12+ | Django API + FastAPI AI |
| **Node.js** | 20 LTS | Next.js admin |
| **pnpm or npm** | per repo | Admin web package manager |

## Optional Local Services

| Tool | Purpose |
|------|---------|
| **Mailhog** | Capture outbound email |
| **ClamAV** | Upload virus scan in dev |
| **FFmpeg** | AI interview media processing |

## Project Structure

- `apps/api/` - Django API backend
- `apps/admin-web/` - Next.js frontend for HR/Admins/Employees
- `apps/ai-service/` - FastAPI AI/ATS backend
- `infra/docker/` - Docker compose configuration
- `docs/` - Architecture and per-module specifications

## Environment Setup

### 1. Database & Services (Docker)

```bash
docker-compose -f infra/docker/docker-compose.yml up -d
```
This runs PostgreSQL, Redis, MinIO, and MailHog.

### 2. Django API

```bash
cd apps/api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Create an `.env` file in `apps/api/`:
```env
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key
DATABASE_URL=postgres://aastraahr:password@localhost:5432/aastraahr_db
REDIS_URL=redis://localhost:6379/0
ALLOW_S3=False
```

### 3. Next.js Admin Web

```bash
cd apps/admin-web
npm install
npm run dev
```

Create an `.env.local` file in `apps/admin-web/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. AI Service (FastAPI)

```bash
cd apps/ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Create an `.env` file in `apps/ai-service/`:
```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_STT_MODEL=whisper-1
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=nova
```

Also configure OpenAI under **Super Admin → Platform Config → AI** (model: `gpt-5.4-mini`). Django forwards the key to ai-service per request.

### Astra AI Interview (Module 9)

| Component | Where | Notes |
|-----------|--------|--------|
| **JD / resume parse** | Django (`recruitment/document_parser.py`) | PDF + DOCX only, no AI |
| **Match score** | Django (`matching.py`) | sentence-transformers + skill dictionary |
| **Hindi → English** | Django (`translation.py`) | Argos Translate offline |
| **Answer scoring** | Django (`answer_scoring.py`) | Embedding similarity |
| **HR reports** | Django (`report_builder.py`) | HTML template, no LLM |
| **Questions + MCQ** | ai-service | **gpt-5.4-mini** |
| **STT / TTS** | ai-service | OpenAI `whisper-1` + `tts-1` |

**One-time Argos Hindi model (Django API venv):**
```bash
argospm update
argospm install translate-hi_en
```

**First match/score request** downloads `all-MiniLM-L6-v2` (~90MB) via sentence-transformers.

Run **Celery worker + beat** for interview invite emails and report delivery.

Add to `apps/api/.env`:
```env
AI_SERVICE_BASE_URL=http://127.0.0.1:8001
FRONTEND_APP_URL=http://localhost:3000
```

Add to `apps/admin-web/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**HR flow:** `/recruitment/candidates/new` → upload resume → match ≥70% → invite link or auto-email.

**Candidate flow:** `/interview/join/{token}` → voice with Astra → optional `/assessment/{token}` (camera on, 20 min, 10 MCQs).

## Useful Ports

- 8000: Django API
- 3000: Next.js Admin Web
- 8001: FastAPI AI Service
- 5432: PostgreSQL
- 6379: Redis
- 9000: MinIO API
- 9001: MinIO Console
- 8025: MailHog Web UI
