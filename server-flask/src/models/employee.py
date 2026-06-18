from src.core.db import db

class Empleado(db.Model):
    """Tabla para datos de empleados"""
    __tablename__ = 'empleados'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    national_id = db.Column(db.String, nullable=False, index=True)
    city = db.Column(db.String, nullable=False)

    # Relationships
    actas = db.relationship('Acta', back_populates='empleado', lazy=True)
