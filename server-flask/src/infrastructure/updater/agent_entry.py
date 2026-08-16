"""
infrastructure/updater/agent_entry.py

Entry point de SaludsaUpdaterAgent.exe -- proceso separado en Python puro
(sin PowerShell) que espera a que la app principal cierre, corre el
instalador Inno Setup en modo silencioso, y relanza la app actualizada.

Por qué existe: Windows bloquea un .exe/carpeta en uso, así que la propia
app principal no puede reemplazarse a sí misma. Este agente corre aparte,
espera el cierre real del proceso principal, y recién ahí dispara el
instalador. Con PrivilegesRequired=lowest en el instalador, todo esto corre
sin admin y sin UAC en ningún punto.

Se compila aparte con PyInstaller (--onefile, CON consola -- es el
placeholder de progreso pedido) y se distribuye junto a SaludsaActas.exe
dentro del mismo instalador de Inno Setup.

Invocación (desde infrastructure/updater/updater.py):
    subprocess.Popen([
        str(agent_path),
        "--pid", str(os.getpid()),
        "--installer", installer_path,
        "--app-exe", str(app_exe_path),
    ], creationflags=subprocess.CREATE_NEW_CONSOLE)

Build:
    pyinstaller --onefile --name SaludsaUpdaterAgent src/infrastructure/updater/agent_entry.py
"""

import argparse
import ctypes
import logging
import subprocess
import sys
import time
from pathlib import Path

SYNCHRONIZE = 0x00100000
WAIT_TIMEOUT = 0x00000102
PID_WAIT_TIMEOUT_SECONDS = 60
HEALTH_CHECK_SECONDS = 8


def _setup_logging(install_dir: Path) -> Path:
    # logs/ vive al nivel raíz de instalación -- persiste entre corridas,
    # a diferencia de updates/ que sí se limpia al terminar.
    log_path = install_dir / "logs" / "updater.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_path


def _wait_for_pid_exit(pid: int, timeout_seconds: int) -> bool:
    """Espera a que el proceso principal termine. True si terminó, False si timeout."""
    handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return True  # el proceso ya no existe
    try:
        result = ctypes.windll.kernel32.WaitForSingleObject(handle, timeout_seconds * 1000)
        return result != WAIT_TIMEOUT
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _run_installer(installer_path: Path) -> int:
    """Corre el instalador Inno Setup en modo silencioso. Retorna el exit code."""
    result = subprocess.run(
        [str(installer_path), "/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logging.error(f"Instalador terminó con código {result.returncode}")
        if result.stdout:
            logging.error(f"stdout: {result.stdout.strip()}")
        if result.stderr:
            logging.error(f"stderr: {result.stderr.strip()}")
    return result.returncode


def _relaunch(app_exe: Path) -> subprocess.Popen:
    return subprocess.Popen([str(app_exe)], cwd=str(app_exe.parent))


def _process_is_alive(proc: subprocess.Popen, seconds: int) -> bool:
    """Health check simple: si sigue vivo después de N segundos, no crasheó al arrancar."""
    try:
        proc.wait(timeout=seconds)
        return False  # terminó solo -> mala señal
    except subprocess.TimeoutExpired:
        return True  # sigue corriendo -> buena señal


def _cleanup(installer_path: Path) -> None:
    """Borra el instalador y las carpetas updates/pending/ vacías."""
    try:
        if installer_path.exists():
            installer_path.unlink()

        # Subir: .../updates/pending/ -> borrar si quedó vacía
        pending_dir = installer_path.parent
        if pending_dir.exists() and pending_dir.name.lower() == "pending":
            try:
                pending_dir.rmdir()          # solo borra si está vacía
            except OSError:
                pass

        # Subir: .../updates/ -> borrar si quedó vacía
        updates_dir = pending_dir.parent
        if updates_dir.exists() and updates_dir.name.lower() == "updates":
            try:
                updates_dir.rmdir()
            except OSError:
                pass

    except OSError as e:
        logging.warning(f"No se pudo borrar el instalador temporal: {e}")

def _self_delete() -> None:
    """
    Programa el borrado del propio .exe después de que el proceso termine.
    Como Windows bloquea un .exe en ejecución, lanzamos un proceso cmd
    desatachado que espera 3 segundos y luego borra el archivo.
    """
    try:
        exe_path = Path(sys.executable).resolve()
        # Comando silencioso: espera 3s y borra; si aún está bloqueado, reintenta en el próximo arranque
        cmd = f'cmd /c "timeout /t 3 /nobreak >nul 2>&1 && del \"{exe_path}\" >nul 2>&1"'
        subprocess.Popen(
            cmd,
            shell=True,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logging.info(f"Auto-eliminación programada para: {exe_path.name}")
    except Exception as e:
        logging.warning(f"No se pudo programar auto-eliminación del agente: {e}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--app-exe", type=Path, required=True)
    args = parser.parse_args()

    install_dir = args.app_exe.parent
    log_path = _setup_logging(install_dir)

    print("=== SaludsaActas - Actualizador ===")
    print(f"Log: {log_path}\n")

    logging.info(f"Agent iniciado. Esperando cierre del proceso principal (PID {args.pid})...")
    print("Esperando a que la aplicación se cierre...")

    if not _wait_for_pid_exit(args.pid, PID_WAIT_TIMEOUT_SECONDS):
        msg = "Timeout esperando el cierre de la aplicación. Actualización cancelada."
        logging.error(msg)
        print(f"\n{msg}")
        input("Presioná Enter para cerrar esta ventana...")
        return 1

    print("Instalando actualización, esto puede tardar unos segundos...")
    logging.info("Ejecutando instalador en modo silencioso.")
    exit_code = _run_installer(args.installer)

    if exit_code != 0:
        msg = f"La instalación falló (código {exit_code}). La versión anterior no se modificó."
        logging.error(msg)
        print(f"\n{msg}")
        input("Presioná Enter para cerrar esta ventana...")
        return 1

    logging.info("Instalación completada. Relanzando la aplicación.")
    print("Instalación completada. Reabriendo SaludsaActas...")

    try:
        proc = _relaunch(args.app_exe)
    except Exception:
        logging.exception("No se pudo relanzar la aplicación tras la instalación.")
        print("\nLa actualización se instaló, pero no se pudo reabrir la app automáticamente.")
        print(f"Abrila manualmente desde: {args.app_exe}")
        input("Presioná Enter para cerrar esta ventana...")
        return 1

    if _process_is_alive(proc, HEALTH_CHECK_SECONDS):
        logging.info("Actualización verificada correctamente.")
        _cleanup(args.installer)
        print("Actualización completada con éxito.")
        time.sleep(2)
        _self_delete()
        time.sleep(1)
        return 0
    else:
        msg = "La nueva versión se cerró inesperadamente al iniciar."
        logging.error(msg)
        print(f"\n{msg}")
        print("Puede que necesites reinstalar manualmente desde una versión anterior.")
        input("Presioná Enter para cerrar esta ventana...")
        return 1


if __name__ == "__main__":
    sys.exit(main())
