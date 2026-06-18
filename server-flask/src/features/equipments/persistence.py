from datetime import datetime
from typing import Dict, Any
from src.core.db import db
from src.models.equipment import Activo, Accesorio


def upsert_activo(equipo_data: Dict[str, Any]) -> Activo:
    """Upsert activo: si serial_number existe, reusar; si no, crear nuevo"""
    serial_number = equipo_data.get('serial_number')
    activo = Activo.query.filter_by(serial_number=serial_number).first()
    
    if not activo:
        activo = Activo(
            manufacturer=equipo_data.get('manufacturer'),
            model=equipo_data.get('model'),
            serial_number=serial_number,
            hostname=equipo_data.get('hostname'),
            purchase_cost=equipo_data.get('purchase_cost'),
            status=equipo_data.get('status'),
            location=equipo_data.get('location'),
            observation=equipo_data.get('observation', '')
        )
        db.session.add(activo)
        db.session.flush()
    
    return activo


def insert_accesorio(equipo_data: Dict[str, Any]) -> Accesorio:
    """Inserta un nuevo accesorio (siempre crea registro nuevo)"""
    accesorio = Accesorio(
        equipment_type=equipo_data.get('equipment_type'),
        manufacturer=equipo_data.get('manufacturer'),
        model=equipo_data.get('model'),
        serial_number=equipo_data.get('serial_number', 'NA'),
        quantity=equipo_data.get('quantity'),
        purchase_cost=equipo_data.get('purchase_cost'),
        status=equipo_data.get('status'),
        location=equipo_data.get('location'),
        observation=equipo_data.get('observation', '')
    )
    db.session.add(accesorio)
    db.session.flush()
    return accesorio


