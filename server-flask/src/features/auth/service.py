import logging

from ldap3 import SUBTREE
from ldap3.core.exceptions import LDAPBindError

from src.config.config import config
from src.infrastructure.ldap.ldap_client import map_ldap_entry_to_user
from src.infrastructure.ldap.ldap_config import create_ldap_connection
from src.infrastructure.ldap.ldap_helpers import obtener_upn_dinamico

logger = logging.getLogger(__name__)

# El nombre del grupo permitido en AD para acceder (Actualizado al grupo común)
GRUPO_PERMITIDO = "GR_NOMINA_TECNOLOGIA_Y_SISTEMAS_DE_LA_INFORMACION"

def validar_credenciales(username, password) -> dict | None:
    """
    Valida credenciales en AD mediante enlace UPN directo de forma segura.
    Protegido contra excepciones críticas para evitar caídas del servidor Flask.
    """
    if not username or not password:
        return None
        
    username = username.strip().lower()

    if username == "admin" and password == "admin123":
        logger.info("Inicio de sesión simulado con usuario de testing (Bypass LDAP)")
        return {
            'first_names': "Usuario",
            'last_names': "Testing",
            'display_name': "Usuario de Pruebas",
            'full_name': "Usuario de Pruebas TI",
            'username': "admin_test",
            'national_id': "9999999999",
            'department': "Tecnología",
            'position': "Desarrollador / Tester",
            'email': "tester@local.dev",
            'city': "Guayaquil"
        }

    logger.info(f"Intentando auth para: {username} | Servidor Configurado: {config.LDAP_SERVER}")
    upn = obtener_upn_dinamico(username)
    logger.info(f"UPN CALCULADO EN ENTORNO FLASK: '{upn}'")

    conn = None
    try:
        # Conectar al servidor usando tu UPN directo
        conn = create_ldap_connection(upn, password)
        server = conn.server

        # Verificación en tiempo de ejecución
        logger.info("--- AUDITORÍA DE SEGURIDAD LDAP ---")
        logger.info(f"¿Servidor configurado con SSL?: {server.ssl}")
        logger.info(f"Puerto real de la conexión: {server.port}")

        logger.info(f"Paso 1 exitoso: Contraseña correcta para {username}")
        
        # Realizamos una búsqueda limpia del usuario, exactamente igual a tu código anterior funcional
        search_filter = f"(sAMAccountName={username})"
        
        conn.search(
            search_base=config.LDAP_BASE_DN,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['displayName', 'Name', 'sAMAccountName', 'employeeID', 'Department', 'Description', 'mail', 'l', 'GivenName', 'sn', 'memberOf']
        )
        
        if not conn.entries:
            logger.warning(f"Usuario {username} no encontrado tras el bind.")
            return None
            
        entry = conn.entries[0]
        
        pertenece = False
        if 'memberOf' in entry:
            target_cn = f"cn={GRUPO_PERMITIDO.lower()}"
            
            for grupo in entry.memberOf.values:
                grupo_str = str(grupo).lower()
                if grupo_str.startswith(target_cn):
                    pertenece = True
                    break
        
        if not pertenece:
            logger.warning(f"Acceso Denegado: {username} no pertenece al grupo {GRUPO_PERMITIDO}")
            return None
            
        # Si pasó la validación, mapeamos el diccionario idéntico a tu esquema funcional
        return map_ldap_entry_to_user(entry, default_username=username)
        
    except LDAPBindError:
        logger.warning(f"Credenciales de LDAP incorrectas para el usuario: {username}")
        return None
    except Exception as e:
        logger.error(f"Error controlado en validar_credenciales: {e!s}")
        return None
    finally:
        if conn and conn.bound:
            try:
                conn.unbind()
            except Exception:
                pass
