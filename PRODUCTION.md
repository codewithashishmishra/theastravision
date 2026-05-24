# AastraaHR Production Deployment Guide

This document outlines the complete step-by-step process for deploying the AastraaHR platform (API, AI Service, and Admin Web) into a production environment (typically Ubuntu 22.04 LTS or similar).

---

## 1. System Requirements & Infrastructure

Ensure your production server meets the following minimum requirements:
- **OS**: Ubuntu 22.04 LTS (Recommended)
- **CPU**: 4+ Cores
- **RAM**: 8GB+ (16GB recommended if running AI models and optional ClickHouse)
- **Storage**: 100GB+ SSD

### Required External Services
Before configuring the application, ensure the following services are installed and running (either locally or via managed cloud providers):
1. **PostgreSQL** (Relational Database)
2. **Redis** (Caching & Celery Message Broker)
3. **MinIO / AWS S3** (Object Storage for media and document assets)

### Optional External Services
- **ClickHouse** — High-volume platform/audit log analytics. **Not required.** With `CLICKHOUSE_ENABLED=False` (default), all audit and login-session queries use PostgreSQL tables (`SystemAuditLog`, `AuthSession`) only.

---

## 2. System Dependencies

First, update your package lists and install essential system libraries. The AI service (specifically OpenCV) requires native OS graphic libraries.

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv python3-dev build-essential libpq-dev \
    nginx curl git \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev  # Required for OpenCV/Face Auth
```

Install Node.js (v18+) and PM2:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g pm2
```

---

## 3. Clone Repository & Environment Setup

Clone your repository to the production directory (e.g., `/var/www/aastraahr`).

```bash
cd /var/www
git clone <your-repo-url> aastraahr
cd aastraahr
```

---

## 4. Deploying the Django API (`apps/api`)

### Setup Virtual Environment
```bash
cd /var/www/aastraahr/apps/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure `.env`
Create your production `.env` file in `apps/api/.env`.
```env
DEBUG=False
SECRET_KEY=your-secure-production-key
DATABASE_URL=postgres://user:pass@localhost:5432/aastraahr
REDIS_URL=redis://localhost:6379/0

# Security & performance (required in production)
E2EE_ENABLED=True
REDIS_ALLOW=True
METRICS_ENABLED=True

# ClickHouse (optional — default off; audit logs use PostgreSQL when disabled)
CLICKHOUSE_ENABLED=False
# CLICKHOUSE_HOST=localhost
# CLICKHOUSE_PORT=8123
# CLICKHOUSE_USER=default
# CLICKHOUSE_PASSWORD=
# CLICKHOUSE_DATABASE=default

# MinIO / S3
ALLOW_S3=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_ENDPOINT_URL=...
```

### Migrate and Collect Static Files
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### Run API using Systemd (Daphne/Gunicorn)
Because AastraaHR uses WebSockets for notifications, use Daphne as the ASGI server. Create a systemd service `/etc/systemd/system/aastraa-api.service`:

```ini
[Unit]
Description=AastraaHR Django API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aastraahr/apps/api
ExecStart=/var/www/aastraahr/apps/api/venv/bin/daphne -b 127.0.0.1 -p 8000 config.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable aastraa-api
sudo systemctl start aastraa-api
```

---

## 5. Deploying Background Workers (Celery)

Create a systemd service for the Celery Worker (`/etc/systemd/system/aastraa-celery-worker.service`):
```ini
[Unit]
Description=AastraaHR Celery Worker
After=network.target redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aastraahr/apps/api
ExecStart=/var/www/aastraahr/apps/api/venv/bin/celery -A config worker -l INFO
Restart=always

[Install]
WantedBy=multi-user.target
```

Create a systemd service for Celery Beat (`/etc/systemd/system/aastraa-celery-beat.service`):
```ini
[Unit]
Description=AastraaHR Celery Beat
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aastraahr/apps/api
ExecStart=/var/www/aastraahr/apps/api/venv/bin/celery -A config beat -l INFO
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the background workers:
```bash
sudo systemctl enable aastraa-celery-worker aastraa-celery-beat
sudo systemctl start aastraa-celery-worker aastraa-celery-beat
```

---

## 6. Deploying the AI Service (`apps/ai-service`)

### Setup Virtual Environment
```bash
cd /var/www/aastraahr/apps/ai-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure `.env`
Ensure your `apps/ai-service/.env` contains your OpenAI production keys.

### Run AI Service using Systemd
Create `/etc/systemd/system/aastraa-ai.service`:

```ini
[Unit]
Description=AastraaHR FastAPI AI Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aastraahr/apps/ai-service
ExecStart=/var/www/aastraahr/apps/ai-service/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aastraa-ai
sudo systemctl start aastraa-ai
```

---

## 7. Deploying the Next.js Frontend (`apps/admin-web`)

### Build the Application
```bash
cd /var/www/aastraahr/apps/admin-web
npm install
npm run build
```

### Run using PM2
Next.js should be managed by PM2 to ensure high availability.
```bash
pm2 start npm --name "aastraa-web" -- start
pm2 save
pm2 startup
```

---

## 8. Nginx Reverse Proxy Setup

Nginx will route traffic to the Next.js frontend, the Django API, and the FastAPI service. Create `/etc/nginx/sites-available/aastraahr`:

```nginx
server {
    listen 80;
    server_name aastraa.yourdomain.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API (Django / Daphne)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSockets (Daphne)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # AI Service (FastAPI)
    location /ai/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static / Media Files (If not using S3)
    location /static/ {
        alias /var/www/aastraahr/apps/api/static/;
    }
    location /media/ {
        alias /var/www/aastraahr/apps/api/media/;
    }
}
```

Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/aastraahr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 9. Security & SSL
Secure your Nginx server with Let's Encrypt / Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d aastraa.yourdomain.com
```

**Congratulations! Your AastraaHR platform is now fully operational in production!**

---

## 10. Pricing & Business Strategy

### Go-To-Market Strategy
- **Early Adopter Promotion:** The first 100 client companies receive a **Lifetime Free Package** granting them full access to all 3 modules (Core HR, ATS/Recruitment, Performance/Analytics). This acts as a powerful marketing lever to gain immediate user traction, beta feedback, and case studies.

### Recommended SaaS Pricing Plans

**India Pricing (INR)**
1. **Starter (Perfect for growing teams):** ₹8,000 /mo
   - *Covers first 100 users (+ ₹100 per additional user)*
   - 24hrs Payroll Delay, 10 AI Interviews/yr, 24/7 AI Chatbot
   - Core HR, QR/GPS Attendance, Basic Leave & Shifts, ESS Portal
2. **Professional (Most Popular):** ₹12,000 /mo
   - *Covers first 100 users (+ ₹70 per additional user)*
   - 10hrs Payroll Delay, 50 AI Interviews/yr, 24/7 Human + AI Support
   - Full Statutory Compliance (PF, TDS, ESIC), Expense/Claims, HR Helpdesk, Face Recognition
3. **Enterprise (Uncapped power):** ₹18,000 /mo
   - *Covers first 100 users (+ ₹50 per additional user)*
   - Instant Hassle-Free Payroll, Unlimited AI Interviews, VIP Support
   - Predictive Attrition & Sentiment, Performance/OKRs, Project Timesheets, Asset Management

**USA / Global Pricing (USD)**
1. **Starter:** $5 / user / month
2. **Professional:** $12 / user / month
3. **Enterprise:** $18 / user / month

### Optional Add-ons (billed in addition to core plans)

| Add-on | India (INR) | US / Global (USD) |
|--------|-------------|-------------------|
| **Job Portal & Career Board SDK** | ₹2,000 / month | $5 / month |

Includes a hosted careers page (Greenhouse-style), public job board API, and an embeddable SDK for your corporate website. Applications create candidates in the ATS pipeline. Enabled manually by platform admin in v1 (no self-serve billing).

### Revenue & Costing Analysis (5,000 India Users + 500 USA Users)

For phased hosting (shared VM → dedicated VM at 5k users), app store fees, migration, and profit-after-deductions tables, see [`docs/PRODUCTION_MONTHLY_COSTING.md`](docs/PRODUCTION_MONTHLY_COSTING.md).


**1. Estimated Gross Revenue (Per Month):**
- **India (5,000 users):** Assuming an average distribution of companies on the Professional plan (e.g., 50 mid-sized companies): ~₹6,00,000 INR / month (approx. $7,200 USD).
- **USA (500 users):** Assuming the average user is on the Professional plan ($12/user): $6,000 USD / month (approx. ₹5,00,000 INR).
- **Total Gross Revenue:** **~$13,200 USD** (or **~₹11,00,000 INR**) per month.

**2. AI Inference Costs (GPT-4o-mini):**
- Since you are utilizing `gpt-4o-mini`, AI processing is incredibly cheap ($0.15 per 1M input tokens).
- Even with heavy automated screening, resume parsing, and 24/7 chatbot usage across 5,500 users, monthly consumption will easily stay under 100 Million tokens.
- **Estimated AI Cost:** **~$15 to $30 USD / month**.

**3. Total Profit (Excluding Base Infrastructure):**
- Revenue: ~$13,200
- AI Costs: -$30
- **Net Operating Income:** **~$13,170 USD per month** (or **~₹10,95,000 INR**).
- *(Note: Your baseline Linux/PostgreSQL server infrastructure costs remain fixed at roughly ~$400-$600/month until you exceed 10,000 users).*

---

## 11. Infrastructure Scaling Strategy (Beyond 5,000 Users)

The current monolithic deployment (everything running on 1-2 large servers) is perfect for 1 to 5,000 users. However, as your platform scales beyond 5,000 users, you must implement the following horizontal scaling strategies:

### 1. What to Increase at 10,000+ Users
- **Load Balancing:** Place an AWS Application Load Balancer (ALB) or Nginx Load Balancer in front of your application.
- **API Servers (Horizontal Scaling):** Spin up 2 or 3 separate Django/FastAPI servers instead of 1. Because Daphne and Uvicorn are stateless, you can keep adding duplicate API servers behind the load balancer as traffic grows.
- **Database Scaling (Vertical):** Increase your PostgreSQL server to 32GB RAM / 8 Cores to handle higher concurrent connections.

### 2. What to Increase at 25,000+ Users
- **Database Read Replicas:** The database will become the bottleneck. Set up PostgreSQL Read Replicas. Configure Django's database router to send all `SELECT` queries to the replicas, leaving the primary database only for `INSERT/UPDATE` operations.
- **Dedicated Celery Fleet:** Move the Celery Workers and Celery Beat scheduler off the main API servers onto their own dedicated fleet of droplets. Increase the Celery concurrency limit.

### 3. What to Increase at 50,000+ Users
- **Redis Clustering:** Move from a single Redis instance to a Redis Cluster for distributed caching and websocket state management.
- **ClickHouse Scaling:** ClickHouse easily handles billions of rows on a single machine, but for high concurrency queries across hundreds of tenant dashboards, you should shard ClickHouse across multiple nodes or migrate to ClickHouse Cloud.
