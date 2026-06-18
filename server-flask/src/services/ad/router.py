from flask import Blueprint, request, jsonify
from src.services.ad.service import search_user_ad
from src.core.decorators import requiere_login

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/api/ad/users', methods=['GET'])
@requiere_login
def get_user_info():
    """
    Endpoint para obtener información de usuario desde Active Directory.
    Usa configuraciones centralizadas desde src.config.config
    """
    query = request.args.get('q')

    if not query:
        return jsonify({'error': 'Falta el parámetro de búsqueda (q)'}), 400

    try: 
        results = search_user_ad(query)

        return jsonify({'usuarios': results}), 200

    except Exception as e:
        return jsonify({'error': 'Error en búsqueda AD', 'details': str(e)}), 500
