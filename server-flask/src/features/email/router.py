from flask import Blueprint, request, session
from src.features.email import email_service
from src.core.responses import success_response, error_response
from src.core.decorators import requiere_login

email_bp = Blueprint('email_bp', __name__)

@email_bp.route('/api/email/test', methods=['POST'])
@requiere_login
def test_email():
    data = request.get_json() or {}
    recipient = data.get("test_recipient")

    if not recipient:
        return error_response("Falta el destinatario de prueba", 400)

    success = email_service._send(
        to      = recipient,
        cc      = email_service._build_cc_list(),
        subject = "Prueba de configuración SMTP — Saludsa App",
        body    = "Este es un correo de prueba para verificar la configuración SMTP."
    )

    if success:
        return success_response(message="Correo de prueba enviado correctamente")
    return error_response("No se pudo enviar el correo — revisar configuración SMTP", 500)
