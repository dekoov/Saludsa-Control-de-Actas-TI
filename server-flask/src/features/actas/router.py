# src/features/actas/actas_route.py
"""Rutas HTTP del feature Actas para el backend Flask.

Expone endpoints para generar actas, consultar historial paginado, descargar
 documentos PDF, marcar actas como firmadas, reintentar sincronización con
Saludsa y anular actas. Todas las rutas requieren sesión activa del técnico.
"""

from flask import Blueprint, request, send_file

from src.api.responses import error_response, success_response
from src.core.decorators import requiere_login
from src.features.actas.orchestrator import ActaOrchestrator
from src.features.actas.service import ActaDocumentService, ActaHistoryService

equipment_bp = Blueprint("equipment_bp", __name__)

doc_service = ActaDocumentService()
acta_orchestrator = ActaOrchestrator(doc_service)
history_service = ActaHistoryService()


@equipment_bp.route("/api/actas/generate", methods=["POST"])
@requiere_login
def generate_acta():
    """Genera y procesa un acta de entrega de equipos.

    Recibe el payload JSON con usuario, equipos y configuraciones opcionales,
    delega el flujo pesado (validación, PDFs, bot, base de datos, email) al
    ActaOrchestrator y retorna el acta generada con sus documentos y estados.

    HTTP:
        POST /api/actas/generate

    Headers:
        Authorization: Sesión Flask activa (cookie de sesión).
        Content-Type: application/json

    Request JSON:
        {
            "usuario": dict,            # Datos del empleado destinatario.
            "equipos": list[dict],      # Lista de equipos a entregar.
            "marcar_firmada": bool,     # Opcional. Si es true, estado FIRMADA.
            "syncHrPortal": bool,       # Opcional. Solicita sincronización Saludsa.
            "sendEmail": bool,          # Opcional. Envía correo al empleado.
            "emailType": str,           # Opcional. "Dotacion" o "Renovacion".
            "draft_id": int             # Opcional. ID del borrador a usar.
        }

    Returns:
        Response: JSON con código 200 y la estructura:
            {
                "success": true,
                "message": "Acta generada y procesada exitosamente",
                "data": {
                    "acta": {
                        "id": str,
                        "estado": str,
                        "empleado": {"username": str, "full_name": str},
                        "tipo": str,
                        "fecha": str | null,
                        "tiene_pagare": bool
                    },
                    "documents": list[dict],
                    "sincronizacion": dict,
                    "email_enviado": bool
                }
            }

    Response codes:
        200: Acta generada y procesada exitosamente.
        400: El body no es un JSON válido o estructura incorrecta.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno al generar o persistir el acta.
    """
    data = request.json

    if not data or not isinstance(data, dict):
        return error_response(
            message="Se esperaba un objeto JSON válido", status_code=400
        )

    result = acta_orchestrator.execute(payload=data)
    response_data = {
        "acta": {
            "id": result["acta_id"],
            "estado": result["estado"],
            "empleado": {
                "username": result["usuario"].get("username"),
                "full_name": result["usuario"].get("full_name"),
            },
            "tipo": "Dotacion",
            "fecha": result["fecha"],
            "tiene_pagare": result["tiene_pagare"],
        },
        "documents": result["documents"],
        "sincronizacion": result["sincronizacion"],
        "email_enviado": result["email_enviado"],
    }

    return success_response(
        data=response_data,
        message="Acta generada y procesada exitosamente",
        status_code=200,
    )


@equipment_bp.route("/api/actas/historial", methods=["GET"])
@requiere_login
def get_actas_history():
    """Obtiene el historial paginado de actas generadas.

    Recupera actas aplicando filtros de búsqueda, estado, tipo, sincronización,
    pagaré, fechas y modo "solo atención"; delega la consulta y formateo al
    servicio de historial.

    HTTP:
        GET /api/actas/historial

    Headers:
        Authorization: Sesión Flask activa.

    Query Args:
        page (int): Número de página. Default: 1.
        per_page (int): Tamaño de página. Máximo 20, default 10.
        q (str): Búsqueda global por ID, nombre, usuario, serial, modelo, etc.
        estado (str): Filtro por estado(s) separados por coma.
        tipo (str): Filtro por tipo de acta.
        sync_status (str): Filtro por estado de sincronización.
        tiene_pagare (str): "true" o "false".
        fecha_desde (str): Fecha inicial (ISO).
        fecha_hasta (str): Fecha final (ISO).
        solo_atencion (str): "true" para actas que requieren atención.

    Returns:
        Response: JSON 200 con:
            {
                "success": true,
                "message": "Historial recuperado con éxito",
                "data": {
                    "items": list[dict],
                    "total": int,
                    "page": int,
                    "per_page": int
                }
            }

    Response codes:
        200: Historial recuperado exitosamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno del servidor.
    """
    MAX_PER_PAGE = 20
    requested_per_page = request.args.get("per_page", 10, type=int)
    safe_per_page = min(requested_per_page, MAX_PER_PAGE)

    # 1. Empaquetar parámetros de la URL
    filters = {
        "page": request.args.get("page", 1, type=int),
        "per_page": safe_per_page,
        "q": request.args.get("q", ""),
        "estado": request.args.get("estado"),
        "tipo": request.args.get("tipo"),
        "sync_status": request.args.get("sync_status"),
        "tiene_pagare": request.args.get("tiene_pagare"),
        "fecha_desde": request.args.get("fecha_desde"),
        "fecha_hasta": request.args.get("fecha_hasta"),
        "solo_atencion": request.args.get("solo_atencion"),
    }

    # 2. Llamar al servicio
    data = history_service.fetch_history(filters)

    # 3. Retornar respuesta estándar
    return success_response(
        data=data, message="Historial recuperado con éxito", status_code=200
    )


@equipment_bp.route(
    "/api/actas/<string:acta_id>/documents/<string:doc_type>/pdf", methods=["GET"]
)
@requiere_login
def get_acta_document_pdf(acta_id: str, doc_type: str):
    """Descarga un documento del acta en formato PDF.

    Permite obtener el acta principal o el pagaré asociado a un acta. Si el
    archivo físico no existe, aplica auto-curación regenerándolo desde la data
    histórica almacenada en base de datos.

    HTTP:
        GET /api/actas/<acta_id>/documents/<doc_type>/pdf

    Headers:
        Authorization: Sesión Flask activa.

    Args:
        acta_id: Identificador del acta.
        doc_type: Tipo de documento, debe ser "acta" o "pagare".

    Returns:
        Response: Archivo PDF adjunto con Content-Type application/pdf.

    Response codes:
        200: Documento PDF entregado correctamente.
        400: Tipo de documento inválido o acta sin pagaré.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        404: Acta no encontrada.
        500: Error al regenerar o convertir el documento.
    """
    pdf_buffer, filename = history_service.get_acta_document_stream(acta_id, doc_type)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@equipment_bp.route("/api/actas/<string:acta_id>/firmar", methods=["PATCH"])
@requiere_login
def marcar_acta_firmada(acta_id: str):
    """Marca un acta específica como firmada.

    Actualiza el estado del acta a FIRMADA siempre que no esté ya en ese estado.

    HTTP:
        PATCH /api/actas/<acta_id>/firmar

    Headers:
        Authorization: Sesión Flask activa.

    Args:
        acta_id: Identificador del acta a firmar.

    Returns:
        Response: JSON 200 con mensaje de confirmación.

    Response codes:
        200: Acta marcada como firmada.
        400: El acta ya estaba firmada.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        404: Acta no encontrada.
        500: Error interno del servidor.
    """
    data = history_service.marcar_como_firmada(acta_id)
    return success_response(
        data=data,
        message="El acta ha sido marcada como firmada exitosamente.",
        status_code=200,
    )


@equipment_bp.route("/api/actas/<string:acta_id>/sync", methods=["POST"])
@requiere_login
def reintentar_sync(acta_id: str):
    """Reintenta la sincronización de un acta con el portal de Saludsa.

    Recupera el acta, reconstruye los datos de empleado y equipos, ejecuta el
    bot de automatización Playwright y actualiza el estado de sincronización.

    HTTP:
        POST /api/actas/<acta_id>/sync

    Headers:
        Authorization: Sesión Flask activa.

    Args:
        acta_id: Identificador del acta a sincronizar.

    Returns:
        Response: JSON 200 con el resultado de la sincronización:
            {
                "success": true,
                "data": {
                    "id": str,
                    "estado_sincronizacion": str,
                    "screenshot_path": str | null
                }
            }

    Response codes:
        200: Sincronización ejecutada exitosamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        404: Acta no encontrada.
        500: Fallo en la sincronización o error interno.
    """
    resultado = history_service.ejecutar_sincronizacion_saludsa(acta_id)

    return success_response(
        data={
            "id": acta_id,
            "estado_sincronizacion": "Exitosa",
            "screenshot_path": resultado["screenshot"],
        },
        message=resultado["mensaje"],
        status_code=200,
    )


@equipment_bp.route("/api/actas/<string:acta_id>/anular", methods=["PATCH"])
@requiere_login
def anular_acta(acta_id: str):
    """Anula un acta específica.

    Cambia el estado del acta a ANULADA. No elimina el registro de base de datos.

    HTTP:
        PATCH /api/actas/<acta_id>/anular

    Headers:
        Authorization: Sesión Flask activa.

    Args:
        acta_id: Identificador del acta a anular.

    Returns:
        Response: JSON 200 confirmando la anulación:
            {
                "success": true,
                "data": {"id": str, "estado": "ANULADA"},
                "message": "El acta ha sido anulada correctamente."
            }

    Response codes:
        200: Acta anulada correctamente.
        400: El acta ya se encuentra anulada.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        404: Acta no encontrada.
        500: Error interno del servidor.
    """
    history_service.anular_acta(acta_id)

    return success_response(
        data={"id": acta_id, "estado": "ANULADA"},
        message="El acta ha sido anulada correctamente.",
        status_code=200,
    )
