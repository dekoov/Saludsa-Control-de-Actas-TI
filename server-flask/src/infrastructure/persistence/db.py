"""Inicialización de la base de datos SQLAlchemy para la aplicación Flask.

Este módulo expone la instancia global ``db`` de ``SQLAlchemy`` y la función
``init_db`` que configura el ``SQLALCHEMY_DATABASE_URI``, inicializa la
extensión y crea todas las tablas definidas por los modelos del dominio.
"""
import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app: Flask) -> None:
    """Inicializa SQLAlchemy con la configuración de la aplicación Flask.

    Resuelve la ruta de la base de datos SQLite en función de si la aplicación
    está congelada (ejecutable compilado) o en desarrollo. Permite sobrescribir
    la URI mediante la variable de entorno ``DATABASE_URI``.

    Args:
        app: Instancia de la aplicación Flask.

    Returns:
        None. Este método no retorna valor.

    Side Effects:
        - Modifica ``app.config`` con ``SQLALCHEMY_DATABASE_URI`` y
          ``SQLALCHEMY_TRACK_MODIFICATIONS``.
        - Inicializa la extensión ``db`` con la aplicación.
        - Crea todas las tablas dentro de un ``app_context``.
        - Imprime por consola la URI final de la base de datos.
    """
    # Obtener la ruta de la aplicación
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    # Configurar SQLite por defecto
    db_path = os.path.join(application_path, "saludsa.db")

    # Permitir sobrescribir con variable de entorno si existe
    database_uri = os.environ.get("DATABASE_URI", f"sqlite:///{db_path}")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar la base de datos
    db.init_app(app)

    # Crear todas las tablas si no existen
    with app.app_context():
        db.create_all()

    print(f"Base de datos inicializada: {database_uri}")