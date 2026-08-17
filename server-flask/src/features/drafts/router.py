"""Rutas HTTP para la gestión de borradores de actas.

Expone endpoints para crear, listar, consultar, actualizar y eliminar
borradores. Los borradores permiten guardar progreso parcial antes de generar
el acta definitiva. Todas las rutas requieren sesión activa del técnico.
"""

from typing import Any

from flask import Blueprint, jsonify, request

from src.core.decorators import requiere_login
from src.features.drafts.persistence import (
    delete_draft,
    get_all_drafts,
    get_draft_by_id,
    save_draft,
    update_draft,
)

drafts_bp = Blueprint("drafts_bp", __name__)


@drafts_bp.route("/api/drafts", methods=["POST"])
@requiere_login
def create_draft():
    """Crea un nuevo borrador de acta.

    Recibe los datos del usuario, equipos y la bandera marcar_firmada, y los
    almacena en base de datos para su uso posterior al generar el acta.

    HTTP:
        POST /api/drafts

    Headers:
        Authorization: Sesión Flask activa.
        Content-Type: application/json

    Request JSON:
        {
            "usuario": dict,
            "equipos": list[dict],
            "marcar_firmada": bool  # Opcional, default false.
        }

    Returns:
        Response: JSON 201 con mensaje e id del borrador.

    Response codes:
        201: Borrador guardado correctamente.
        400: Body JSON inválido o faltan campos obligatorios.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno al guardar el borrador.
    """
    try:
        data: dict[str, Any] | None = request.json

        if not data or not isinstance(data, dict):
            return jsonify({"error": "Se esperaba un objeto JSON válido"}), 400

        required_fields = ["usuario", "equipos"]
        if not all(field in data for field in required_fields):
            return (
                jsonify({"error": f"El JSON debe contener: {required_fields}"}),
                400,
            )

        usuario = data.get("usuario")
        equipos = data.get("equipos")
        marcar_firmada = data.get("marcar_firmada", False)

        draft_id = save_draft(usuario, equipos, marcar_firmada)

        return jsonify({"message": "Borrador guardado", "id": draft_id}), 201

    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return jsonify({"error": "Error al guardar borrador", "detalle": str(e)}), 500


@drafts_bp.route("/api/drafts", methods=["GET"])
@requiere_login
def list_drafts():
    """Lista todos los borradores existentes.

    Retorna los borradores ordenados por fecha de actualización descendente.

    HTTP:
        GET /api/drafts

    Headers:
        Authorization: Sesión Flask activa.

    Returns:
        Response: JSON 200 con lista de borradores resumidos.

    Response codes:
        200: Lista obtenida correctamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno al obtener los borradores.
    """
    try:
        drafts = get_all_drafts()
        return jsonify(drafts), 200
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return (
            jsonify({"error": "Error al obtener borradores", "detalle": str(e)}),
            500,
        )


@drafts_bp.route("/api/drafts/<int:draft_id>", methods=["GET"])
@requiere_login
def get_draft(draft_id: int):
    """Obtiene un borrador específico con su contenido completo.

    HTTP:
        GET /api/drafts/<draft_id>

    Headers:
        Authorization: Sesión Flask activa.

    Args:
        draft_id: Identificador del borrador.

    Returns:
        Response: JSON 200 con el contenido completo del borrador.

    Response codes:
        200: Borrador encontrado.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        404: Borrador no encontrado.
        500: Error interno al obtener el borrador.
    """
    try:
        draft = get_draft_by_id(draft_id)

        if not draft:
            return jsonify({"error": "Borrador no encontrado"}), 404

        return jsonify(draft), 200
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return (
            jsonify({"error": "Error al obtener borrador", "detalle": str(e)}),
            500,
        )


@drafts_bp.route("/api/drafts/<int:draft_id>", methods=["DELETE"])
@requiere_login
def delete_draft_endpoint(draft_id: int):
    """Elimina un borrador existente.

    HTTP:
        DELETE /api/drafts/<draft_id>

    Headers:
        Authorization: Sesión Flask activa.

    Args:
        draft_id: Identificador del borrador a eliminar.

    Returns:
        Response: JSON 200 confirmando la eliminación.

    Response codes:
        200: Borrador eliminado correctamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        404: Borrador no encontrado.
        500: Error interno al eliminar el borrador.
    """
    try:
        success = delete_draft(draft_id)

        if not success:
            return jsonify({"error": "Borrador no encontrado"}), 404

        return jsonify({"message": "Borrador eliminado"}), 200
    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return (
            jsonify({"error": "Error al eliminar borrador", "detalle": str(e)}),
            500,
        )


@drafts_bp.route("/api/drafts/<int:draft_id>", methods=["PUT"])
@requiere_login
def update_draft_endpoint(draft_id: int):
    """Actualiza un borrador existente.

    HTTP:
        PUT /api/drafts/<draft_id>

    Headers:
        Authorization: Sesión Flask activa.
        Content-Type: application/json

    Args:
        draft_id: Identificador del borrador a actualizar.

    Request JSON:
        {
            "usuario": dict,
            "equipos": list[dict],
            "marcar_firmada": bool  # Opcional, default false.
        }

    Returns:
        Response: JSON 200 confirmando la actualización.

    Response codes:
        200: Borrador actualizado correctamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        404: Borrador no encontrado.
        500: Error interno al actualizar el borrador.
    """
    try:
        data: dict[str, Any] | None = request.json
        usuario = data.get("usuario")
        equipos = data.get("equipos")
        marcar_firmada = data.get("marcar_firmada", False)

        success = update_draft(draft_id, usuario, equipos, marcar_firmada)

        if not success:
            return jsonify({"error": "Borrador no encontrado"}), 404

        return jsonify({"message": "Borrador actualizado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": "Error al actualizar", "detalle": str(e)}), 500
