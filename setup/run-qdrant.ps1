#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Run a local Qdrant via podman (Windows side) as a shared MemPalace backend.
.DESCRIPTION
  Idempotent: starts the podman machine if needed, (re)starts the container if it
  already exists, otherwise creates it with a host-folder bind mount for the data,
  then waits until Qdrant answers /readyz. Data persists at -DataDir on the host.
  Use -Recreate to replace an existing container (e.g. to switch its data mount).
.EXAMPLE
  ./run-qdrant.ps1
  ./run-qdrant.ps1 -DataDir D:\qdrant-data
  ./run-qdrant.ps1 -Recreate            # remove + recreate to apply a new -DataDir
#>
param(
  [string]$Name     = "qdrant",
  [int]$RestPort    = 6333,
  [int]$GrpcPort    = 6334,
  [string]$DataDir  = "D:\qdrant-data",
  [string]$Image    = "docker.io/qdrant/qdrant:latest",
  [switch]$Recreate
)

# --- ensure the podman machine (rootless podman on Windows runs in a VM) ---
$machines = (& podman machine list -q 2>$null)
if (-not $machines) {
  Write-Host "No podman machine found; initializing one (first run, may take a few min)..."
  & podman machine init
}
# 'start' errors harmlessly if it's already running — ignore and continue.
& podman machine start 2>$null | Out-Null

# --- create or (re)start the container ---
$exists = ((& podman ps -a --filter "name=^$Name$" --format '{{.Names}}') -eq $Name)
if ($exists -and $Recreate) {
  Write-Host "Removing existing container '$Name' to recreate with -DataDir=$DataDir ..."
  & podman rm -f $Name | Out-Null
  $exists = $false
}
if ($exists) {
  Write-Host "Container '$Name' exists - starting it. (use -Recreate to apply a new -DataDir)"
  & podman start $Name | Out-Null
} else {
  if (-not (Test-Path $DataDir)) {
    Write-Host "Creating data directory $DataDir ..."
    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
  }
  Write-Host "Creating container '$Name' from $Image (data -> $DataDir) ..."
  & podman run -d --name $Name `
    -p "${RestPort}:6333" -p "${GrpcPort}:6334" `
    -v "${DataDir}:/qdrant/storage" `
    --restart unless-stopped `
    $Image | Out-Null
}

# --- wait for readiness ---
$url = "http://localhost:$RestPort"
Write-Host "Waiting for Qdrant at $url ..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing "$url/readyz" -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $ready = $true; break }
  } catch { Start-Sleep -Seconds 1 }
}

if ($ready) {
  Write-Host "Qdrant is READY."
  Write-Host "  REST:      $url"
  Write-Host "  Dashboard: $url/dashboard"
  Write-Host "  Data dir:  $DataDir  (persists on the host)"
  Write-Host ""
  Write-Host "Next: run setup\mempalace-env.ps1 (Windows) and source setup/mempalace-env.fish (WSL)."
  Write-Host "If WSL cannot reach $url, enable WSL mirrored networking (see the setup notes)."
} else {
  Write-Warning "Qdrant did not become ready in time. Check: podman logs $Name"
  exit 1
}
