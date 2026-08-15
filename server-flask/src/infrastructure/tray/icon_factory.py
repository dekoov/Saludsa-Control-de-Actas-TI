import os
import sys

from PIL import Image, ImageDraw


def crear_icono_por_defecto():
    """Genera un icono temporal (un cuadrado azul con bordes redondeados)."""
    img = Image.new("RGB", (64, 64), color=(30, 144, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([(16, 16), (48, 48)], fill=(255, 255, 255))
    return img


def cargar_icono(application_path: str):
    """Intenta cargar el favicon del proyecto; si falla, usa el icono por defecto."""
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
