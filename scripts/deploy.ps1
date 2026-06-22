# ============================================================
# RE Expert — deploy completo (Netlify + Railway)
# ============================================================
# Uso:
#   .\scripts\deploy.ps1
#
# Requiere:
#   - netlify CLI instalado (npm i -g netlify-cli) y logueado
#   - railway CLI instalado (npm i -g @railway/cli) y logueado
#     (o RAILWAY_TOKEN seteado en el ambiente)
# ============================================================

$ErrorActionPreference = "Stop"
# Raíz del repo = carpeta padre de scripts/ (no hardcodear rutas de una máquina).
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host "`n=== 1. Netlify deploy (frontend) ===" -ForegroundColor Cyan
$netlifyOk = $false
try {
    netlify status 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        netlify deploy --prod --dir=frontend
        $netlifyOk = $true
    } else {
        Write-Host "Netlify no logueado. Corré: netlify login" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Netlify CLI no disponible: $_" -ForegroundColor Yellow
}

Write-Host "`n=== 2. Railway deploy (backend) ===" -ForegroundColor Cyan
$railwayOk = $false
try {
    railway whoami 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        # Railway ya linkado a un service
        railway up --service backend
        $railwayOk = $true
    } else {
        Write-Host "Railway no logueado. Corré: railway login" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Railway CLI no disponible: $_" -ForegroundColor Yellow
}

Write-Host "`n=== 3. Verificación post-deploy ===" -ForegroundColor Cyan
if ($railwayOk) {
    Start-Sleep -Seconds 30  # esperar que el deploy termine
    $url = "https://re-expert-production.up.railway.app/openapi.json"
    try {
        $r = Invoke-RestMethod $url -TimeoutSec 15
        $count = $r.paths.PSObject.Properties.Name.Count
        Write-Host "Backend prod: $count rutas" -ForegroundColor Green
        $sol = $r.paths.PSObject.Properties.Name | Where-Object { $_ -match "sol/agent|reminders|channels|contacts" }
        if ($sol.Count -gt 0) {
            Write-Host "  Rutas SOL agente activas:" -ForegroundColor Green
            $sol | ForEach-Object { Write-Host "   - $_" }
        } else {
            Write-Host "  ⚠ Las rutas nuevas todavía no aparecen — esperá 1 min y refrescá" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== Resumen ===" -ForegroundColor Cyan
if ($netlifyOk) { Write-Host "[OK] Netlify deployado" -ForegroundColor Green } else { Write-Host "[X] Netlify pendiente" -ForegroundColor Red }
if ($railwayOk) { Write-Host "[OK] Railway deployado" -ForegroundColor Green } else { Write-Host "[X] Railway pendiente" -ForegroundColor Red }
