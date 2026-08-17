"""Rutas HTTP para la generación de actas de descuento.

Expone un endpoint para generar un documento PDF de acta de descuento a partir
de los datos del empleado y el equipo a descontar. No realiza persistencia en
base de datos. Requiere sesión activa del técnico.
"""

import base64
from typing import Any

from flask import Blueprint, request

from src.api.responses import error_response, success_response
from src.core.decorators import requiere_login

# Importamos el esquema y servicio de este mismo feature
from src.features.discounts.schemas import validate_discount_payload
from src.features.discounts.service import DiscountDocumentService

discounts_bp = Blueprint("discounts_bp", __name__)
discount_service = DiscountDocumentService()


@discounts_bp.route("/api/discounts/generate", methods=["POST"])
@requiere_login
def generate_discount_acta():
    """Genera el documento PDF de un acta de descuento.

    Valida el payload, genera el documento Word/PDF mediante el servicio de
    descuentos y retorna el contenido PDF codificado en base64 junto con el
    nombre del archivo.

    HTTP:
        POST /api/discounts/generate

    Headers:
        Authorization: Sesión Flask activa.
        Content-Type: application/json

    Request JSON:
        {
            "usuario": {
                "full_name": str,
                "national_id": str,
                "username": str
            },
            "equipos": list[dict],      # Al menos un equipo.
            "deduction_month": str      # Mes de aplicación del descuento.
        }

    Returns:
        Response: JSON 200 con:
            {
                "success": true,
                "data": {
                    "pdf_base64": str,
                    "file_name": str
                },
                "message": "Acta generada exitosamente"
            }

    Response codes:
        200: Documento generado correctamente.
        400: Payload inválido según validate_discount_payload.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error crítico durante la generación del documento.
    """
    data: dict[str, Any] | None = request.json
    try:
        valid_data = validate_discount_payload(data)
        doc_info = discount_service.generate_discount_document(valid_data)

        # 1. Obtenemos el buffer
        pdf_buffer = doc_info["pdf_buffer"]
        pdf_buffer.seek(0)

        # 2. Convertimos a Base64
        pdf_base64 = base64.b64encode(pdf_buffer.read()).decode("utf-8")

        # 3. Retornamos en el formato que espera tu frontend (el de Actas)
        response_data = {"pdf_base64": pdf_base64, "file_name": doc_info["file_name"]}

        return success_response(
            data=response_data, message="Acta generada exitosamente", status_code=200
        )

    except Exception as e:
        return error_response(message="Error crítico", details=str(e), status_code=500)
