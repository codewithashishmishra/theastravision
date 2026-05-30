# Resets local PostgreSQL superuser password to "password" for AastraaHR dev (.env.example).
# Requires Administrator (edits pg_hba.conf under Program Files).
#Usage: Right-click PowerShell -> Run as Administrator, then:
#  Set-ExecutionPolicy -Scope Process Bypass -Force
#  & "c:\theastravision\apps\api\scripts\reset-native-postgres-dev-password.ps1"

#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$dataDir = "C:\Program Files\PostgreSQL\18\data"
$hbaPath = Join-Path $dataDir "pg_hba.conf"
$devPassword = "password"
$trustMarker = "# AastraaHR dev trust (temporary)"

if (-not (Test-Path $hbaPath)) {
    Write-Error "pg_hba.conf not found at $hbaPath. Adjust paths for your PostgreSQL version."
}

function Reload-PostgresConfig {
    & (Join-Path $pgBin "pg_ctl.exe") reload -D $dataDir
    if ($LASTEXITCODE -ne 0) {
        Restart-Service postgresql-x64-18
        Start-Sleep -Seconds 4
    }
}

$backup = "$hbaPath.bak.aastraahr"
if (-not (Test-Path $backup)) {
    Copy-Item $hbaPath $backup -Force
    Write-Host "Backed up pg_hba.conf to $backup"
}

$content = [System.IO.File]::ReadAllText($hbaPath)
if ($content -notmatch [regex]::Escape($trustMarker)) {
    $insert = @"

$trustMarker
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust

"@
    $content = $content -replace "(# TYPE  DATABASE        USER            ADDRESS                 METHOD\r?\n)", "`$1$insert"
    [System.IO.File]::WriteAllText($hbaPath, $content)
    Write-Host "Enabled temporary trust auth for localhost."
    Reload-PostgresConfig
}

$psql = Join-Path $pgBin "psql.exe"
& $psql -U postgres -h 127.0.0.1 -p 5432 -v ON_ERROR_STOP=1 -c "ALTER USER postgres WITH PASSWORD '$devPassword';"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to set postgres password."
}

# Restore original pg_hba (first matching rule must not stay on trust)
Copy-Item $backup $hbaPath -Force
Write-Host "Restored pg_hba.conf from backup."
Reload-PostgresConfig

$env:PGPASSWORD = $devPassword
& $psql -U postgres -h 127.0.0.1 -p 5432 -c "SELECT 'postgres password is now: $devPassword' AS status;"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Password verification failed."
}

Write-Host "Done. DATABASE_URL=postgres://postgres:password@localhost:5432/aastraahr_db"
