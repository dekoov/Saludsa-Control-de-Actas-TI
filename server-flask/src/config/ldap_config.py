from ldap3 import Server, Connection, ALL
from flask import session
import logging
from .config import config
from src.utils.ldap_helpers import obtener_upn_dinamico

logger = logging.getLogger(__name__)

def create_ldap_connection(upn=None, password=None):
    """
    Crea y retorna una conexión LDAP dinámica utilizando el UPN calculado por el helper.
    """
    if not upn or not password:
        tecnico = session.get("tecnico_actual")
        pass_retained = session.get("ldap_password")
        
        if not tecnico or not pass_retained:
            raise Exception("No hay una sesión activa con credenciales LDAP válidas.")
            
        username = tecnico.get("username")
        password = pass_retained

        upn = obtener_upn_dinamico(username)

    if not config.LDAP_SERVER:
        raise Exception("Falta la variable de entorno LDAP_SERVER")

    try:
        server = Server(config.LDAP_SERVER, get_info=ALL, connect_timeout=3)
        return Connection(
            server,
            user=upn,
            password=password,
            auto_bind=True,
            auto_referrals=False,
            receive_timeout=10
        )
    except Exception as e:
        logger.error(f"Fallo al crear la conexión LDAP dinámica para {upn}: {str(e)}")
        raise e
