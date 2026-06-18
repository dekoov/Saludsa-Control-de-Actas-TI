from datetime import datetime
from src.core.db import db

# Relationship tables
acta_activos = db.Table('acta_activos',
    db.Column('acta_id', db.String, db.ForeignKey('actas.id'), primary_key=True),
    db.Column('activo_id', db.Integer, db.ForeignKey('activos.id'), primary_key=True)
)

acta_accesorios = db.Table('acta_accesorios',
    db.Column('acta_id', db.String, db.ForeignKey('actas.id'), primary_key=True),
    db.Column('accesorio_id', db.Integer, db.ForeignKey('accesorios.id'), primary_key=True)
)


class Activo(db.Model):
    """Tabla para Laptops únicamente"""
    __tablename__ = 'activos'

    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String, nullable=False)
    model = db.Column(db.String, nullable=False)
    serial_number = db.Column(db.String, unique=True, nullable=False)
    hostname = db.Column(db.String, nullable=False, index=True)
    purchase_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False, index=True)
    location = db.Column(db.String, nullable=False, index=True)
    observation = db.Column(db.String, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    actas = db.relationship('Acta', secondary=acta_activos, back_populates='activos')


class Accesorio(db.Model):
    """Tabla para todo lo que no sea Laptop (Cargador, Diadema, Mochila)"""
    __tablename__ = 'accesorios'

    id = db.Column(db.Integer, primary_key=True)
    equipment_type = db.Column(db.String, nullable=False, index=True)  # Cargador/Diadema/Mochila
    manufacturer = db.Column(db.String, nullable=False)
    model = db.Column(db.String, nullable=True)
    serial_number = db.Column(db.String, nullable=True, default='NA')
    quantity = db.Column(db.Integer, nullable=False)
    purchase_cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False, index=True)
    location = db.Column(db.String, nullable=False, index=True)
    observation = db.Column(db.String, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    actas = db.relationship('Acta', secondary=acta_accesorios, back_populates='accesorios')
