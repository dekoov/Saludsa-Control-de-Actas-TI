import base64
from typing import Dict, Any

from src.config.config import config
from src.features.actas.schemas import validate_acta_payload
from src.features.actas.persistence import save_acta_to_database
from src.features.drafts.persistence import get_draft_by_id, delete_draft

from src.core.exceptions import ValidationError, DatabaseError, ExternalServiceError
from src.models.enums import ActaStatus, EquipmentType
from src.features.actas.service import ActaDocumentService
from src.services.saludsa_bot_service import SaludsaBotService
from src.features.email import email_service
from flask import session

class ActaOrchestrator:
    """
    Director del flujo de Actas. Coordina la validación, generación de documentos,
    sincronización con sistemas externos (Bot) y la persistencia.
    """
    def __init__(self, doc_service: ActaDocumentService):
        self.doc_service = doc_service

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        
        draft_id = payload.get('draft_id')
        if draft_id:
            draft = get_draft_by_id(draft_id)
            if not draft:
                raise ValidationError(f"No se encontró borrador con ID {draft_id}")
            data_to_process = draft
            marcar_firmada = draft.get('marcar_firmada', False)
            sync_request = draft.get('syncHrPortal', False)
        else: 
            data_to_process = payload
            marcar_firmada = payload.get('marcar_firmada', False)
            sync_request = payload.get('syncHrPortal', False)

        # PASO 1: Validar y limpiar datos
        try:
            clean_data = validate_acta_payload(data_to_process)
        except ValidationError as e:
            raise ValidationError(message="Estructura de datos incorrecta o faltan campos", payload=str(e))

        user_data = clean_data['usuario']
        equipment_list = clean_data['equipos']

        # PASO 2: Generar Documentos
        docs = self.doc_service.generate_documents(user_data, equipment_list)
        if not docs:
            raise ExternalServiceError("No se generaron documentos, revise la información enviada")
        
        # DEFINICIÓN INDEPENDIENTE DEL ESTADO:
        # Se define aquí y NO depende de lo que pase con el bot más adelante.
        estado_final = ActaStatus.FIRMADA.value if marcar_firmada else ActaStatus.PENDIENTE_FIRMA.value

        # PASO 3: Sincronización con el Bot de Saludsa
        sync_result_dict = None
        if sync_request:
            if not config.SALUDSA_USERNAME or not config.SALUDSA_PASSWORD:
                raise ExternalServiceError("Faltan credenciales de Saludsa en la configuración del servidor")

            try:
                bot_service = SaludsaBotService(
                    username=config.SALUDSA_USERNAME,
                    password=config.SALUDSA_PASSWORD,
                    headless=config.is_production(), 
                    timeout_ms=60000
                )
                
                bot_result = bot_service.sincronizar_acta(
                    equipos=equipment_list,
                    usuario=user_data,
                    marcar_firmada=marcar_firmada,
                    max_retries=2
                )
                
                sync_result_dict = {
                    'exitosa': bot_result.exitosa,
                    'mensaje': bot_result.mensaje,
                    'timestamp': bot_result.timestamp,
                    'error_detalle': bot_result.error_detalle
                }
                
                # Se eliminó el IF redundante que reasignaba estado_final aquí.
                    
            except Exception as e:
                sync_result_dict = {
                    'exitosa': False,
                    'mensaje': "Falló la sincronización con YoSoySaludsa por un error inesperado",
                    'timestamp': None,
                    'error_detalle': str(e)
                }
        
        # PASO 4: Persistir en base de datos
        try:
            acta_id = save_acta_to_database(
                equipos=equipment_list,
                usuario=user_data,
                generated_docs=docs,
                estado=estado_final, # Se guarda el estado real sin importar el bot
                sync_result=sync_result_dict
            )
            if not acta_id:
                raise DatabaseError("No se pudo guardar el acta en la base de datos")
        except Exception as e:
            raise DatabaseError(message="Error al guardar acta en base de datos", payload=str(e))

        if draft_id:
            delete_draft(draft_id)

        formatted_docs = []
        for doc in docs:
            pdf_base64 = base64.b64encode(doc['pdf_buffer'].getvalue()).decode('utf-8')
            formatted_docs.append({
                "document_type": doc['document_type'],
                "file_name": doc['file_name'],
                "pdf_base64": pdf_base64
            })
        
        # --- BLOQUE EMAIL — fire and forget ---
        email_enviado = False
        debe_enviar_email = data_to_process.get("sendEmail", payload.get("sendEmail", False))

        if debe_enviar_email:
            username = user_data["username"]
            full_name = user_data["full_name"]
            tecnico = session.get("tecnico_actual", {})
            tecnico_nombre = tecnico.get("display_name", tecnico.get("username", "el técnico asignado"))
            
            # Buscamos 'emailType' en el borrador o en el payload directo
            input_email_type = data_to_process.get("emailType", payload.get("emailType", "Dotacion"))

            tipo = "Renovacion" if "Renovacio" in input_email_type else "Dotacion"

            if tipo == "Renovacion":
                email_enviado = email_service.send_renovacion_email(username, full_name, tecnico_nombre)
            else:
                email_enviado = email_service.send_dotacion_email(username, full_name, tecnico_nombre)

        return {
            "acta_id": acta_id,
            "estado": estado_final,
            "usuario": user_data,
            "fecha": docs[0].get('timestamp') if docs else None,
            "tiene_pagare": any(eq.get('equipment_type') == EquipmentType.LAPTOP.value for eq in equipment_list),
            "documents": formatted_docs,
            "sincronizacion": sync_result_dict if sync_request else {"solicitada": False},
            "email_enviado": email_enviado
        }
