"""Configuración centralizada del backend.

Este módulo carga y expone las variables de entorno utilizadas por la
aplicación Flask a través de la clase ``Config``. También proporciona
métodos de utilidad para validar grupos de variables críticas (LDAP, bot,
correo) y detectar las que aún no han sido configuradas.

Uso típico::

    from src.config import config
    valor = config.LDAP_SERVER
"""

import os


def get_bool_env(name: str, default: bool = False) -> bool:
    """Obtiene una variable de entorno y la convierte a valor booleano.

    Considera como verdaderos los valores ``'true'``, ``'1'``, ``'yes'`` y
    ``'on'`` (insensible a mayúsculas/minúsculas). Si la variable no existe,
    retorna el valor por defecto.

    Args:
        name: Nombre de la variable de entorno a leer.
        default: Valor booleano por defecto si la variable no está definida.

    Returns:
        Representación booleana de la variable de entorno.
    """
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"true", "1", "yes", "on"}


class Config:
    """Configuración centralizada del proyecto.

    Carga todas las variables de entorno al iniciar la aplicación. Los valores
    definidos aquí pueden ser sobreescritos mediante un archivo ``.env`` o
    variables de entorno del sistema operativo.
    """

    # === Flask Configuration ===
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    """str: Entorno de ejecución de Flask (``development`` o ``production``)."""

    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    """bool: Activa o desactiva el modo debug de Flask."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    """str: Clave secreta para la gestión de sesiones de Flask."""

    PORT: int = int(os.getenv("PORT", "5000"))
    """int: Puerto en el que escucha el servidor."""

    # === LDAP Configuration ===
    LDAP_SERVER: str = os.getenv("LDAP_SERVER", "")
    """str: URL o dirección del servidor LDAP."""

    LDAP_BASE_DN: str = os.getenv("LDAP_BASE_DN", "dc=saludsa,dc=com,dc=ec")
    """str: Distinguished Name base utilizado en las búsquedas LDAP."""

    LDAP_SEARCH_LIMIT: int = int(os.getenv("LDAP_SEARCH_LIMIT", "15"))
    """int: Límite de resultados devueltos por una búsqueda LDAP."""

    # === Saludsa Bot Configuration ===
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    """str: Nivel de severidad mínimo para los mensajes de log."""

    PLAYWRIGHT_HEADLESS: bool = get_bool_env(
        "PLAYWRIGHT_HEADLESS",
        default=True,
    )
    """bool: Ejecuta Playwright en modo headless cuando es ``True``."""

    SALUDSA_USERNAME: str = os.getenv("SALUDSA_USERNAME", "")
    """str: Usuario para la autenticación en el portal YoSoySaludsa."""

    SALUDSA_PASSWORD: str = os.getenv("SALUDSA_PASSWORD", "")
    """str: Contraseña para la autenticación en el portal YoSoySaludsa."""

    SALUDSA_INTERNAL_IP: str = os.getenv("SALUDSA_INTERNAL_IP", "")
    """str: IP interna opcional asociada al portal YoSoySaludsa."""

    # === Email / SMTP Configuration ===
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.office365.com")
    """str: Servidor SMTP para el envío de correos."""

    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    """int: Puerto del servidor SMTP."""

    SMTP_FROM: str = os.getenv("SMTP_FROM", "")
    """str: Dirección de correo del remitente por defecto."""

    EMAIL_DOMAIN: str = os.getenv("EMAIL_DOMAIN", "saludsa.com.ec")
    """str: Dominio de correo electrónico de la organización."""

    # Manejo del CC de correos: Convierte la cadena "user1,user2" en una lista ['user1', 'user2']
    _cc_usernames_raw: str = os.getenv("EMAIL_CC_USERNAMES", "")
    EMAIL_CC_USERNAMES: list[str] = (
        [u.strip() for u in _cc_usernames_raw.split(",") if u.strip()]
        if _cc_usernames_raw
        else []
    )
    """list[str]: Lista de usuarios en copia para los correos enviados."""

    # === Legal Representative Configuration (Mapeo Seguro) ===
    LEGAL_REPRESENTATIVE_NAME: str = os.getenv(
        "LEGAL_REPRESENTATIVE_NAME", "[REPRESENTANTE LEGAL NO CONFIGURADO]"
    )
    """str: Nombre del representante legal para documentos."""

    LEGAL_REPRESENTATIVE_ID: str = os.getenv(
        "LEGAL_REPRESENTATIVE_ID", "[CEDULA NO CONFIGURADA]"
    )
    """str: Identificación del representante legal para documentos."""

    # === Database Configuration (Futuro) ===
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    """str | None: URL completa de conexión a la base de datos, si está definida."""

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    """str: Host del servidor de base de datos."""

    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    """int: Puerto del servidor de base de datos."""

    DB_NAME: str = os.getenv("DB_NAME", "saludsa_db")
    """str: Nombre de la base de datos."""

    DB_USER: str = os.getenv("DB_USER", "")
    """str: Usuario de la base de datos."""

    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    """str: Contraseña del usuario de la base de datos."""

    # === API Configuration ===
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    """str: Prefijo base para las rutas de la API REST."""

    # CORS restringido a loopback. main.py ya hardcodea estos orígenes;
    # este default evita que una variable mal configurada abra la app a '*'
    _cors_origins_raw: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5000,http://127.0.0.1:5000",
    )
    CORS_ORIGINS: list[str] = [
        o.strip() for o in _cors_origins_raw.split(",") if o.strip()
    ]
    """list[str]: Orígenes permitidos para solicitudes CORS."""

    @classmethod
    def is_production(cls) -> bool:
        """Determina si la aplicación está configurada en modo producción.

        Returns:
            ``True`` si ``FLASK_ENV`` es ``'production'``; de lo contrario,
            ``False``.
        """
        return cls.FLASK_ENV.lower() == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Determina si la aplicación está configurada en modo desarrollo.

        Returns:
            ``True`` si ``FLASK_ENV`` es ``'development'``; de lo contrario,
            ``False``.
        """
        return cls.FLASK_ENV.lower() == "development"

    # === VALIDACIONES ===
    @classmethod
    def validate_ldap_config(cls) -> bool:
        """Valida que las variables del servidor LDAP estén configuradas.

        Returns:
            ``True`` si ``LDAP_SERVER`` y ``LDAP_BASE_DN`` tienen valor;
            de lo contrario, ``False``.
        """
        return all([cls.LDAP_SERVER, cls.LDAP_BASE_DN])

    @classmethod
    def validate_bot_config(cls) -> bool:
        """Valida que las credenciales de YoSoySaludsa estén configuradas.

        Returns:
            ``True`` si ``SALUDSA_USERNAME`` y ``SALUDSA_PASSWORD`` tienen
            valor; de lo contrario, ``False``.
        """
        return all([cls.SALUDSA_USERNAME, cls.SALUDSA_PASSWORD])

    @classmethod
    def validate_email_config(cls) -> bool:
        """Valida que el servidor SMTP y el emisor estén configurados.

        Returns:
            ``True`` si ``SMTP_SERVER``, ``SMTP_FROM`` y ``EMAIL_DOMAIN``
            tienen valor; de lo contrario, ``False``.
        """
        return all([cls.SMTP_SERVER, cls.SMTP_FROM, cls.EMAIL_DOMAIN])

    # === RECOLECTORES DE VARIABLES FALTANTES ===
    @classmethod
    def get_missing_ldap_vars(cls) -> list[str]:
        """Retorna la lista de variables LDAP que no están configuradas.

        Returns:
            Lista con los nombres de las variables LDAP faltantes. Puede ser
            una lista vacía si todas están configuradas.
        """
        missing = []
        if not cls.LDAP_SERVER:
            missing.append("LDAP_SERVER")
        if not cls.LDAP_BASE_DN:
            missing.append("LDAP_BASE_DN")
        return missing

    @classmethod
    def get_missing_bot_vars(cls) -> list[str]:
        """Retorna la lista de variables del bot que no están configuradas.

        Returns:
            Lista con los nombres de las variables del bot faltantes. Puede ser
            una lista vacía si todas están configuradas.
        """
        missing = []
        if not cls.SALUDSA_USERNAME:
            missing.append("SALUDSA_USERNAME")
        if not cls.SALUDSA_PASSWORD:
            missing.append("SALUDSA_PASSWORD")
        return missing

    @classmethod
    def get_missing_email_vars(cls) -> list[str]:
        """Retorna la lista de variables de correo que no están configuradas.

        Returns:
            Lista con los nombres de las variables de correo faltantes. Puede
            ser una lista vacía si todas están configuradas.
        """
        missing = []
        if not cls.SMTP_SERVER:
            missing.append("SMTP_SERVER")
        if not cls.SMTP_FROM:
            missing.append("SMTP_FROM")
        if not cls.EMAIL_DOMAIN:
            missing.append("EMAIL_DOMAIN")
        return missing


# Instancia global para importar directamente
config = Config()
"""Config: Instancia global de configuración del proyecto."""
