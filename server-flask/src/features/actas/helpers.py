# src/features/actas/helpers.py
import base64
from src.services.document_service import (
    generate_file_docx,
    convert_to_pdf_buffer,
)

def _build_document(doc_type: str, context: dict, template: str, filename: str) -> dict:
    """Función pura: entra template+context, sale dict con buffers listos."""
    docx_path  = generate_file_docx(context, template, filename)
    pdf_buffer = convert_to_pdf_buffer(docx_path)

    return {
        "document_type": doc_type,
        "file_name":     filename.replace('.docx', '.pdf'),
        "pdf_buffer":    pdf_buffer,
        "docx_path":     docx_path,
        "pdf_base64":    base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    }
