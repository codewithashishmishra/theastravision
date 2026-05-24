# AastraaHR - Project Setup & Local Development Guide

Welcome to the **AastraaHR** project! This repository contains the backend APIs, AI microservices, Next.js frontend panels, and the Desktop Tracker.

Below you'll find the complete start-to-end instructions for getting this project up and running locally.

---

## 🏗 Project Structure

- `apps/api/` - Django API backend (Primary backend service).
- `apps/admin-web/` - Next.js frontend for HR/Admins/Employees.
- `apps/ai-service/` - FastAPI AI/ATS backend for AI processing, STT/TTS.
- `apps/tracker-desktop/` - Python Desktop Tracker App.
- `infra/docker/` - Docker compose configuration for databases and storage.
- `docs/` - Architecture and per-module specifications.

---

## 🛠 Prerequisites & Required Services

Before you begin, ensure you have the following installed on your machine:
- **Docker Desktop** (latest stable)
- **Python** (3.12+)
- **Node.js** (20 LTS)
- **pnpm or npm** (for the Next.js app)
- **Git**

The following services will run inside Docker:
- **PostgreSQL 16+** (Primary DB)
- **Redis 7+** (Cache, Celery broker, sessions)
- **MinIO** (S3-compatible local object storage)
- **MailHog** (Capture outbound email)

---

## 🚀 Full Start-to-End Setup Guide

Follow these steps in order to start all parts of the application.

### Step 1: Start Database & Infrastructure (Docker)

Launch the background services using Docker Compose.

```bash
docker-compose -f infra/docker/docker-compose.yml up -d
```
*This starts PostgreSQL on port `5432`, Redis on `6379`, MinIO on `9000`/`9001`, and MailHog on `8025`.*

### Step 2: Setup the Django API Backend

Open a new terminal and navigate to the API directory:

```bash
cd apps/api
```

Create your `.env` file in `apps/api/`:
```env
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-change-this
DATABASE_URL=postgres://aastraahr:password@localhost:5432/aastraahr_db
REDIS_URL=redis://localhost:6379/0
ALLOW_S3=False
AI_SERVICE_BASE_URL=http://127.0.0.1:8001
FRONTEND_APP_URL=http://localhost:3000
REDIS_ALLOW=True
E2EE_ENABLED=True
METRICS_ENABLED=False
CLICKHOUSE_ENABLED=False
```

See [`apps/api/.env.example`](apps/api/.env.example) for all optional variables. In production, keep `E2EE_ENABLED=True`, set `METRICS_ENABLED=True`, and use `REDIS_ALLOW=True` so E2EE sessions use Redis instead of PostgreSQL. **ClickHouse is optional** — leave `CLICKHOUSE_ENABLED=False` to store and query audit/login logs in PostgreSQL only.

Create a virtual environment, install dependencies, and run migrations:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
```

Start the Django API Server:
```bash
python manage.py runserver 8000
```

### Step 3: Setup the AI Service (FastAPI)

Open a new terminal and navigate to the AI service directory:

```bash
cd apps/ai-service
```

Create your `.env` file in `apps/ai-service/`:
```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_STT_MODEL=whisper-1
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=nova
```

Create a virtual environment, install dependencies, and start the service:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Step 4: Setup the Next.js Admin Web Frontend

Open a new terminal and navigate to the web directory:

```bash
cd apps/admin-web
```

Create your `.env.local` file in `apps/admin-web/`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

Install dependencies and start the development server:
```bash
npm install
npm run dev
```

### Step 5: (Optional) Background Workers (Celery) & AI Translations

If you are testing the AI Interview module or email invites, you'll need the background workers and language models installed.

In your **Django API terminal (with venv activated)**, run:
```bash
# Start Celery Worker (Windows requires eventlet or solo pool usually, Linux doesn't)
celery -A aastraahr worker -l info --pool=solo

# Install the Hindi to English translation models manually
argospm update
argospm install translate-hi_en
```
*Note: The first time a resume match or interview scoring runs, the API will automatically download the `all-MiniLM-L6-v2` embedding model (~90MB).*

---

## Lightweight local dev (lower CPU/RAM)

You do not need every process for day-to-day UI work. `start_services.py` launches the full stack (Django, Celery worker, Celery beat, AI service, admin-web), which can use most of a 16GB machine.

| What you are doing | Start | Skip |
|--------------------|--------|------|
| UI + API only | `runserver`, `npm run dev` | Celery beat/worker, AI service |
| WFH, cold campaigns, interviews | Add Celery worker (`--pool=solo` on Windows) | Celery beat unless testing scheduled jobs |
| Full stack | `python start_services.py` from repo root | — |

**Celery beat** runs platform utilization sampling every 30s and other periodic tasks. Skip it locally unless you need scheduled jobs.

**Turbopack cache:** If `apps/admin-web` dev RAM keeps growing, stop the dev server, delete `apps/admin-web/.next`, and run `npm run dev` again.

Platform utilization **cooldown is not applied when `DEBUG=True`** (metrics still update for the monitoring UI). High local RAM from dev tools will not block saves.

---

## 🌍 Useful Local Ports

You can access the services at the following local addresses:

- **Admin Web UI:** [http://localhost:3000](http://localhost:3000)
- **Django API:** [http://localhost:8000](http://localhost:8000)
- **FastAPI AI Service:** [http://localhost:8001](http://localhost:8001)
- **PostgreSQL Database:** `localhost:5432`
- **Redis Server:** `localhost:6379`
- **MinIO Console:** [http://localhost:9001](http://localhost:9001)
- **MailHog (Emails):** [http://localhost:8025](http://localhost:8025)
