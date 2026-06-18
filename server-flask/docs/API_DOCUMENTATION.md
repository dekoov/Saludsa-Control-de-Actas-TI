# API Documentation - Saludsa Demo App Flask Server

## Overview
Esta documentación describe los endpoints disponibles en el servidor Flask de Saludsa para que una IA de frontend pueda entender cómo interactuar con el backend, qué datos enviar y qué esperar como respuesta.

## Base URL
```
http://localhost:5000
```

## Base de Datos

### Motor
- **SQLite** (por defecto) o PostgreSQL (configurable vía `DATABASE_URL`)
- Archivo: `saludsa.db` (ubicado en el directorio raíz del servidor)

### Modelos de Datos

#### Tabla: `empleados`
Almacena información de empleados/usuarios.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | ID autogenerado |
| username | String (unique) | Nombre de usuario |
| full_name | String | Nombre completo |
| national_id | String (indexed) | Cédula/RUC |
| city | String | Ciudad |

#### Tabla: `activos`
Almacena laptops únicamente.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | ID autogenerado |
| manufacturer | String | Fabricante |
| model | String | Modelo |
| serial_number | String (unique) | Número de serie |
| hostname | String (indexed) | Hostname del equipo |
| purchase_cost | Float | Costo de compra |
| status | String (indexed) | Estado (Nuevo/Usado) |
| location | String (indexed) | Ubicación |
| observation | String | Observaciones |
| fecha_registro | DateTime | Fecha de registro |

#### Tabla: `accesorios`
Almacena accesorios (Cargador, Diadema, Mochila).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | ID autogenerado |
| equipment_type | String (indexed) | Tipo (Cargador/Diadema/Mochila) |
| manufacturer | String | Fabricante |
| model | String | Modelo |
| serial_number | String | Número de serie (default: "NA") |
| quantity | Integer | Cantidad |
| purchase_cost | Float | Costo de compra |
| status | String (indexed) | Estado (Nuevo/Usado) |
| location | String (indexed) | Ubicación |
| observation | String | Observaciones |
| fecha_registro | DateTime | Fecha de registro |

#### Tabla: `actas`
Almacena actas oficiales generadas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | String (PK) | ID formato "ACT-YYYYMMDD-NNN" |
| fecha | DateTime (indexed) | Fecha de creación |
| tipo | String (indexed) | Tipo (Dotacion/Renovacion) |
| estado | String (indexed) | Estado (Pendiente Firma/Firmada) |
| sincronizado_saludsa | Boolean (indexed) | Sincronizado con YoSoySaludsa |
| empleado_id | Integer (FK, indexed) | ID del empleado |
| tiene_pagare | Boolean | Tiene pagaré asociado |
| archivo_acta | String | Ruta del archivo acta |
| archivo_pagare | String | Ruta del archivo pagaré |

#### Tabla: `acta_drafts`
Almacena borradores de formularios (sin documentos generados).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer (PK) | ID autogenerado |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de última actualización |
| titulo | String (indexed) | Título generado automáticamente |
| usuario_json | Text | Datos del usuario en JSON |
| equipos_json | Text | Datos de equipos en JSON |
| marcar_firmada | Boolean | Toggle de marcar como firmada |

#### Tablas de Relación
- `acta_activos`: Relación muchos-a-muchos entre actas y activos
- `acta_accesorios`: Relación muchos-a-muchos entre actas y accesorios

## Endpoints Disponibles

### 1. Generación de Actas de Entrega

#### `POST /api/actas/generate`

**Descripción**: Registra equipos y genera un acta de entrega en formato Word. Si el primer equipo es una Laptop, también genera un pagaré.

**Headers Requeridos**:
```
Content-Type: application/json
```

**Body (JSON)**:
```json
{
  "equipos": [
    {
      "id": 1,
      "equipment_type": "Laptop",
      "quantity": 1,
      "manufacturer": "Dell",
      "model": "Latitude 5420",
      "serial_number": "DL123456789",
      "purchase_cost": 1200.50,
      "status": "Nuevo",
      "hostname": "LPT-JDOE",
      "observation": "Entregado en perfecto estado",
      "location": "BODEGA GYE"
    },
    {
      "id": 2,
      "equipment_type": "Cargador",
      "quantity": 1,
      "manufacturer": "Dell",
      "model": "65W USB-C",
      "serial_number": "CG987654321",
      "purchase_cost": 45.00,
      "status": "Nuevo",
      "observation": "",
      "location": "BODEGA GYE"
    }
  ],
  "usuario": {
    "username": "jdoe",
    "full_name": "Juan Doe Pérez",
    "national_id": "1712345678",
    "city": "Guayaquil"
  },
  "marcar_firmada": false,
  "draft_id": null
}
```

**Campos Adicionales (Opcionales)**:
- `marcar_firmada` (bool): Si es `true`, el estado del acta será "Firmada". Si es `false` o no se envía, el estado será "Pendiente Firma".
- `draft_id` (int): Si se proporciona, carga los datos del borrador con ese ID y lo elimina después de generar el acta exitosamente.

**Campos Obligatorios del Objeto `equipos`**:
- `id` (int): Identificador único del equipo
- `equipment_type` (str): Tipo de equipo. Valores válidos: `"Laptop"`, `"Cargador"`, `"Diadema"`, `"Mochila"`
- `quantity` (int): Cantidad (debe ser > 0)
- `manufacturer` (str): Fabricante
- `purchase_cost` (float): Costo de compra (no puede ser negativo)
- `status` (str): Estado. Valores válidos: `"Nuevo"`, `"Usado"`

**Campos Condicionales por Tipo de Equipo**:

**Para Laptop**:
- `serial_number` (str): **Obligatorio** - Número de serie
- `model` (str): **Obligatorio** - Modelo del equipo
- `hostname` (str): **Obligatorio** - Nombre del host (no puede ser "N/A")

**Para Cargador/Diadema**:
- `model` (str): **Obligatorio** - Modelo
- `serial_number` (str): Opcional, si no se proporciona se asigna "NA"

**Para Mochila**:
- `model` (str): Opcional, si no se proporciona se asigna "Genérico"
- `serial_number` (str): Opcional, si no se proporciona se asigna "NA"

**Campos Opcionales del Objeto `equipos`**:
- `observation` (str): Observaciones (default: "")
- `location` (str): Ubicación (default: "BODEGA GYE")

**Campos del Objeto `usuario`**:
- `username` (str): Nombre de usuario para nombres de archivo
- `full_name` (str): Nombre completo del usuario
- `national_id` (str): Cédula/RUC del usuario
- `city` (str): Ciudad del usuario

**Respuestas Exitosas**:

**Status 200 - OK**:
```json
{
  "message": "Documentos generados exitosamente",
  "documents": [
    {
      "document_type": "acta",
      "file_name": "ENTREGA_jdoe_Laptop_DL123456789.docx",
      "pdf_base64": "base64_encoded_pdf_data"
    },
    {
      "document_type": "pagare",
      "file_name": "PAGARE_jdoe_LAPTOP_DL123456789.docx",
      "pdf_base64": "base64_encoded_pdf_data"
    }
  ]
}
```
*Nota: Si el primer equipo no es Laptop, solo se genera un documento (acta).*

**Respuestas de Error**:

**Status 400 - Bad Request**:
```json
{
  "error": "Se esperaba un objeto JSON valido o con datos"
}
```
```json
{
  "error": "El JSON debe contener los campos requeridos: 'equipos' y 'usuario'"
}
```
```json
{
  "error": "Error de validación",
  "detalle": "Una Laptop DEBE tener número de serie."
}
```
```json
{
  "error": "Borrador no encontrado"
}
```

**Status 500 - Internal Server Error**:
```json
{
  "error": "Error al registrar el equipo",
  "detalle": "Mensaje específico del error"
}
```

---

### 2. Búsqueda de Usuarios en Active Directory

#### `GET /api/ad/users`

**Descripción**: Busca usuarios en Active Directory basado en un query de búsqueda.

**Parámetros Query**:
- `q` (string, **obligatorio**): Término de búsqueda. Puede ser nombre de usuario (sAMAccountName) o parte del nombre completo (displayName).

**Ejemplos de Uso**:
```
GET /api/ad/users?q=jdoe
GET /api/ad/users?q=Juan Perez
GET /api/ad/users?q=juan
```

**Lógica de Búsqueda**:
- **Una palabra**: Busca coincidencias parciales en `sAMAccountName` o `displayName`
- **Múltiples palabras**: Busca coincidencias en `displayName` que contengan todas las palabras (AND lógico)

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
{
  "usuarios": [
    {
      "first_names": "Juan",
      "last_names": "Doe Pérez",
      "display_name": "Juan Doe Pérez",
      "full_name": "Juan Doe Pérez",
      "username": "jdoe",
      "national_id": "1712345678",
      "department": "TI",
      "position": "Desarrollador",
      "email": "juan.doe@saludsa.com",
      "city": "Guayaquil"
    }
  ]
}
```

**Campos de Respuesta**:
- `first_names` (str): Nombres del usuario
- `last_names` (str): Apellidos del usuario
- `display_name` (str): Nombre completo para mostrar
- `full_name` (str): Nombre completo
- `username` (str): Nombre de usuario (sAMAccountName)
- `national_id` (str): Cédula/RUC (employeeID)
- `department` (str): Departamento
- `position` (str): Cargo/Posición (Description)
- `email` (str): Correo electrónico
- `city` (str): Ciudad

**Respuestas de Error**:

**Status 400 - Bad Request**:
```json
{
  "error": "Falta el parámetro de búsqueda (q)"
}
```

**Status 500 - Internal Server Error**:
```json
{
  "error": "Error en búsqueda AD",
  "details": "Fallo la conexión o busqueda en LDAP: Mensaje específico del error"
}
```

---

### 3. Dashboard - Estadísticas

#### `GET /api/dashboard/stats`

**Descripción**: Obtiene estadísticas del dashboard para mostrar resumen de actas.

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
{
  "total_actas": 124,
  "pendientes_firma": 18,
  "borradores": 7,
  "pendientes_saludsa": 14
}
```

**Campos de Respuesta**:
- `total_actas` (int): Total de actas registradas
- `pendientes_firma` (int): Actas pendientes de firma
- `borradores` (int): Borradores guardados
- `pendientes_saludsa` (int): Actas pendientes de sincronizar con YoSoySaludsa

---

### 4. Dashboard - Usuarios Recientes

#### `GET /api/dashboard/recent-users`

**Descripción**: Obtiene lista de usuarios con actas recientes.

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
[
  {
    "username": "jdoe",
    "full_name": "Juan Doe Pérez",
    "city": "Guayaquil",
    "fecha_ultima_acta": "2024-04-29T10:30:00"
  },
  {
    "username": "msmith",
    "full_name": "María Smith",
    "city": "Quito",
    "fecha_ultima_acta": "2024-04-28T15:45:00"
  }
]
```

**Campos de Respuesta**:
- `username` (str): Nombre de usuario
- `full_name` (str): Nombre completo
- `city` (str): Ciudad
- `fecha_ultima_acta` (str): Fecha de la última acta (ISO 8601)

---

### 5. Historial de Actas

#### `GET /api/actas/historial`

**Descripción**: Obtiene el historial de actas con paginación.

**Parámetros Query**:
- `page` (int, opcional): Número de página (default: 1)
- `per_page` (int, opcional): Items por página (default: 20, max: 100)

**Ejemplos de Uso**:
```
GET /api/actas/historial
GET /api/actas/historial?page=2&per_page=10
```

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
{
  "data": [
    {
      "id": "ACT-20240429-001",
      "fecha": "2024-04-29T10:30:00",
      "empleado": "Juan Doe Pérez",
      "equipos_resumen": "Dell Latitude 5420 + Dell 65W USB-C",
      "tipo": "Dotacion",
      "estado": "Pendiente Firma",
      "tiene_pagare": true
    }
  ],
  "total": 124,
  "page": 1,
  "per_page": 20
}
```

**Campos de Respuesta**:
- `data` (array): Lista de actas
- `total` (int): Total de actas
- `page` (int): Página actual
- `per_page` (int): Items por página

**Campos de cada Acta**:
- `id` (str): ID del acta
- `fecha` (str): Fecha de creación (ISO 8601)
- `empleado` (str): Nombre del empleado
- `equipos_resumen` (str): Resumen de equipos
- `tipo` (str): Tipo de acta (Dotacion/Renovacion)
- `estado` (str): Estado (Pendiente Firma/Firmada)
- `tiene_pagare` (bool): Tiene pagaré asociado

---

### 6. Borradores - Guardar

#### `POST /api/drafts`

**Descripción**: Guarda un borrador del formulario de acta sin generar documentos.

**Headers Requeridos**:
```
Content-Type: application/json
```

**Body (JSON)**:
```json
{
  "usuario": {
    "username": "jdoe",
    "full_name": "Juan Doe Pérez",
    "national_id": "1712345678",
    "city": "Guayaquil"
  },
  "equipos": [
    {
      "equipment_type": "Laptop",
      "manufacturer": "Dell",
      "model": "Latitude 5420",
      "serial_number": "DL123456789",
      "purchase_cost": 1200.50,
      "status": "Nuevo",
      "hostname": "LPT-JDOE",
      "observation": "",
      "location": "BODEGA GYE"
    }
  ],
  "marcar_firmada": false
}
```

**Respuesta Exitosa**:

**Status 201 - Created**:
```json
{
  "message": "Borrador guardado",
  "id": 1
}
```

**Respuestas de Error**:

**Status 400 - Bad Request**:
```json
{
  "error": "El JSON debe contener: ['usuario', 'equipos']"
}
```

---

### 7. Borradores - Listar

#### `GET /api/drafts`

**Descripción**: Obtiene todos los borradores ordenados por fecha más reciente.

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
[
  {
    "id": 1,
    "titulo": "Juan Doe Pérez - Laptop Dell - 29/04 10:30",
    "updated_at": "2024-04-29T10:30:00"
  },
  {
    "id": 2,
    "titulo": "María Smith - Laptop + 2 accesorios - 29/04",
    "updated_at": "2024-04-29T09:15:00"
  }
]
```

**Campos de Respuesta**:
- `id` (int): ID del borrador
- `titulo` (str): Título generado automáticamente
- `updated_at` (str): Fecha de última actualización (ISO 8601)

---

### 8. Borradores - Obtener

#### `GET /api/drafts/<id>`

**Descripción**: Obtiene un borrador específico con su contenido completo.

**Parámetros URL**:
- `id` (int, **obligatorio**): ID del borrador

**Ejemplo de Uso**:
```
GET /api/drafts/1
```

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
{
  "id": 1,
  "titulo": "Juan Doe Pérez - Laptop Dell - 29/04 10:30",
  "usuario": {
    "username": "jdoe",
    "full_name": "Juan Doe Pérez",
    "national_id": "1712345678",
    "city": "Guayaquil"
  },
  "equipos": [
    {
      "equipment_type": "Laptop",
      "manufacturer": "Dell",
      "model": "Latitude 5420",
      "serial_number": "DL123456789",
      "purchase_cost": 1200.50,
      "status": "Nuevo",
      "hostname": "LPT-JDOE",
      "observation": "",
      "location": "BODEGA GYE"
    }
  ],
  "marcar_firmada": false
}
```

**Respuestas de Error**:

**Status 404 - Not Found**:
```json
{
  "error": "Borrador no encontrado"
}
```

---

### 9. Borradores - Eliminar

#### `DELETE /api/drafts/<id>`

**Descripción**: Elimina un borrador específico.

**Parámetros URL**:
- `id` (int, **obligatorio**): ID del borrador

**Ejemplo de Uso**:
```
DELETE /api/drafts/1
```

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
{
  "message": "Borrador eliminado"
}
```

**Respuestas de Error**:

**Status 404 - Not Found**:
```json
{
  "error": "Borrador no encontrado"
}
```

---

### 10. Usuarios - Listar

#### `GET /api/user`

**Descripción**: Obtiene la lista de usuarios disponibles.

**Respuesta Exitosa**:

**Status 200 - OK**:
```json
{
  "users": [
    {
      "username": "jdoe",
      "name": "Juan Doe Pérez"
    }
  ]
}
```

---

## Consideraciones Importantes para el Frontend

### 1. Validaciones del Lado del Cliente
Antes de enviar datos al backend, el frontend debería validar:
- Que todos los campos obligatorios estén presentes
- Que `equipment_type` sea uno de los valores permitidos
- Que `status` sea "Nuevo" o "Usado"
- Que `quantity` sea > 0
- Que `purchase_cost` no sea negativo
- Validaciones específicas por tipo de equipo (ver sección de campos condicionales)

### 2. Flujo de Generación de Documentos
- Siempre se genera un Acta de Entrega
- El Pagaré solo se genera si el **primer equipo** en la lista es una Laptop
- Los nombres de archivo siguen el patrón: `ENTREGA_{username}_{tipo}_{serie}.docx`
- Los documentos se retornan en base64 para que el frontend pueda mostrarlos directamente

### 3. Estados de Actas
- **Pendiente Firma**: Estado por defecto cuando `marcar_firmada` es `false` o no se envía
- **Firmada**: Estado cuando `marcar_firmada` es `true`
- **BORRADOR**: Estado antiguo (mantenido para compatibilidad con datos existentes, pero no se usa para nuevas actas)

### 4. Sistema de Borradores
- Los borradores son snapshots del formulario sin generar documentos
- Se almacenan en la tabla `acta_drafts` separada de `actas`
- El título se genera automáticamente basado en usuario y equipos
- Al generar un acta desde un borrador, este se elimina automáticamente
- Los borradores pueden cargarse para rellenar el formulario en `/nueva-acta`

### 5. Manejo de Errores
- El backend retorna mensajes detallados de validación
- Los errores 400 indican problemas con los datos enviados
- Los errores 404 indican recursos no encontrados (borradores)
- Los errores 500 indican problemas internos del servidor

### 6. Búsqueda de Usuarios
- La búsqueda es case-insensitive
- Soporta búsqueda por nombre de usuario exacto o parcial
- Soporta búsqueda por múltiples palabras en nombre completo
- Retorna máximo el número configurado en `LDAP_SEARCH_LIMIT`

### 7. Formatos de Datos
- Todos los valores numéricos deben enviarse como números, no como strings
- Las fechas se manejan internamente, no es necesario enviarlas
- Los campos opcionales pueden omitirse completamente o enviarse como null/vacíos
- Las fechas en respuestas están en formato ISO 8601

---

## Ejemplo Completo de Flujo de Trabajo

### Paso 1: Buscar Usuario
```javascript
// Búsqueda de usuario
fetch('/api/ad/users?q=Juan Perez')
  .then(response => response.json())
  .then(data => {
    // Seleccionar usuario de los resultados
    const usuario = data.usuarios[0];
  });
```

### Paso 2: Preparar Datos de Equipos
```javascript
const equipos = [
  {
    id: 1,
    equipment_type: "Laptop",
    quantity: 1,
    manufacturer: "Dell",
    model: "Latitude 5420",
    serial_number: "DL123456789",
    purchase_cost: 1200.50,
    status: "Nuevo",
    hostname: "LPT-JDOE"
  }
];

const usuario = {
  username: "jdoe",
  full_name: "Juan Doe Pérez",
  national_id: "1712345678",
  city: "Guayaquil"
};
```

### Paso 3: Generar Acta
```javascript
fetch('/api/actas/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    equipos: equipos,
    usuario: usuario,
    marcar_firmada: false
  })
})
.then(response => response.json())
.then(data => {
  // Procesar documentos en base64
  data.documents.forEach(doc => {
    const byteCharacters = atob(doc.pdf_base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
  });
});
```

### Paso 4: Guardar Borrador (Opcional)
```javascript
// Guardar formulario como borrador
fetch('/api/drafts', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    usuario: usuario,
    equipos: equipos,
    marcar_firmada: false
  })
})
.then(response => response.json())
.then(data => {
  console.log('Borrador guardado con ID:', data.id);
});
```

### Paso 5: Cargar Borrador y Generar Acta
```javascript
// Obtener borrador
fetch('/api/drafts/1')
  .then(response => response.json())
  .then(draft => {
    // Generar acta desde borrador
    return fetch('/api/actas/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        draft_id: draft.id
      })
    });
  })
  .then(response => response.json())
  .then(data => {
    // Procesar documentos - el borrador se elimina automáticamente
    console.log('Acta generada desde borrador');
  });
```

---

## Configuración Adicional

### Variables de Entorno Relevantes
- `LDAP_BASE_DN`: Base DN para búsquedas LDAP
- `LDAP_SEARCH_LIMIT`: Límite de resultados de búsqueda
- `DATABASE_URI`: URL de conexión a base de datos (default: SQLite local)
- Configuración de conexión LDAP en `src/config/ldap_config.py`
- Configuración general en `src/config/config.py`

### Templates Utilizados
- `acta_template.docx`: Plantilla para actas de entrega
- `pagare_template.docx`: Plantilla para pagarés (solo laptops)

### Estructura del Proyecto
```
server-flask/
├── main.py                 # Punto de entrada y registro de blueprints
├── src/
│   ├── config/             # Configuración centralizada
│   │   └── config.py
│   ├── db/                 # Inicialización de base de datos
│   │   └── __init__.py
│   ├── models/             # Modelos SQLAlchemy
│   │   └── equipment.py    # Activo, Accesorio, Empleado, Acta, ActaDraft
│   ├── routes/             # Blueprints de API
│   │   ├── actas_route.py  # Generación de actas e historial
│   │   ├── users_route.py  # Búsqueda AD y usuarios
│   │   ├── dashboard_route.py # Dashboard stats
│   │   └── drafts_route.py # Sistema de borradores
│   └── services/           # Lógica de negocio
│       ├── acta_service.py          # Generación de documentos
│       ├── acta_persistence_service.py # Persistencia en BD
│       ├── draft_service.py         # Gestión de borradores
│       ├── dashboard_service.py     # Consultas de dashboard
│       ├── ad_service.py            # Integración LDAP
│       └── document_service.py     # Manipulación DOCX/PDF
└── docs/                   # Documentación
    ├── API_DOCUMENTATION.md
    └── CONFIG_GUIDE.md
```

Esta documentación está diseñada para que una IA de frontend pueda implementar correctamente la integración con el backend Flask de Saludsa.
