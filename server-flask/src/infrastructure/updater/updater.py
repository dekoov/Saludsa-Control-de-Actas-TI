"""
Núcleo del sistema de auto-actualización.

Flujo general:
1. check_for_updates(): descarga version.json desde la URL pública del último
   release de GitHub (sin usar la API → sin rate limits) y compara versiones
   con packaging.version.
2. request_apply_update(): lanza en segundo plano la descarga del instalador a
   %TEMP% con progreso y verificación SHA-256.
3. Al terminar la descarga se escribe y lanza updater.ps1 desacoplado
   (DETACHED_PROCESS) y la app se cierra 1.5s después; el script espera al
   cierre, instala en modo /VERYSILENT y reabre la aplicación.

El chequeo programado (scheduler) solo se activa en la app compilada
(sys.frozen). En desarrollo local nunca se ofrecen actualizaciones.
"""

import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timezone

from packaging.version import InvalidVersion, Version

from src.core.version import CURRENT_VERSION

logger = logging.getLogger(__name__)

# URL web estable del manifiesto del último release (NO usa la API de GitHub)
MANIFEST_URL = "https://github.com/dekoov/Saludsa-Control-de-Actas-TI/releases/latest/download/version.json"
INSTALLER_NAME = "SaludsaActas_Setup.exe"
INSTALLER_FALLBACK_URL = f"https://github.com/dekoov/Saludsa-Control-de-Actas-TI/releases/latest/download/{INSTALLER_NAME}"

CHECK_TIMEOUT = 10          # segundos para el chequeo de versión
DOWNLOAD_TIMEOUT = 60       # segundos por lectura durante la descarga
CHECK_INTERVAL = 4 * 3600   # 4 horas
CHECK_START_DELAY = 15      # primer chequeo a los 15 segundos del arranque
SHUTDOWN_DELAY = 1.5        # cierre de la app tras lanzar el updater

# Script de actualización totalmente parametrizado (no requiere interpolación)
UPDATER_PS1 = r"""param(
    [Parameter(Mandatory=$true)][int]$ProcessId,
    [Parameter(Mandatory=$true)][string]$InstallerPath,
    [Parameter(Mandatory=$true)][string]$AppExePath
)

$ErrorActionPreference = 'SilentlyContinue'

# 1. Esperar a que la aplicacion se cierre por completo (max. 60 s)
$elapsed = 0
while ((Get-Process -Id $ProcessId) -and ($elapsed -lt 60000)) {
    Start-Sleep -Milliseconds 500
    $elapsed += 500
}
Start-Sleep -Seconds 2

# 2. Quitar la marca de "descargado de internet" (mitiga SmartScreen)
Unblock-File -Path $InstallerPath

# 3. Ejecutar el instalador en modo totalmente silencioso
Start-Process -FilePath $InstallerPath -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait

# 4. Reabrir la aplicacion actualizada
if (Test-Path $AppExePath) {
    Start-Process -FilePath $AppExePath
}

# 5. Limpieza de temporales
Remove-Item -Path $InstallerPath -Force
Remove-Item -Path $MyInvocation.MyCommand.Path -Force
"""

# Estado en memoria del sistema de actualización
_state = {
    "update_available": False,
    "latest_version": None,
    "sha256": None,
    "download_url": None,
    "published_at": None,
    "last_check": None,
    "applying": False,
    "progress": None,   # 0-100 durante la descarga
    "stage": None,      # downloading | verifying | restarting
    "error": None,
}
_state_lock = threading.Lock()


def _update_state(**kwargs):
    with _state_lock:
        _state.update(kwargs)


def get_version_info() -> dict:
    """Retorna una copia del estado actual para exponerlo vía API."""
    with _state_lock:
        info = dict(_state)
    info["current_version"] = CURRENT_VERSION
    return info


def check_for_updates() -> bool:
    """
    Consulta el manifiesto version.json del último release oficial y determina
    si hay una versión más nueva disponible. Los errores de red son silenciosos.
    Retorna True si hay actualización disponible.
    """
    # La auto-actualización solo aplica a la app instalada/compilada
    if not getattr(sys, 'frozen', False):
        logger.debug("Chequeo de actualizaciones omitido: entorno de desarrollo.")
        return False

    try:
        request = urllib.request.Request(
            MANIFEST_URL,
            headers={"User-Agent": f"SaludsaActas/{CURRENT_VERSION}"}
        )
        with urllib.request.urlopen(request, timeout=CHECK_TIMEOUT) as response:
            manifest = json.loads(response.read().decode('utf-8'))

        remote_version = Version(str(manifest["version"]))
        current_version = Version(CURRENT_VERSION)
        available = remote_version > current_version

        _update_state(
            update_available=available,
            latest_version=str(remote_version),
            sha256=(manifest.get("sha256") or "").lower() or None,
            download_url=manifest.get("url") or INSTALLER_FALLBACK_URL,
            published_at=manifest.get("published_at"),
            last_check=datetime.now(timezone.utc).isoformat(),
        )

        if available:
            logger.info(f"Nueva versión disponible: v{remote_version} (actual: v{CURRENT_VERSION})")
        else:
            logger.info(f"La aplicación está actualizada (v{CURRENT_VERSION})")
        return available

    except (InvalidVersion, KeyError, json.JSONDecodeError) as e:
        logger.warning(f"Manifiesto de actualización inválido: {e}")
    except Exception as e:
        # Errores de red silenciosos: no deben interrumpir el uso de la app
        logger.warning(f"No se pudo comprobar actualizaciones (se reintentará luego): {e}")

    _update_state(last_check=datetime.now(timezone.utc).isoformat())
    return False


def request_apply_update():
    """
    Punto de entrada desde la API. Valida el estado y lanza la descarga +
    aplicación de la actualización en un hilo en segundo plano.
    Retorna (ok: bool, mensaje: str).
    """
    if not getattr(sys, 'frozen', False):
        return False, "Las actualizaciones automáticas solo están disponibles en la aplicación instalada"

    info = get_version_info()
    if info["applying"]:
        return True, "La actualización ya está en curso"
    if not info["update_available"]:
        return False, "No hay ninguna actualización disponible"

    _update_state(applying=True, progress=0, stage="downloading", error=None)
    thread = threading.Thread(target=_download_and_apply, name="update-apply", daemon=True)
    thread.start()
    return True, f"Descargando actualización v{info['latest_version']}..."


def _download_and_apply():
    """Descarga el instalador, verifica su integridad y lanza el updater."""
    try:
        info = get_version_info()
        update_dir = os.path.join(tempfile.gettempdir(), "SaludsaActas_Update")
        os.makedirs(update_dir, exist_ok=True)
        installer_path = os.path.join(update_dir, f"SaludsaActas_Setup_v{info['latest_version']}.exe")

        logger.info(f"Descargando instalador v{info['latest_version']} desde {info['download_url']}")
        _download_installer(info["download_url"], installer_path)

        _update_state(stage="verifying")
        if info["sha256"] and not _verify_sha256(installer_path, info["sha256"]):
            os.remove(installer_path)
            raise RuntimeError("La verificación de integridad (SHA-256) del instalador falló")

        _launch_updater(installer_path)

        # La app se cierra 1.5s después para que la respuesta HTTP llegue al navegador
        _update_state(stage="restarting", progress=100)
        logger.info("Actualización lista. Reiniciando la aplicación...")
        threading.Timer(SHUTDOWN_DELAY, os._exit, args=(0,)).start()

    except Exception as e:
        logger.exception("Error aplicando la actualización")
        _update_state(applying=False, progress=None, stage=None, error=str(e))


def _download_installer(url: str, dest_path: str):
    """Descarga el instalador a disco actualizando el progreso en _state."""
    request = urllib.request.Request(url, headers={"User-Agent": f"SaludsaActas/{CURRENT_VERSION}"})
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        with open(dest_path, 'wb') as f:
            while True:
                chunk = response.read(1024 * 256)  # 256 KB
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    _update_state(progress=min(99, int(downloaded * 100 / total)))


def _verify_sha256(file_path: str, expected_sha256: str) -> bool:
    """Verifica el hash SHA-256 del archivo descargado."""
    digest = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 256), b''):
            digest.update(chunk)
    actual = digest.hexdigest().lower()
    if actual != expected_sha256.lower():
        logger.error(f"SHA-256 no coincide. Esperado: {expected_sha256} | Obtenido: {actual}")
        return False
    return True


def _launch_updater(installer_path: str):
    """Escribe updater.ps1 en %TEMP% y lo lanza como proceso desacoplado."""
    update_dir = os.path.dirname(installer_path)
    script_path = os.path.join(update_dir, "updater.ps1")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(UPDATER_PS1)

    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    CREATE_NO_WINDOW = 0x08000000

    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden",
            "-File", script_path,
            "-ProcessId", str(os.getpid()),
            "-InstallerPath", installer_path,
            "-AppExePath", sys.executable,
        ],
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
        close_fds=True,
    )
    logger.info(f"Updater lanzado (PID actual: {os.getpid()}, script: {script_path})")


def start_update_scheduler():
    """
    Inicia el chequeo programado de actualizaciones en un hilo daemon:
    primer chequeo a los 15s del arranque y luego cada 4 horas.
    Solo se activa en la aplicación compilada (.exe).
    """
    if not getattr(sys, 'frozen', False):
        logger.info("Scheduler de actualizaciones deshabilitado (entorno de desarrollo).")
        return

    def _scheduler_loop():
        time.sleep(CHECK_START_DELAY)
        while True:
            try:
                check_for_updates()
            except Exception:
                logger.exception("Error inesperado en el chequeo programado de actualizaciones")
            time.sleep(CHECK_INTERVAL)

    thread = threading.Thread(target=_scheduler_loop, name="update-scheduler", daemon=True)
    thread.start()
    logger.info("Scheduler de actualizaciones iniciado (cada 4 horas).")
