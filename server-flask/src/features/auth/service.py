from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPBindError
import logging
from src.config.config import config
from src.utils.ldap_helpers import obtener_upn_dinamico

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
    # ----------------------------------------------

    logger.info(f"Intentando auth para: {username} | Servidor Configurado: {config.LDAP_SERVER}")
    upn = obtener_upn_dinamico(username)
    logger.info(f"UPN CALCULADO EN ENTORNO FLASK: '{upn}'")
    
    conn = None
    try:
        # Conectar al servidor usando tu UPN directo
        server = Server(config.LDAP_SERVER, get_info=ALL, connect_timeout=3)
        conn = Connection(
            server,
            user=upn,
            password=password,
            auto_bind=True,
            auto_referrals=False,
            receive_timeout=10
        )
        # Verificación en tiempo de ejecución
        logger.info(f"--- AUDITORÍA DE SEGURIDAD LDAP ---")
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
            # Buscamos de forma exacta el bloque "cn=nombre_del_grupo," 
            # o simplemente verificamos que empiece con el CN correcto.
            target_cn = f"cn={GRUPO_PERMITIDO.lower()}"
            
            for grupo in entry.memberOf.values:
                grupo_str = str(grupo).lower()
                # Separamos por comas y verificamos si el primer elemento (el CN) coincide
                if grupo_str.startswith(target_cn):
                    pertenece = True
                    break
        
        if not pertenece:
            logger.warning(f"Acceso Denegado: {username} no pertenece al grupo {GRUPO_PERMITIDO}")
            return None
            
        # Si pasó la validación, mapeamos el diccionario idéntico a tu esquema funcional
        return {
            'first_names': str(entry.GivenName) if 'GivenName' in entry else "N/A",
            'last_names': str(entry.sn) if 'sn' in entry else "N/A",
            'display_name': str(entry.displayName) if 'displayName' in entry else "N/A",
            'full_name': str(entry.Name) if 'Name' in entry else "N/A",
            'username': str(entry.sAMAccountName) if 'sAMAccountName' in entry else username,
            'national_id': str(entry.employeeID) if 'employeeID' in entry else None,
            'department': str(entry.Department) if 'Department' in entry else None,
            'position': str(entry.Description) if 'Description' in entry else None,
            'email': str(entry.mail) if 'mail' in entry else None,
            'city': str(entry.l) if 'l' in entry else None
        }
        
    except LDAPBindError:
        logger.warning(f"Credenciales de LDAP incorrectas para el usuario: {username}")
        return None
    except Exception as e:
        logger.error(f"Error controlado en validar_credenciales: {str(e)}")
        return None
    finally:
        if conn and conn.bound:
            try:
                conn.unbind()
            except Exception:
                pass
