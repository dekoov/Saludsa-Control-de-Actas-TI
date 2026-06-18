# C:/Users/Usuario/Code_/WindSurf/Saludsa-Demo-App/server-flask/src/config/config.py
import os
from typing import Optional, List


class Config:
    """
    Configuración centralizada del proyecto.
    Carga todas las variables de entorno al iniciar la aplicación.
    Uso: from src.config import config
         valor = config.LDAP_SERVER
    """
    
    # === Flask Configuration ===
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG: bool = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    PORT: int = int(os.getenv('PORT', '5000'))

    # === LDAP Configuration ===
    LDAP_SERVER: str = os.getenv('LDAP_SERVER', '')
    LDAP_BASE_DN: str = os.getenv('LDAP_BASE_DN', 'dc=saludsa,dc=com,dc=ec')
    LDAP_SEARCH_LIMIT: int = int(os.getenv('LDAP_SEARCH_LIMIT', '15'))

    # === Saludsa Bot Configuration ===
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    SALUDSA_USERNAME: str = os.getenv('SALUDSA_USERNAME', '')
    SALUDSA_PASSWORD: str = os.getenv('SALUDSA_PASSWORD', '')
    SALUDSA_INTERNAL_IP: str = os.getenv('SALUDSA_INTERNAL_IP', '')
    
    # === Testing & Bypass Configuration ===
    ALLOW_AUTH_BYPASS: bool = os.getenv('ALLOW_AUTH_BYPASS', 'False').lower() == 'true'
    TEST_AUTH_USER: str = os.getenv('TEST_AUTH_USER', 'admin')
    TEST_AUTH_PASS: str = os.getenv('TEST_AUTH_PASS', 'admin123')
    
    # === Email / SMTP Configuration ===
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.office365.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    SMTP_FROM: str = os.getenv('SMTP_FROM', '')
    EMAIL_DOMAIN: str = os.getenv('EMAIL_DOMAIN', 'saludsa.com.ec')
    
    # Manejo del CC de correos: Convierte la cadena "user1,user2" en una lista ['user1', 'user2']
    _cc_usernames_raw: str = os.getenv('EMAIL_CC_USERNAMES', '')
    EMAIL_CC_USERNAMES: List[str] = [u.strip() for u in _cc_usernames_raw.split(',') if u.strip()] if _cc_usernames_raw else []
    
    # === Legal Representative Configuration (Mapeo Seguro) ===
    LEGAL_REPRESENTATIVE_NAME: str = os.getenv('LEGAL_REPRESENTATIVE_NAME', '[REPRESENTANTE LEGAL NO CONFIGURADO]')
    LEGAL_REPRESENTATIVE_ID: str = os.getenv('LEGAL_REPRESENTATIVE_ID', '[CEDULA NO CONFIGURADA]')

    # === Database Configuration (Futuro) ===
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'saludsa_db')
    DB_USER: str = os.getenv('DB_USER', '')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # === API Configuration ===
    API_PREFIX: str = os.getenv('API_PREFIX', '/api')
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')
    
    @classmethod
    def is_production(cls) -> bool:
        return cls.FLASK_ENV.lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        return cls.FLASK_ENV.lower() == 'development'
    
    # === VALIDACIONES ===
    @classmethod
    def validate_ldap_config(cls) -> bool:
        """Valida que las variables del Servidor LDAP estén configuradas."""
        return all([cls.LDAP_SERVER, cls.LDAP_BASE_DN])

    @classmethod
    def validate_bot_config(cls) -> bool:
        """Valida que las credenciales de YoSoySaludsa estén configuradas."""
        return all([cls.SALUDSA_USERNAME, cls.SALUDSA_PASSWORD])

    @classmethod
    def validate_email_config(cls) -> bool:
        """Valida que el servidor SMTP y el emisor estén configurados."""
        return all([cls.SMTP_SERVER, cls.SMTP_FROM, cls.EMAIL_DOMAIN])
    
    # === RECOLECTORES DE VARIABLES FALTANTES ===
    @classmethod
    def get_missing_ldap_vars(cls) -> list:
        """Retorna lista de variables LDAP faltantes."""
        missing = []
        if not cls.LDAP_SERVER:
            missing.append('LDAP_SERVER')
        if not cls.LDAP_BASE_DN:
            missing.append('LDAP_BASE_DN')
        return missing

    @classmethod
    def get_missing_bot_vars(cls) -> list:
        """Retorna lista de variables del bot faltantes."""
        missing = []
        if not cls.SALUDSA_USERNAME:
            missing.append('SALUDSA_USERNAME')
        if not cls.SALUDSA_PASSWORD:
            missing.append('SALUDSA_PASSWORD')
        return missing

    @classmethod
    def get_missing_email_vars(cls) -> list:
        """Retorna lista de variables de correo faltantes."""
        missing = []
        if not cls.SMTP_SERVER:
            missing.append('SMTP_SERVER')
        if not cls.SMTP_FROM:
            missing.append('SMTP_FROM')
        if not cls.EMAIL_DOMAIN:
            missing.append('EMAIL_DOMAIN')
        return missing


# Instancia global para importar directamente
config = Config()
