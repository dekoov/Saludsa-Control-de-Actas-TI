import logging

from flask import session
from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPExceptionError

from src.config.config import config
from src.core.exceptions import ExternalServiceError, ValidationError
from src.infrastructure.ldap.ldap_helpers import obtener_upn_dinamico

logger = logging.getLogger(__name__)


def create_ldap_connection(upn=None, password=None):
    """
    Crea y retorna una conexión LDAP dinámica utilizando el UPN calculado por el helper.

    Args:
        upn: UPN completo (opcional). Si no se provee, se calcula desde la sesión Flask.
        password: Contraseña (opcional). Si no se provee, se toma de la sesión Flask.

    Raises:
        ValidationError: Si no hay sesión activa o faltan credenciales del técnico.
        ExternalServiceError: Si falta configuración del servidor o falla la conexión/bind LDAP.
    """
    if not upn or not password:
        tecnico = session.get("tecnico_actual")
        pass_retained = session.get("ldap_password")

        if not tecnico or not pass_retained:
            raise ValidationError(
                message="No hay una sesión activa con credenciales LDAP válidas",
                payload={
                    "tecnico_presente": bool(tecnico),
                    "password_presente": bool(pass_retained),
                },
            )

        username = tecnico.get("username")
        if not username:
            raise ValidationError(
                message="El técnico en sesión no tiene username",
                payload={
                    "tecnico_keys": list(tecnico.keys())
                    if isinstance(tecnico, dict)
                    else None
                },
            )

        password = pass_retained
        upn = obtener_upn_dinamico(username)

    if not config.LDAP_SERVER:
        raise ExternalServiceError(
            message="Falta la variable de entorno LDAP_SERVER",
            payload={"config_key": "LDAP_SERVER"},
        )

    try:
        server = Server(config.LDAP_SERVER, get_info=ALL, connect_timeout=3)
        conn = Connection(
            server,
            user=upn,
            password=password,
            auto_bind=True,
            auto_referrals=False,
            receive_timeout=10,
        )
        return conn

    except LDAPExceptionError as e:
        logger.error(f"Fallo de conexión/bind LDAP para {upn}: {e!s}")
        raise ExternalServiceError(
            message="No se pudo establecer conexión con el servidor de directorio",
            payload={"upn": upn, "ldap_server": config.LDAP_SERVER, "detail": str(e)},
        ) from e

    except Exception as e:
        logger.error(f"Fallo inesperado al crear conexión LDAP para {upn}: {e!s}")
        raise ExternalServiceError(
            message="Error inesperado al conectar con el servicio de directorio",
            payload={"upn": upn, "detail": str(e)},
        ) from e
