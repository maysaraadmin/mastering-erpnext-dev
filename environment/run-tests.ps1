# ============================================================
# run-tests.ps1
# Runs the book's test suite inside the frappe_docker container.
#
# Usage (run from repo root in PowerShell):
#   .\environment\run-tests.ps1
#   .\environment\run-tests.ps1 -App asset_management_app
#   .\environment\run-tests.ps1 -SiteName frontend -Container frappe_docker-backend-1
# ============================================================

param(
    [string]$SiteName  = "frontend",
    [string]$Container = "frappe_docker-backend-1",
    [string]$App       = ""
)

$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "==> Site: $SiteName  |  Container: $Container"
Write-Host ""

# ── Sync latest app files into the container ───────────────
Write-Host "==> Syncing app files..."

$Apps = @{
    "asset_management_app"    = "projects\asset_management\asset_management_app"
    "production_planning_app" = "projects\production_planning\production_planning_app"
    "vendor_portal_app"       = "projects\vendor_portal\vendor_portal_app"
}

foreach ($AppName in $Apps.Keys) {
    $Src = Join-Path $RepoRoot $Apps[$AppName]
    docker cp "$Src\." "${Container}:/home/frappe/frappe-bench/apps/$AppName/"
}

Write-Host ""

# ── Run tests ──────────────────────────────────────────────
if ($App -ne "") {
    Write-Host "==> Running tests for: $App"
    docker exec $Container bash -c "cd /home/frappe/frappe-bench && bench --site $SiteName run-tests --app $App --verbose 2>&1"
} else {
    Write-Host "==> Running tests for all book apps..."
    foreach ($AppName in $Apps.Keys) {
        Write-Host ""
        Write-Host "── $AppName ──────────────────────────────────────" -ForegroundColor Cyan
        docker exec $Container bash -c "cd /home/frappe/frappe-bench && bench --site $SiteName run-tests --app $AppName 2>&1 | tail -10"
    }
}

Write-Host ""
Write-Host "Test run complete." -ForegroundColor Green
