"""Rutas HTTP del dashboard para el backend Flask.

Expone endpoints para obtener estadísticas agregadas del sistema y la lista de
empleados más recientes con actas generadas. Ambas rutas requieren sesión activa.
"""

from flask import Blueprint

from src.api.responses import success_response
from src.core.decorators import requiere_login
from src.features.dashboard.service import get_dashboard_stats, get_recent_users

dashboard_bp = Blueprint("dashboard_bp", __name__)


@dashboard_bp.route("/api/dashboard/stats", methods=["GET"])
@requiere_login
def get_stats():
    """Obtiene estadísticas resumidas para el dashboard.

    Retorna contadores de actas totales, actas pendientes de firma, borradores
    y actas pendientes de sincronización con Saludsa.

    HTTP:
        GET /api/dashboard/stats

    Headers:
        Authorization: Sesión Flask activa.

    Returns:
        Response: JSON 200 con:
            {
                "success": true,
                "data": {
                    "total_actas": int,
                    "pendientes_firma": int,
                    "borradores": int,
                    "pendientes_saludsa": int
                }
            }

    Response codes:
        200: Estadísticas obtenidas correctamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno del servidor.
    """
    stats = get_dashboard_stats()

    return success_response(
        message="Dashboard stats retrieved successfully",
        data=stats,
    )


@dashboard_bp.route("/api/dashboard/recent-users", methods=["GET"])
@requiere_login
def get_recent_users_endpoint():
    """Obtiene los últimos empleados con acta generada.

    Retorna hasta 5 empleados distintos ordenados por la fecha de su acta más
    reciente, incluyendo username, nombre completo, ciudad y fecha.

    HTTP:
        GET /api/dashboard/recent-users

    Headers:
        Authorization: Sesión Flask activa.

    Returns:
        Response: JSON 200 con:
            {
                "success": true,
                "data": [
                    {
                        "username": str,
                        "full_name": str,
                        "city": str,
                        "fecha_ultima_acta": str | null
                    }
                ]
            }

    Response codes:
        200: Lista obtenida correctamente.
        401: No hay sesión activa.
        403: Sesión sin permisos suficientes.
        500: Error interno del servidor.
    """
    users = get_recent_users()

    return success_response(
        message="Recent users retrieved successfully",
        data=users,
    )
