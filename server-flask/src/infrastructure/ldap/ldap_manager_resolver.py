import logging
import re

from ldap3 import SUBTREE
from ldap3.core.exceptions import LDAPExceptionError

from src.config.config import config
from src.core.exceptions import ExternalServiceError
from src.infrastructure.ldap.ldap_config import create_ldap_connection

logger = logging.getLogger(__name__)


def extract_cn_from_dn(manager_dn: str) -> str | None:
    """
    Extrae el Common Name (CN) de un Distinguished Name (DN).
    Ej: 'CN=CHOEZ PIGUAVE RONNY LUIS,OU=...' -> 'CHOEZ PIGUAVE RONNY LUIS'
    """
    if not manager_dn or not isinstance(manager_dn, str):
        return None

    match = re.match(r"CN=([^,]+)", manager_dn.strip(), re.IGNORECASE)
    if not match:
        logger.warning(f"extract_cn_from_dn: formato de DN inesperado '{manager_dn}'")
        return None

    return match.group(1).strip()


def resolve_manager_email(manager_dn: str | None) -> str | None:
    """
    Resuelve el correo del jefe inmediato a partir de su DN en Active Directory.

    - Retorna el email si lo encuentra.
    - Retorna None si no hay manager, no se encuentra o no tiene email.
    - Propaga ExternalServiceError si hay un fallo real de conexión/servicio LDAP.
    """
    if not manager_dn:
        return None

    cn = extract_cn_from_dn(manager_dn)
    if not cn:
        return None

    conn = None
    try:
        # create_ldap_connection ahora lanza ValidationError o ExternalServiceError
        conn = create_ldap_connection()

        conn.search(
            search_base=config.LDAP_BASE_DN,
            search_filter=f"(CN={cn})",
            search_scope=SUBTREE,
            attributes=["sAMAccountName", "mail", "displayName"],
            size_limit=1,
        )

        if not conn.entries:
            logger.info(f"resolve_manager_email: no se encontró manager con CN='{cn}'")
            return None

        entry = conn.entries[0]

        mail = getattr(entry, "mail", None)
        if mail and mail.value:
            return str(mail.value).strip().lower()

        sam = getattr(entry, "sAMAccountName", None)
        if sam and sam.value:
            return f"{sam.value}@{config.EMAIL_DOMAIN}".lower()

        logger.warning(
            f"resolve_manager_email: manager '{cn}' sin mail ni sAMAccountName"
        )
        return None

    except LDAPExceptionError as e:
        logger.error(
            f"resolve_manager_email: error LDAP buscando manager '{cn}': {e!s}"
        )
        raise ExternalServiceError(
            message="Error del servicio de directorio al consultar el jefe inmediato",
            payload={"manager_cn": cn, "detail": str(e)},
        ) from e

    finally:
        if conn and conn.bound:
            conn.unbind()
