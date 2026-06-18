# Saludsa Control Actas TI

Sistema de Gestión de Actas de Entrega de Equipos informáticos. Aplicación web full-stack que permite buscar usuarios en Active Directory, registrar equipos asignados y generar actas de entrega en formato Word.

## Función Principal

El sistema facilita la **creación de actas de entrega de equipos informáticos** para el personal de la organización. Integra búsqueda de usuarios en Active Directory (LDAP) con generación automatizada de documentos Word, proporcionando una interfaz moderna y eficiente para el registro de asignación de activos tecnológicos.

## Funcionalidades Adicionales

- **Búsqueda de Usuarios (LDAP)**
  - Búsqueda en tiempo real de usuarios en Active Directory
  - Visualización de información completa del usuario (nombre, cargo, departamento, email, cédula)
  - Integración automática de datos del usuario seleccionado en el acta

- **Gestión de Equipos**
  - Registro de múltiples tipos de equipos (laptops, monitores, impresoras, etc.)
  - Catálogo de modelos predefinidos con valores automáticos
  - Estados de equipo: Nuevo, Usado
  - Campos: cantidad, marca, modelo, serie, valor, observaciones

- **Generación de Documentos**
  - Generación automática de actas en formato Word (.docx)
  - Plantillas personalizables con datos dinámicos
  - Conversión de valores numéricos a texto (ej: "$1,250" → "mil doscientos cincuenta dólares")

- **Dashboard Administrativo**
  - Vista resumen con estadísticas de entregas
  - Widget de calendario y actividad reciente
  - Indicadores de estado del sistema

- **Configuración Centralizada**
  - Sistema de configuración tipo Laravel con variables de entorno
  - Soporte para múltiples entornos (desarrollo, producción)
  - Validación automática de configuración LDAP

- **Interfaz Moderna**
  - Diseño responsive con Bootstrap 5 y React Bootstrap
  - Componentes UI reutilizables (Cards, Buttons, Forms, Tables)
  - Feedback visual con spinners, badges y alertas

- **Automatizaciones Incluidas**
  - Automatización del envio de correos de dotación y renovación
  - Integración con portal YoSoySaludsa para la dotación de equipos a colaboradores
  - Historico de entregas con opción de exportar a PDF

---

## Instalación Rápida (Windows)

### Opción 1: Script Automático (Recomendado)

El script `install.ps1` es **seguro para repositorios públicos** - no contiene credenciales y **nunca sobrescribe** archivos `.env` existentes.

Ejecuta en **PowerShell como Administrador**:

```powershell
# Clonar y ejecutar
git clone https://github.com/tu-usuario/Saludsa-Demo-App.git
cd Saludsa-Demo-App
.\install.ps1
```

**El script automáticamente:**
- Verifica/instala Python y Node.js
- Crea entorno virtual e instala dependencias
- **Preserva** tu `.env` si ya existe (nunca lo borra)
- Crea `.env` template si no existe (sin credenciales)
- Instala dependencias npm
- Genera scripts de inicio (`start-app.bat`)

**Nota de seguridad:** Después de la instalación, debes editar `server-flask/.env` con tus credenciales LDAP reales.

### Opción 2: Instalación Manual

#### Requisitos Previos
- Python 3.12 o superior
- Node.js 24 o superior
- LibreOffice instalado
- Git

#### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/Saludsa-Demo-App.git
cd Saludsa-Demo-App

# 2. Configurar Backend (Flask)
cd server-flask

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales LDAP

# Correr el servidor para verificar
python .\main.py

cd ..

# 3. Configurar Frontend (React)
cd client-react

# Instalar dependencias
npm install

# Correr la aplicación para verificar
npm run dev
```

---

## Uso

### Iniciar Backend (Flask)

```bash
cd server-flask
venv\Scripts\activate
python main.py
```

El servidor estará disponible en: `http://localhost:5000`

### Iniciar Frontend (React)

```bash
cd client-react
npm run dev
```

La aplicación estará disponible en: `http://localhost:5173`

---

## Tecnologías Utilizadas

### Backend
- **Flask (v3.1):** Framework principal para la creación de la API REST y el manejo de rutas.
- **Playwright (v1.59):** Motor de automatización y web scraping para interactuar con la plataforma externa (YoSoySaludsa).
- **Flask-SQLAlchemy & SQLAlchemy (v2.0):** ORM para la gestión, consultas y persistencia de datos en la base de datos de forma relacional.
- **PyInstaller (v6.19):** Herramienta para empaquetar el backend en un ejecutable (.exe), facilitando su distribución a los técnicos.
- **LDAP3:** Integración y autenticación con el Directorio Activo corporativo.
- **PyJWT (v2.13):** Manejo de tokens de seguridad (JSON Web Tokens) para la autenticación segura en la API.
- **Flask-CORS:** Control de accesos de origen cruzado para permitir la comunicación segura con el Frontend.
- **Docxtpl & Python-docx:** Plantillaje y manipulación de archivos Word para la generación automática de actas y pagarés.
- **Docx2pdf:** Conversor automatizado de los documentos generados a formato PDF.
- **Python-dotenv:** Gestión segura de variables de entorno y credenciales locales (`.env`).

### Frontend
- **React (v19.2):** Librería principal para la construcción de una interfaz de usuario reactiva, modular y de una sola página (SPA).
- **Vite (v8.0):** Herramienta de empaquetado (Bundler) ultrarrápida para el entorno de desarrollo y compilación de producción.
- **React Router DOM (v7.14):** Gestor de rutas del cliente para la navegación interna de la aplicación (Dashboard, Historial, Logs).
- **Tailwind CSS (v4.0) & PostCSS:** Framework de diseño utilitario para construir una interfaz estilizada, responsiva y corporativa de forma ágil.
- **Radix UI (Primitives):** Componentes de UI accesibles y sin estilos (Select, Dialog, Dropdown, Checkbox) que garantizan un comportamiento nativo y robusto.
- **Lucide React:** Conjunto de íconos vectoriales modernos y ligeros utilizados en el sidebar y botones del sistema.
- **Sonner:** Sistema de notificaciones emergentes (Toasts) dinámicas para informar éxitos o errores de sincronización en tiempo real.

---

## ⚙️ Configuración LDAP

Edita el archivo `server-flask/.env`:

```env
# LDAP Configuration
LDAP_SERVER=dominio.com
LDAP_BASE_DN=dc=dominio,dc=com
LDAP_SEARCH_LIMIT=20

# Credenciales para el ingreso a YoSoySaludsa (si se requiere automatización)
SALUDSA_USERNAME=username
SALUDSA_PASSWORD=password

# IP o hostname del servidor de correo interno
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587

# Cuenta de correo desde la cual se enviarán las notificaciones (debe ser una cuenta válida en el dominio)
SMTP_FROM=test@example.com.ec
# para construir destinatario: {username}@example.com.ec
EMAIL_DOMAIN=example.com.ec

# Usernames separados por coma — SIN @dominio
# Para agregar o quitar personas del CC: editar esta línea, sin tocar código
EMAIL_CC_USERNAMES=user1,user2,user3

```

---

## Contribución

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## Uso Interno

Este software fue desarrollado durante las pasantías realizadas en Saludsa y está destinado exclusivamente para uso interno de la organización.


## Autor

Proyecto desarrollado e implementado por David Correa durante sus pasantías en el área de TI de Saludsa.
