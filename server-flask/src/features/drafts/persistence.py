"""Capa de persistencia para borradores de actas.

Gestiona el ciclo de vida completo de los borradores en base de datos:
guardado, listado, consulta individual, actualización y eliminación. Los datos
del usuario y equipos se serializan como JSON para almacenamiento flexible.
"""

import json
from typing import Any

from src.infrastructure.persistence.db import db
from src.features.drafts.service import generate_draft_title
from src.models.acta import ActaDraft


def save_draft(
    usuario: dict[str, Any],
    equipos: list[dict[str, Any]],
    marcar_firmada: bool = False,
) -> int:
    """Guarda un nuevo borrador en la base de datos.

    Args:
        usuario: Datos del empleado destinatario.
        equipos: Lista de equipos asociados al borrador.
        marcar_firmada: Indica si el borrador debe generar el acta como firmada.

    Returns:
        int: Identificador del borrador creado.

    Raises:
        Exception: Propaga cualquier error de base de datos después de hacer
            rollback.
    """
    try:
        titulo = generate_draft_title(usuario, equipos)

        draft = ActaDraft(
            titulo=titulo,
            usuario_json=json.dumps(usuario),
            equipos_json=json.dumps(equipos),
            marcar_firmada=marcar_firmada,
        )

        db.session.add(draft)
        db.session.commit()

        return draft.id
    except Exception as e:
        db.session.rollback()
        raise e


def get_all_drafts() -> list[dict[str, Any]]:
    """Obtiene todos los borradores ordenados por fecha de actualización.

    Returns:
        list[dict[str, Any]]: Lista resumida de borradores con id, titulo y
        updated_at.
    """
    drafts = ActaDraft.query.order_by(ActaDraft.updated_at.desc()).all()

    result: list[dict[str, Any]] = []
    for draft in drafts:
        result.append(
            {
                "id": draft.id,
                "titulo": draft.titulo,
                "updated_at": draft.updated_at.isoformat()
                if draft.updated_at
                else None,
            }
        )

    return result


def get_draft_by_id(draft_id: int) -> dict[str, Any] | None:
    """Obtiene un borrador específico con su contenido completo.

    Args:
        draft_id: Identificador del borrador.

    Returns:
        dict[str, Any] | None: Diccionario con id, titulo, usuario, equipos y
        marcar_firmada; o None si no existe.
    """
    draft = ActaDraft.query.get(draft_id)

    if not draft:
        return None

    return {
        "id": draft.id,
        "titulo": draft.titulo,
        "usuario": json.loads(draft.usuario_json),
        "equipos": json.loads(draft.equipos_json),
        "marcar_firmada": draft.marcar_firmada,
    }


def delete_draft(draft_id: int) -> bool:
    """Elimina un borrador de la base de datos.

    Args:
        draft_id: Identificador del borrador a eliminar.

    Returns:
        bool: True si se eliminó correctamente, False si no se encontró.
    """
    draft = ActaDraft.query.get(draft_id)

    if not draft:
        return False

    db.session.delete(draft)
    db.session.commit()
    return True


def update_draft(
    draft_id: int,
    usuario: dict[str, Any],
    equipos: list[dict[str, Any]],
    marcar_firmada: bool = False,
) -> bool:
    """Actualiza un borrador existente en la base de datos.

    Args:
        draft_id: Identificador del borrador a actualizar.
        usuario: Nuevos datos del empleado destinatario.
        equipos: Nueva lista de equipos.
        marcar_firmada: Nuevo indicador de firma automática.

    Returns:
        bool: True si se actualizó correctamente, False si no se encontró.
    """
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
