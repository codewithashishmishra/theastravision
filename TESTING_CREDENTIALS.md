Here is the login credential list for every role on the **primary demo tenant** (`Aastraa Demo`, email domain `aastraa.com`). Password for all accounts: `password123`.

Re-seed after changes:

```bash
cd apps/api
python manage.py migrate
python manage.py seed_dev
python manage.py seed_wfh
```

### Application-layer E2EE (all JSON APIs)

When `E2EE_ENABLED=True` (default), clients must complete `POST /api/v1/public/e2ee/handshake/` before any other JSON API call. The admin-web and careers-web apps handle this automatically. Session blobs are stored in PostgreSQL table `REDIS` when `REDIS_ALLOW=False` (default), or in Redis DB 2 when `REDIS_ALLOW=True`.

### Global / Platform Roles

**Super Admin** (full system access, tenant creation, global analytics)

- **Email:** `superadmin@aastraa.com`
- **Password:** `password123`

### Tenant / Company Roles (primary tenant)

**Company Admin**

- **Email:** `companyadmin@aastraa.com`

**HR Admin**

- **Email:** `hradmin@aastraa.com`

**Payroll Admin**

- **Email:** `payrolladmin@aastraa.com`

**Finance Admin**

- **Email:** `financeadmin@aastraa.com`

**IT Admin**

- **Email:** `itadmin@aastraa.com`

### Departmental & Operational Roles (primary tenant)

**Manager** — `manager@aastraa.com`

**Recruiter** — `recruiter@aastraa.com` (Career board: `/recruitment/career-portal` after Job Portal add-on is enabled)

### Job Portal add-on (after `seed_dev`)

- **Super Admin** enables add-on: `/tenants/addons` → select **Aastraa Demo** → toggle Job Portal.
- **Hosted careers:** `http://localhost:3001/aastraa-demo` (run `npm run dev` in `apps/careers-web`).
- **API key:** printed once when running `python manage.py seed_dev` (look for `Job Portal API key` in output).
- **Public API:** `GET http://127.0.0.1:8000/api/v1/public/job-board/config/` with header `X-Job-Board-Key: <key>`.
- **Sample job:** `senior-software-engineer` on demo tenant careers page.

**Interviewer** — `interviewer@aastraa.com` (home: `/interviewer/upcoming`)

**Auditor** — `auditor@aastraa.com`

### Base Role (primary tenant)

**Employee** — `employee@aastraa.com` (home: `/dashboards/employee`)

---

### Sample tenants (multi-tenant login testing)

**Astra Corp** (`astra.com`)

- `employee@astra.com` / `password123` (Employee)
- `hradmin@astra.com` / `password123` (HR Admin)

**Astra Net Ltd** (`astra.net`)

- `employee@astra.net` / `password123` (Employee)
- `hradmin@astra.net` / `password123` (HR Admin)

After login, the sidebar shows the email and display name from `GET /api/v1/auth/me/` (roles come from `UserRoleMapping`, not email guessing).

### Cold email campaigns (Super Admin)

1. Log in as **Super Admin** (`superadmin@aastraa.com` / `password123`).
2. Open **Platform Config** → **SMTP** tab and save GoDaddy SMTP (credentials stored encrypted; never commit passwords to git).
3. Set API env var `PUBLIC_API_BASE_URL` to your publicly reachable API base (e.g. `https://api.yourdomain.com`) so open-tracking pixels work.
4. Open **Cold Email Campaigns** under Super Admin Operations: create a campaign, upload CSV (`email`, optional `first_name`, `company`), send test, then send.
5. Run Celery worker for bulk send:

```bash
cd apps/api
celery -A config worker -l info
```

Optional: **Platform Config** → **AI** tab for OpenAI-powered email rewrite.
