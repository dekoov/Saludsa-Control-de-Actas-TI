import os
import io
from typing import List, Dict, Any

from src.features.email import email_service
from src.utils.formatters import fecha_a_texto, ubicacion_a_letras, fecha_a_texto_legal, monto_a_letras
from src.features.actas.enums import DocumentType
from src.features.actas.helpers import _build_document
from src.features.actas.persistence import get_paginated_actas_history, update_acta_status, get_acta_by_id, update_acta_document_paths, update_acta_sync_status
from src.services.document_service import convert_to_pdf_buffer
from src.services.saludsa_bot_service import SaludsaBotService

from src.models.acta import Acta
from src.models.enums import ActaStatus, EquipmentType
from src.core.exceptions import AppError

class ActaDocumentService:
    """
    Servicio de dominio estrictamente dedicado a la generación de documentos físicos/virtuales.
    No realiza persistencia ni interactúa con APIs externas.
    """
    def generate_documents(self, user_data: Dict[str, Any], equipment_list: List[Any]) -> List[Dict]:
        """
        Evalúa la lógica de negocio y genera los documentos correspondientes.
        Retorna una lista con las rutas de los archivos generados.
        """
        if not equipment_list:
            return []
        main_equipment = equipment_list[0]

        # 1. Extraemos los valores de forma segura asumiendo que son diccionarios
        eq_type = main_equipment.get('equipment_type')
        eq_serial = main_equipment.get('serial_number')
        eq_cost = main_equipment.get('purchase_cost', 0)

        context_base = {
            'equipos': equipment_list,
            'full_name': user_data.get('full_name', user_data.get('display_name', 'NA')),
            'national_id': user_data.get('national_id', 'NA'),
            'city': ubicacion_a_letras(user_data.get('city')),
            'actual_date': fecha_a_texto(),
        }

        processed_documents = []

        # 2. Generar el Acta Principal (siempre se genera)
        acta_name = f"ENTREGA_{user_data.get('username')}_{eq_type}_{eq_serial}.docx"
        processed_documents.append(
            _build_document(
                doc_type=DocumentType.ACTA.value,
                context=context_base,
                template='acta_template.docx',
                filename=acta_name
            )
        )

        # 3. Lógica del Pagaré (Solo si el primer elemento es Laptop)
        if main_equipment.get('equipment_type') == EquipmentType.LAPTOP.value:
            pagare_filename = f"PAGARE_{user_data.get('username')}_LAPTOP_{eq_serial}.docx"
            numerical_amount = int(eq_cost)
            text_amount = monto_a_letras(numerical_amount, incluir_centavos=False)
            
            # Copiamos el contexto base y le añadimos los campos exclusivos del pagaré
            context_pagare = context_base.copy()
            context_pagare.update({
                'main_equipment': main_equipment,
                'numerical_amount': numerical_amount,
                'actual_date_header': fecha_a_texto_legal(),
                'text_amount': text_amount
            })

            processed_documents.append(
                _build_document(
                    doc_type=DocumentType.PAGARE.value,
                    context=context_pagare,
                    template='pagare_template.docx',
                    filename=pagare_filename
                )
            )
        # Retorna la lista de archivos creados (puede ser 1 o 2 archivos)
        return processed_documents


class ActaHistoryService:
    """
    Servicio dedicado a la recuperación y formateo del historial de actas.
    """
    def fetch_history(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Obtenemos la data cruda paginada desde persistencia
        pagination = get_paginated_actas_history(filters)
        
        # 2. Formateamos la data para la vista del frontend
        formatted_data = []
        for acta in pagination.items:
            equipos_resumen_parts = []
            
            for activo in acta.activos:
                # Usamos getattr por seguridad en caso de que hostname no esté poblado
                hostname = getattr(activo, 'hostname', 'N/A')
                equipos_resumen_parts.append(
                    f"Host: {hostname} | SN: {activo.serial_number} | {activo.manufacturer} {activo.model}"
                )
            
            num_accesorios = len(acta.accesorios)
            str_accesorios = f"+{num_accesorios} accesorios" if num_accesorios > 0 else "Sin accesorios"
                
            formatted_data.append({
                "id": acta.id,
                "fecha": acta.fecha.isoformat() if acta.fecha else None,
                "empleado": {
                    "full_name": acta.empleado.full_name if acta.empleado else "N/A",
                    "username": getattr(acta.empleado, 'username', 'N/A') if acta.empleado else "N/A"
                },
                "equipos_resumen": " / ".join(equipos_resumen_parts) if equipos_resumen_parts else "Sin equipo principal",
                "accesorios_resumen": str_accesorios,
                "tipo": getattr(acta, 'tipo', 'Dotacion'),
                "estado": getattr(acta, 'estado', 'Desconocido'),
                "sincronizado_saludsa": getattr(acta, 'sincronizado_saludsa', False),
                "estado_sincronizacion": getattr(acta, 'estado_sincronizacion', 'pendiente'),
                "tiene_pagare": getattr(acta, 'tiene_pagare', False)
            })
        
        # 3. Retornamos el diccionario listo para la respuesta JSON
        return {
            "items": formatted_data,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page
        }

    def anular_acta(self, acta_id: str) -> bool:
        """Valida las reglas de negocio para la anulación y delega la persistencia."""
        acta = Acta.query.get(acta_id)
        if not acta:
            raise AppError(message=f"No se encontró el acta con ID {acta_id}", status_code=404)
            
        if acta.estado == ActaStatus.ANULADA.value:
            raise AppError(message="El acta ya se encuentra anulada.", status_code=400)

        # Delegación limpia a la capa de persistencia
        update_acta_status(acta_id, ActaStatus.ANULADA.value)
        return True

    def marcar_como_firmada(self, acta_id: str) -> bool:
        """Valida las reglas de negocio para la firma y delega la persistencia."""
        acta = Acta.query.get(acta_id)
        if not acta:
            raise AppError(message=f"No se encontró el acta con ID {acta_id}", status_code=404)

        if acta.estado == ActaStatus.FIRMADA.value:
            raise AppError(message="El acta ya estaba marcada como firmada.", status_code=400)

        # Delegación limpia a la capa de persistencia
        update_acta_status(acta_id, ActaStatus.FIRMADA.value)
        return True

    def get_acta_document_stream(self, acta_id: str, doc_type: str) -> tuple[io.BytesIO, str]:
        """
        Coordina el flujo de descarga de un documento. Si el archivo base no existe, 
        aplica la estrategia de Auto-curación (Self-Healing) regenerándolo desde la data histórica.
        
        Returns:
            tuple: (pdf_buffer: io.BytesIO, filename: str)
        """
        if doc_type not in ['acta', 'pagare']:
            raise AppError(message="El tipo de documento debe ser 'acta' o 'pagare'", status_code=400)

        # 1. Recuperar el acta usando la capa de persistencia aislada
        acta = get_acta_by_id(acta_id)
        if not acta:
            raise AppError(message=f"No se encontró el acta con ID {acta_id}", status_code=404)

        if doc_type == 'pagare' and not acta.tiene_pagare:
            raise AppError(message="Esta acta no cuenta con un pagaré asociado", status_code=400)

        target_path = acta.archivo_acta if doc_type == 'acta' else acta.archivo_pagare

        # 2. Estrategia Self-Healing: Si el archivo físico desapareció, lo volvemos a generar
        if not target_path or not os.path.exists(target_path):
            
            # Reconstituir estructuras necesarias para el ActaDocumentService
            user_data = {
                "username": getattr(acta.empleado, 'username', 'NA'),
                "full_name": getattr(acta.empleado, 'full_name', 'NA'),
                "national_id": getattr(acta.empleado, 'national_id', 'NA'),
                "city": getattr(acta.empleado, 'city', 'Quito')
            }

            equipment_list = []
            
            # SOLUCCIÓN CRÍTICA 1: Forzar la evaluación de la relación o usar una lista vacía si es None
            activos = getattr(acta, 'activos', []) or []
            for activo in activos:
                equipment_list.append({
                    "equipment_type": "Laptop",
                    "serial_number": getattr(activo, 'serial_number', 'NA'),
                    "purchase_cost": getattr(activo, 'purchase_cost', 0),
                    "manufacturer": getattr(activo, 'manufacturer', 'NA'),
                    "model": getattr(activo, 'model', 'NA'),
                    "hostname": getattr(activo, 'hostname', 'NA')
                })
                
            accesorios = getattr(acta, 'accesorios', []) or []
            for accesorio in accesorios:
                equipment_list.append({
                    "equipment_type": getattr(accesorio, 'type', 'Accesorio'),
                    "serial_number": getattr(accesorio, 'serial_number', 'NA'),
                    "purchase_cost": getattr(accesorio, 'purchase_cost', 0),
                    "manufacturer": getattr(accesorio, 'manufacturer', 'NA'),
                    "model": getattr(accesorio, 'model', 'NA')
                })

            # Llamamos al generador de la misma capa de dominio
            doc_service = ActaDocumentService()
            new_docs = doc_service.generate_documents(user_data, equipment_list)
            if not new_docs:
                raise AppError(message="Error crítico interno al regenerar los documentos base", status_code=500)

            # SOLUCIÓN CRÍTICA 2: Asegurar valores 'str' usando el operador 'or' por si el diccionario viene incompleto
            archivo_acta = str(new_docs[0].get('docx_path') or '')
            archivo_pagare = str(new_docs[1].get('docx_path') or '') if len(new_docs) > 1 else None

            if not archivo_acta:
                raise AppError(message="El documento generado no tiene una ruta válida", status_code=500)

            # Actualizar de forma limpia la BD
            update_acta_document_paths(acta_id, archivo_acta, archivo_pagare)
            
            # Reasignamos la ruta correcta una vez subsanado el error de infraestructura
            target_path = archivo_acta if doc_type == 'acta' else archivo_pagare

        # SOLUCIÓN CRÍTICA 3: Garantizar que target_path nunca sea None ni vacío antes de pasar a os.path y buffer
        if not target_path:
            raise AppError(message="No se pudo determinar una ruta física válida para el archivo", status_code=500)

        # 3. Conversión del binario a PDF en memoria
        try:
            pdf_buffer = convert_to_pdf_buffer(target_path)
            filename_base = os.path.basename(target_path).replace('.docx', '.pdf')
            return pdf_buffer, filename_base
        except Exception as e:
            # SOLUCIÓN CRÍTICA 4: Cambiar el parámetro 'details' por 'payload' para alinearse con tu AppError/ExternalServiceError
            raise AppError(message="Error al transformar el archivo original a PDF", payload=str(e), status_code=500)

    def ejecutar_sincronizacion_saludsa(self, acta_id: str) -> dict:
        """
        Recupera el acta de la DB, inicializa el bot de Playwright y actualiza los estados de sincronización.
        """
        # 1. Buscar el registro real usando tu función de persistencia aislada
        acta = get_acta_by_id(acta_id)
        if not acta:
            raise AppError(f"No se encontró ninguna acta con el ID {acta_id}", status_code=404)

        # 2. Reconstruir los datos del Empleado tal como los espera tu Playwright Bot
        usuario_payload = {
            "full_name": acta.empleado.full_name if acta.empleado else "N/A",
            "username": getattr(acta.empleado, 'username', 'N/A') if acta.empleado else "N/A"
        }

        # 3. Mapear Activos y Accesorios de las relaciones reales a la lista plana del Bot
        equipos_payload = []
        
        # Procesar Laptops (Activos principales)
        activos = getattr(acta, 'activos', []) or []
        for activo in activos:
            equipos_payload.append({
                "equipment_type": "Laptop",
                "serial_number": getattr(activo, 'serial_number', 'NA'),
                "purchase_cost": getattr(activo, 'purchase_cost', 0),
                "manufacturer": getattr(activo, 'manufacturer', 'NA'),
                "model": getattr(activo, 'model', 'NA'),
                "hostname": getattr(activo, 'hostname', 'NA'),
                "status": "Bueno"  # O el atributo que guarde el estado físico en tu modelo
            })
            
        # Procesar Componentes Secundarios (Accesorios)
        accesorios = getattr(acta, 'accesorios', []) or []
        for accesorio in accesorios:
            equipos_payload.append({
                "equipment_type": getattr(accesorio, 'type', 'Accesorio'),
                "serial_number": getattr(accesorio, 'serial_number', 'NA'),
                "purchase_cost": getattr(accesorio, 'purchase_cost', 0),
                "manufacturer": getattr(accesorio, 'manufacturer', 'NA'),
                "model": getattr(accesorio, 'model', 'NA'),
                "status": "Bueno"
            })

        # 4. Inicializar el Bot con el entorno del sistema (.env)
        bot = SaludsaBotService(
            username=os.environ.get("SALUDSA_USERNAME", ""),
            password=os.environ.get("SALUDSA_PASSWORD", ""),
            headless=os.environ.get("FLASK_ENV") == "production"
        )

        # 5. Ejecutar la automatización de Playwright
        sync_result = bot.sincronizar_acta(equipos=equipos_payload, usuario=usuario_payload)

        # 6. Persistir el resultado final delegando en update_acta_sync_status
        if sync_result.exitosa:
            update_acta_sync_status(acta_id, exitosa=True, estado_sincronizacion="Exitosa")
            return {
                "exito": True,
                "mensaje": "Sincronización procesada y validada en el portal de Saludsa.",
                "screenshot": sync_result.screenshot_path
            }
        else:
            update_acta_sync_status(acta_id, exitosa=False, estado_sincronizacion="Fallida")
            return {
                "exito": False,
                "mensaje": sync_result.mensaje,
                "error_detalle": sync_result.error_detalle
            }
