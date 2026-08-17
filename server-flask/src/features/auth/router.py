"""Rutas HTTP de autenticación para técnicos de TI.

Expone endpoints para iniciar y cerrar sesión, así como para consultar el
estado de autenticación actual. La validación de credenciales se realiza contra
Active Directory verificando pertenencia al grupo de seguridad autorizado.
"""

import time
from typing import Any

from flask import Blueprint, request, session

from src.api.responses import error_response, success_response
from src.features.auth.service import validar_credenciales

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """Autentica a un técnico contra Active Directory.

    Valida credenciales, verifica que el usuario pertenezca al grupo de
    seguridad de TI configurado y almacena los datos del técnico en la sesión
    Flask, incluyendo la contraseña LDAP de forma temporal para operaciones
    posteriores.

    HTTP:
        POST /api/auth/login

    Headers:
        Content-Type: application/json

    Request JSON:
        {
            "username": str,  # Nombre de usuario sin dominio.
            "password": str   # Contraseña de Active Directory.
        }

    Returns:
        Response: JSON 200 con los datos del técnico autenticado, o error 401/400.

    Response codes:
        200: Inicio de sesión exitoso.
        400: Faltan usuario o contraseña.
        401: Credenciales incorrectas o usuario no autorizado.
        500: Error interno del servidor.
    """
    data: dict[str, Any] = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return error_response(
            message="El usuario y la contraseña son requeridos", status_code=400
        )

    username = username.strip().lower()

    # Llama al servicio que valida UPN + Grupo Soporte_TI
    tecnico = validar_credenciales(username, password)

    if tecnico is None:
        # Retardo preventivo contra ataques de fuerza bruta/diccionario
        time.sleep(1)
        return error_response(
            message="Credenciales incorrectas o usuario no autorizado",
            status_code=401,
        )

    # Configuración de sesión Flask persistente ligada a la cookie del navegador
    session.permanent = True
    session["tecnico_actual"] = tecnico

    session["ldap_password"] = password

    return success_response(
        message="Inicio de sesión exitoso",
        data=tecnico,
    )


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    """Cierra la sesión del técnico actual.

    Destruye todos los datos retenidos en la sesión del servidor, incluyendo la
    contraseña LDAP temporal.

    HTTP:
        POST /api/auth/logout

    Returns:
        Response: JSON 200 confirmando el cierre de sesión.

    Response codes:
        200: Sesión cerrada correctamente.
        500: Error interno del servidor.
    """
    session.clear()  # Destruye de forma definitiva el 'ldap_password' de la memoria
    return success_response(message="Sesión cerrada correctamente")


@auth_bp.route("/api/auth/estado", methods=["GET"])
def estado():
    """Consulta el estado de autenticación de la sesión actual.

    Permite al frontend hidratar el estado de login sin necesidad de hacer un
    POST adicional.

    HTTP:
        GET /api/auth/estado

    Returns:
        Response: JSON 200 indicando si hay sesión activa y los datos del
        técnico:
            {
                "autenticado": bool,
                "tecnico": dict | None
            }

    Response codes:
        200: Consulta exitosa.
        500: Error interno del servidor.
    """
    if "tecnico_actual" in session:
        return success_response(
            message="Sesión activa",
            data={
                "autenticado": True,
                "tecnico": session["tecnico_actual"],
            },
        )
    return success_response(
        message="No autenticado",
        data={
            "autenticado": False,
            "tecnico": None,
        },
    )
