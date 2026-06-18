from src.models.acta import ActaDraft
from src.core.db import db
from src.features.drafts.service import generate_draft_title
import json

def save_draft(usuario, equipos, marcar_firmada=False):
    """Guarda un borrador en la base de datos"""
    try:
        titulo = generate_draft_title(usuario, equipos)
        
        draft = ActaDraft(
            titulo=titulo,
            usuario_json=json.dumps(usuario),
            equipos_json=json.dumps(equipos),
            marcar_firmada=marcar_firmada
        )
        
        db.session.add(draft)
        db.session.commit()
        
        return draft.id
    except Exception as e:
        db.session.rollback()
        raise e


def get_all_drafts():
    """Retorna todos los borradores ordenados por fecha más reciente"""
    drafts = ActaDraft.query.order_by(ActaDraft.updated_at.desc()).all()
    
    result = []
    for draft in drafts:
        result.append({
            "id": draft.id,
            "titulo": draft.titulo,
            "updated_at": draft.updated_at.isoformat() if draft.updated_at else None
        })
    
    return result


def get_draft_by_id(draft_id):
    """Retorna un borrador específico con su contenido completo"""
    draft = ActaDraft.query.get(draft_id)
    
    if not draft:
        return None
    
    return {
        "id": draft.id,
        "titulo": draft.titulo,
        "usuario": json.loads(draft.usuario_json),
        "equipos": json.loads(draft.equipos_json),
        "marcar_firmada": draft.marcar_firmada
    }


def delete_draft(draft_id):
    """Elimina un borrador"""
    draft = ActaDraft.query.get(draft_id)
    
    if not draft:
        return False
    
    db.session.delete(draft)
    db.session.commit()
    return True

def update_draft(draft_id, usuario, equipos, marcar_firmada=False):
    """Actualiza un borrador existente en la base de datos"""
    draft = ActaDraft.query.get(draft_id)
    if not draft:
        return False
        
    # Actualizamos los campos
    draft.titulo = generate_draft_title(usuario, equipos)
    draft.usuario_json = json.dumps(usuario)
    draft.equipos_json = json.dumps(equipos)
    draft.marcar_firmada = marcar_firmada
    
    db.session.commit()
    return True
