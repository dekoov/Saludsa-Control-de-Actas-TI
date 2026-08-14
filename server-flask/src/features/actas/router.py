# src/features/actas/actas_route.py
from flask import Blueprint, request, send_file
from src.core.decorators import requiere_login
from src.core.responses import error_response, success_response
from src.features.actas.orchestrator import ActaOrchestrator
from src.features.actas.service import ActaDocumentService, ActaHistoryService

equipment_bp = Blueprint("equipment_bp", __name__)

doc_service = ActaDocumentService()
acta_orchestrator = ActaOrchestrator(doc_service)
history_service = ActaHistoryService()


@equipment_bp.route("/api/actas/generate", methods=["POST"])
@requiere_login
def generate_acta():
    """
    Endpoint para registrar equipos y generar un acta de entrega.
    El flujo pesado (borradores, PDFs, validación, bot, DB) es delegado al Orquestador.
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
    """
    Obtiene el historial paginado de actas generadas delegando la lógica al servicio.
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
def get_acta_document_pdf(acta_id, doc_type):
    """
    Endpoint para descargar actas o pagarés en formato PDF de forma segura.
    Toda la lógica de negocio, búsquedas y auto-curación se delega al servicio.
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
def marcar_acta_firmada(acta_id):
    """
    Actualiza el estado de un acta específica a 'FIRMADA'.
    """
    data = history_service.marcar_como_firmada(acta_id)
    return success_response(
        data=data,
        message="El acta ha sido marcada como firmada exitosamente.",
        status_code=200,
    )


@equipment_bp.route("/api/actas/<string:acta_id>/sync", methods=["POST"])
@requiere_login
def reintentar_sync(acta_id):
    """
    Vuelve a invocar al bot de Playwright para intentar sincronizar un acta con Saludsa.
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
def anular_acta(acta_id):
    history_service.anular_acta(acta_id)

    return success_response(
        data={"id": acta_id, "estado": "ANULADA"},
        message="El acta ha sido anulada correctamente.",
        status_code=200,
    )
