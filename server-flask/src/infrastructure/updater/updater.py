"""Núcleo del sistema de auto-actualización de SaludsaActas.

Flujo general:

1. ``check_for_updates()`` descarga ``version.json`` desde la URL pública del
   último release de GitHub (sin usar la API, evitando rate limits) y compara
   versiones con ``packaging.version``.
2. ``request_apply_update()`` lanza en segundo plano la descarga del
   instalador a una carpeta dentro del directorio de instalación con progreso
   y verificación SHA-256.
3. Al terminar la descarga se lanza ``SaludsaUpdaterAgent.exe`` como proceso
   separado (Python puro, sin PowerShell) y la aplicación se cierra 1.5s
   después; el agente espera el cierre, instala en modo ``/VERYSILENT`` y
   reabre la aplicación.

El chequeo programado (scheduler) solo se activa en la aplicación compilada
(``sys.frozen``). En desarrollo local nunca se ofrecen actualizaciones.
"""
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packaging.version import InvalidVersion, Version

from src.core.version import CURRENT_VERSION

logger = logging.getLogger(__name__)

# Canal de actualizaciones: se detecta a partir del propio version.txt
# embebido al compilar (ej. "1.2.3-beta.1"), no de una variable de entorno.
# Así el binario sabe qué canal le corresponde desde que se compiló -- nadie
# puede olvidarse de setear algo y terminar mezclando canales sin querer.
_IS_BETA = bool(re.search(r"-(beta|alpha|rc|dev)", CURRENT_VERSION, re.IGNORECASE))

# URL web estable del manifiesto del último release (NO usa la API de GitHub)
INSTALLER_NAME = "SaludsaActas_Setup.exe"
_REPO_BASE = "https://github.com/dekoov/Saludsa-Control-de-Actas-TI/releases"

if _IS_BETA:
    MANIFEST_URL = f"{_REPO_BASE}/download/beta-channel/version-beta.json"
    INSTALLER_FALLBACK_URL = f"{_REPO_BASE}/download/beta-channel/{INSTALLER_NAME}"
else:
    MANIFEST_URL = f"{_REPO_BASE}/latest/download/version.json"
    INSTALLER_FALLBACK_URL = f"{_REPO_BASE}/latest/download/{INSTALLER_NAME}"

UPDATER_AGENT_NAME = "SaludsaUpdaterAgent.exe"

CHECK_TIMEOUT = 10          # segundos para el chequeo de versión
DOWNLOAD_TIMEOUT = 60       # segundos por lectura durante la descarga
CHECK_INTERVAL = 4 * 3600   # 4 horas
CHECK_START_DELAY = 15      # primer chequeo a los 15 segundos del arranque
SHUTDOWN_DELAY = 1.5        # cierre de la app tras lanzar el updater

# Estado en memoria del sistema de actualización
_state: dict[str, Any] = {
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


def _update_state(**kwargs: Any) -> None:
    """Actualiza el estado global del updater de forma thread-safe.

    Args:
        **kwargs: Clave/valor a actualizar en ``_state``.

    Returns:
        None. Este método no retorna valor.
    """
    with _state_lock:
        _state.update(kwargs)


def cleanup_updater_runtime() -> None:
    """Elimina la copia temporal del updater si quedó de una actualización previa.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        Intenta borrar ``SaludsaUpdaterAgent_runtime.exe`` con reintentos.
    """
    if not getattr(sys, "frozen", False):
        return

    runtime = Path(sys.executable).parent / "SaludsaUpdaterAgent_runtime.exe"
    if not runtime.exists():
        return

    # Reintentos: el agente puede tardar unos segundos en morir después del health-check
    for attempt in range(1, 4):
        try:
            runtime.unlink()
            print(f"[Updater] Limpieza: {runtime.name} eliminado.")
            return
        except PermissionError:
            if attempt < 3:
                time.sleep(1.5 * attempt)  # 1.5s, 3s
            else:
                logger.warning(
                    "No se pudo eliminar la copia temporal (aún en uso). "
                    "Se reintentará en el próximo arranque."
                )
        except Exception:
            logger.warning("No se pudo eliminar la copia temporal")
            return


def get_version_info() -> dict[str, Any]:
    """Retorna una copia del estado actual del sistema de actualización.

    Returns:
        dict[str, Any]: Diccionario con el estado interno más la versión
        actual de la aplicación bajo la clave ``current_version``.
    """
    with _state_lock:
        info = dict(_state)
    info["current_version"] = CURRENT_VERSION
    return info


def check_for_updates() -> bool:
    """Consulta el manifiesto de versiones y determina si hay una actualización.

    Los errores de red o de formato son silenciosos y se registran como
    advertencias. Solo opera cuando la aplicación está compilada.

    Returns:
        bool: ``True`` si hay una versión más nueva disponible, ``False`` en
        cualquier otro caso.

    Side Effects:
        Actualiza el estado en memoria con la información del release remoto y
        el timestamp del último chequeo.
    """
    if not getattr(sys, "frozen", False):
        logger.debug("Chequeo de actualizaciones omitido: entorno de desarrollo.")
        return False

    try:
        request = urllib.request.Request(
            MANIFEST_URL,
            headers={"User-Agent": f"SaludsaActas/{CURRENT_VERSION}"},
        )
        with urllib.request.urlopen(request, timeout=CHECK_TIMEOUT) as response:
            manifest = json.loads(response.read().decode("utf-8"))

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
            logger.info(
                f"Nueva versión disponible: v{remote_version} (actual: v{CURRENT_VERSION})"
            )
        else:
            logger.info(f"La aplicación está actualizada (v{CURRENT_VERSION})")
        return available

    except (InvalidVersion, KeyError, json.JSONDecodeError) as e:
        logger.warning(f"Manifiesto de actualización inválido: {e}")
    except Exception as e:
        logger.warning(f"No se pudo comprobar actualizaciones (se reintentará luego): {e}")

    _update_state(last_check=datetime.now(timezone.utc).isoformat())
    return False


def request_apply_update() -> tuple[bool, str]:
    """Valida el estado y lanza la descarga/aplicación de la actualización.

    Returns:
        tuple[bool, str]: Par ``(ok, mensaje)``. ``ok`` indica si se pudo
        iniciar el proceso; ``mensaje`` describe el resultado.

    Side Effects:
        Inicia un hilo daemon que descarga el instalador, verifica su hash y
        lanza el agente de actualización.
    """
    if not getattr(sys, "frozen", False):
        return (
            False,
            "Las actualizaciones automáticas solo están disponibles en la aplicación instalada",
        )

    info = get_version_info()
    if info["applying"]:
        return True, "La actualización ya está en curso"
    if not info["update_available"]:
        return False, "No hay ninguna actualización disponible"

    _update_state(applying=True, progress=0, stage="downloading", error=None)
    thread = threading.Thread(target=_download_and_apply, name="update-apply", daemon=True)
    thread.start()
    return True, f"Descargando actualización v{info['latest_version']}..."


def _get_update_dir() -> str:
    """Resuelve el directorio de descarga de actualizaciones.

    Prefiere la carpeta de instalación de la aplicación sobre ``%TEMP%`` para
    evitar falsos positivos de EDR/antivirus al ejecutar instaladores desde el
    directorio temporal.

    Returns:
        str: Ruta absoluta del directorio ``updates/pending``.

    Side Effects:
        Crea los directorios intermedios si no existen.
    """
    if getattr(sys, "frozen", False):
        install_dir = Path(sys.executable).parent
    else:
        install_dir = Path(tempfile.gettempdir())  # solo como fallback en dev
    update_dir = install_dir / "updates" / "pending"
    update_dir.mkdir(parents=True, exist_ok=True)
    return str(update_dir)


def _download_and_apply() -> None:
    """Descarga el instalador, verifica su integridad y lanza el agente.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        - Escribe el instalador en disco.
        - Actualiza el progreso de descarga en ``_state``.
        - Lanza ``SaludsaUpdaterAgent.exe``.
        - Programa el cierre de la aplicación.
    """
    try:
        info = get_version_info()
        update_dir = _get_update_dir()
        installer_path = os.path.join(
            update_dir, f"SaludsaActas_Setup_v{info['latest_version']}.exe"
        )

        logger.info(
            f"Descargando instalador v{info['latest_version']} desde {info['download_url']}"
        )
        _download_installer(info["download_url"], installer_path)

        _update_state(stage="verifying")
        if info["sha256"] and not _verify_sha256(installer_path, info["sha256"]):
            os.remove(installer_path)
            raise RuntimeError(
                "La verificación de integridad (SHA-256) del instalador falló"
            )

        _launch_updater(installer_path)

        # La app se cierra 1.5s después para que la respuesta HTTP llegue al navegador
        _update_state(stage="restarting", progress=100)
        logger.info("Actualización lista. Reiniciando la aplicación...")
        threading.Timer(SHUTDOWN_DELAY, os._exit, args=(0,)).start()

    except Exception as e:
        logger.exception("Error aplicando la actualización")
        _update_state(applying=False, progress=None, stage=None, error=str(e))


def _download_installer(url: str, dest_path: str) -> None:
    """Descarga el instalador a disco actualizando el progreso en ``_state``.

    Args:
        url: URL del instalador a descargar.
        dest_path: Ruta local donde se guardará el archivo.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        Escribe el archivo en disco y actualiza ``_state["progress"]``.
    """
    request = urllib.request.Request(
        url, headers={"User-Agent": f"SaludsaActas/{CURRENT_VERSION}"}
    )
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = response.read(1024 * 256)  # 256 KB
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    _update_state(progress=min(99, int(downloaded * 100 / total)))


def _verify_sha256(file_path: str, expected_sha256: str) -> bool:
    """Verifica el hash SHA-256 de un archivo descargado.

    Args:
        file_path: Ruta del archivo a verificar.
        expected_sha256: Hash SHA-256 esperado en formato hexadecimal.

    Returns:
        bool: ``True`` si el hash coincide, ``False`` en caso contrario.
    """
    digest = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 256), b""):
            digest.update(chunk)
    actual = digest.hexdigest().lower()
    if actual != expected_sha256.lower():
        logger.error(
            f"SHA-256 no coincide. Esperado: {expected_sha256} | Obtenido: {actual}"
        )
        return False
    return True


def _launch_updater(installer_path: str) -> None:
    """Lanza ``SaludsaUpdaterAgent.exe`` como proceso separado.

    Args:
        installer_path: Ruta del instalador descargado y verificado.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        Crea una copia temporal (shadow copy) del agente para permitir que el
        instalador lo reemplace durante la actualización, y lanza el agente.
    """
    if not getattr(sys, "frozen", False):
        logger.warning("No se puede lanzar el updater fuera de la app compilada.")
        return

    app_exe_path = Path(sys.executable)
    original_agent = app_exe_path.parent / UPDATER_AGENT_NAME
    runtime_agent = app_exe_path.parent / "SaludsaUpdaterAgent_runtime.exe"

    if not original_agent.exists():
        logger.error(f"No se encontró {UPDATER_AGENT_NAME} en {original_agent}")
        _update_state(applying=False, error="No se encontró el componente de actualización")
        return

    # Crear shadow copy para que el instalador pueda reemplazar el original
    try:
        import shutil
        shutil.copy2(original_agent, runtime_agent)
        launch_target = runtime_agent
        logger.info(f"Shadow copy del agente creada: {runtime_agent}")
    except Exception as e:
        logger.warning(f"No se pudo crear copia runtime del agente ({e}), usando original.")
        launch_target = original_agent

    subprocess.Popen(
        [
            str(launch_target),
            "--pid", str(os.getpid()),
            "--installer", installer_path,
            "--app-exe", str(app_exe_path),
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        close_fds=True,
    )
    logger.info(
        f"SaludsaUpdaterAgent lanzado desde: {launch_target} (PID actual: {os.getpid()})"
    )


def start_update_scheduler() -> None:
    """Inicia el chequeo programado de actualizaciones en un hilo daemon.

    El primer chequeo ocurre a los ``CHECK_START_DELAY`` segundos del arranque
    y luego cada ``CHECK_INTERVAL`` segundos. Solo se activa en la aplicación
    compilada.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        Lanza un hilo daemon que ejecuta ``check_for_updates`` periódicamente.
    """
    if not getattr(sys, "frozen", False):
        logger.info("Scheduler de actualizaciones deshabilitado (entorno de desarrollo).")
        return

    def _scheduler_loop() -> None:
        """Bucle daemon que consulta actualizaciones periódicamente.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Ejecuta ``check_for_updates`` cada ``CHECK_INTERVAL`` segundos.
        """
        time.sleep(CHECK_START_DELAY)
        while True:
            try:
                check_for_updates()
            except Exception:
                logger.exception("Error inesperado en el chequeo programado de actualizaciones")
            time.sleep(CHECK_INTERVAL)

    thread = threading.Thread(
        target=_scheduler_loop, name="update-scheduler", daemon=True
    )
    thread.start()
    logger.info("Scheduler de actualizaciones iniciado (cada 4 horas).")