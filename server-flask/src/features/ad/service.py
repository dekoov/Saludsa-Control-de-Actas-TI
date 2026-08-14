import logging

from ldap3 import SUBTREE

from src.config.config import config
from src.infrastructure.ldap.ldap_client import map_ldap_entry_to_user
from src.infrastructure.ldap.ldap_config import create_ldap_connection

logger = logging.getLogger(__name__)

def search_user_ad(query):
    """
    Función principal para realizar la búsqueda en Active Directory.
    Utiliza conexión delegada inteligente desde config.
    """
    results = []
    search_base = config.LDAP_BASE_DN
    tokens = query.strip().split()
    conn = None

    try:
        # ¡Magia! create_ldap_connection resolverá la sesión de Flask por nosotros
        conn = create_ldap_connection()

        # CONSTRUCCIÓN DEL FILTRO DINÁMICO
        if len(tokens) > 1:
            sub_filters = "".join([f"(displayName=*{t}*)" for t in tokens])
            search_filter = f"(&{sub_filters})"
        else:
            search_filter = f"(|(sAMAccountName={query}*)(displayName=*{query}*))"
        
        conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['displayName', 'Name', 'sAMAccountName', 'employeeID', 'Department', 'Description', 'mail', 'l', 'GivenName', 'sn'],
            size_limit=config.LDAP_SEARCH_LIMIT 
        )

        for entry in conn.entries:
            results.append(map_ldap_entry_to_user(entry))
        return results
        
    except Exception as e:
        logger.error(f"Error en la búsqueda delegada AD: {str(e)}")
        raise Exception(f"Fallo la conexión o búsqueda en LDAP: {str(e)}")
        
    finally:
        if conn and conn.bound:
            conn.unbind()
