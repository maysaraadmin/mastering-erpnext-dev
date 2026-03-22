# ============================================================
# install-book-apps.ps1
# Installs all three book project apps into a running
# frappe_docker bench container.
#
# Usage (run from repo root in PowerShell):
#   .\environment\install-book-apps.ps1
#   .\environment\install-book-apps.ps1 -SiteName mysite -Container frappe_docker-backend-1
# ============================================================

param(
    [string]$SiteName  = "frontend",
    [string]$Container = "frappe_docker-backend-1"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "==> Repo root  : $RepoRoot"
Write-Host "==> Site name  : $SiteName"
Write-Host "==> Container  : $Container"
Write-Host ""

# ── 1. Copy app source into the container ──────────────────
Write-Host "==> Copying app source into container..."

$Apps = @{
    "asset_management_app"    = "projects\asset_management\asset_management_app"
    "production_planning_app" = "projects\production_planning\production_planning_app"
    "vendor_portal_app"       = "projects\vendor_portal\vendor_portal_app"
}

foreach ($App in $Apps.Keys) {
    $Src = Join-Path $RepoRoot $Apps[$App]
    Write-Host "  Copying $App..."
    docker cp "$Src" "${Container}:/home/frappe/frappe-bench/apps/$App"
}

# ── 2. pip-install each app (editable) ─────────────────────
Write-Host ""
Write-Host "==> Installing apps into bench Python environment..."

foreach ($App in $Apps.Keys) {
    Write-Host "  pip install -e $App"
    docker exec $Container bash -c "cd /home/frappe/frappe-bench && ./env/bin/pip install -e apps/$App -q"
}

# ── 3. Add apps to apps.txt ────────────────────────────────
Write-Host ""
Write-Host "==> Registering apps in bench..."

foreach ($App in $Apps.Keys) {
    docker exec $Container bash -c "grep -qxF '$App' /home/frappe/frappe-bench/sites/apps.txt || echo '$App' >> /home/frappe/frappe-bench/sites/apps.txt"
}

# ── 4. Install apps on the site ────────────────────────────
Write-Host ""
Write-Host "==> Installing apps on site: $SiteName"

foreach ($App in $Apps.Keys) {
    Write-Host "  bench --site $SiteName install-app $App"
    docker exec $Container bash -c "cd /home/frappe/frappe-bench && bench --site $SiteName install-app $App"
}

# ── 5. Run migrations ──────────────────────────────────────
Write-Host ""
Write-Host "==> Running migrations..."
docker exec $Container bash -c "cd /home/frappe/frappe-bench && bench --site $SiteName migrate"

# ── 6. Clear cache ─────────────────────────────────────────
Write-Host ""
Write-Host "==> Clearing cache..."
docker exec $Container bash -c "cd /home/frappe/frappe-bench && bench --site $SiteName clear-cache"

Write-Host ""
Write-Host "All three apps installed successfully on site: $SiteName" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  Open ERPNext: http://localhost:8080"
Write-Host "  Run tests:    .\environment\run-tests.ps1"
