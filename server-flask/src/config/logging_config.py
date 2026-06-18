import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(app=None):
    """
    Configura el logging para la aplicación Flask.
    Si se proporciona app, configura el logger de Flask.
    """
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nombre del archivo de log con fecha
    log_filename = os.path.join(log_dir, f"saludsa_app_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configurar formato de log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurar handler de archivo con rotación
    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)
    
    # Configurar handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configurar logger específico para Playwright
    playwright_logger = logging.getLogger('playwright')
    playwright_logger.setLevel(logging.WARNING)
    
    # Configurar logger específico para SQLAlchemy
    sqlalchemy_logger = logging.getLogger('sqlalchemy')
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    # Si se proporciona app Flask, configurar su logger
    if app:
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)
    
    logging.info("Sistema de logging inicializado")
