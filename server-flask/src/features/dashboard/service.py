from typing import List, Dict, Any
from sqlalchemy import func, desc
from src.core.db import db

from src.models.enums import ActaStatus, SyncStatus
from src.models.acta import Acta, ActaDraft
from src.models.employee import Empleado


def get_dashboard_stats() -> Dict[str, int]:
    """
    Retorna estadísticas para el dashboard.
    - total_actas: total de actas en el sistema
    - pendientes_firma: actas con estado 'Pendiente Firma'
    - borradores: actas con estado 'Borrador'
    - pendientes_saludsa: actas firmadas pero no sincronizadas con Saludsa
    """
    total_actas = Acta.query.count()
    
    pendientes_firma = Acta.query.filter_by(
        estado=ActaStatus.PENDIENTE_FIRMA.value
    ).count()
    
    borradores = ActaDraft.query.count()

    pendientes_saludsa = Acta.query.filter(
        Acta.sincronizado_saludsa == False
    ).count()

    return {
        "total_actas": total_actas,
        "pendientes_firma": pendientes_firma,
        "borradores": borradores,
        "pendientes_saludsa": pendientes_saludsa
    }


def get_recent_users() -> List[Dict[str, Any]]:
    """
    Retorna los últimos 5 empleados con acta generada, sin duplicados,
    ordenados por la fecha de su acta más reciente.
    """
    # Subquery para obtener la fecha más reciente de acta por empleado
    subquery = db.session.query(
        Acta.empleado_id,
        func.max(Acta.fecha).label('max_fecha')
    ).group_by(Acta.empleado_id).subquery()
    
    # Query principal para obtener los empleados con sus fechas
    recent_employees = db.session.query(
        Empleado,
        subquery.c.max_fecha
    ).join(
        subquery, Empleado.id == subquery.c.empleado_id
    ).order_by(
        desc(subquery.c.max_fecha)
    ).limit(5).all()
    
    result = []
    for empleado, fecha in recent_employees:
        result.append({
            "username": empleado.username,
            "full_name": empleado.full_name,
            "city": empleado.city,
            "fecha_ultima_acta": fecha.isoformat() if fecha else None
        })
    
    return result
