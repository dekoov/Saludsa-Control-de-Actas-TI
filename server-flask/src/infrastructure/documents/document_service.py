"""Servicio de generación y conversión de documentos DOCX/PDF.

Utiliza ``docxtpl`` para renderizar plantillas Word y LibreOffice en modo
headless para convertir DOCX a PDF. La carpeta de salida se resuelve
dinámicamente priorizando OneDrive de Saludsa o la carpeta ``Documents`` del
usuario.
"""
import io
import os
import subprocess

from docxtpl import DocxTemplate

from src.config import config, resolve_route
from src.core.exceptions import ExternalServiceError


def get_save_directory() -> str:
    """Resuelve y crea el directorio donde se almacenan los documentos generados.

    Prioriza ``OneDrive - SALUD S.A/Documentos`` si existe; de lo contrario
    usa ``~/Documents``. Dentro de la carpeta base crea el subdirectorio
    ``Actas_Generadas``.

    Returns:
        str: Ruta absoluta del directorio de salida ``Actas_Generadas``.

    Side Effects:
        Crea el directorio de salida si no existe mediante ``os.makedirs``.
    """
    user_home = os.path.expanduser("~")
    onedrive_path = os.path.join(user_home, "OneDrive - SALUD S.A")

    # Decidir carpeta base
    if os.path.exists(onedrive_path):
        base_dir = os.path.join(onedrive_path, "Documentos")
    else:
        base_dir = os.path.join(user_home, "Documents")

    # Crear carpeta final
    save_dir = os.path.join(base_dir, "Actas_Generadas")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def generate_file_docx(
    context: dict[str, object],
    template_filename: str,
    output_filename: str,
) -> str:
    """Genera un archivo DOCX renderizando una plantilla con el contexto dado.

    Inyecta automáticamente en el contexto los datos del representante legal
    definidos en la configuración y guarda el resultado en el directorio
    retornado por ``get_save_directory``.

    Args:
        context: Variables de reemplazo para la plantilla DOCX.
        template_filename: Nombre del archivo de plantilla dentro de
            ``src/infrastructure/documents/templates/``.
        output_filename: Nombre con el que se guardará el archivo DOCX.

    Returns:
        str: Ruta absoluta del archivo DOCX generado.

    Raises:
        ExternalServiceError: Si ocurre cualquier error durante la carga de la
            plantilla, el renderizado o el guardado del documento.
    """
    try:
        template_path = resolve_route(
            f"src/infrastructure/documents/templates/{template_filename}",
            is_frontend=False,
        )
        doc = DocxTemplate(template_path)
        context["legal_representative_name"] = config.LEGAL_REPRESENTATIVE_NAME
        context["legal_representative_id"] = config.LEGAL_REPRESENTATIVE_ID
        doc.render(context)
        save_dir = get_save_directory()
        save_path = os.path.join(save_dir, output_filename)
        doc.save(save_path)

        return save_path
    except Exception as e:
        raise ExternalServiceError(
            "Error al generar el documento Word", payload=str(e)
        ) from e


def convert_to_pdf_libreoffice(docx_path: str) -> str:
    """Convierte un archivo DOCX a PDF usando LibreOffice en modo headless.

    Args:
        docx_path: Ruta absoluta del archivo DOCX a convertir.

    Returns:
        str: Ruta absoluta del archivo PDF generado.

    Raises:
        ExternalServiceError: Si LibreOffice falla o no genera el archivo PDF.
    """
    libreoffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    output_dir = os.path.dirname(docx_path)
    command = [
        libreoffice_path,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        output_dir,
        docx_path,
    ]
    try:
        subprocess.run(command, check=True, shell=True)
        pdf_path = docx_path.replace(".docx", ".pdf")
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(
                f"LibreOffice no genero el archivo en: {pdf_path}"
            )
        return pdf_path
    except Exception as e:
        raise ExternalServiceError(
            "Error al convertir DOCX a PDF usando LibreOffice", payload=str(e)
        ) from e


def convert_to_pdf_buffer(docx_path: str) -> io.BytesIO:
    """Convierte un DOCX a PDF y lo carga en un buffer en memoria.

    El PDF temporal generado por LibreOffice se elimina después de leerlo,
    conservando únicamente el buffer en memoria.

    Args:
        docx_path: Ruta absoluta del archivo DOCX a convertir.

    Returns:
        io.BytesIO: Buffer posicionado al inicio con el contenido binario del
        PDF.

    Raises:
        ExternalServiceError: Si falla la conversión a PDF.

    Side Effects:
        Crea y luego elimina un archivo PDF intermedio en disco.
    """
    pdf_path: str | None = None
    try:
        pdf_path = convert_to_pdf_libreoffice(docx_path)
        # Leer el archivo en memoria
        with open(pdf_path, "rb") as f:
            buffer = io.BytesIO(f.read())
        buffer.seek(0)
        return buffer
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)