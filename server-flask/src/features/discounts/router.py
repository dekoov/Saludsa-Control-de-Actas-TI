from flask import Blueprint, request
from src.core.responses import error_response
from src.core.decorators import requiere_login
import base64
from src.core.responses import success_response, error_response

# Importamos el esquema y servicio de este mismo feature
from src.features.discounts.schemas import validate_discount_payload
from src.features.discounts.service import DiscountDocumentService

discounts_bp = Blueprint('discounts_bp', __name__)
discount_service = DiscountDocumentService()

@discounts_bp.route('/api/discounts/generate', methods=['POST'])
@requiere_login
def generate_discount_acta():
    data = request.json
    try:
        valid_data = validate_discount_payload(data)
        doc_info = discount_service.generate_discount_document(valid_data)

        # 1. Obtenemos el buffer
        pdf_buffer = doc_info["pdf_buffer"]
        pdf_buffer.seek(0)
        
        # 2. Convertimos a Base64
        pdf_base64 = base64.b64encode(pdf_buffer.read()).decode('utf-8')

        # 3. Retornamos en el formato que espera tu frontend (el de Actas)
        response_data = {
            "pdf_base64": pdf_base64,
            "file_name": doc_info["file_name"]
        }

        return success_response(
            data=response_data,
            message="Acta generada exitosamente",
            status_code=200
        )

    except Exception as e:
        return error_response(message="Error crítico", details=str(e), status_code=500)
