#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Give WSL a STABLE localhost address for the Windows-hosted Qdrant, so it never
  breaks when the Windows DHCP IP changes.
.DESCRIPTION
  Why this is needed (WSL "mirrored" networking + podman):
    * In mirrored mode every WSL distro AND Windows share the host's LAN IP, which
      is why WSL can reach Qdrant at the Windows host IP (e.g. 192.168.200.56:6333).
      That IP is DHCP-assigned and can change across reboots/networks -> fragile.
    * hostAddressLoopback=true lets a WSL distro reach the Windows host's REAL
      loopback (127.0.0.1) services -- but podman publishes its port from inside the
      podman WSL VM on the shared LAN IP, NOT on the Windows host loopback. So
      WSL's localhost can't see podman's port directly.

  Fix: add a netsh portproxy -- a REAL Windows-host loopback listener on
  127.0.0.1:<ListenPort> that forwards to the podman relay at
  127.0.0.1:<ConnectPort>. hostAddressLoopback bridges WSL -> that real listener, so
  WSL can use http://localhost:<ListenPort> forever, with no IP dependency.

  The rule is stored in the registry and re-applied by the Windows IP Helper service
  (iphlpsvc) on every boot -- persistent, no running process. Needs admin once.

  After running this, point WSL's config at the stable address:
    uv run python setup/setup-shared-qdrant.py `
      --palace-id /mnt/d/mempalace-shared --qdrant-url http://localhost:6433
.EXAMPLE
  # from an ELEVATED PowerShell:
  pwsh -ExecutionPolicy Bypass -File setup\setup-wsl-localhost.ps1
  pwsh -ExecutionPolicy Bypass -File setup\setup-wsl-localhost.ps1 -Remove
#>
param(
  [string]$ListenAddr  = "127.0.0.1",
  [int]$ListenPort     = 6433,
  [string]$ConnectAddr = "127.0.0.1",
  [int]$ConnectPort    = 6333,
  [switch]$Remove
)

# portproxy is managed by the IP Helper service and requires admin to change.
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Write-Warning "This needs admin (netsh portproxy). Re-run from an elevated PowerShell:"
  Write-Host    "  Start-Process pwsh -Verb RunAs   # then re-run this script"
  exit 1
}

# Idempotent: drop any existing rule for this listen endpoint first.
& netsh interface portproxy delete v4tov4 listenaddress=$ListenAddr listenport=$ListenPort 2>$null | Out-Null

if ($Remove) {
  Write-Host "Removed portproxy ${ListenAddr}:${ListenPort}."
  & netsh interface portproxy show all
  exit 0
}

& netsh interface portproxy add v4tov4 `
    listenaddress=$ListenAddr listenport=$ListenPort `
    connectaddress=$ConnectAddr connectport=$ConnectPort
Write-Host "Added portproxy ${ListenAddr}:${ListenPort} -> ${ConnectAddr}:${ConnectPort}"
Write-Host ""
& netsh interface portproxy show all
Write-Host ""
Write-Host "Verify from WSL:  curl -sf http://localhost:${ListenPort}/readyz"
Write-Host "Point WSL config: uv run python setup/setup-shared-qdrant.py --palace-id /mnt/d/mempalace-shared --qdrant-url http://localhost:${ListenPort}"
Write-Host ""
Write-Host "This rule persists across reboots (re-applied by the IP Helper service)."
