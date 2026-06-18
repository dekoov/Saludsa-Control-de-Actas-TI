from ldap3 import SUBTREE
import logging
from src.config.ldap_config import create_ldap_connection
from src.config.config import config

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
            results.append({
                'first_names': str(entry.GivenName) if 'GivenName' in entry else "N/A",
                'last_names': str(entry.sn) if 'sn' in entry else "N/A",
                'display_name': str(entry.displayName) if 'displayName' in entry else "N/A",
                'full_name': str(entry.Name) if 'Name' in entry else "N/A",
                'username': str(entry.sAMAccountName) if 'sAMAccountName' in entry else None,
                'national_id': str(entry.employeeID) if 'employeeID' in entry else None,
                'department': str(entry.Department) if 'Department' in entry else None,
                'position': str(entry.Description) if 'Description' in entry else None,
                'email': str(entry.mail) if 'mail' in entry else None,
                'city': str(entry.l) if 'l' in entry else None
            })
        return results
        
    except Exception as e:
        logger.error(f"Error en la búsqueda delegada AD: {str(e)}")
        raise Exception(f"Fallo la conexión o búsqueda en LDAP: {str(e)}")
        
    finally:
        if conn and conn.bound:
            conn.unbind()
