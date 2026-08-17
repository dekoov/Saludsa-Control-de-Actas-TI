"""Servicio de automatización para sincronización con YoSoySaludsa.

Este módulo utiliza Playwright para navegar el portal de YoSoySaludsa,
buscar empleados y registrar la entrega de dotación según los equipos de un
acta. Soporta redirección dinámica de DNS para entornos corporativos y
registra comprobantes visuales de cada sincronización.
"""
import logging
import os
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from src.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EquipmentType(Enum):
    """Tipos de equipo reconocidos por el portal de YoSoySaludsa."""

    LAPTOP = "Laptop"
    CARGADOR = "Cargador"
    DIADEMA = "Diadema"
    MOCHILA = "Mochila"
    MOUSE = "Mouse"
    TECLADO = "Teclado"
    MONITOR = "Monitor"
    OTROS = "Otros"


# Mapeo Maestro de IDs de Saludsa
MAPEO_SALUDSA: dict[str, dict[str, Any]] = {
    EquipmentType.LAPTOP.value: {
        "es_computador": True,
        "marcas": {
            "Lenovo": "19",
            "Apple": "102",
            "Asus": "103",
            "MSI": "37",
            "Microsoft": "45",
        },
    },
    EquipmentType.DIADEMA.value: {"id": "36", "es_computador": False},
    EquipmentType.MOCHILA.value: {"id": "21", "es_computador": False},
    EquipmentType.CARGADOR.value: {"id": "21", "es_computador": False},
    EquipmentType.MONITOR.value: {"id": "21", "es_computador": False},
    EquipmentType.OTROS.value: {"id": "21", "es_computador": False},
    EquipmentType.MOUSE.value: {"id": "23", "es_computador": False},
    EquipmentType.TECLADO.value: {"id": "10", "es_computador": False},
}


@dataclass
class SyncResult:
    """Resultado de una sincronización con YoSoySaludsa.

    Attributes:
        exitosa: ``True`` si la sincronización finalizó correctamente.
        mensaje: Mensaje descriptivo del resultado.
        timestamp: Fecha y hora en que se intentó la sincronización.
        screenshot_path: Ruta de la captura de pantalla generada, si aplica.
        error_detalle: Detalle del error en caso de fallo.
    """

    exitosa: bool
    mensaje: str
    timestamp: datetime
    screenshot_path: str | None = None
    error_detalle: str | None = None


class SaludsaBotService:
    """Servicio para automatizar la sincronización con YoSoySaludsa usando Playwright.

    Gestiona el ciclo completo de navegación: login, menú de dotación,
    búsqueda del empleado, registro de equipos y guardado de la entrega.
    También detecta si la ejecución ocurre dentro de la red corporativa o
    externa para aplicar las reglas de resolución DNS correspondientes.

    Attributes:
        username: Usuario de YoSoySaludsa.
        password: Contraseña de YoSoySaludsa.
        headless: Indica si el navegador se ejecuta sin interfaz gráfica.
        timeout_ms: Tiempo máximo de espera por operación en milisegundos.
        screenshots_dir: Carpeta donde se guardan las capturas de pantalla.
    """

    def __init__(
        self,
        username: str,
        password: str,
        headless: bool = False,
        timeout_ms: int = 60000,
    ) -> None:
        """Inicializa el servicio de sincronización.

        Args:
            username: Usuario de YoSoySaludsa.
            password: Contraseña de YoSoySaludsa.
            headless: Ejecutar el navegador en modo headless.
            timeout_ms: Timeout por defecto para operaciones de Playwright en
                milisegundos.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Crea el directorio de screenshots si no existe.
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.screenshots_dir = "comprobantes"
        self._ensure_screenshots_dir()

    def _ensure_screenshots_dir(self) -> None:
        """Crea el directorio de screenshots si no existe.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Crea ``self.screenshots_dir`` en disco si aún no existe.
        """
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
            logger.info(f"Directorio de screenshots creado: {self.screenshots_dir}")

    def _get_frame_by_url(
        self,
        page: Page,
        part: str,
        timeout_ms: int | None = None,
    ) -> Page:
        """Busca un frame cuya URL contenga una subcadena específica.

        Args:
            page: Página principal de Playwright.
            part: Subcadena que debe contener la URL del frame.
            timeout_ms: Tiempo máximo de búsqueda en milisegundos. Si es
                ``None`` se usa ``self.timeout_ms``.

        Returns:
            Page: Frame de Playwright cuya URL coincide con el criterio.

        Raises:
            Exception: Si transcurre el timeout sin encontrar el frame.
        """
        timeout = timeout_ms or self.timeout_ms
        end_time = page.evaluate("performance.now()") + timeout
        while page.evaluate("performance.now()") < end_time:
            for f in page.frames:
                if part in f.url and "_blanks.asp" not in f.url:
                    return f
            page.wait_for_timeout(100)
        raise Exception(
            f"Timeout: No se encontró el frame con parte de URL '{part}' en {timeout} ms"
        )

    def _configurar_bloqueo_recursos(self, page: Page) -> None:
        """Bloquea la carga de imágenes, fuentes, media y rastreadores.

        Args:
            page: Página de Playwright a configurar.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Registra un handler de ruteo en la página para abortar recursos
            no esenciales.
        """
        def interceptar(route: Any) -> None:
            """Intercepta y filtra recursos no esenciales de la página.

            Args:
                route: Ruta de red de Playwright en curso.

            Returns:
                None. Este método no retorna valor.
            """
            if route.request.resource_type in ["image", "font", "media", "other"]:
                route.abort()
            elif (
                "google-analytics" in route.request.url
                or "doubleclick" in route.request.url
            ):
                route.abort()
            else:
                route.continue_()

        page.route("**/*", interceptar)

    def _modulo_login(self, page: Page) -> None:
        """Realiza el inicio de sesión en YoSoySaludsa.

        Args:
            page: Página de Playwright.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Navega al portal, completa credenciales y accede al módulo de
            Gestión de Personal.
        """
        logger.info("Iniciando sesión en YoSoySaludsa...")
        page.goto(
            "https://www.yosoysaludsa.com/",
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )
        page.locator('input[id="username"]').fill(self.username)
        page.locator('input[id="password"]').fill(self.password)
        page.locator('button[type="submit"]').click()
        page.locator("div.icon-container", has_text="Gestión de Personal").locator(
            "a"
        ).click()
        page.wait_for_url("**/00_paginas/entorno.html", timeout=self.timeout_ms)
        logger.info("Login exitoso")

    def _modulo_navegacion_menu(self, page: Page) -> None:
        """Navega al menú de Entrega de Dotación.

        Args:
            page: Página de Playwright.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Interactúa con el menú de beneficios y selecciona la opción de
            entrega de dotación.
        """
        logger.info("Navegando a Gestión de Personal -> Entrega de Dotación...")
        marco_macro = page.frame_locator(
            'iframe[name="entornomacro"], iframe[name="entornomacro"]'
        )
        marco_macro.locator('td.menuadmin:has-text("Beneficios")').hover()

        submenu = marco_macro.locator("a.submenu", has_text="Entrega de Dotación")
        submenu.wait_for(state="visible", timeout=self.timeout_ms)
        submenu.click()
        page.keyboard.press("Escape")
        logger.info("Navegación completada")

    def _modulo_busqueda_empleado(self, page: Page, full_name: str) -> None:
        """Busca y selecciona un empleado por nombre completo.

        Args:
            page: Página de Playwright.
            full_name: Nombre completo del empleado a buscar.

        Returns:
            None. Este método no retorna valor.

        Raises:
            Exception: Si no se encuentra el frame de cabecera de búsqueda.
        """
        logger.info(f"Buscando empleado: {full_name}")
        frame_cabe = self._get_frame_by_url(page, "cab_entrdotaempl.asp")
        if not frame_cabe:
            raise Exception("No se pudo encontrar el frame de cabecera (cab_entrdotaempl.asp)")

        # Clic en lupa
        frame_cabe.locator("a.linktabl").first.click(force=True)

        # Clic en combo de empleados
        frame_cabe.locator("#s2id_autogen1 a.select2-choice").click()
        input_busc = frame_cabe.locator("input.select2-input")
        input_busc.wait_for(state="visible", timeout=self.timeout_ms)
        input_busc.fill(full_name)

        frame_cabe.page.wait_for_timeout(600)  # Espera AJAX
        frame_cabe.page.keyboard.press("Enter")

        frame_cabe.locator('input[name="cmdComando"][value="Consultar"]').click()
        logger.info(f"Empleado seleccionado: {full_name}")

    def _modulo_relleno_dinamico(
        self,
        page: Page,
        equipo: dict[str, Any],
        accesorio_vinculado: dict[str, Any] | None = None,
    ) -> None:
        """Rellena el formulario de dotación según el tipo de equipo.

        Args:
            page: Página de Playwright.
            equipo: Diccionario con los datos del equipo a registrar.
            accesorio_vinculado: Datos de un accesorio relacionado, por ejemplo
                un cargador vinculado a una laptop.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Completa textarea, cantidad y campos específicos de laptop en el
            frame del formulario.
        """
        tipo_base = equipo.get("equipment_type", "")
        datos_mapeo = MAPEO_SALUDSA.get(tipo_base)

        if not datos_mapeo:
            logger.warning(f"No hay mapeo para tipo de equipo: {tipo_base}")
            return

        # Determinamos el ID de Saludsa
        idx: str | None = None
        es_laptop = False

        if tipo_base == EquipmentType.LAPTOP.value:
            modelo_json = equipo.get("manufacturer", "")
            idx = next(
                (
                    id_asp
                    for marca, id_asp in datos_mapeo["marcas"].items()
                    if marca.lower() in modelo_json.lower()
                ),
                None,
            )
            es_laptop = True
            if not idx:
                logger.warning(f"Marca no encontrada en mapeo: {modelo_json}")
                return
        else:
            idx = datos_mapeo.get("id")

        if not idx:
            return

        frame_form = self._get_frame_by_url(page, "frm_entrdotaempl.asp")

        # Construcción de la observación compuesta
        if es_laptop:
            lineas_obs = [
                f"EQUIPO: {equipo.get('model', 'N/A')}",
                f"S/N: {equipo.get('serial_number', 'N/A')}",
                f"HOSTNAME: {equipo.get('hostname', '')}",
                f"ESTADO: {equipo.get('status', '')}",
            ]
        else:
            lineas_obs = [
                f"MODELO: {equipo.get('model', 'N/A')}",
                f"MARCA: {equipo.get('manufacturer', 'N/A')}",
                f"S/N: {equipo.get('serial_number', 'N/A')}",
                f"ESTADO: {equipo.get('status', '')}",
            ]

        # Si hay un cargador vinculado, lo añadimos aquí mismo
        if es_laptop and accesorio_vinculado:
            lineas_obs.append(
                f"INCLUYE CARGADOR S/N: {accesorio_vinculado.get('serial_number', 'N/A')}"
            )
            lineas_obs.append(f"MARCA: {accesorio_vinculado.get('manufacturer', '')}")

        observacion_final = "\n".join(lineas_obs)

        # Rellenamos el cuadro de texto de esa marca específica
        textarea = frame_form.locator(f'textarea[name="txtObseCate_{idx}"]')
        texto_actual = textarea.input_value()

        if texto_actual:
            observacion_final = (
                f"{texto_actual}\n\n--- [Adicional: {tipo_base}] ---\n{observacion_final}"
            )
        else:
            observacion_final = f"--- {tipo_base} ---\n{observacion_final}"

        textarea.fill(observacion_final)

        # Llenamos los campos de cabecera si es Laptop
        if es_laptop:
            frame_form.locator(f'input[name="txtModeCate_{idx}"]').fill(
                equipo.get("model")
            )
            frame_form.locator(f'input[name="txtSeriCate_{idx}"]').fill(
                equipo.get("serial_number")
            )
            frame_form.locator(f'input[name="txtValoCate_{idx}"]').fill(
                str(equipo.get("purchase_cost"))
            )

        frame_form.locator(f'input[name="txtCantCate_{idx}"]').fill(
            str(equipo.get("quantity", 1))
        )
        logger.info(f"Campo rellenado para {tipo_base}: {equipo.get('model')}")

    def _modulo_guardar_entrega(self, page: Page) -> None:
        """Guarda la entrega de dotación definitiva.

        Args:
            page: Página de Playwright.

        Returns:
            None. Este método no retorna valor.

        Side Effects:
            Hace clic en el botón de guardar entrega definitiva del formulario.
        """
        logger.info("Guardando entrega definitiva...")
        frame_form = self._get_frame_by_url(page, "frm_entrdotaempl.asp")
        frame_form.locator(
            'input[name="cmdComando"][value="Guardar Entrega Definitiva"]'
        ).click()
        logger.info("Entrega guardada exitosamente")

    def _take_screenshot(self, page: Page, prefix: str = "sync") -> str:
        """Toma una captura de pantalla con marca de tiempo.

        Args:
            page: Página de Playwright.
            prefix: Prefijo para el nombre del archivo generado.

        Returns:
            str: Ruta absoluta del archivo PNG guardado.

        Side Effects:
            Guarda un archivo PNG en ``self.screenshots_dir``.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)
        page.screenshot(path=filepath)
        logger.info(f"Screenshot guardado: {filepath}")
        return filepath

    def sincronizar_acta(
        self,
        equipos: list[dict[str, Any]],
        usuario: dict[str, Any],
        marcar_firmada: bool = False,
        max_retries: int = 3,
    ) -> SyncResult:
        """Sincroniza un acta con el portal de YoSoySaludsa.

        Separa laptop y cargador, detecta el tipo de red (empresa vs hogar),
        navega el portal, registra los equipos y guarda la entrega. Aplica
        reintentos con backoff exponencial en caso de fallo.

        Args:
            equipos: Lista de equipos a sincronizar. Cada equipo debe incluir
                al menos ``equipment_type``, ``model``, ``manufacturer``,
                ``serial_number`` y ``status``.
            usuario: Diccionario con los datos del empleado. Debe contener al
                menos ``full_name``.
            marcar_firmada: No utilizado actualmente. Reservado para futuras
                expansiones.
            max_retries: Número máximo de intentos de sincronización.

        Returns:
            SyncResult: Resultado de la operación con estado, mensaje,
            timestamp y ruta del screenshot o detalle del error.

        Raises:
            Exception: Se captura internamente; se refleja en ``SyncResult``.

        Side Effects:
            Lanza un navegador Chromium, navega por el portal, puede guardar
            screenshots y finalmente cierra el navegador.
        """
        timestamp = datetime.now()

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Intento de sincronización {attempt + 1}/{max_retries}"
                )

                # Separar laptop y cargador
                laptop = next(
                    (e for e in equipos if e["equipment_type"] == "Laptop"), None
                )
                cargador = next(
                    (e for e in equipos if e["equipment_type"] == "Cargador"), None
                )

                if laptop:
                    otros_accesorios = [
                        e for e in equipos if e["equipment_type"] not in ["Laptop", "Cargador"]
                    ]
                else:
                    otros_accesorios = [
                        e for e in equipos if e["equipment_type"] != "Laptop"
                    ]

                # -------------------------------------------------------------
                # DETECCIÓN DINÁMICA DE RED (HOGAR VS EMPRESA)
                # -------------------------------------------------------------
                chrome_args = ["--ignore-certificate-errors"]
                try:
                    # Intentamos resolver el dominio usando el DNS del entorno actual
                    socket.gethostbyname("www.yosoysaludsa.com")
                    logger.info(
                        "Red Externa/Hogar detectada. El dominio resuelve correctamente vía DNS."
                    )
                except socket.gaierror:
                    # Si falla el DNS, asumimos que estamos dentro de la red corporativa
                    internal_ip = config.SALUDSA_INTERNAL_IP
                    logger.info(
                        f"Red Privada/Empresa detectada (DNS no resuelve). "
                        f"Aplicando bypass de IP interna ({internal_ip})."
                    )
                    chrome_args.append(
                        f"--host-resolver-rules=MAP www.yosoysaludsa.com {internal_ip}"
                    )

                print(f"DEBUG - ¿El bot cree que es headless?: {self.headless}")
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=self.headless,
                        args=chrome_args,
                    )
                    context = browser.new_context(
                        ignore_https_errors=True,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36",
                    )
                    page = context.new_page()

                    self._configurar_bloqueo_recursos(page)

                    try:
                        self._modulo_login(page)
                        self._modulo_navegacion_menu(page)
                        self._modulo_busqueda_empleado(page, usuario["full_name"])

                        # Procesar laptop con cargador vinculado
                        if laptop:
                            self._modulo_relleno_dinamico(
                                page, laptop, accesorio_vinculado=cargador
                            )

                        # Procesar otros accesorios
                        for acc in otros_accesorios:
                            self._modulo_relleno_dinamico(page, acc)

                        # Guardar entrega
                        self._modulo_guardar_entrega(page)

                        # Tomar screenshot como comprobante
                        screenshot_path = self._take_screenshot(page, "sync_success")

                        browser.close()

                        return SyncResult(
                            exitosa=True,
                            mensaje="Sincronización exitosa",
                            timestamp=timestamp,
                            screenshot_path=screenshot_path,
                        )

                    except Exception as e:
                        logger.error(f"Error durante la ejecución: {str(e)}")
                        screenshot_path = self._take_screenshot(page, "sync_error")
                        browser.close()
                        raise

            except Exception as e:
                logger.error(f"Intento {attempt + 1} falló: {str(e)}")
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(
                        f"Esperando {backoff_time} segundos antes de reintentar..."
                    )
                    time.sleep(backoff_time)
                else:
                    # Último intento falló
                    return SyncResult(
                        exitosa=False,
                        mensaje=f"Sincronización falló después de {max_retries} intentos",
                        timestamp=timestamp,
                        error_detalle=str(e),
                    )

        return SyncResult(
            exitosa=False,
            mensaje="Sincronización falló",
            timestamp=timestamp,
            error_detalle="Max retries exceeded",
        )