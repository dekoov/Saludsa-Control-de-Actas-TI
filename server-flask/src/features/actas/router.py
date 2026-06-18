# src/features/actas/actas_route.py
from flask import Blueprint, request, send_file
from sqlalchemy import desc

# Core y Config
from src.core.responses import success_response, error_response
from src.core.exceptions import AppError

# Dominios y Orquestador
from src.features.actas.service import ActaDocumentService, ActaHistoryService
from src.features.actas.orchestrator import ActaOrchestrator
from src.core.decorators import requiere_login

equipment_bp = Blueprint('equipment_bp', __name__)

# Instanciamos nuestras dependencias (En proyectos más grandes se usa un contenedor de inyección)
doc_service = ActaDocumentService()
acta_orchestrator = ActaOrchestrator(doc_service)
history_service = ActaHistoryService()

@equipment_bp.route('/api/actas/generate', methods=['POST'])
@requiere_login
def generate_acta():
    """
    Endpoint para registrar equipos y generar un acta de entrega.
    El flujo pesado (borradores, PDFs, validación, bot, DB) es delegado al Orquestador.
    """
    data = request.json

    if not data or not isinstance(data, dict):
        return error_response(message="Se esperaba un objeto JSON válido", status_code=400)

    try:
        # ¡Magia! 🪄 Una sola línea delega toda la responsabilidad.
        result = acta_orchestrator.execute(payload=data)

        response_data = {
            "acta": {
                "id": result["acta_id"],
                "estado": result["estado"],
                "empleado": {
                    "username": result["usuario"].get('username'),
                    "full_name": result["usuario"].get('full_name')
                },
                "tipo": "Dotacion",
                "fecha": result["fecha"],
                "tiene_pagare": result["tiene_pagare"]
            },
            "documents": result["documents"],
            "sincronizacion": result["sincronizacion"],
            "email_enviado": result["email_enviado"]
        }

        return success_response(
            data=response_data,
            message="Acta generada y procesada exitosamente",
            status_code=200
        )

    except AppError as e:
        # Atrapa ValidationError, DatabaseError y ExternalServiceError y las mapea limpiamente
        return error_response(message=e.message, details=e.payload, status_code=e.status_code)


@equipment_bp.route('/api/actas/historial', methods=['GET'])
@requiere_login
def get_actas_history():
    """
    Obtiene el historial paginado de actas generadas delegando la lógica al servicio.
    """
    try:
        MAX_PER_PAGE = 20
        requested_per_page = request.args.get('per_page', 10, type=int)
        safe_per_page = min(requested_per_page, MAX_PER_PAGE)

        # 1. Empaquetar parámetros de la URL
        filters = {
            'page': request.args.get('page', 1, type=int),
            'per_page': safe_per_page,
            'q': request.args.get('q', ''),
            'estado': request.args.get('estado'),
            'tipo': request.args.get('tipo'),
            'sync_status': request.args.get('sync_status'),
            'tiene_pagare': request.args.get('tiene_pagare'),
            'fecha_desde': request.args.get('fecha_desde'),
            'fecha_hasta': request.args.get('fecha_hasta'),
            'solo_atencion': request.args.get('solo_atencion')
        }

        # 2. Llamar al servicio
        data = history_service.fetch_history(filters)
        
        # 3. Retornar respuesta estándar
        return success_response(
            data=data,
            message="Historial recuperado con éxito",
            status_code=200
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(message="Error al obtener el historial", details=str(e), status_code=500)


@equipment_bp.route('/api/actas/<string:acta_id>/documents/<string:doc_type>/pdf', methods=['GET'])
@requiere_login
def get_acta_document_pdf(acta_id, doc_type):
    """
    Endpoint para descargar actas o pagarés en formato PDF de forma segura.
    Toda la lógica de negocio, búsquedas y auto-curación se delega al servicio.
    """
    try:
        # Consumimos el servicio de forma directa y elegante
        pdf_buffer, filename = history_service.get_acta_document_stream(acta_id, doc_type)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except AppError as e:
        return error_response(message=e.message, status_code=e.status_code)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(message="Error crítico en el servidor de descargas", details=str(e), status_code=500)

@equipment_bp.route('/api/actas/<string:acta_id>/firmar', methods=['PATCH'])
@requiere_login
def marcar_acta_firmada(acta_id):
    """
    Actualiza el estado de un acta específica a 'FIRMADA'.
    """
    try:
        # Aquí deberías delegar a tu history_service o acta_service
        data = history_service.marcar_como_firmada(acta_id)
        
        # Simulación de respuesta exitosa
        return success_response(
            data=data,
            message="El acta ha sido marcada como firmada exitosamente.",
            status_code=200
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(message="Error al marcar acta como firmada", details=str(e), status_code=500)

@equipment_bp.route('/api/actas/<string:acta_id>/sync', methods=['POST'])
@requiere_login
def reintentar_sync(acta_id):
    """
    Vuelve a invocar al bot de Playwright para intentar sincronizar un acta con Saludsa.
    """
    try:
        # Ejecuta la orquestación del bot y retorna la respuesta procesada
        resultado = history_service.ejecutar_sincronizacion_saludsa(acta_id)
        
        if resultado["exito"]:
            return success_response(
                data={
                    "id": acta_id, 
                    "estado_sincronizacion": "Exitosa", 
                    "screenshot_path": resultado["screenshot"]
                },
                message=resultado["mensaje"],
                status_code=200
            )
        else:
            return error_response(
                message=resultado["mensaje"], 
                details=resultado["error_detalle"], 
                status_code=502  # Bad Gateway porque el portal de Saludsa falló
            )
            
    except AppError as e:
        return error_response(message=e.message, status_code=e.status_code)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(message="El reintento de sincronización falló", details=str(e), status_code=500)

@equipment_bp.route('/api/actas/<string:acta_id>/anular', methods=['PATCH'])
@requiere_login
def anular_acta(acta_id):
    try:
        # ¡Llamamos al borrado lógico del servicio!
        history_service.anular_acta(acta_id)
        
        return success_response(
            data={"id": acta_id, "estado": "ANULADA"},
            message="El acta ha sido anulada correctamente.",
            status_code=200
        )
    except AppError as e:
        return error_response(message=e.message, status_code=e.status_code)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(message="Error crítico al anular el acta", details=str(e), status_code=500)
