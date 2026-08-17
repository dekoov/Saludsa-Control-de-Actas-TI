"""Fábrica de iconos para la bandeja del sistema.

Proporciona funciones para generar un icono por defecto programáticamente o
 cargar el favicon del proyecto cuando está disponible.
"""
import os
import sys

from PIL import Image, ImageDraw


def crear_icono_por_defecto() -> Image.Image:
    """Genera un icono por defecto como fallback.

    Returns:
        Image.Image: Imagen de 64x64 píxeles con un cuadrado azul y un rectángulo
        blanco central.
    """
    img = Image.new("RGB", (64, 64), color=(30, 144, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([(16, 16), (48, 48)], fill=(255, 255, 255))
    return img


def cargar_icono(application_path: str) -> Image.Image:
    """Carga el favicon del proyecto o retorna el icono por defecto.

    Args:
        application_path: Ruta base de la aplicación. En modo desarrollo se
            asume que ``client-react/dist`` es hermano de ``server-flask``.

    Returns:
        Image.Image: Imagen lista para usar como icono de bandeja.

    Side Effects:
        Puede leer el archivo ``favicon.svg`` desde disco.
    """
    if getattr(sys, "frozen", False):
        ruta_logo = os.path.join(application_path, "_internal", "dist", "favicon.svg")
    else:
        ruta_logo = os.path.abspath(
            os.path.join(application_path, "..", "client-react", "dist", "favicon.svg")
        )

    if os.path.exists(ruta_logo):
        try:
            return Image.open(ruta_logo)
        except Exception:
            return crear_icono_por_defecto()
    return crear_icono_por_defecto()