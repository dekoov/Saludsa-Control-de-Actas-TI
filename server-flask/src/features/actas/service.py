"""Servicios de dominio para el feature Actas.

Contiene la lógica de negocio relacionada con la generación física de
documentos (acta y pagaré) y la gestión del historial de actas: consulta,
formateo, firma, anulación, descarga con auto-curación y sincronización con
Saludsa. Los servicios no interactúan directamente con el framework Flask; su
comunicación con la infraestructura se realiza a través de la capa de
persistencia y utilidades especializadas.
"""

import io
import os
from typing import Any

from src.config import config
from src.core.exceptions import AppError, ExternalServiceError, NotFoundError
from src.features.actas.enums import DocumentType
from src.features.actas.helpers import _build_document
from src.features.actas.persistence import (
    get_acta_by_id,
    get_paginated_actas_history,
    update_acta_document_paths,
    update_acta_status,
    update_acta_sync_status,
)
from src.infrastructure.documents.document_service import convert_to_pdf_buffer
from src.infrastructure.saludsa_bot.saludsa_bot_service import SaludsaBotService
from src.models.enums import ActaStatus, EquipmentType
from src.utils.formatters import (
    fecha_a_texto,
    fecha_a_texto_legal,
    monto_a_letras,
    ubicacion_a_letras,
)


class ActaDocumentService:
    """Servicio de dominio dedicado a la generación de documentos físicos/virtuales.

    No realiza persistencia ni interactúa con APIs externas. Se encarga de
    construir el contexto de renderizado, seleccionar la plantilla adecuada y
    generar el acta principal y, opcionalmente, el pagaré cuando el equipo
    principal es una laptop.

    Attributes:
        None: clase sin estado interno.
    """

    def generate_documents(
        self, user_data: dict[str, Any], equipment_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Genera los documentos DOCX/PDF asociados a un acta.

        Siempre genera el acta principal. Si el primer equipo es una laptop,
        también genera el pagaré correspondiente con el monto en letras y la
        fecha legal.

        Args:
            user_data: Datos del empleado/usuario destinatario.
            equipment_list: Lista de equipos a incluir en el acta.

        Returns:
            list[dict[str, Any]]: Lista con uno o dos diccionarios de documentos
            generados (acta y pagaré). Cada diccionario incluye document_type,
            file_name, pdf_buffer, docx_path y pdf_base64.
        """
        if not equipment_list:
            return []
        main_equipment = equipment_list[0]

        # 1. Extraemos los valores de forma segura asumiendo que son diccionarios
        eq_type = main_equipment.get("equipment_type")
        eq_serial = main_equipment.get("serial_number")
        eq_cost = main_equipment.get("purchase_cost", 0)

        context_base = {
            "equipos": equipment_list,
            "full_name": user_data.get(
                "full_name", user_data.get("display_name", "NA")
            ),
            "national_id": user_data.get("national_id", "NA"),
            "city": ubicacion_a_letras(user_data.get("city")),
            "actual_date": fecha_a_texto(),
        }

        processed_documents: list[dict[str, Any]] = []

        # 2. Generar el Acta Principal (siempre se genera)
        acta_name = f"ENTREGA_{user_data.get('username')}_{eq_type}_{eq_serial}.docx"
        processed_documents.append(
            _build_document(
                doc_type=DocumentType.ACTA.value,
                context=context_base,
                template="acta_template.docx",
                filename=acta_name,
            )
        )

        # 3. Lógica del Pagaré (Solo si el primer elemento es Laptop)
        if main_equipment.get("equipment_type") == EquipmentType.LAPTOP.value:
            pagare_filename = (
                f"PAGARE_{user_data.get('username')}_LAPTOP_{eq_serial}.docx"
            )
            numerical_amount = int(eq_cost)
            text_amount = monto_a_letras(numerical_amount, incluir_centavos=False)

            # Copiamos el contexto base y le añadimos los campos exclusivos del pagaré
            context_pagare = context_base.copy()
            context_pagare.update(
                {
                    "main_equipment": main_equipment,
                    "numerical_amount": numerical_amount,
                    "actual_date_header": fecha_a_texto_legal(),
                    "text_amount": text_amount,
                }
            )

            processed_documents.append(
                _build_document(
                    doc_type=DocumentType.PAGARE.value,
                    context=context_pagare,
                    template="pagare_template.docx",
                    filename=pagare_filename,
                )
            )
        # Retorna la lista de archivos creados (puede ser 1 o 2 archivos)
        return processed_documents


class ActaHistoryService:
    """Servicio dedicado a la recuperación y gestión del historial de actas.

    Expone operaciones de lectura, firma, anulación, descarga de documentos y
    sincronización con el portal de Saludsa. Actúa como capa de negocio entre
    los routers y la capa de persistencia.

    Attributes:
        None: clase sin estado interno.
    """

    def fetch_history(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Recupera y formatea el historial paginado de actas.

        Args:
            filters: Diccionario con criterios de búsqueda, filtros y paginación.

        Returns:
            dict[str, Any]: Diccionario con items formateados y metadatos de
            paginación (total, page, per_page).
        """
        # 1. Obtenemos la data cruda paginada desde persistencia
        pagination = get_paginated_actas_history(filters)

        # 2. Formateamos la data para la vista del frontend
        formatted_data = [
            acta.to_dict(include_history_details=True) for acta in pagination.items
        ]

        # 3. Retornamos el diccionario listo para la respuesta JSON
        return {
            "items": formatted_data,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
        }

    def anular_acta(self, acta_id: str) -> bool:
        """Anula un acta validando las reglas de negocio.

        Args:
            acta_id: Identificador del acta a anular.

        Returns:
            bool: True si la anulación fue exitosa.

        Raises:
            NotFoundError: Si el acta no existe.
            AppError: Si el acta ya está anulada.
        """
        acta = get_acta_by_id(acta_id)
        if not acta:
            raise NotFoundError(
                message=f"No se encontró el acta con ID {acta_id}"
            )

        if acta.estado == ActaStatus.ANULADA.value:
            raise AppError(message="El acta ya se encuentra anulada.", status_code=400)

        update_acta_status(acta_id, ActaStatus.ANULADA.value)
        return True

    def marcar_como_firmada(self, acta_id: str) -> bool:
        """Marca un acta como firmada validando las reglas de negocio.

        Args:
            acta_id: Identificador del acta a firmar.

        Returns:
            bool: True si la firma fue exitosa.

        Raises:
            NotFoundError: Si el acta no existe.
            AppError: Si el acta ya estaba firmada.
        """
        acta = get_acta_by_id(acta_id)
        if not acta:
            raise NotFoundError(
                message=f"No se encontró el acta con ID {acta_id}"
            )

        if acta.estado == ActaStatus.FIRMADA.value:
            raise AppError(
                message="El acta ya estaba marcada como firmada.", status_code=400
            )

        # Delegación limpia a la capa de persistencia
        update_acta_status(acta_id, ActaStatus.FIRMADA.value)
        return True

    def get_acta_document_stream(
        self, acta_id: str, doc_type: str
    ) -> tuple[io.BytesIO, str]:
        """Obtiene el stream PDF de un documento del acta.

        Coordina la descarga del acta o pagaré. Si el archivo físico no existe,
        aplica la estrategia de Auto-curación (Self-Healing) regenerándolo desde
        la data histórica del acta y actualizando las rutas en base de datos.

        Args:
            acta_id: Identificador del acta.
            doc_type: Tipo de documento solicitado ("acta" o "pagare").

        Returns:
            tuple[io.BytesIO, str]: Tupla con el buffer PDF y el nombre del
            archivo resultante.

        Raises:
            AppError: Si el tipo de documento es inválido, el acta no tiene
                pagaré, no se pudo regenerar el documento o no se determinó una
                ruta física válida.
            NotFoundError: Si el acta no existe.
            ExternalServiceError: Si falla la conversión a PDF.
        """
        if doc_type not in ["acta", "pagare"]:
            raise AppError(
                message="El tipo de documento debe ser 'acta' o 'pagare'"
            )

        # 1. Recuperar el acta usando la capa de persistencia aislada
        acta = get_acta_by_id(acta_id)
        if not acta:
            raise NotFoundError(
                message=f"No se encontró el acta con ID {acta_id}"
            )

        if doc_type == "pagare" and not acta.tiene_pagare:
            raise AppError(
                message="Esta acta no cuenta con un pagaré asociado", status_code=400
            )

        target_path = acta.archivo_acta if doc_type == "acta" else acta.archivo_pagare

        # 2. Estrategia Self-Healing: Si el archivo físico desapareció, lo volvemos a generar
        if not target_path or not os.path.exists(target_path):
            # Reconstituir estructuras necesarias para el ActaDocumentService
            user_data = {
                "username": getattr(acta.empleado, "username", "NA"),
                "full_name": getattr(acta.empleado, "full_name", "NA"),
                "national_id": getattr(acta.empleado, "national_id", "NA"),
                "city": getattr(acta.empleado, "city", "Quito"),
            }

            equipment_list: list[dict[str, Any]] = []

            # SOLUCIÓN CRÍTICA 1: Forzar la evaluación de la relación o usar una lista vacía si es None
            activos = getattr(acta, "activos", []) or []
            for activo in activos:
                equipment_list.append(
                    {
                        "equipment_type": "Laptop",
                        "serial_number": getattr(activo, "serial_number", "NA"),
                        "purchase_cost": getattr(activo, "purchase_cost", 0),
                        "manufacturer": getattr(activo, "manufacturer", "NA"),
                        "model": getattr(activo, "model", "NA"),
                        "hostname": getattr(activo, "hostname", "NA"),
                    }
                )

            accesorios = getattr(acta, "accesorios", []) or []
            for accesorio in accesorios:
                equipment_list.append(
                    {
                        "equipment_type": getattr(accesorio, "type", "Accesorio"),
                        "serial_number": getattr(accesorio, "serial_number", "NA"),
                        "purchase_cost": getattr(accesorio, "purchase_cost", 0),
                        "manufacturer": getattr(accesorio, "manufacturer", "NA"),
                        "model": getattr(accesorio, "model", "NA"),
                    }
                )

            # Llamamos al generador de la misma capa de dominio
            doc_service = ActaDocumentService()
            new_docs = doc_service.generate_documents(user_data, equipment_list)
            if not new_docs:
                raise AppError(
                    message="Error crítico interno al regenerar los documentos base",
                    status_code=500,
                )

            # SOLUCIÓN CRÍTICA 2: Asegurar valores 'str' usando el operador 'or' por si el diccionario viene incompleto
            archivo_acta = str(new_docs[0].get("docx_path") or "")
            archivo_pagare = (
                str(new_docs[1].get("docx_path") or "") if len(new_docs) > 1 else None
            )

            if not archivo_acta:
                raise AppError(
                    message="El documento generado no tiene una ruta válida",
                    status_code=500,
                )

            # Actualizar de forma limpia la BD
            update_acta_document_paths(acta_id, archivo_acta, archivo_pagare)

            # Reasignamos la ruta correcta una vez subsanado el error de infraestructura
            target_path = archivo_acta if doc_type == "acta" else archivo_pagare

        if not target_path:
            raise AppError(
                message="No se pudo determinar una ruta física válida para el archivo",
                status_code=500,
            )

        # 3. Conversión del binario a PDF en memoria
        try:
            pdf_buffer = convert_to_pdf_buffer(target_path)
            filename_base = os.path.basename(target_path).replace(".docx", ".pdf")
            return pdf_buffer, filename_base
        except Exception as e:
            raise ExternalServiceError(
                message="Error al transformar el archivo original a PDF",
                payload=str(e),
            ) from e

    def ejecutar_sincronizacion_saludsa(self, acta_id: str) -> dict[str, Any]:
        """Reintenta la sincronización de un acta con el portal de Saludsa.

        Recupera el acta de la base de datos, reconstruye los payloads de
        empleado y equipos, inicializa el bot de Playwright y actualiza los
        estados de sincronización según el resultado.

        Args:
            acta_id: Identificador del acta a sincronizar.

        Returns:
            dict[str, Any]: Diccionario con mensaje y ruta del screenshot:
                {"mensaje": str, "screenshot": str | None}.

        Raises:
            NotFoundError: Si el acta no existe.
            ExternalServiceError: Si la sincronización falla.
        """
        # 1. Buscar el registro real usando tu función de persistencia aislada
        acta = get_acta_by_id(acta_id)
        if not acta:
            raise NotFoundError(
                message=f"No se encontró ninguna acta con el ID {acta_id}"
            )

        # 2. Reconstruir los datos del Empleado
        # TODO: Revisar el manejo de excepciones en esta construccion
        usuario_payload = {
            "full_name": getattr(acta.empleado, "full_name", "N/A") if acta.empleado else "N/A",
            "username": getattr(acta.empleado, "username", "N/A")
            if acta.empleado
            else "N/A",
        }

        # 3. Mapear Activos y Accesorios de las relaciones reales a la lista plana del Bot
        equipos_payload: list[dict[str, Any]] = []

        # Procesar Laptops (Activos principales)
        activos = getattr(acta, "activos", []) or []
        for activo in activos:
            equipos_payload.append(
                {
                    "equipment_type": "Laptop",
                    "serial_number": getattr(activo, "serial_number", "NA"),
                    "purchase_cost": getattr(activo, "purchase_cost", 0),
                    "manufacturer": getattr(activo, "manufacturer", "NA"),
                    "model": getattr(activo, "model", "NA"),
                    "hostname": getattr(activo, "hostname", "NA"),
                    "status": "Bueno",
                }
            )

        # Procesar Componentes Secundarios (Accesorios)
        accesorios = getattr(acta, "accesorios", []) or []
        for accesorio in accesorios:
            equipos_payload.append(
                {
                    "equipment_type": getattr(accesorio, "type", "Accesorio"),
                    "serial_number": getattr(accesorio, "serial_number", "NA"),
                    "purchase_cost": getattr(accesorio, "purchase_cost", 0),
                    "manufacturer": getattr(accesorio, "manufacturer", "NA"),
                    "model": getattr(accesorio, "model", "NA"),
                    "status": "Bueno",
                }
            )

        # 4. Inicializar el Bot con el entorno del sistema (.env)
        bot = SaludsaBotService(
            username=config.SALUDSA_USERNAME,
            password=config.SALUDSA_PASSWORD,
            headless=config.PLAYWRIGHT_HEADLESS,
        )

        # 5. Ejecutar la automatización de Playwright
        sync_result = bot.sincronizar_acta(
            equipos=equipos_payload, usuario=usuario_payload
        )

        # 6. Persistir el resultado final delegando en update_acta_sync_status
        if sync_result.exitosa:
            update_acta_sync_status(
                acta_id, exitosa=True, estado_sincronizacion="Exitosa"
            )
            return {
                "mensaje": "Sincronización procesada y validada en el portal de Saludsa.",
                "screenshot": sync_result.screenshot_path,
            }
        update_acta_sync_status(acta_id, exitosa=False, estado_sincronizacion="Fallida")
        raise ExternalServiceError(
            message=sync_result.mensaje,
            payload=sync_result.error_detalle,
        )
