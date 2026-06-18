#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Script de instalación automática para Saludsa Control Actas TI
.DESCRIPTION
    Este script instala automáticamente:
    - Python (si no está instalado)
    - Entorno virtual Python
    - Dependencias del backend (Flask)
    - Node.js (si no está instalado)
    - Dependencias del frontend (React)
    - Configura las variables de entorno
.NOTES
    Versión: 1.0
    Autor: David Leandro Correa Beltran
    Requiere: PowerShell 5.1 o superior
#>

[CmdletBinding()]
param()

# Configuración
$PythonVersion = "3.12.3"
$NodeVersion = "20.12.2"
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

# Colores para output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($Message) {
    Write-ColorOutput Green "[✓] $Message"
}

function Write-Info($Message) {
    Write-ColorOutput Cyan "[ℹ] $Message"
}

function Write-Warning($Message) {
    Write-ColorOutput Yellow "[!] $Message"
}

function Write-Error($Message) {
    Write-ColorOutput Red "[✗] $Message"
}

function Write-Step($Number, $Message) {
    Write-ColorOutput Magenta ""
    Write-ColorOutput Magenta "========================================"
    Write-ColorOutput Magenta "PASO $Number`: $Message"
    Write-ColorOutput Magenta "========================================"
}

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

function Test-CommandExists($Command) {
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

function Get-PythonVersion() {
    try {
        $version = python --version 2>&1
        if ($version -match "Python (\d+\.\d+)" ) {
            return [version]$matches[1]
        }
    } catch {
        return $null
    }
    return $null
}

function Get-NodeVersion() {
    try {
        $version = node --version
        if ($version -match "v(\d+\.\d+)" ) {
            return [version]$matches[1]
        }
    } catch {
        return $null
    }
    return $null
}

function Install-Python() {
    Write-Info "Descargando Python $PythonVersion..."
    
    $url = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
    $output = "$env:TEMP\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
        Write-Info "Instalando Python (esto puede tardar unos minutos)..."
        
        # Instalación silenciosa con agregar al PATH
        $process = Start-Process -FilePath $output -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Success "Python $PythonVersion instalado correctamente"
            # Refrescar PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            return $true
        } else {
            Write-Error "Error al instalar Python (Exit code: $($process.ExitCode))"
            return $false
        }
    } catch {
        Write-Error "Error descargando/instalando Python: $_"
        return $false
    } finally {
        if (Test-Path $output) {
            Remove-Item $output -Force
        }
    }
}

function Install-NodeJS() {
    Write-Info "Descargando Node.js $NodeVersion..."
    
    $url = "https://nodejs.org/dist/v$NodeVersion/node-v$NodeVersion-x64.msi"
    $output = "$env:TEMP\nodejs-installer.msi"
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
        Write-Info "Instalando Node.js (esto puede tardar unos minutos)..."
        
        $process = Start-Process -FilePath "msiexec.exe" -ArgumentList "/i", $output, "/quiet", "/norestart" -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Success "Node.js $NodeVersion instalado correctamente"
            # Refrescar PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            return $true
        } else {
            Write-Error "Error al instalar Node.js (Exit code: $($process.ExitCode))"
            return $false
        }
    } catch {
        Write-Error "Error descargando/instalando Node.js: $_"
        return $false
    } finally {
        if (Test-Path $output) {
            Remove-Item $output -Force
        }
    }
}

# ============================================
# SCRIPT PRINCIPAL
# ============================================

Clear-Host
Write-ColorOutput Magenta @"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🚀 INSTALADOR - SALUDSA DEMO APP                  ║
║                                                          ║
║  Este script instalará automáticamente todo lo           ║
║  necesario para ejecutar la aplicación.                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"@

Write-Info "Directorio del proyecto: $ProjectRoot"

# Verificar si estamos en la carpeta correcta
if (-not (Test-Path "$ProjectRoot\client-react") -or -not (Test-Path "$ProjectRoot\server-flask")) {
    Write-Error "No se encontraron las carpetas 'client-react' y 'server-flask'"
    Write-Error "Por favor ejecuta este script desde la raíz del proyecto"
    exit 1
}

# ============================================
# PASO 1: Verificar/Instalar Python
# ============================================
Write-Step "1" "Verificando Python"

$pythonInstalled = $false
$pythonVersion = Get-PythonVersion

if ($pythonVersion) {
    Write-Success "Python encontrado: versión $pythonVersion"
    if ($pythonVersion -ge [version]"3.10") {
        $pythonInstalled = $true
    } else {
        Write-Warning "Se requiere Python 3.10 o superior"
    }
} else {
    Write-Warning "Python no encontrado"
}

if (-not $pythonInstalled) {
    Write-Info "Python no está instalado o es una versión antigua"
    $installPython = Read-Host "¿Deseas instalar Python $PythonVersion automáticamente? (S/N)"
    
    if ($installPython -eq 'S' -or $installPython -eq 's') {
        if (-not (Install-Python)) {
            Write-Error "No se pudo instalar Python automáticamente"
            Write-Info "Por favor instala Python manualmente desde: https://python.org"
            exit 1
        }
    } else {
        Write-Error "Python es requerido para continuar"
        exit 1
    }
}

# ============================================
# PASO 2: Crear entorno virtual
# ============================================
Write-Step "2" "Configurando Entorno Virtual Python"

Set-Location "$ProjectRoot\server-flask"

if (Test-Path "venv") {
    Write-Warning "El entorno virtual ya existe"
    $recreate = Read-Host "¿Deseas recrearlo? (S/N)"
    if ($recreate -eq 'S' -or $recreate -eq 's') {
        Remove-Item -Recurse -Force "venv"
        Write-Info "Entorno virtual anterior eliminado"
    }
}

if (-not (Test-Path "venv")) {
    Write-Info "Creando entorno virtual..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error creando entorno virtual"
        exit 1
    }
    Write-Success "Entorno virtual creado"
}

# ============================================
# PASO 3: Instalar dependencias Python
# ============================================
Write-Step "3" "Instalando Dependencias del Backend"

Write-Info "Activando entorno virtual..."
$venvPip = "$ProjectRoot\server-flask\venv\Scripts\pip.exe"

Write-Info "Instalando dependencias desde requirements.txt..."
& $venvPip install --upgrade pip
& $venvPip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error instalando dependencias Python"
    exit 1
}
Write-Success "Dependencias del backend instaladas"

# ============================================
# PASO 4: Configurar variables de entorno
# ============================================
Write-Step "4" "Configurando Variables de Entorno"

# NUNCA sobrescribir un .env existente - siempre preservar configuración del usuario
if (Test-Path ".env") {
    Write-Success "Archivo .env ya existe - preservando configuración existente"
    Write-Info "Si necesitas reconfigurar, edita manualmente el archivo .env"
} else {
    # Crear .env vacío o desde template - SIN CREDENCIALES REALES
    $envTemplate = @"
# ==========================================
# CONFIGURACION FLASK
# ==========================================
PORT=5000
FLASK_DEBUG=True
FLASK_ENV=development

# ==========================================
# CONFIGURACION LDAP - REQUERIDO
# ==========================================
# Configura estas variables con tus credenciales LDAP reales:
# LDAP_SERVER=ldap://tu-servidor-ldap
# LDAP_USER=dominio\usuario
# LDAP_PASSWORD=tu-contraseña-segura
# LDAP_BASE_DN=dc=dominio,dc=com
# LDAP_SEARCH_LIMIT=20
"@
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Success "Archivo .env creado desde .env.example"
    } else {
        $envTemplate | Out-File -FilePath ".env" -Encoding utf8
        Write-Success "Archivo .env creado con template base"
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  ATENCION: CONFIGURACION REQUERIDA    " -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "El archivo .env ha sido creado pero necesita configuracion." -ForegroundColor White
    Write-Host ""
    Write-Host "DEBES editar el archivo y configurar tus credenciales LDAP:" -ForegroundColor White
    Write-Host "   1. Abre: server-flask\.env" -ForegroundColor Cyan
    Write-Host "   2. Configura: LDAP_SERVER, LDAP_USER, LDAP_PASSWORD, LDAP_BASE_DN" -ForegroundColor Cyan
    Write-Host "   3. Guarda el archivo" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Sin estas credenciales, la busqueda de usuarios no funcionara." -ForegroundColor Red
}

# ============================================
# PASO 5: Verificar/Instalar Node.js
# ============================================
Write-Step "5" "Verificando Node.js"

Set-Location $ProjectRoot

$nodeInstalled = $false
$nodeVersion = Get-NodeVersion

if ($nodeVersion) {
    Write-Success "Node.js encontrado: versión $nodeVersion"
    if ($nodeVersion -ge [version]"18.0") {
        $nodeInstalled = $true
    } else {
        Write-Warning "Se requiere Node.js 18 o superior"
    }
} else {
    Write-Warning "Node.js no encontrado"
}

if (-not $nodeInstalled) {
    Write-Info "Node.js no está instalado o es una versión antigua"
    $installNode = Read-Host "¿Deseas instalar Node.js $NodeVersion automáticamente? (S/N)"
    
    if ($installNode -eq 'S' -or $installNode -eq 's') {
        if (-not (Install-NodeJS)) {
            Write-Error "No se pudo instalar Node.js automáticamente"
            Write-Info "Por favor instala Node.js manualmente desde: https://nodejs.org"
            exit 1
        }
    } else {
        Write-Error "Node.js es requerido para continuar"
        exit 1
    }
}

# ============================================
# PASO 6: Instalar dependencias Node.js
# ============================================
Write-Step "6" "Instalando Dependencias del Frontend"

Set-Location "$ProjectRoot\client-react"

Write-Info "Ejecutando npm install (esto puede tardar varios minutos)..."
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error instalando dependencias npm"
    exit 1
}
Write-Success "Dependencias del frontend instaladas"

# ============================================
# PASO 7: Crear scripts de inicio
# ============================================
Write-Step "7" "Creando Scripts de Inicio"

Set-Location $ProjectRoot

# Script para iniciar backend
$startBackend = @"
@echo off
echo Iniciando Backend Flask...
cd /d "%~dp0server-flask"
call venv\Scripts\activate
python main.py
pause
"@
$startBackend | Out-File -FilePath "start-backend.bat" -Encoding utf8

# Script para iniciar frontend
$startFrontend = @"
@echo off
echo Iniciando Frontend React...
cd /d "%~dp0client-react"
npm run dev
pause
"@
$startFrontend | Out-File -FilePath "start-frontend.bat" -Encoding utf8

# Script para iniciar ambos (usando start para ventanas separadas)
$startBoth = @"
@echo off
echo ==========================================
echo   INICIANDO SALUDSA DEMO APP
echo ==========================================
echo.
echo Se abriran dos ventanas:
echo - Backend Flask (puerto 5000)
echo - Frontend React (puerto 5173)
echo.
pause

start "Backend Flask" cmd /c "cd /d "%~dp0server-flask" && call venv\Scripts\activate && python main.py"
timeout /t 3 /nobreak >nul
start "Frontend React" cmd /c "cd /d "%~dp0client-react" && npm run dev"

echo.
echo Aplicacion iniciada!
echo - Backend: http://localhost:5000
echo - Frontend: http://localhost:5173
echo.
pause
"@
$startBoth | Out-File -FilePath "start-app.bat" -Encoding utf8

Write-Success "Scripts de inicio creados"

# ============================================
# RESUMEN FINAL
# ============================================
Write-ColorOutput Magenta @"

╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        ✅ INSTALACIÓN COMPLETADA                        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

📋 RESUMEN:
"@

Write-Success "Python configurado correctamente"
Write-Success "Entorno virtual creado en server-flask\venv"
Write-Success "Dependencias del backend instaladas"
Write-Success "Node.js configurado correctamente"
Write-Success "Dependencias del frontend instaladas"
Write-Success "Scripts de inicio creados"

# Verificar si .env ya existía antes de la instalación
$envExistedBefore = Test-Path "$ProjectRoot\server-flask\.env"

Write-Host ""
if (-not $envExistedBefore) {
    Write-Host "IMPORTANTE:" -ForegroundColor Yellow
    Write-Host "   El archivo .env fue creado nuevo. DEBES configurar tus credenciales" -ForegroundColor White
    Write-Host "   LDAP en server-flask\.env antes de iniciar la aplicación." -ForegroundColor White
} else {
    Write-Host "CONFIGURACION PRESERVADA:" -ForegroundColor Green
    Write-Host "   Se mantuvo tu archivo .env existente con la configuracion anterior." -ForegroundColor White
    Write-Host "   No se requieren cambios si ya estaba configurado." -ForegroundColor White
}
Write-Host ""
Write-Host "PARA INICIAR LA APLICACION:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Opcion 1 - Doble clic en: start-app.bat" -ForegroundColor White
Write-Host "   (Abre backend y frontend automaticamente)" -ForegroundColor Gray
Write-Host ""
Write-Host "   Opcion 2 - Ventanas separadas:" -ForegroundColor White
Write-Host "   - start-backend.bat  (Terminal 1)" -ForegroundColor Gray
Write-Host "   - start-frontend.bat (Terminal 2)" -ForegroundColor Gray
Write-Host ""
Write-Host "   Opcion 3 - Manual:" -ForegroundColor White
Write-Host "   Backend:  cd server-flask && venv\Scripts\activate && python main.py" -ForegroundColor Gray
Write-Host "   Frontend: cd client-react && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "ACCESO:" -ForegroundColor Cyan
Write-Host "   - Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   - Backend API: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "DOCUMENTACION:" -ForegroundColor Cyan
Write-Host "   - Guia de configuracion: server-flask\docs\CONFIG_GUIDE.md" -ForegroundColor White

# Solo ofrecer abrir .env si fue creado nuevo (no si existía)
if (-not (Test-Path "$ProjectRoot\server-flask\.env" -PathType Leaf) -or 
    (Get-Item "$ProjectRoot\server-flask\.env").CreationTime -gt (Get-Date).AddMinutes(-5)) {
    $openEnv = Read-Host "¿Deseas abrir el archivo .env para configurar las credenciales ahora? (S/N)"
    if ($openEnv -eq 'S' -or $openEnv -eq 's') {
        notepad "$ProjectRoot\server-flask\.env"
    }
}

Write-ColorOutput Green "¡Instalación completada! 🎉"
