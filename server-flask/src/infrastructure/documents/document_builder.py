"""Constructor de documentos PDF a partir de plantillas DOCX.

Este módulo actúa como fachada de alto nivel sobre ``document_service``:
recibe el tipo de documento, el contexto de renderizado y la plantilla, y
devuelve un diccionario con el buffer PDF, la ruta DOCX generada y la
representación base64 del PDF.
"""
import base64
from io import BytesIO

from src.infrastructure.documents.document_service import (
    generate_file_docx,
    convert_to_pdf_buffer,
    convert_to_pdf_libreoffice,
)


def build_document(
    doc_type: str,
    context: dict[str, object],
    template: str,
    filename: str,
) -> dict[str, object]:
    """Construye un documento PDF a partir de una plantilla DOCX y un contexto.

    Renderiza la plantilla con el contexto proporcionado, convierte el DOCX
    resultante a PDF en memoria y retorna todos los artefactos generados.

    Args:
        doc_type: Tipo o categoría del acta/documento (ej. "Acta de Entrega").
        context: Diccionario con las variables de reemplazo para la plantilla.
        template: Nombre del archivo de plantilla DOCX ubicado en
            ``src/infrastructure/documents/templates/``.
        filename: Nombre base para el archivo DOCX de salida.

    Returns:
        dict[str, object]: Diccionario con:
            - ``document_type`` (str): Tipo de documento recibido.
            - ``file_name`` (str): Nombre del PDF equivalente al DOCX.
            - ``pdf_buffer`` (BytesIO): Buffer en memoria con el contenido PDF.
            - ``docx_path`` (str): Ruta absoluta del archivo DOCX generado.
            - ``pdf_base64`` (str): Representación base64 del contenido PDF.

    Raises:
        ExternalServiceError: Si falla la generación del DOCX o la conversión
            a PDF.
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
