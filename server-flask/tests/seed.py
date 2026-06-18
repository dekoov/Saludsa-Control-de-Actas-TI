"""
Script para generar datos de prueba en la base de datos.
Ejecutar con: python src/seed.py
"""
import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio src al path para poder importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from src.core.db import db, init_db
from src.models.equipment import Activo, Accesorio, Empleado, Acta, ActaType, ActaStatus


def create_test_data():
    """Crea ~15 actas de prueba con diferentes estados y fechas"""
    
    # Crear aplicación Flask mínima para inicializar la BD
    app = Flask(__name__)
    init_db(app)
    
    with app.app_context():
        # Limpiar datos existentes (opcional, comentar si se quiere preservar)
        print("Limpiando datos existentes...")
        Acta.query.delete()
        db.session.execute(db.text('DELETE FROM acta_accesorios'))
        db.session.execute(db.text('DELETE FROM acta_activos'))
        Accesorio.query.delete()
        Activo.query.delete()
        Empleado.query.delete()
        db.session.commit()
        
        # Crear empleados
        empleados_data = [
            {"username": "jdoe", "full_name": "Juan Doe Pérez", "national_id": "1712345678", "city": "Guayaquil"},
            {"username": "mgarcia", "full_name": "María García López", "national_id": "1723456789", "city": "Quito"},
            {"username": "crodriguez", "full_name": "Carlos Rodríguez Mendoza", "national_id": "1734567890", "city": "Cuenca"},
            {"username": "aperez", "full_name": "Ana Pérez Torres", "national_id": "1745678901", "city": "Guayaquil"},
            {"username": "lromero", "full_name": "Luis Romero Silva", "national_id": "1756789012", "city": "Quito"},
        ]
        
        empleados = []
        for emp_data in empleados_data:
            emp = Empleado(**emp_data)
            db.session.add(emp)
            empleados.append(emp)
        db.session.commit()
        print(f"Creados {len(empleados)} empleados")
        
        # Crear activos (laptops)
        activos_data = [
            {"manufacturer": "Dell", "model": "Latitude 5420", "serial_number": "DL123456789", "hostname": "LPT-JDOE", "purchase_cost": 1200.50, "status": "Nuevo", "location": "BODEGA GYE", "observation": ""},
            {"manufacturer": "HP", "model": "ProBook 450", "serial_number": "HP987654321", "hostname": "LPT-MGARCIA", "purchase_cost": 1350.00, "status": "Nuevo", "location": "BODEGA UIO", "observation": ""},
            {"manufacturer": "Lenovo", "model": "ThinkPad T14", "serial_number": "LN456789123", "hostname": "LPT-CRODRIGUEZ", "purchase_cost": 1450.00, "status": "Usado", "location": "BODEGA CUE", "observation": "Ligero desgaste en teclado"},
            {"manufacturer": "Dell", "model": "Latitude 5520", "serial_number": "DL789123456", "hostname": "LPT-APEREZ", "purchase_cost": 1400.00, "status": "Nuevo", "location": "BODEGA GYE", "observation": ""},
            {"manufacturer": "HP", "model": "EliteBook 840", "serial_number": "HP321654987", "hostname": "LPT-LROMERO", "purchase_cost": 1550.00, "status": "Nuevo", "location": "BODEGA UIO", "observation": ""},
        ]
        
        activos = []
        for act_data in activos_data:
            act = Activo(**act_data)
            db.session.add(act)
            activos.append(act)
        db.session.commit()
        print(f"Creados {len(activos)} activos")
        
        # Crear accesorios
        accesorios_data = [
            {"equipment_type": "Cargador", "manufacturer": "Dell", "model": "65W USB-C", "serial_number": "CG987654321", "quantity": 1, "purchase_cost": 45.00, "status": "Nuevo", "location": "BODEGA GYE", "observation": ""},
            {"equipment_type": "Cargador", "manufacturer": "HP", "model": "65W Smart", "serial_number": "CG123456789", "quantity": 1, "purchase_cost": 50.00, "status": "Nuevo", "location": "BODEGA UIO", "observation": ""},
            {"equipment_type": "Diadema", "manufacturer": "Logitech", "model": "H540", "serial_number": "DH456789123", "quantity": 1, "purchase_cost": 35.00, "status": "Nuevo", "location": "BODEGA GYE", "observation": ""},
            {"equipment_type": "Mochila", "manufacturer": "Targus", "model": "Genérico", "serial_number": "NA", "quantity": 1, "purchase_cost": 40.00, "status": "Nuevo", "location": "BODEGA UIO", "observation": ""},
            {"equipment_type": "Cargador", "manufacturer": "Lenovo", "model": "65W", "serial_number": "CG789123456", "quantity": 1, "purchase_cost": 48.00, "status": "Usado", "location": "BODEGA CUE", "observation": ""},
        ]
        
        accesorios = []
        for acc_data in accesorios_data:
            acc = Accesorio(**acc_data)
            db.session.add(acc)
            accesorios.append(acc)
        db.session.commit()
        print(f"Creados {len(accesorios)} accesorios")
        
        # Crear actas con diferentes estados y fechas
        now = datetime.utcnow()
        estados = [ActaStatus.BORRADOR.value, ActaStatus.PENDIENTE_FIRMA.value, ActaStatus.FIRMADA.value]
        
        actas_config = [
            # Actas recientes (últimos 5 días)
            {"empleado_idx": 0, "activo_idx": 0, "accesorio_idxs": [0], "estado": ActaStatus.BORRADOR.value, "dias_atras": 0, "sincronizado": False},
            {"empleado_idx": 1, "activo_idx": 1, "accesorio_idxs": [1], "estado": ActaStatus.PENDIENTE_FIRMA.value, "dias_atras": 1, "sincronizado": False},
            {"empleado_idx": 2, "activo_idx": 2, "accesorio_idxs": [2], "estado": ActaStatus.FIRMADA.value, "dias_atras": 2, "sincronizado": False},
            {"empleado_idx": 3, "activo_idx": 3, "accesorio_idxs": [3], "estado": ActaStatus.FIRMADA.value, "dias_atras": 3, "sincronizado": True},
            {"empleado_idx": 4, "activo_idx": 4, "accesorio_idxs": [4], "estado": ActaStatus.BORRADOR.value, "dias_atras": 4, "sincronizado": False},
            
            # Actas de hace 1-2 semanas
            {"empleado_idx": 0, "activo_idx": 0, "accesorio_idxs": [0, 2], "estado": ActaStatus.FIRMADA.value, "dias_atras": 7, "sincronizado": True},
            {"empleado_idx": 1, "activo_idx": 1, "accesorio_idxs": [1, 3], "estado": ActaStatus.FIRMADA.value, "dias_atras": 8, "sincronizado": False},
            {"empleado_idx": 2, "activo_idx": 2, "accesorio_idxs": [2], "estado": ActaStatus.PENDIENTE_FIRMA.value, "dias_atras": 10, "sincronizado": False},
            {"empleado_idx": 3, "activo_idx": 3, "accesorio_idxs": [3, 4], "estado": ActaStatus.BORRADOR.value, "dias_atras": 12, "sincronizado": False},
            {"empleado_idx": 4, "activo_idx": 4, "accesorio_idxs": [4], "estado": ActaStatus.FIRMADA.value, "dias_atras": 14, "sincronizado": True},
            
            # Actas de hace 3-4 semanas
            {"empleado_idx": 0, "activo_idx": 0, "accesorio_idxs": [0], "estado": ActaStatus.FIRMADA.value, "dias_atras": 21, "sincronizado": True},
            {"empleado_idx": 1, "activo_idx": 1, "accesorio_idxs": [1], "estado": ActaStatus.FIRMADA.value, "dias_atras": 22, "sincronizado": False},
            {"empleado_idx": 2, "activo_idx": 2, "accesorio_idxs": [2, 3], "estado": ActaStatus.FIRMADA.value, "dias_atras": 25, "sincronizado": True},
            {"empleado_idx": 3, "activo_idx": 3, "accesorio_idxs": [3], "estado": ActaStatus.PENDIENTE_FIRMA.value, "dias_atras": 28, "sincronizado": False},
            {"empleado_idx": 4, "activo_idx": 4, "accesorio_idxs": [4], "estado": ActaStatus.FIRMADA.value, "dias_atras": 30, "sincronizado": True},
        ]
        
        actas_count = 0
        sequence = 1
        
        for config in actas_config:
            fecha = now - timedelta(days=config["dias_atras"])
            fecha_str = fecha.strftime('%Y%m%d')
            
            # Generar ID único
            acta_id = f'ACT-{fecha_str}-{str(sequence).zfill(3)}'
            sequence += 1
            
            empleado = empleados[config["empleado_idx"]]
            activo = activos[config["activo_idx"]]
            accesorios_list = [accesorios[i] for i in config["accesorio_idxs"]]
            
            acta = Acta(
                id=acta_id,
                fecha=fecha,
                tipo=ActaType.DOTACION.value,
                estado=config["estado"],
                sincronizado_saludsa=config["sincronizado"],
                empleado_id=empleado.id,
                tiene_pagare=True,
                archivo_acta=f"generated/ACTA_{empleado.username}_{activo.serial_number}.docx",
                archivo_pagare=f"generated/PAGARE_{empleado.username}_{activo.serial_number}.docx"
            )
            
            db.session.add(acta)
            db.session.flush()
            
            # Relacionar con activo
            acta.activos.append(activo)
            
            # Relacionar con accesorios
            for acc in accesorios_list:
                acta.accesorios.append(acc)
            
            actas_count += 1
        
        db.session.commit()
        print(f"Creadas {actas_count} actas de prueba")
        
        # Mostrar estadísticas
        total_actas = Acta.query.count()
        pendientes_firma = Acta.query.filter_by(estado=ActaStatus.PENDIENTE_FIRMA.value).count()
        borradores = Acta.query.filter_by(estado=ActaStatus.BORRADOR.value).count()
        pendientes_saludsa = Acta.query.filter(
            Acta.estado == ActaStatus.FIRMADA.value,
            Acta.sincronizado_saludsa == False
        ).count()
        
        print("\n=== Estadísticas después de seed ===")
        print(f"Total actas: {total_actas}")
        print(f"Pendientes de firma: {pendientes_firma}")
        print(f"Borradores: {borradores}")
        print(f"Pendientes de sincronización con Saludsa: {pendientes_saludsa}")
        print("\n¡Datos de prueba creados exitosamente!")


if __name__ == '__main__':
    create_test_data()
