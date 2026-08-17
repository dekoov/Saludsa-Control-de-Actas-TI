"""Rutas HTTP para pruebas de envío de correo.

Expone un endpoint protegido que permite a un técnico autenticado enviar un
correo de prueba a una dirección específica, verificando la configuración SMTP
del sistema.
"""

from typing import Any

from flask import Blueprint, request

from src.api.responses import error_response, success_response
from src.core.decorators import requiere_login
from src.features.email import email_service

email_bp = Blueprint("email_bp", __name__)


@email_bp.route("/api/email/test", methods=["POST"])
@requiere_login
def test_email():
    """Envía un correo de prueba para validar la configuración SMTP.

    Recibe un destinatario en el body JSON y reutiliza el EmailService para
    enviar un mensaje de prueba, incluyendo la lista de copias configurada.

    HTTP:
        POST /api/email/test

    Headers:
        Authorization: Sesión Flask activa.
        Content-Type: application/json

    Request JSON:
        {
            "test_recipient": str  # Dirección de correo destino.
        }

    Returns:
        Response: JSON 200 si el correo se envió correctamente, o JSON 400/500.

    Response codes:
        200: Correo de prueba enviado correctamente.
        400: Falta el destinatario de prueba.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Fallo en el envío del correo o configuración SMTP incompleta.
    """
    data: dict[str, Any] = request.get_json() or {}
    recipient = data.get("test_recipient")

    if not recipient:
        return error_response("Falta el destinatario de prueba", 400)

    success = email_service._send(
        to=recipient,
        cc=email_service._build_cc_list(),
        subject="Prueba de configuración SMTP — Saludsa App",
        body="Este es un correo de prueba para verificar la configuración SMTP.",
    )

    if success:
        return success_response(message="Correo de prueba enviado correctamente")
    return error_response(
        "No se pudo enviar el correo — revisar configuración SMTP", 500
    )
