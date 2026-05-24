# Job Portal & Career Board SDK

Optional add-on (`job_portal`) for AASTRAA HRMS.

## Pricing

| Region | Monthly |
|--------|---------|
| India | ₹2,000 |
| US / Global | $5 |

Enabled manually by **Super Admin** → Tenants → Add-ons.

## HR workflow

1. Super Admin enables **Job Portal** for the tenant.
2. HR / Recruiter opens **Recruitment → Career Board** to configure branding, API key, and embed origins.
3. Create requisitions under **Job Management → Requisitions**; set status to **Open**.
4. **Publish** from Active Postings or Career Board (requires add-on).
5. Applications from hosted careers or embed create **Candidate** records (stage `Sourced`) and trigger AI resume match.

## Hosted careers app

- App: `apps/careers-web` (port `3001` in dev)
- URL: `{CAREERS_APP_URL}/{tenant-slug}` (e.g. `http://localhost:3001/aastraa-demo`)
- Uses slug-based public API (no API key for reads/apply on hosted routes)

## Public API (embed SDK)

Base: `/api/v1/public/job-board/`

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /config/` | `X-Job-Board-Key` | Tenant branding |
| `GET /jobs/` | API key | Published jobs list |
| `GET /jobs/{slug}/` | API key | Job detail |
| `POST /jobs/{slug}/apply/` | API key | Submit application (multipart) |

Hosted (no API key):

| Endpoint | Description |
|----------|-------------|
| `GET /hosted/{tenant_slug}/config/` | Branding |
| `GET /hosted/{tenant_slug}/jobs/` | Job list |
| `GET /hosted/{tenant_slug}/jobs/{job_slug}/` | Job detail |
| `POST /hosted/{tenant_slug}/jobs/{job_slug}/apply/` | Apply |

## Embed SDK

Build: `cd packages/job-board-sdk && npm install && npm run build`

```html
<script
  src="http://localhost:4173/embed.js"
  data-api-base="http://127.0.0.1:8000/api/v1"
  data-api-key="jb_live_..."
  data-target="aastraa-job-board"
></script>
<div id="aastraa-job-board"></div>
```

Events: `aastraa:job-selected`, `aastraa:applied` on the mount element.

## Environment

| Variable | Purpose |
|----------|---------|
| `CAREERS_APP_URL` | Hosted careers base (admin UI links) |
| `JOB_BOARD_CDN_URL` | Embed script URL |
| `PUBLIC_API_BASE_URL` | API base for embed snippet |

## Seed

```bash
cd apps/api
python manage.py seed_dev
```

Prints a one-time Job Portal API key for the demo tenant.
