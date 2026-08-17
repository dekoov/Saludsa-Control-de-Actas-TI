"""Orquestador del flujo completo de generación de actas.

Este módulo coordina las distintas etapas del proceso de entrega de equipos:
validación del payload, recuperación de borradores, generación de documentos,
sincronización con el portal de Saludsa mediante un bot de automatización,
persistencia en base de datos, envío de correos electrónicos y eliminación del
borrador asociado. Centraliza la lógica de alto nivel que de otra forma quedaría
dispersa entre routers, servicios y capas de persistencia.
"""

import base64
import logging
from typing import Any

from flask import session
from sqlalchemy.exc import SQLAlchemyError

from src.config.config import config
from src.core.exceptions import DatabaseError, ExternalServiceError, ValidationError
from src.features.actas.persistence import save_acta_to_database
from src.features.actas.schemas import validate_acta_payload
from src.features.actas.service import ActaDocumentService
from src.features.drafts.persistence import delete_draft, get_draft_by_id
from src.features.email import email_service
from src.infrastructure.ldap.ldap_manager_resolver import resolve_manager_email
from src.infrastructure.saludsa_bot.saludsa_bot_service import SaludsaBotService
from src.models.enums import ActaStatus, EquipmentType

logger = logging.getLogger(__name__)


class ActaOrchestrator:
    """Director del flujo de Actas.

    Coordina la validación, generación de documentos, sincronización con
    sistemas externos (bot de Saludsa) y la persistencia del acta. Recibe un
    servicio de documentos inyectado en su constructor para mantener el acoplamiento
    bajo y facilitar pruebas unitarias.

    Attributes:
        doc_service: Instancia de ActaDocumentService encargada de generar los
            documentos DOCX/PDF del acta y pagaré.
    """

    def __init__(self, doc_service: ActaDocumentService) -> None:
        """Inicializa el orquestador con el servicio de documentos.

        Args:
            doc_service: Servicio de dominio que genera documentos físicos/virtuales.
        """
        self.doc_service = doc_service

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta el flujo completo de creación de un acta.

        El proceso incluye:
        1. Resolución del payload efectivo (directo o desde borrador).
        2. Validación y limpieza del payload mediante schemas.
        3. Generación de documentos (acta y pagaré si aplica).
        4. Sincronización opcional con el portal de Saludsa mediante bot.
        5. Persistencia del acta, activos, accesorios y empleado en base de datos.
        6. Eliminación del borrador si fue usado.
        7. Envío de correo electrónico al empleado/CC manager si fue solicitado.

        Args:
            payload: Diccionario con la información del acta. Puede contener los
                campos directos (usuario, equipos, marcar_firmada, syncHrPortal,
                sendEmail, emailType) o una referencia draft_id para cargar un
                borrador existente.

        Returns:
            dict[str, Any]: Diccionario con el resultado del procesamiento:
                - acta_id (str): Identificador generado para el acta.
                - estado (str): Estado final del acta (FIRMADA o PENDIENTE_FIRMA).
                - usuario (dict): Datos del usuario/empleado normalizados.
                - fecha (str | None): Timestamp del primer documento generado.
                - tiene_pagare (bool): Indica si el acta incluye pagaré por laptop.
                - documents (list[dict]): Lista de documentos en formato base64.
                - sincronizacion (dict | None): Resultado de la sincronización.
                - email_enviado (bool): Indica si se envió correo al empleado.

        Raises:
            ValidationError: Si el payload es inválido o no se encuentra el borrador.
            ExternalServiceError: Si falla la generación de documentos, faltan
                credenciales de Saludsa o falla la sincronización de forma crítica.
            DatabaseError: Si ocurre un error de base de datos al guardar el acta.
        """
        draft_id = payload.get("draft_id")
        if draft_id:
            draft = get_draft_by_id(draft_id)
            if not draft:
                raise ValidationError(f"No se encontró borrador con ID {draft_id}")
            data_to_process = draft
            marcar_firmada = draft.get("marcar_firmada", False)
            sync_request = draft.get("syncHrPortal", False)
        else:
            data_to_process = payload
            marcar_firmada = payload.get("marcar_firmada", False)
            sync_request = payload.get("syncHrPortal", False)

        # PASO 1: Validar y limpiar datos
        try:
            clean_data = validate_acta_payload(data_to_process)
        except ValidationError as e:
            raise ValidationError(
                message="Estructura de datos incorrecta o faltan campos", payload=str(e)
            )

        user_data = clean_data["usuario"]
        equipment_list = clean_data["equipos"]

        # PASO 2: Generar Documentos
        docs = self.doc_service.generate_documents(user_data, equipment_list)
        if not docs:
            raise ExternalServiceError(
                "No se generaron documentos, revise la información enviada"
            )

        estado_final = (
            ActaStatus.FIRMADA.value
            if marcar_firmada
            else ActaStatus.PENDIENTE_FIRMA.value
        )

        # PASO 3: Sincronización con el Bot de Saludsa
        sync_result_dict: dict[str, Any] | None = None
        if sync_request:
            if not config.SALUDSA_USERNAME or not config.SALUDSA_PASSWORD:
                raise ExternalServiceError(
                    "Faltan credenciales de Saludsa en la configuración del servidor"
                )

            try:
                bot_service = SaludsaBotService(
                    username=config.SALUDSA_USERNAME,
                    password=config.SALUDSA_PASSWORD,
                    headless=config.is_production(),
                    timeout_ms=60000,
                )

                bot_result = bot_service.sincronizar_acta(
                    equipos=equipment_list,
                    usuario=user_data,
                    marcar_firmada=marcar_firmada,
                    max_retries=2,
                )

                sync_result_dict = {
                    "exitosa": bot_result.exitosa,
                    "mensaje": bot_result.mensaje,
                    "timestamp": bot_result.timestamp,
                    "error_detalle": bot_result.error_detalle,
                }

            except ExternalServiceError as e:
                logger.warning(
                    f"Sincronización de acta fallida (continuando flujo): {e}"
                )
                sync_result_dict = {
                    "exitosa": False,
                    "mensaje": "Falló la sincronización con YoSoySaludsa por un error inesperado",
                    "timestamp": None,
                    "error_detalle": str(e),
                }

        # PASO 4: Persistir en base de datos
        try:
            acta_id = save_acta_to_database(
                equipos=equipment_list,
                usuario=user_data,
                generated_docs=docs,
                estado=estado_final,
                sync_result=sync_result_dict,
            )
            if not acta_id:
                raise DatabaseError("No se pudo guardar el acta en la base de datos")
        except SQLAlchemyError as e:
            raise DatabaseError(
                message="Error al guardar acta en base de datos", payload=str(e)
            ) from e

        if draft_id:
            delete_draft(draft_id)

        formatted_docs: list[dict[str, Any]] = []
        for doc in docs:
            pdf_base64 = base64.b64encode(doc["pdf_buffer"].getvalue()).decode("utf-8")
            formatted_docs.append(
                {
                    "document_type": doc["document_type"],
                    "file_name": doc["file_name"],
                    "pdf_base64": pdf_base64,
                }
            )

        # --- BLOQUE EMAIL — fire and forget ---
        email_enviado = False
        debe_enviar_email = data_to_process.get(
            "sendEmail", payload.get("sendEmail", False)
        )
        manager_email: str | None = None
        manager_dn = user_data.get("manager")
        if not manager_dn:
            logger.warning(
                f"[MANAGER_DEBUG] Usuario '{user_data.get('username')}' "
                f"NO tiene atributo 'manager' en user_data. "
                f"El email se enviará SIN CC al jefe."
            )
        else:
            logger.info(
                f"[MANAGER_DEBUG] Usuario '{user_data.get('username')}' "
                f"tiene manager DN"
            )
            try:
                manager_email = resolve_manager_email(manager_dn)
                if manager_email:
                    logger.info(
                        f"[MANAGER_DEBUG] Manager resuelto: {manager_email}"
                    )
                else:
                    logger.warning(
                        f"[MANAGER_DEBUG] No se pudo resolver email del manager "
                        f"para '{user_data.get('username')}'"
                    )
            except ExternalServiceError as e:
                logger.warning(
                    f"[MANAGER_DEBUG] Error LDAP resolviendo manager "
                    f"(continuando sin CC): {e.message}"
                )

        if debe_enviar_email:
            username = user_data["username"]
            full_name = user_data["full_name"]
            tecnico = session.get("tecnico_actual", {})
            tecnico_nombre = tecnico.get(
                "display_name", tecnico.get("username", "el técnico asignado")
            )

            # Buscamos 'emailType' en el borrador o en el payload directo
            input_email_type = data_to_process.get(
                "emailType", payload.get("emailType", "Dotacion")
            )

            tipo = "Renovacion" if "Renovacio" in input_email_type else "Dotacion"

            if tipo == "Renovacion":
                email_enviado = email_service.send_renovacion_email(
                    username, full_name, tecnico_nombre, manager_email
                )
            else:
                email_enviado = email_service.send_dotacion_email(
                    username, full_name, tecnico_nombre, manager_email
                )

        return {
            "acta_id": acta_id,
            "estado": estado_final,
            "usuario": user_data,
            "fecha": docs[0].get("timestamp") if docs else None,
            "tiene_pagare": any(
                eq.get("equipment_type") == EquipmentType.LAPTOP.value
                for eq in equipment_list
            ),
            "documents": formatted_docs,
            "sincronizacion": sync_result_dict
            if sync_request
            else {"solicitada": False},
            "email_enviado": email_enviado,
        }
