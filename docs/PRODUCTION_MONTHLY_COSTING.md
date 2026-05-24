# AastraaHR — Infrastructure, App Stores & Profitability Costing

Planning guide for **demo (Vercel)**, **lean production (0–5,000 users, shared VM)**, **scale production (5,000+ users, dedicated VM)**, **iOS/Android store fees**, **migration**, and **net profit after deductions**.

> **Price basis:** Hetzner EU (Germany/Finland), **post–1 April 2026**, excl. German VAT.  
> **FX:** €1 = ₹92 · $1 = ₹85 · €1 = $1.10  
> **Last updated:** May 2026 — verify in [Hetzner Console](https://console.hetzner.cloud/) before purchase.

**Related:** [`PRODUCTION.md`](../PRODUCTION.md) · [`website/assets/pricing-config.js`](../website/assets/pricing-config.js)

---

## Table of contents

1. [Architecture phases overview](#1-architecture-phases-overview)  
2. [Demo on Vercel](#2-demo-on-vercel)  
3. [Phase 1 — 0 to 5,000 users (shared VM, no dedicated CCX)](#3-phase-1--0-to-5000-users-shared-vm-no-dedicated-ccx)  
4. [Migration at ~5,000 users → dedicated VM](#4-migration-at-5000-users--dedicated-vm)  
5. [Phase 2 — 5,000+ users (dedicated VM)](#5-phase-2--5000-users-dedicated-vm)  
6. [Mobile apps — Play Store & App Store (one-time & recurring)](#6-mobile-apps--play-store--app-store-one-time--recurring)  
7. [GST / tax (India)](#7-gst--tax-india)  
8. [Revenue model assumptions](#8-revenue-model-assumptions)  
9. [Profit after all deductions (by scale)](#9-profit-after-all-deductions-by-scale)  
10. [Summary timeline](#10-summary-timeline)  
11. [Checklists](#11-checklists)  
12. [Disclaimer](#12-disclaimer)

---

## 1. Architecture phases overview

Django + Celery + Postgres **cannot** run on Vercel alone. “Without dedicated VM” means **no CCX dedicated server** — you still use one **small shared VPS** (Hetzner CPX) for the API until you outgrow it.

| Phase | User range | Production compute | ClickHouse | Marketing / demo |
|-------|------------|-------------------|------------|------------------|
| **0 — Dev** | 0 customers | Local PC + Docker | Off | Vercel Hobby **₹0** |
| **1 — Lean SaaS** | 1 – **5,000** | **Hetzner CPX41** (shared vCPU, 16 GB) | **Off** (`CLICKHOUSE_ENABLED=False`) | Vercel |
| **2 — Scale** | **5,000+** | **Hetzner CCX23/33** (dedicated vCPU) | Optional on same VM | Vercel |

```text
Phase 0          Phase 1 (0–5k users)              Phase 2 (5k+)
────────         ─────────────────────            ──────────────
[Laptop]    →    [CPX41: API+DB+Redis+Celery]  →  [CCX23: dedicated]
[Vercel demo]    [R2 storage]                     [+ optional ClickHouse]
                 [No ClickHouse]                  [pg_dump migration]
```

---

## 2. Demo on Vercel

| Tier | USD/mo | INR/mo | Use |
|------|--------|--------|-----|
| **Hobby** | 0 | 0 | Marketing `website/`, light previews (check commercial ToS) |
| **Pro** | 20 | ~1,700 | Client demos, password previews, more bandwidth |

Production **API and admin app** for paying tenants run on the VPS (Phase 1/2), not on Vercel. Vercel can host a **read-only demo** that calls a public demo API if needed.

---

## 3. Phase 1 — 0 to 5,000 users (shared VM, no dedicated CCX)

### 3.1 Recommended server (shared, not dedicated)

| Plan | vCPU | RAM | Disk | EUR/mo (excl. VAT) | Why |
|------|------|-----|------|-------------------|-----|
| **CPX31** | 4 shared | 8 GB | 160 GB | **~€13.99** | Tight; OK for &lt;500 users, light AI |
| **CPX41** *(recommended)* | 8 shared | 16 GB | 240 GB | **~€25.49** | Matches `PRODUCTION.md` RAM guidance until 5k users |

`PRODUCTION.md` allows **ClickHouse off** — audit logs stay in **PostgreSQL** only. That saves RAM and complexity in Phase 1.

### 3.2 Phase 1 monthly line items (CPX41, EU)

| # | Item | EUR/mo | INR/mo |
|---|------|--------|--------|
| 1 | **CPX41** VM | 25.49 | 2,345 |
| 2 | Primary IPv4 | 0.60 | 55 |
| 3 | Automated backups (+20%) | 5.10 | 469 |
| 4 | Object storage R2 (~50–150 GB) | — | 425–850 |
| 5 | Email (Resend/SES) | — | 255 |
| 6 | Domain (amortized) | — | 85 |
| 7 | **OpenAI** (see scale table) | — | 850–3,400 |
| 8 | **Other misc** | — | **500** |
| 9 | **App stores** (amortized, §6) | — | **~880** |
| | **Subtotal (excl. IGST)** | **~31.19** + AI | **~₹6,764–9,314** |

### 3.3 OpenAI budget by user count (Phase 1)

| Licensed users | Planning USD/mo | INR/mo |
|----------------|-----------------|--------|
| 0 – 500 | 10 | 850 |
| 500 – 1,500 | 15 | 1,275 |
| 1,500 – 3,000 | 25 | 2,125 |
| 3,000 – 5,000 | 40 | 3,400 |

Set a **hard cap** in the OpenAI dashboard at each tier.

### 3.4 Phase 1 total with tax (CPX41, ~1,000 users, ITC claimed)

| | INR/mo |
|---|--------|
| Infra + email + domain + misc + app amort + OpenAI ($10) | **~₹6,764** |
| IGST 18% on imports (if no ITC) | +~₹1,050 |
| **Cash out (with ITC)** | **~₹6,764** |
| **Cash out (no ITC)** | **~₹7,814** |

### 3.5 Phase 1 at 5,000 users (upper bound before migration)

| | INR/mo (excl. ITC) |
|---|---------------------|
| CPX41 stack + R2 ~150 GB + OpenAI $40 + misc + app amort | **~₹9,314** |
| + IGST (no ITC) | **~₹10,900** |

**Watch signals to migrate earlier than 5,000:** sustained RAM &gt;85%, payroll/Celery queue delays, PostgreSQL DB &gt;80 GB, or p95 API latency degrading during month-end.

---

## 4. Migration at ~5,000 users → dedicated VM

### 4.1 What you migrate

| Component | Action |
|-----------|--------|
| PostgreSQL | `pg_dump` / `pg_restore` or replication then cutover |
| Redis | Short maintenance window (sessions refresh) |
| Object storage (R2) | **No move** — same bucket, update env only |
| ClickHouse | N/A if was disabled; if enabling on new VM, run migrations + optional `backfill_clickhouse_logs` |
| App code | Git pull on new server, same `.env` secrets |
| DNS | Lower TTL to 300s before cutover; point `app.domain` to new IP |
| SSL | Certbot on new host |

### 4.2 Migration cost (money)

| Item | One-time INR | Notes |
|------|--------------|-------|
| **Overlap** (old + new VM 24–48 h) | **~₹150–400** | ~1–2 days of CPX41 hourly while testing |
| **Extra snapshot** | **~₹100–300** | Safety rollback |
| **Downtime** | ₹0 | Plan 30–60 min maintenance window |
| **Developer time** | Your time | 4–8 hours if scripted |

**No mandatory migration SaaS fee** if you DIY. Optional managed DB migration tools are not required for monolith → monolith.

### 4.3 Migration checklist (technical)

1. Provision **CCX23** (or CCX33) in same EU region.  
2. Install Docker or native Postgres/Redis; match Postgres major version.  
3. Restore database; run `python manage.py migrate`.  
4. Smoke-test E2EE handshake, login, payroll read, file upload to R2.  
5. Switch DNS; monitor 24 h.  
6. **Delete old CPX41** (stops billing — powering off does **not**).  
7. Optionally enable `CLICKHOUSE_ENABLED=true` after stable week.

---

## 5. Phase 2 — 5,000+ users (dedicated VM)

### 5.1 Recommended server (dedicated vCPU)

| Plan | vCPU | RAM | EUR/mo (excl. VAT) | When |
|------|------|-----|-------------------|------|
| **CCX23** | 4 dedicated | 16 GB | **€31.49** | 5k–10k users, monolith |
| **CCX33** | 8 dedicated | 32 GB | **€62.49** | 10k+ or ClickHouse + heavy AI on same box |

### 5.2 Phase 2 monthly (CCX23, ~5,000–7,000 users)

| # | Item | INR/mo |
|---|------|--------|
| CCX23 + IP + backups | 3,532 |
| R2 ~200 GB | 850 |
| Email + domain | 340 |
| OpenAI (~$40–60) | 3,400–5,100 |
| Misc | 500 |
| App store amort | 880 |
| **Subtotal (excl. ITC)** | **~₹9,502–11,202** |

At **10,000+ users**, add **~₹2,850** for CCX33 upgrade and consider Celery on second small VM per `PRODUCTION.md` §11.

---

## 6. Mobile apps — Play Store & App Store (one-time & recurring)

Native **iOS/Android** apps are planned (React Native per project docs) but not required for web-only launch. Budget below for first store release.

### 6.1 Mandatory store fees

| Platform | Fee type | USD | INR (approx.) | Frequency |
|----------|----------|-----|---------------|-----------|
| **Google Play** | Developer registration | **$25** | **~₹2,125** | **One-time** (lifetime account) |
| **Apple App Store** | Apple Developer Program | **$99** | **~₹8,415** | **Every year** |

### 6.2 Typical first-release extras (one-time or optional)

| Item | USD | INR | Notes |
|------|-----|-----|-------|
| **Apple Mac access** (build/sign) | 0–99/mo | 0–8,400 | Own Mac, Mac mini, or CI (Codemagic ~$50/mo only while shipping) |
| **Google Play closed test** | 0 | 0 | 12 testers × 14 days before production (policy) |
| **Privacy policy + terms** (hosted) | 0 | 0 | Use existing website URL |
| **Firebase** (push, analytics) | 0 | 0 | Free tier usually enough at start |
| **App icons / screenshots** | 0–200 | 0–17,000 | DIY vs designer |
| **Optional: enterprise D-U-N-S** | 0 | 0 | Only if Apple org verification delays |

### 6.3 Amortized monthly (planning)

| Period | Calculation | INR/mo |
|--------|-------------|--------|
| **Year 1** | ($25 + $99) ÷ 12 | **~₹880** |
| **Year 2+** | $99 ÷ 12 only | **~₹715** |

### 6.4 Store requirements checklist

**Both stores**

- [ ] Privacy policy URL (GDPR/data collection for HR data)  
- [ ] Account deletion / data export flow (HR apps often scrutinized)  
- [ ] HTTPS API only; certificate pinning optional  
- [ ] App signing keys secured (Play App Signing, Apple certs in Keychain)  

**Google Play**

- [ ] Play Console account ($25)  
- [ ] Target API level per current Play policy  
- [ ] Data safety form (location, photos if attendance/WFH)  
- [ ] 14-day closed testing track (if new personal developer account)  

**Apple App Store**

- [ ] Apple Developer Program ($99/yr)  
- [ ] App Store Connect app record, screenshots per device size  
- [ ] **Mac + Xcode** for archive/upload  
- [ ] Export compliance, encryption questionnaire  
- [ ] Review notes + demo login for Apple reviewer  

**AastraaHR-specific:** Attendance GPS, camera (face), microphone (AI interview) → declare permissions clearly to avoid rejection.

---

## 7. GST / tax (India)

| Service | Typical Indian GST treatment |
|---------|------------------------------|
| Hetzner / OpenAI / R2 (foreign) | **18% IGST** under RCM; **ITC** if GST-registered |
| Indian domain registrar | Often 18% GST on invoice |
| Google Play / Apple | Billed in USD; confirm with CA |
| Your SaaS sales (India B2B) | **18% GST** charged to customers (separate from this doc) |

**Planning:** Use **excl. ITC** totals for conservative profit; use **incl. ITC** for cash-flow reality if registered.

---

## 8. Revenue model assumptions

From [`pricing-config.js`](../website/assets/pricing-config.js) — **India Professional** (most common):

| Metric | Value |
|--------|--------|
| Base price | **₹12,000 / company / month** |
| Included users | 100 per company |
| Overage | **₹70 / extra user / month** |

**Tenant math for user milestones:**

| Total licensed users | Example tenant mix | **Gross MRR (INR)** |
|----------------------|-------------------|---------------------|
| 500 | 5 × 100 users | **₹60,000** |
| 1,000 | 10 × 100 users | **₹1,20,000** |
| 2,500 | 25 × 100 users | **₹3,00,000** |
| **5,000** | 50 × 100 users | **₹6,00,000** |
| 7,500 | 50 × 100 + 2,500 overage @ ₹70 | **₹7,75,000** |
| 10,000 | 100 × 100 users | **₹12,00,000** |

*`PRODUCTION.md` uses **₹6,00,000/mo** at 5,000 India users on Professional — aligned above.*

**Early adopter promo:** First 100 companies lifetime free → **₹0 revenue** from those tenants; model above assumes **paying** customers only.

**US/Global (reference):** $12/user/mo Professional → 500 users ≈ **$6,000/mo** (~₹5,10,000).

---

## 9. Profit after all deductions (by scale)

**Deductions included:** Phase-appropriate hosting, R2, email, domain, OpenAI, **₹500 misc**, **app store amort (~₹880/mo)**, **no IGST** (assumes GST registration + ITC on imports).

### 9.1 Phase 1 — Shared CPX41 (0–5,000 users)

| Users | Paying tenants | **Gross revenue** | **Total opex** | **Net profit** | **Margin** |
|------:|---------------|------------------:|---------------:|---------------:|-----------:|
| 0 | 0 | ₹0 | ₹6,764 | **−₹6,764** | — |
| 500 | 5 | ₹60,000 | ₹7,189 | **₹52,811** | **88%** |
| 1,000 | 10 | ₹1,20,000 | ₹7,814 | **₹1,12,186** | **93%** |
| 2,500 | 25 | ₹3,00,000 | ₹8,864 | **₹2,91,136** | **97%** |
| **5,000** | 50 | **₹6,00,000** | **₹10,214** | **₹5,89,786** | **98%** |

*Opex at 5k: CPX41 + larger R2 + OpenAI $40 + misc + app amort.*

### 9.2 Phase 2 — Dedicated CCX23 (after migration, 5,000–10,000 users)

| Users | **Gross revenue** | **Total opex** | **Net profit** | **Margin** |
|------:|------------------:|---------------:|---------------:|-----------:|
| 5,000 | ₹6,00,000 | ₹10,502 | **₹5,89,498** | **98%** |
| 7,500 | ₹7,75,000 | ₹11,202 | **₹7,63,798** | **99%** |
| 10,000 | ₹12,00,000 | ₹14,052* | **₹11,85,948** | **99%** |

\*10k opex includes **CCX33** upgrade (+₹2,850/mo) and OpenAI ~$60.

### 9.3 Conservative case (no ITC, +18% IGST on imports, higher AI)

At **5,000 users**, Phase 2:

| | INR/mo |
|---|--------|
| Gross revenue | 6,00,000 |
| Opex (incl. IGST, no ITC) | ~12,200 |
| **Net profit** | **~₹5,87,800** |
| **Margin** | **~98%** |

### 9.4 One-time costs in first 12 months (cash, not monthly)

| Item | INR (approx.) |
|------|----------------|
| Google Play registration | 2,125 |
| Apple Developer (year 1) | 8,415 |
| **Store fees year 1** | **~₹10,540** |
| Migration overlap (once at 5k) | 400 |
| **Total one-time (stores + migration)** | **~₹10,940** |

Amortized over year 1: **~₹911/mo** — already included in tables as **₹880/mo**.

### 9.5 Break-even (Phase 1, CPX41)

| | |
|---|---|
| Monthly opex (0 customers, ITC) | **~₹6,764** |
| Revenue per paying company (Professional) | **₹12,000** |
| **Break-even** | **1 paying tenant** (covers infra; ignores your time & support) |

---

## 10. Summary timeline

```text
MONTH 0–3 (no paying customers)
  Dev: local Docker · Demo: Vercel ₹0
  Cash burn: ~₹0–1,700/mo (Vercel Pro optional)

LAUNCH → 5,000 USERS (Phase 1)
  Prod: Hetzner CPX41 (~₹4,400/mo infra) + OpenAI + misc + app amort
  ClickHouse: OFF · Audit in PostgreSQL
  @ 1,000 users: ~₹1.12L profit/mo on ₹1.2L revenue (93% margin)
  @ 5,000 users: ~₹5.9L profit/mo on ₹6L revenue (98% margin)

~5,000 USERS — MIGRATION WEEKEND
  Provision CCX23 · pg_dump/restore · DNS cutover
  One-time cash: ~₹400–10,900 (overlap + stores if not yet paid)

5,000+ USERS (Phase 2)
  Prod: Hetzner CCX23 (~₹3,500/mo infra) — predictable CPU
  Optional: ClickHouse ON
  @ 10,000 users: ~₹11.9L profit/mo on ₹12L revenue
```

---

## 11. Checklists

### Phase 1 go-live (CPX41)

- [ ] `CLICKHOUSE_ENABLED=False`  
- [ ] `E2EE_ENABLED=True`, `REDIS_ALLOW=True`, `ALLOW_S3=True`  
- [ ] Vercel for marketing; `app.` subdomain → VPS  
- [ ] OpenAI monthly hard limit  
- [ ] Hetzner backups enabled  

### Phase 2 cutover (CCX23)

- [ ] Migration §4 completed  
- [ ] Old CPX41 **deleted**  
- [ ] Consider `CLICKHOUSE_ENABLED=true` if audit volume high  
- [ ] Review `PRODUCTION.md` §11 scaling (ALB, read replicas at 10k+)  

### Mobile release

- [ ] §6 store fees paid  
- [ ] Permissions & privacy policy for HR data  
- [ ] Demo credentials for store reviewers  

---

## 12. Disclaimer

Estimates only — not tax, legal, or investment advice. Hetzner prices increased **~30–35% in April 2026**. User counts ≠ concurrent users. **Lifetime free** promo tenants reduce revenue. Confirm GST with a chartered accountant. Mobile apps require separate security review for employee PII.

**Files:** [`PRODUCTION.md`](../PRODUCTION.md) · [`README.md`](../README.md)
