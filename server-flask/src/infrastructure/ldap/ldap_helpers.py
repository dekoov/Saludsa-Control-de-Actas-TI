import logging
import re

from src.config.config import config
from src.core.exceptions import ExternalServiceError, ValidationError

logger = logging.getLogger(__name__)


def obtener_upn_dinamico(username: str) -> str:
    """
    Toma un sAMAccountName y calcula su UPN dinámicamente
    extrayendo las particiones DC del LDAP_BASE_DN.

    Raises:
        ValidationError: Si el username está vacío o es inválido.
        ExternalServiceError: Si LDAP_BASE_DN no está configurado o está malformado.
    """
    if not username or not isinstance(username, str):
        raise ValidationError(
            message="El username es requerido para calcular el UPN dinámico",
            payload={"username": username},
        )

    username = username.strip().lower().replace("|", "").strip()
    username = re.sub(r"[^a-zA-Z0-9._-]", "", username)

    if not username:
        raise ValidationError(
            message="El username quedó vacío después de saneamiento",
            payload={"original": username},
        )

    if not config.LDAP_BASE_DN:
        raise ExternalServiceError(
            message="LDAP_BASE_DN no está configurado en el entorno",
            payload={"config_key": "LDAP_BASE_DN"},
        )

    try:
        parts = [
            p.split("=")[1]
            for p in config.LDAP_BASE_DN.split(",")
            if p.lower().strip().startswith("dc=")
        ]

        if not parts:
            raise ValueError("No se encontraron componentes DC en LDAP_BASE_DN")

        domain = ".".join(parts)
        return f"{username}@{domain}"

    except Exception as e:
        logger.error(f"Error al calcular UPN dinámico desde LDAP_BASE_DN: {e!s}")
        raise ExternalServiceError(
            message="LDAP_BASE_DN está malformado; no se pudo calcular el dominio",
            payload={"ldap_base_dn": config.LDAP_BASE_DN, "detail": str(e)},
        ) from e
