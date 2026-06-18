from flask import Blueprint, request, session
import time

from src.core.responses import success_response, error_response
from src.features.auth.service import validar_credenciales

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    Endpoint para autenticar al técnico contra Active Directory.
    Valida credenciales, comprueba grupo de seguridad y guarda los datos temporalmente.
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return error_response(message="El usuario y la contraseña son requeridos", status_code=400)
        
    username = username.strip().lower()
    
    # Llama al servicio que valida UPN + Grupo Soporte_TI
    tecnico = validar_credenciales(username, password)
    
    if tecnico is None:
        # Retardo preventivo contra ataques de fuerza bruta/diccionario
        time.sleep(1)
        return error_response(message="Credenciales incorrectas o usuario no autorizado", status_code=401)
        
    # Configuración de sesión Flask persistente ligada a la cookie del navegador
    session.permanent = True
    session["tecnico_actual"] = tecnico
    
    session["ldap_password"] = password
    
    return success_response(
        message="Inicio de sesión exitoso",
        data=tecnico
    )

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """
    Cierra la sesión del técnico actual y destruye todos los datos retenidos en el servidor.
    """
    session.clear() # Destruye de forma definitiva el 'ldap_password' de la memoria
    return success_response(message="Sesión cerrada correctamente")

@auth_bp.route('/api/auth/estado', methods=['GET'])
def estado():
    """
    Verifica el estado de autenticación actual de la sesión para hidratar el Frontend.
    """
    if "tecnico_actual" in session:
        return success_response(
            message="Sesión activa",
            data={
                "autenticado": True,
                "tecnico": session["tecnico_actual"]
            }
        )
    return success_response(
        message="No autenticado",
        data={
            "autenticado": False,
            "tecnico": None
        }
    )
