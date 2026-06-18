from src.core.responses import success_response, error_response
from flask import Blueprint, jsonify
from src.features.dashboard.service import get_dashboard_stats, get_recent_users
from src.core.decorators import requiere_login

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@requiere_login
def get_stats():
    """
    Endpoint para obtener estadísticas del dashboard.
    Retorna: total_actas, pendientes_firma, borradores, pendientes_saludsa
    """
    stats = get_dashboard_stats()

    return success_response(
        message="Dashboard stats retrieved successfully",
        data=stats
    )


@dashboard_bp.route('/api/dashboard/recent-users', methods=['GET'])
@requiere_login
def get_recent_users_endpoint():
    """
    Endpoint para obtener los últimos 5 empleados con acta generada.
    Retorna lista de usuarios con username, full_name, city, fecha_ultima_acta
    """
    users = get_recent_users()

    return success_response(
        message="Recent users retrieved successfully",
        data=users
    )
