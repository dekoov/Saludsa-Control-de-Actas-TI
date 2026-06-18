import os
import subprocess
import io
from docxtpl import DocxTemplate
from src.config import resolve_route
from src.core.exceptions import ExternalServiceError

# Este codigo le vendria bien una refactorizacion mucho ESPANGLISH > actas_route.py - document_service.py

def get_save_directory() -> str:
    """
    Determina la ruta de guardado basada en la existencia de OneDrive - Saludsa.
    Prioridad: 
    """
    user_home = os.path.expanduser('~')
    onedrive_path = os.path.join(user_home, 'OneDrive - SALUD S.A')
    
    # Decidir carpeta base
    if os.path.exists(onedrive_path):
        base_dir = os.path.join(onedrive_path, 'Documentos')
    else:
        base_dir = os.path.join(user_home, 'Documents')
    
    # Crear carpeta final
    save_dir = os.path.join(base_dir, 'Actas_Generadas')
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def generate_file_docx(context: dict, template_filename: str, output_filename: str) -> str:
    """Toma un diccionario de contexto, llena la plantilla especificada y guarda en disco"""

    try:
        template_path = resolve_route(f'src/templates/{template_filename}', is_frontend=False)
        doc = DocxTemplate(template_path)
        context['legal_representative_name'] = os.getenv('LEGAL_REPRESENTATIVE_NAME', '[REPRESENTANTE LEGAL DEBE CONFIGURARSE EN ENV]')
        context['legal_representative_id'] = os.getenv('LEGAL_REPRESENTATIVE_ID', '[CEDULA DEBE CONFIGURARSE EN ENV]')
        doc.render(context)
        save_dir = get_save_directory()
        save_path = os.path.join(save_dir, output_filename)
        doc.save(save_path)

        return save_path
    except Exception as e:
        raise ExternalServiceError("Error al generar el documento Word", payload=str(e))

def convert_to_pdf_libreoffice(docx_path: str):
    libreoffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    output_dir = os.path.dirname(docx_path)
    command = [
        libreoffice_path,
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', output_dir,
        docx_path
    ]
    try:
        subprocess.run(command, check=True, shell=True)
        pdf_path = docx_path.replace('.docx', '.pdf')
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"LibreOffice no genero el archivo en: {pdf_path}")
        return pdf_path
    except Exception as e:
        raise ExternalServiceError("Error al convertir DOCX a PDF usando LibreOffice", payload=str(e))

def convert_to_pdf_buffer(docx_path: str) -> io.BytesIO:
    """Convierte un docx a pdf, lo lee en memoria y borra el pdf temporal"""
    pdf_path = None
    try:
        pdf_path = convert_to_pdf_libreoffice(docx_path)
        # Leer el archivo en memoria
        with open(pdf_path, 'rb') as f:
            buffer = io.BytesIO(f.read())
        buffer.seek(0)
        return buffer
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

