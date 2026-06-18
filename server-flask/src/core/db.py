import os
import sys
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """
    Inicializa la base de datos con la configuración de la aplicación Flask.
    Soporta SQLite por defecto, pero puede configurarse para otros motores.
    """
    # Obtener la ruta de la aplicación
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Configurar SQLite por defecto
    db_path = os.path.join(application_path, 'saludsa.db')
    
    # Permitir sobrescribir con variable de entorno si existe
    database_uri = os.environ.get('DATABASE_URI', f'sqlite:///{db_path}')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar la base de datos
    db.init_app(app)
    
    # Crear todas las tablas si no existen
    with app.app_context():
        db.create_all()
    
    print(f"Base de datos inicializada: {database_uri}")
