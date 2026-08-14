import logging
import re
from src.config.config import config

logger = logging.getLogger(__name__)

def obtener_upn_dinamico(username: str) -> str:
    """
    Toma un sAMAccountName (ej. dcorrea) y calcula su UPN dinámicamente
    extrayendo las particiones DC del LDAP_BASE_DN (ej. dc=saludsa,dc=local -> dcorrea@saludsa.com.ec).
    """
    if not username:
        return ""

    # SANEAMIENTO SEGURO:
    # 1. Pasamos a minúsculas y quitamos espacios extremos
    username = username.strip().lower()
    # 2. Eliminamos el caracter '|' específico y cualquier espacio remanente
    username = username.replace('|', '').strip()
    # 3. Opcional pero recomendado: Dejar solo caracteres válidos para un sAMAccountName
    username = re.sub(f'[^a-zA-Z0-9._-]', '', username)
    try:
        if not config.LDAP_BASE_DN:
            raise ValueError("LDAP_BASE_DN no está configurado en el entorno.")
            
        # Parsea "dc=saludsa,dc=local" -> ['saludsa', 'local']
        parts = [p.split('=')[1] for p in config.LDAP_BASE_DN.split(',') if p.lower().strip().startswith('dc=')]
        domain = ".".join(parts) # "saludsa.local"
        
        return f"{username}@{domain}"
    except Exception as e:
        logger.error(f"Error al calcular UPN dinámico desde LDAP_BASE_DN: {str(e)}")
        # Fallback seguro por si el string de la Base DN llegase a estar malformado
        return f"{username}@saludsa.com.ec"
