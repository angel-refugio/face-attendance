# FaceAttendance - Sistema de Control de Asistencia con Reconocimiento Facial

Sistema de control de asistencia empresarial que utiliza **reconocimiento facial con OpenCV y LBPH** para registrar la entrada de empleados. Incluye dashboard web con estadísticas, historial, exportación de reportes y cámara en vivo.

## Demo en Vivo

**URL:** `https://face-attendance.onrender.com`  
**Credenciales:** admin / admin123

## Tecnologías

| Componente | Tecnología |
|---|---|
| Backend | Python 3.12 + Flask |
| Base de datos | PostgreSQL + SQLAlchemy |
| Reconocimiento facial | OpenCV + LBPH Face Recognizer |
| Data augmentation | OpenCV (6 variantes por imagen) |
| Frontend | Bootstrap 5 + Chart.js |
| Cámara | WebRTC (JavaScript) |
| Despliegue | Docker + Render.com |
| Testing | pytest + pytest-cov |

## Arquitectura

```
Empleado frente a cámara
    |
    v
WebRTC (navegador) → Flask API
    |
    ├── 1. Decodifica imagen base64
    ├── 2. Detecta rostro (Haar Cascade)
    ├── 3. LBPH predict → identifica empleado
    ├── 4. Registra check-in en PostgreSQL
    ├── 5. Previene duplicados (ventana 5 min)
    └── 6. Retorna resultado + notificación
```

## Funcionalidades

### Dashboard
- Empleados presentes hoy con hora de entrada
- Estadísticas rápidas: total, puntuales, tardanzas, % asistencia
- Lista de empleados activos con estado de registro facial

### Cámara en Vivo
- Feed de webcam en el navegador (WebRTC)
- Reconocimiento facial automático cada 2 segundos
- Registro automático de asistencia al reconocer empleado
- Notificaciones en tiempo real de check-ins

### Gestión de Empleados
- CRUD completo de empleados
- Registro de rostro vía webcam (captura 15-30 fotos)
- Entrenamiento de modelo LBPH con data augmentation
- Activar/desactivar empleados

### Historial de Asistencia
- Tabla con filtros por empleado, estado, rango de fechas
- Paginación
- Exportar a CSV y Excel

### Estadísticas
- Gráfica de asistencia últimos 14 días (Chart.js)
- Ranking de puntualidad por empleado
- Porcentaje de asistencia por persona

## Estructura del Proyecto

```
face-attendance/
├── app/
│   ├── __init__.py              # Flask factory pattern
│   ├── config.py                # Pydantic Settings
│   ├── extensions.py            # SQLAlchemy, Flask-Login, Flask-Migrate
│   ├── models/
│   │   ├── employee.py          # Modelo Employee
│   │   ├── attendance.py        # Modelo AttendanceRecord
│   │   └── user.py              # Modelo Admin User
│   ├── routes/
│   │   ├── main.py              # Dashboard
│   │   ├── employees.py         # CRUD empleados
│   │   ├── attendance.py        # Historial + exportar
│   │   ├── camera.py            # WebRTC + reconocimiento
│   │   └── auth.py              # Login admin
│   ├── services/
│   │   ├── face_service.py      # OpenCV + LBPH
│   │   ├── attendance_service.py # Lógica check-in
│   │   └── report_service.py    # Exportar CSV/Excel
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/camera.js         # WebRTC client
│   │   └── uploads/rostros/     # Fotos de empleados
│   └── templates/               # HTML con Bootstrap 5
├── tests/
├── Dockerfile
├── docker-compose.yml           # Flask + PostgreSQL
├── requirements.txt
├── Procfile
└── README.md
```

## Instalación Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/face-attendance.git
cd face-attendance
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores. Para desarrollo local usa SQLite (ya configurado).

### 5. Ejecutar

```bash
python run.py
```

Abre `http://localhost:5000`  
**Credenciales por defecto:** admin / admin123

## Docker

```bash
docker-compose up --build
```

Esto levanta Flask + PostgreSQL. Accede en `http://localhost:5000`.

## Testing

```bash
pytest tests/ -v --cov=app
```

## Despliegue en Render.com

1. Sube el proyecto a GitHub
2. Crea un **PostgreSQL Database** en Render (gratis, 90 días trial)
3. Crea un **Web Service** conectado a tu repo
4. Configura:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `waitress-serve --port=$PORT --call app:create_app`
5. Agrega variables de entorno:
   - `DATABASE_URL` (Render lo genera del PostgreSQL)
   - `SECRET_KEY` (genera una aleatoria)
   - `ADMIN_USERNAME` y `ADMIN_PASSWORD`
6. Despliega

## Uso del Sistema

### 1. Registrar empleados
- Ve a **Empleados** → **Nuevo Empleado**
- Completa nombre, departamento, puesto, email

### 2. Registrar rostro
- En la lista de empleados, click en el ícono de cámara
- Inicia la cámara y captura al menos 15 fotos desde diferentes ángulos
- Click en **Entrenar Modelo**

### 3. Marcar asistencia
- Ve a **Cámara**
- Inicia la cámara
- El sistema reconoce automáticamente a los empleados y registra su entrada

### 4. Ver reportes
- **Historial:** filtra por fecha, empleado, estado
- **Estadísticas:** gráficas de asistencia y ranking de puntualidad
- **Exportar:** descarga CSV o Excel

## Licencia

MIT
