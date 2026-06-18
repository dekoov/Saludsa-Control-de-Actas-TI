# Guía de Configuración - Sistema tipo Laravel

## Resumen

El proyecto ahora tiene un sistema de configuración centralizado similar a Laravel. Todas las variables de entorno se cargan automáticamente al iniciar la aplicación y están disponibles globalmente.

## Ubicación

- **Archivo de configuración**: `src/config/config.py`
- **Variables de entorno**: `.env` (local) o `.env.example` (plantilla)
- **Uso**: `from src.config import config`

## Cómo Usar

### 1. Importar la configuración

```python
from src.config import config

# Acceder a cualquier variable
server = config.LDAP_SERVER
port = config.PORT
```

### 2. Variables Disponibles

#### LDAP
- `config.LDAP_SERVER` - Servidor LDAP
- `config.LDAP_USER` - Usuario LDAP
- `config.LDAP_PASSWORD` - Contraseña LDAP
- `config.LDAP_BASE_DN` - Base DN (default: `dc=saludsa,dc=com,dc=ec`)
- `config.LDAP_SEARCH_LIMIT` - Límite de búsqueda (default: `15`)

#### Flask
- `config.FLASK_ENV` - Entorno (`development`/`production`)
- `config.FLASK_DEBUG` - Modo debug (`True`/`False`)
- `config.SECRET_KEY` - Clave secreta
- `config.PORT` - Puerto del servidor (default: `5000`)

#### Base de Datos
- `config.DATABASE_URL` - URL completa de conexión
- `config.DB_HOST` - Host de la base de datos
- `config.DB_PORT` - Puerto
- `config.DB_NAME` - Nombre de la base de datos
- `config.DB_USER` - Usuario
- `config.DB_PASSWORD` - Contraseña

#### API
- `config.API_PREFIX` - Prefijo de API (default: `/api`)
- `config.CORS_ORIGINS` - Orígenes permitidos CORS

### 3. Métodos Útiles

```python
# Verificar entorno
if config.is_production():
    # Código específico para producción
    pass

if config.is_development():
    # Código específico para desarrollo
    pass

# Validar configuración LDAP
if config.validate_ldap_config():
    # Todas las variables LDAP están configuradas
    pass
else:
    # Obtener variables faltantes
    missing = config.get_missing_ldap_vars()
    print(f"Faltan: {', '.join(missing)}")
```

## Ejemplos de Uso

### En un Blueprint

```python
from flask import Blueprint
from src.config import config

my_bp = Blueprint('my_bp', __name__)

@my_bp.route('/api/info')
def get_info():
    return {
        'environment': config.FLASK_ENV,
        'debug_mode': config.FLASK_DEBUG,
        'ldap_server': config.LDAP_SERVER
    }
```

### En un Servicio

```python
from src.config import config
import psycopg2

def connect_db():
    if config.DATABASE_URL:
        return psycopg2.connect(config.DATABASE_URL)
    else:
        return psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
```

### En Main.py

```python
from src.config import config

# Usar para configurar Flask
app.run(
    debug=config.FLASK_DEBUG,
    port=config.PORT,
    host='0.0.0.0' if config.is_production() else '127.0.0.1'
)
```

## Agregar Nuevas Variables

### 1. Agregar al archivo `.env`:

```env
NUEVA_VARIABLE=valor
```

### 2. Agregar a `src/config/config.py`:

```python
class Config:
    # ... variables existentes ...
    
    # Nueva variable
    NUEVA_VARIABLE: str = os.getenv('NUEVA_VARIABLE', 'valor_default')
```

### 3. Actualizar `.env.example`:

```env
# Descripción de la variable
NUEVA_VARIABLE=valor_default
```

### 4. Usar en el código:

```python
from src.config import config

valor = config.NUEVA_VARIABLE
```

## Buenas Prácticas

1. **Siempre usar valores por defecto**: Proporciona defaults sensibles para evitar errores
2. **Validar configuración crítica**: Usa `validate_ldap_config()` antes de conectar
3. **No commitear el `.env`**: Solo el `.env.example` debe estar en git
4. **Documentar nuevas variables**: Agregar a esta guía y al `.env.example`
5. **Usar tipos apropiados**: Strings, ints, bools según corresponda

## Migración desde código anterior

Si tienes código antiguo que usa `os.getenv()` directamente:

```python
# ANTES ❌
import os
ldap_server = os.getenv('LDAP_SERVER')

# DESPUÉS ✅
from src.config import config
ldap_server = config.LDAP_SERVER
```

## Troubleshooting

### Las variables aparecen vacías

Asegúrate de que `load_dotenv()` se ejecute ANTES de importar `config`:

```python
from dotenv import load_dotenv
load_dotenv()  # Primero esto

from src.config import config  # Luego esto
```

### Cambios en .env no se reflejan

Reinicia el servidor. Las variables se cargan una sola vez al iniciar.

### Módulo no encontrado

Verifica que estés importando correctamente:

```python
from src.config import config  # ✅ Correcto
from config import config      # ❌ Incorrecto
```
