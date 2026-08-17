# src/features/actas/helpers.py
"""Helpers puros para la generación de documentos de actas.

Este módulo contiene funciones utilitarias sin estado ni side effects que
construyen documentos Word y PDF a partir de plantillas, contextos y nombres
de archivo. Se encarga exclusivamente de transformar template+contexto en un
diccionario con los buffers y metadatos listos para ser enviados o persistidos.
"""

import base64
from io import BytesIO
from typing import Any

from src.infrastructure.documents.document_service import (
    convert_to_pdf_buffer,
    generate_file_docx,
)


def _build_document(
    doc_type: str,
    context: dict[str, Any],
    template: str,
    filename: str,
) -> dict[str, Any]:
    """Construye un documento DOCX/PDF a partir de una plantilla y contexto.

    Función pura: recibe el tipo de documento, el contexto de renderizado, la
    plantilla y el nombre base del archivo; genera el DOCX, lo convierte a PDF
    en memoria y retorna un diccionario con ambos buffers y metadatos.

    Args:
        doc_type: Tipo semántico del documento (por ejemplo, "Acta" o "Pagare").
        context: Diccionario con las variables de reemplazo para la plantilla.
        template: Nombre del archivo de plantilla DOCX ubicado en el directorio
            de templates del proyecto.
        filename: Nombre base para el archivo DOCX generado.

    Returns:
        dict[str, Any]: Diccionario con los siguientes campos:
            - document_type (str): Tipo de documento recibido.
            - file_name (str): Nombre del archivo PDF resultante.
            - pdf_buffer (BytesIO): Buffer en memoria del PDF generado.
            - docx_path (str): Ruta física del archivo DOCX generado.
            - pdf_base64 (str): Representación base64 del contenido del PDF.
    """
    docx_path = generate_file_docx(context, template, filename)
    pdf_buffer: BytesIO = convert_to_pdf_buffer(docx_path)

    return {
        "document_type": doc_type,
        "file_name": filename.replace(".docx", ".pdf"),
        "pdf_buffer": pdf_buffer,
        "docx_path": docx_path,
        "pdf_base64": base64.b64encode(pdf_buffer.getvalue()).decode("utf-8"),
    }
