"""Modelos de dominio para activos y accesorios de equipos TI.

Este módulo define las entidades ``Activo`` (equipos principales, por
ejemplo laptops) y ``Accesorio`` (elementos complementarios como
cargadores, diademas y mochilas). También incluye las tablas de
asociación many-to-many que vinculan actas con activos y accesorios.
"""

from datetime import datetime

from src.infrastructure.persistence.db import db


# Relationship tables
acta_activos = db.Table('acta_activos',
    db.Column('acta_id', db.String, db.ForeignKey('actas.id'), primary_key=True),
    db.Column('activo_id', db.Integer, db.ForeignKey('activos.id'), primary_key=True)
)
"""Tabla de asociación muchos-a-muchos entre actas y activos.

Attributes:
    acta_id (str): Identificador del acta. Clave foránea hacia
        ``actas.id``. Forma parte de la clave primaria compuesta.
    activo_id (int): Identificador del activo. Clave foránea hacia
        ``activos.id``. Forma parte de la clave primaria compuesta.
"""

acta_accesorios = db.Table('acta_accesorios',
    db.Column('acta_id', db.String, db.ForeignKey('actas.id'), primary_key=True),
    db.Column('accesorio_id', db.Integer, db.ForeignKey('accesorios.id'), primary_key=True)
)
"""Tabla de asociación muchos-a-muchos entre actas y accesorios.

Attributes:
    acta_id (str): Identificador del acta. Clave foránea hacia
        ``actas.id``. Forma parte de la clave primaria compuesta.
    accesorio_id (int): Identificador del accesorio. Clave foránea hacia
        ``accesorios.id``. Forma parte de la clave primaria compuesta.
"""


class Activo(db.Model):
    """Modelo de la tabla de activos principales (laptops).

    Representa un equipo informático principal asignado a un empleado
    mediante un acta. Incluye información técnica, ubicación y estado.

    Attributes:
        id (int): Identificador autoincremental del activo. Clave
            primaria.
        manufacturer (str): Fabricante del equipo (por ejemplo, Dell, HP).
            No nulo.
        model (str): Modelo del equipo. No nulo.
        serial_number (str): Número de serie del equipo. No nulo, único.
        hostname (str): Nombre de red del equipo. No nulo, indexado.
        purchase_cost (float): Costo de adquisición del equipo. No nulo.
        status (str): Estado del activo (por ejemplo, nuevo o usado). No
            nulo, indexado.
        location (str): Ubicación física o ciudad del activo. No nulo,
            indexado.
        observation (str | None): Observaciones adicionales. Nulo
            permitido.
        fecha_registro (datetime): Fecha y hora de registro del activo.
            Valor por defecto: ``datetime.utcnow``.

    Relationships:
        actas (list[Acta]): Relación muchos-a-muchos con las actas en las
            que participa el activo, a través de ``acta_activos``.
            Configurada con ``back_populates='activos'``.
    """

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
    """Modelo de la tabla de accesorios.

    Representa cualquier elemento complementario que no es un equipo
    principal, como cargadores, diademas o mochilas. Se vincula a las
    actas de entrega mediante una relación muchos-a-muchos.

    Attributes:
        id (int): Identificador autoincremental del accesorio. Clave
            primaria.
        equipment_type (str): Tipo de accesorio (por ejemplo,
            Cargador, Diadema, Mochila). No nulo, indexado.
        manufacturer (str): Fabricante del accesorio. No nulo.
        model (str | None): Modelo del accesorio. Nulo permitido.
        serial_number (str | None): Número de serie del accesorio. Nulo
            permitido. Valor por defecto: ``'NA'``.
        quantity (int): Cantidad del accesorio entregada. No nulo.
        purchase_cost (float): Costo de adquisición unitario. No nulo.
        status (str): Estado del accesorio (por ejemplo, nuevo o usado).
            No nulo, indexado.
        location (str): Ubicación física o ciudad del accesorio. No nulo,
            indexado.
        observation (str | None): Observaciones adicionales. Nulo
            permitido.
        fecha_registro (datetime): Fecha y hora de registro del
            accesorio. Valor por defecto: ``datetime.utcnow``.

    Relationships:
        actas (list[Acta]): Relación muchos-a-muchos con las actas en las
            que participa el accesorio, a través de
            ``acta_accesorios``. Configurada con
            ``back_populates='accesorios'``.
    """

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
