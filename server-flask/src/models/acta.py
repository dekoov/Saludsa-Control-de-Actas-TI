from .enums import ActaType, ActaStatus
from .equipment import acta_activos, acta_accesorios
from datetime import datetime
from src.core.db import db

class Acta(db.Model):
    """Tabla principal de actas"""
    __tablename__ = 'actas'

    id = db.Column(db.String, primary_key=True)  # Formato "ACT-YYYYMMDD-NNN"
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    tipo = db.Column(db.String, default=ActaType.DOTACION.value, nullable=False, index=True)
    estado = db.Column(db.String, default=ActaStatus.PENDIENTE_FIRMA.value, nullable=False, index=True)
    sincronizado_saludsa = db.Column(db.Boolean, default=False, nullable=False, index=True)
    estado_sincronizacion = db.Column(db.String, nullable=True)  # 'exitosa', 'fallida', 'pendiente'
    timestamp_sincronizacion = db.Column(db.DateTime, nullable=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False, index=True)
    tiene_pagare = db.Column(db.Boolean, default=False, nullable=False)
    archivo_acta = db.Column(db.String, nullable=True)
    archivo_pagare = db.Column(db.String, nullable=True)

    # Relationships
    empleado = db.relationship('Empleado', back_populates='actas')
    activos = db.relationship('Activo', secondary=acta_activos, back_populates='actas')
    accesorios = db.relationship('Accesorio', secondary=acta_accesorios, back_populates='actas')


class ActaDraft(db.Model):
    """Tabla para borradores de actas (formularios guardados sin generar documentos)"""
    __tablename__ = 'acta_drafts'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    titulo = db.Column(db.String(255), nullable=False, index=True)
    usuario_json = db.Column(db.Text, nullable=False)
    equipos_json = db.Column(db.Text, nullable=False)
    marcar_firmada = db.Column(db.Boolean, default=False, nullable=False)
