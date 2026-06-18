"""
Test script para verificar la integración de SQLAlchemy con SQLite
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(application_path, '.env')
load_dotenv(env_path)

# Importar después de cargar .env
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Crear app Flask de prueba
app = Flask(__name__)
db_path = os.path.join(application_path, 'test_saludsa.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definir modelo de prueba
class TestUser(db.Model):
    __tablename__ = 'test_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<TestUser {self.username}>'

def test_sqlalchemy():
    print("=" * 50)
    print("TEST DE INTEGRACIÓN SQLALCHEMY + SQLITE")
    print("=" * 50)
    
    # 1. Crear todas las tablas
    print("\n1. Creando tablas en la base de datos...")
    try:
        with app.app_context():
            db.create_all()
            print("✓ Tablas creadas exitosamente")
    except Exception as e:
        print(f"✗ Error creando tablas: {e}")
        return False
    
    # 2. Insertar un usuario de prueba
    print("\n2. Insertando usuario de prueba...")
    try:
        with app.app_context():
            test_user = TestUser(
                username='test_user',
                email='test@saludsa.com',
                full_name='Usuario de Prueba'
            )
            db.session.add(test_user)
            db.session.commit()
            print(f"✓ Usuario insertado: {test_user}")
    except Exception as e:
        print(f"✗ Error insertando usuario: {e}")
        return False
    
    # 3. Consultar el usuario
    print("\n3. Consultando usuario de prueba...")
    try:
        with app.app_context():
            user = TestUser.query.filter_by(username='test_user').first()
            if user:
                print(f"✓ Usuario encontrado: {user}")
                print(f"  - ID: {user.id}")
                print(f"  - Username: {user.username}")
                print(f"  - Email: {user.email}")
                print(f"  - Full Name: {user.full_name}")
            else:
                print("✗ Usuario no encontrado")
                return False
    except Exception as e:
        print(f"✗ Error consultando usuario: {e}")
        return False
    
    # 4. Actualizar el usuario
    print("\n4. Actualizando usuario...")
    try:
        with app.app_context():
            user = TestUser.query.filter_by(username='test_user').first()
            user.full_name = 'Usuario de Prueba Actualizado'
            db.session.commit()
            print(f"✓ Usuario actualizado: {user.full_name}")
    except Exception as e:
        print(f"✗ Error actualizando usuario: {e}")
        return False
    
    # 5. Eliminar el usuario
    print("\n5. Eliminando usuario de prueba...")
    try:
        with app.app_context():
            user = TestUser.query.filter_by(username='test_user').first()
            db.session.delete(user)
            db.session.commit()
            print("✓ Usuario eliminado")
    except Exception as e:
        print(f"✗ Error eliminando usuario: {e}")
        return False
    
    # 6. Verificar que la base de datos existe
    print("\n6. Verificando archivo de base de datos...")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✓ Base de datos creada: {db_path}")
        print(f"  - Tamaño: {size} bytes")
    else:
        print("✗ Archivo de base de datos no encontrado")
        return False
    
    print("\n" + "=" * 50)
    print("✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    print("=" * 50)
    print(f"\nBase de datos de prueba: {db_path}")
    print("Puedes eliminar este archivo manualmente si lo deseas.")
    
    return True

if __name__ == '__main__':
    success = test_sqlalchemy()
    sys.exit(0 if success else 1)
