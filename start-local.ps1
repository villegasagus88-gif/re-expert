# ============================================================
# RE Expert — arranque local
# ============================================================
# Lo que hace este script:
#   1. Desetea env vars vacías que pisan al .env.
#   2. Verifica conexión a Supabase.
#   3. Corre la migración 0011 (crea reminders + user_channels).
#   4. Sube tu user a plan='pro' para poder probar SOL agente.
#   5. Levanta backend en :8000 y frontend en :5173.
#
# Uso:
#   PowerShell → cd al repo → .\start-local.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$root = "C:\Users\matia\OneDrive\Escritorio\re-expert"
$venvPy = "$root\backend\.venv\Scripts\python.exe"

# Pisar las env vars vacías que setea Claude Code
Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:JWT_SECRET -ErrorAction SilentlyContinue
Remove-Item Env:SUPABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:SUPABASE_SERVICE_ROLE_KEY -ErrorAction SilentlyContinue

Write-Host "`n=== 1. Test DB connection ===" -ForegroundColor Cyan
Push-Location "$root\backend"
$check = @"
import asyncio
from config.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def check():
    url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    e = create_async_engine(url, connect_args={'statement_cache_size':0,'prepared_statement_cache_size':0})
    async with e.connect() as c:
        r = await c.execute(text('SELECT version()'))
        print('DB OK:', list(r)[0][0][:80])
asyncio.run(check())
"@
& $venvPy -c $check
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Conexión a DB falló. Revisá DATABASE_URL en backend\.env" -ForegroundColor Red; Pop-Location; exit 1 }

Write-Host "`n=== 2. Alembic migrations (upgrade head) ===" -ForegroundColor Cyan
& $venvPy -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { Write-Host "⚠ Migración falló (revisar logs arriba)." -ForegroundColor Yellow; Pop-Location; exit 1 }

Write-Host "`n=== 3. Setting your user to plan='pro' ===" -ForegroundColor Cyan
$promote = @"
import asyncio, sys
from config.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
EMAIL = 'matiasparola100@gmail.com'
async def go():
    url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    e = create_async_engine(url, connect_args={'statement_cache_size':0,'prepared_statement_cache_size':0})
    async with e.begin() as c:
        r = await c.execute(text(\"SELECT id, plan FROM profiles WHERE email = :e\"), {'e': EMAIL})
        row = r.first()
        if not row:
            print(f'NO USER con email={EMAIL}; registrate primero en la app y volve a correr esto.')
            return
        await c.execute(text(\"UPDATE profiles SET plan='pro', onboarding_completed=true WHERE email=:e\"), {'e': EMAIL})
        print(f'OK: user {EMAIL} ahora es plan=pro')
asyncio.run(go())
"@
& $venvPy -c $promote

Write-Host "`n=== 4. Levantar backend (:8000) y frontend (:5173) ===" -ForegroundColor Cyan
Pop-Location

Write-Host "`nAbriendo dos ventanas de PowerShell con backend y frontend..." -ForegroundColor Green

# Backend en una ventana nueva
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Remove-Item Env:ANTHROPIC_API_KEY,Env:DATABASE_URL,Env:JWT_SECRET,Env:SUPABASE_URL,Env:SUPABASE_SERVICE_ROLE_KEY -ErrorAction SilentlyContinue; cd '$root\backend'; & '$venvPy' -m uvicorn main:app --reload --port 8000 --host 127.0.0.1"
)

Start-Sleep -Seconds 2

# Frontend en otra ventana
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root'; npx http-server frontend -p 5173 -c-1 --cors"
)

Write-Host "`n✓ Listo. Abrí en el navegador: http://localhost:5173" -ForegroundColor Green
Write-Host "  Backend API:                    http://localhost:8000/openapi.json" -ForegroundColor Gray
Write-Host "  Backend health:                 http://localhost:8000/health" -ForegroundColor Gray
