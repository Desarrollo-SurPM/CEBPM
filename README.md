# CEB FEM - Sistema de Gestión

Sistema de gestión integral para el club deportivo, desarrollado en Django.

## Características

- 👥 Gestión de usuarios (Administradores y Apoderados)
- 🏃‍♂️ Registro y gestión de jugadores
- 💰 Sistema de pagos y finanzas
- 📅 Programación de partidos y actividades
- 🤝 Gestión de patrocinadores
- 📧 Sistema de comunicaciones
- 📱 Interfaz responsive

## Despliegue en Railway

### Requisitos previos

1. Cuenta en [Railway](https://railway.app)
2. Base de datos PostgreSQL configurada

### Pasos para el despliegue

1. **Conectar repositorio a Railway:**
   - Crear nuevo proyecto en Railway
   - Conectar con tu repositorio de GitHub

2. **Configurar variables de entorno:**
   ```
   DJANGO_SECRET_KEY=tu-clave-secreta-aqui
   DJANGO_DEBUG=False
   DATABASE_URL=postgresql://user:password@host:port/database
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=tu-email@gmail.com
   EMAIL_HOST_PASSWORD=tu-password-email
   EMAIL_USE_TLS=True
   SITE_DOMAIN=https://tu-dominio.railway.app
   ```

3. **Railway se encargará automáticamente de:**
   - Instalar dependencias desde `requirements.txt`
   - Ejecutar migraciones (definido en `Procfile`)
   - Iniciar el servidor con Gunicorn

### Desarrollo local

1. **Clonar el repositorio:**
   ```bash
   git clone <tu-repositorio>
   cd DeportesPuertoMontt
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   - Copiar `.env.example` a `.env`
   - Configurar las variables según tu entorno

5. **Ejecutar migraciones:**
   ```bash
   python manage.py migrate
   ```

6. **Poblar base de datos (opcional):**
   ```bash
   python manage.py seed_data --clear
   ```

7. **Iniciar servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```

### Usuarios de prueba

Después de ejecutar `seed_data`, tendrás acceso a:

**Administradores:**
- admin1 / admin123
- admin2 / admin123

**Apoderados:**
- guardian1 / guardian123
- guardian2 / guardian123
- guardian3 / guardian123
- guardian4 / guardian123
- guardian5 / guardian123

### Estructura del proyecto

```
club/
├── club/                 # Configuración principal
├── users/               # Gestión de usuarios
├── players/             # Gestión de jugadores
├── finance/             # Sistema financiero
├── schedules/           # Programación
├── sponsors/            # Patrocinadores
├── communications/      # Comunicaciones
├── pages/              # Páginas públicas
├── core/               # Funcionalidades base
├── templates/          # Plantillas HTML
├── static/             # Archivos estáticos
└── media/              # Archivos subidos
```

### Tecnologías utilizadas

- **Backend:** Django 5.0
- **Base de datos:** PostgreSQL
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Despliegue:** Railway
- **Servidor web:** Gunicorn
- **Archivos estáticos:** WhiteNoise

### Soporte

Para reportar problemas o solicitar nuevas características, crear un issue en el repositorio.