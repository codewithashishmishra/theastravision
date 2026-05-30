# Apply migrations and seed platform + demo data (same sync as start_services.py step 2).
# Copy apps/api/.env.example to apps/api/.env — set DATABASE_URL + PLATFORM_SMTP_PASSWORD.
# SMTP/IMAP hosts in .env overwrite encrypted DB on each seed_env_config run.
# Safe to re-run: seed_dev may error if demo data already exists.
Set-Location $PSScriptRoot\..
$python = Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

Write-Host "Running migrations..." -ForegroundColor Cyan
& $python manage.py migrate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Seeding env config (SMTP/IMAP, utilization, debug)..." -ForegroundColor Cyan
& $python manage.py seed_env_config
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Seeding demo tenants and sample data..." -ForegroundColor Cyan
& $python manage.py seed_dev
exit $LASTEXITCODE
