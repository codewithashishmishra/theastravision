# WFH Tracking Module

## API base paths

- HRMS: `/api/v1/wfh/`
- Desktop tracker: `/api/v1/tracker/`

## Environment

| Variable | Description |
|----------|-------------|
| `ALLOW_S3` | `False` → local `media/tracker/`; `True` → Django default storage (S3) |
| `TRACKER_MASTER_KEY` | Server master key for wrapping session data keys and at-rest blobs (falls back to `SECRET_KEY` hash) |
| `TRACKER_ENCRYPTION_KEY` | Legacy Fernet key (pre-GCM screenshots only) |
| `WFH_TRACKING_ENABLED` | Feature flag (default True) |
| `REDIS_URL` | Celery broker |

## Seed

```bash
python manage.py seed_wfh
```

## Desktop app

```bash
cd apps/tracker-desktop
pip install -r requirements.txt
python main.py
```

Set `AASTRAA_API_URL=http://127.0.0.1:8000/api/v1` if needed.

### Browser login (recommended)

The desktop app opens **Sign in with HRMS** → your browser → `http://127.0.0.1:3000/login` → after success, redirects back to the app with JWT tokens.

Requires **admin-web** on port 3000 and **API** on port 8000.

Env: `AASTRAA_WEB_LOGIN_URL=http://127.0.0.1:3000/login`

## Celery

```bash
celery -A config worker -l info
celery -A config beat -l info
```

## Packaging (PyInstaller)

```bash
cd apps/tracker-desktop
pyinstaller --onefile --windowed --name AastraaTracker main.py
```

See `.github/workflows/tracker-desktop.yml` for CI matrix builds.

## Encryption (AES-256-GCM)

| Layer | What |
|-------|------|
| In transit | HTTPS/TLS for all API calls |
| Client → server | Screenshots encrypted with per-session `encryption_key` (returned on login/exchange/refresh); wire format `AASTG1` + 12-byte nonce + ciphertext |
| At rest (disk/DB) | Server wraps stored blobs again with `TRACKER_MASTER_KEY` |
| Local desktop | Keyring holds JWT + base64 session key; offline outbox encrypted with HKDF derived from refresh token |

Re-sign in after deploy if `encryption_key` is missing from keyring. Production must set a strong `TRACKER_MASTER_KEY` (32+ random bytes as env string).

**Note:** A determined attacker with the installed app can still extract keys from memory or the keyring. GCM protects data in transit and at rest on the server; use TLS, code signing, and OS disk encryption for defense in depth.

## Desktop tracker behavior

- Opens **fullscreen** after login with split UI: controls (left) and live activity table (right).
- **Auto-pause** after 60 seconds with no keyboard/mouse input; user resumes manually.
- **Spoof detection** (flag-only): repeated same key, scroll-only activity, synthetic mouse intervals — pattern metadata only, no key content stored.
- **Graceful shutdown**: Stop Work, window close, or logout syncs `POST /tracker/session/report/` then `POST /tracker/session/stop/` before exit.

## Security checklist

- Consent required before session start
- Visible UI banner (never tray-only in v1)
- No keylogging — activity uses timestamps and key codes for pattern checks only
- Screenshots: AES-256-GCM client-side, master-key wrap server-side
- RBAC on HRMS screenshot views
- Retention purge via `purge_expired_screenshots` task
