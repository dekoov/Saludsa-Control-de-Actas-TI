"""Helpers para cálculo de UPN y saneamiento de credenciales LDAP.

Funciones de utilidad que transforman un ``sAMAccountName`` en un UPN completo
usando el dominio derivado del ``LDAP_BASE_DN`` configurado.
"""
import logging
import re

from src.config.config import config
from src.core.exceptions import ExternalServiceError, ValidationError

logger = logging.getLogger(__name__)


def obtener_upn_dinamico(username: str) -> str:
    """Calcula el UPN dinámico de un usuario a partir de su ``sAMAccountName``.

    Extrae las particiones ``DC`` del ``LDAP_BASE_DN`` configurado para formar
    el dominio y sanitiza el username antes de componer ``username@dominio``.

    Args:
        username: ``sAMAccountName`` del técnico/usuario.

    Returns:
        str: UPN completo en formato ``username@dominio.ldap``.

    Raises:
        ValidationError: Si el username está vacío o queda vacío después de
            saneamiento.
        ExternalServiceError: Si ``LDAP_BASE_DN`` no está configurado o está
            malformado.
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