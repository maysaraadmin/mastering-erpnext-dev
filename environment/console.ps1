# ============================================================
# console.ps1
# Opens a bench console inside the frappe_docker container.
#
# Usage:
#   .\environment\console.ps1
#   .\environment\console.ps1 -SiteName frontend -Container frappe_docker-backend-1
# ============================================================

param(
    [string]$SiteName  = "frontend",
    [string]$Container = "frappe_docker-backend-1"
)

Write-Host "Opening bench console on site: $SiteName"
Write-Host "Type 'exit' or Ctrl+D to quit."
Write-Host ""

docker exec -it $Container bash -c "cd /home/frappe/frappe-bench && bench --site $SiteName console"
