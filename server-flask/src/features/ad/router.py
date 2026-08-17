"""Rutas HTTP para la integración con Active Directory.

Expone endpoints de búsqueda de usuarios en el directorio activo (AD). Las
rutas requieren sesión activa del técnico y delegan la consulta LDAP al
servicio especializado.
"""

from flask import Blueprint, jsonify, request

from src.core.decorators import requiere_login
from src.features.ad.service import search_user_ad

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/api/ad/users", methods=["GET"])
@requiere_login
def get_user_info():
    """Busca usuarios en Active Directory.

    Recibe un parámetro de búsqueda (nombre, usuario, etc.) y delega la
    consulta al servicio de LDAP. Retorna la lista de usuarios encontrados con
    sus atributos mapeados.

    HTTP:
        GET /api/ad/users

    Headers:
        Authorization: Sesión Flask activa.

    Query Args:
        q (str): Texto de búsqueda. Obligatorio.

    Returns:
        Response: JSON 200 con la lista de usuarios:
            {"usuarios": list[dict]}

    Response codes:
        200: Búsqueda exitosa, incluso si no hay resultados.
        400: Falta el parámetro de búsqueda q.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error en la búsqueda LDAP o en el servicio de directorio activo.
    """
    query = request.args.get("q")

    if not query:
        return jsonify({"error": "Falta el parámetro de búsqueda (q)"}), 400

    try:
        results = search_user_ad(query)

        return jsonify({"usuarios": results}), 200

    except Exception as e:
        return jsonify({"error": "Error en búsqueda AD", "details": str(e)}), 500
