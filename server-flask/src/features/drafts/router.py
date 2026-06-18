from flask import Blueprint, request, jsonify
from src.features.drafts.persistence import save_draft, get_all_drafts, get_draft_by_id, delete_draft, update_draft
from src.core.decorators import requiere_login

drafts_bp = Blueprint('drafts_bp', __name__)


@drafts_bp.route('/api/drafts', methods=['POST'])
@requiere_login
def create_draft():
    """
    Endpoint para guardar un borrador de acta.
    Payload: { usuario: {...}, equipos: [...], marcar_firmada: false }
    """
    try:
        data = request.json
        
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Se esperaba un objeto JSON válido"}), 400
        
        required_fields = ['usuario', 'equipos']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"El JSON debe contener: {required_fields}"}), 400
        
        usuario = data.get('usuario')
        equipos = data.get('equipos')
        marcar_firmada = data.get('marcar_firmada', False)
        
        draft_id = save_draft(usuario, equipos, marcar_firmada)
        
        return jsonify({
            "message": "Borrador guardado",
            "id": draft_id
        }), 201
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Error al guardar borrador", "detalle": str(e)}), 500


@drafts_bp.route('/api/drafts', methods=['GET'])
@requiere_login
def list_drafts():
    """
    Endpoint para obtener todos los borradores.
    Retorna lista ordenada por fecha más reciente.
    """
    try:
        drafts = get_all_drafts()
        return jsonify(drafts), 200
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Error al obtener borradores", "detalle": str(e)}), 500


@drafts_bp.route('/api/drafts/<int:draft_id>', methods=['GET'])
@requiere_login
def get_draft(draft_id):
    """
    Endpoint para obtener un borrador específico con su contenido completo.
    """
    try:
        draft = get_draft_by_id(draft_id)
        
        if not draft:
            return jsonify({"error": "Borrador no encontrado"}), 404
        
        return jsonify(draft), 200
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Error al obtener borrador", "detalle": str(e)}), 500


@drafts_bp.route('/api/drafts/<int:draft_id>', methods=['DELETE'])
@requiere_login
def delete_draft_endpoint(draft_id):
    """
    Endpoint para eliminar un borrador.
    """
    try:
        success = delete_draft(draft_id)
        
        if not success:
            return jsonify({"error": "Borrador no encontrado"}), 404
        
        return jsonify({"message": "Borrador eliminado"}), 200
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": "Error al eliminar borrador", "detalle": str(e)}), 500

@drafts_bp.route('/api/drafts/<int:draft_id>', methods=['PUT'])
@requiere_login
def update_draft_endpoint(draft_id):
    """
    Endpoint para actualizar un borrador existente.
    """
    try:
        data = request.json
        usuario = data.get('usuario')
        equipos = data.get('equipos')
        marcar_firmada = data.get('marcar_firmada', False)
        
        success = update_draft(draft_id, usuario, equipos, marcar_firmada)
        
        if not success:
            return jsonify({"error": "Borrador no encontrado"}), 404
            
        return jsonify({"message": "Borrador actualizado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": "Error al actualizar", "detalle": str(e)}), 500
