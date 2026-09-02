# 💰 Fiskal - Sistema de Finanzas Personales con Dashboard Analítico

Aplicación web integral de finanzas personales construida con arquitectura en capas, base de datos relacional normalizada en **Tercera Forma Normal (3FN)**, API REST modular en **Python / Flask**, motor de analítica y machine learning con **Pandas & Scikit-Learn**, e interfaz moderna con **Chart.js** y diseño *Glassmorphism*.

---

## 🏛️ 1. Estructura del Proyecto

El código está organizado de forma modular y desacoplada respetando la estructura exigida:

```text
finansas/
├── backend/
│   ├── rutas/
│   │   ├── __init__.py
│   │   ├── usuarios.py             # CRUD de usuarios y listados
│   │   ├── categorias.py           # Gestión de categorías de ingreso/gasto
│   │   ├── movimientos.py          # CRUD de transacciones y resumen ejecutivo
│   │   └── analitica.py            # Endpoints de ML y detección de anomalías
│   ├── modelos/
│   │   ├── __init__.py
│   │   └── database.py             # Pool de conexión MySQL + fallback SQLite local
│   ├── analitica/
│   │   ├── __init__.py
│   │   └── engine.py               # Regresión lineal y Z-Score con Scikit-Learn/Pandas
│   ├── app.py                      # Punto de entrada Flask, CORS y Blueprints
│   └── requirements.txt            # Dependencias del backend
├── frontend/
│   ├── index.html                  # Dashboard SPA responsivo y semántico
│   ├── css/
│   │   └── styles.css              # Sistema de diseño moderno Dark Glassmorphism
│   └── js/
│       ├── charts.js               # Instanciación y gestión de Chart.js
│       └── main.js                 # Lógica reactiva, llamadas Fetch y modales
├── database/
│   ├── schema.sql                  # Esquema DDL en 3FN con constraints e índices
│   └── seed.sql                    # Dataset de prueba con >4 meses y anomalía evidente
└── README.md                       # Documentación técnica y guía de despliegue
```

---

## 🔬 2. Especificaciones de Machine Learning & Analítica

### A. Predicción de Gasto del Próximo Mes (Regresión Lineal)
- **Librería**: `scikit-learn` (`LinearRegression`) y `pandas`.
- **Funcionamiento**: Agrupa el gasto mensual acumulado por usuario a lo largo del tiempo, construye una serie temporal $[0, 1, ..., N-1]$ y ajusta un modelo de regresión por mínimos cuadrados ordinarios para proyectar el período $N$.
- **Control de Excepciones**: Valida que existan al menos **3 meses de historial**. Si existen menos de 3 meses, lanza `InsuficientesDatosException` y la API retorna un estado descriptivo con los meses faltantes.

### B. Detección de Transacciones Anómalas ($Z\text{-score}$)
- **Fórmula**: 
  $$Z = \frac{x - \mu}{\sigma}$$
  Donde $x$ es el monto del movimiento, $\mu$ es el promedio histórico de la categoría y $\sigma$ es la desviación estándar.
- **Umbral**: $Z \ge 2.0$ (Desviación mayor a 2 sigmas sobre la media de la categoría).
- **Protección contra división por cero**: Si $\sigma = 0$ o la categoría contiene un único registro / registros idénticos, se asigna automáticamente $Z = 0.0$.

---

## 🚀 3. Guía de Instalación y Despliegue

### Requisitos Previos
- **Python 3.9+** instalado.
- **MySQL Server 8.0+** (o MariaDB) ejecutándose localmente o en Docker.
- Navegador web moderno (Chrome, Edge, Firefox).

---

### Paso 1: Configurar la Base de Datos MySQL

1. Abre tu gestor de base de datos preferido (MySQL Workbench, phpMyAdmin, DBeaver o CLI de MySQL).
2. Ejecuta el archivo de esquema:
   ```bash
   mysql -u root -p < database/schema.sql
   ```
3. Ejecuta el archivo de datos iniciales (semillas con 4 meses de historial y gasto anómalo):
   ```bash
   mysql -u root -p finanzas_db < database/seed.sql
   ```

> 💡 **Nota de Resiliencia**: Si no tienes un servidor MySQL activo en tu máquina durante el desarrollo, el backend incluye un sistema de inicialización y fallback inteligente a SQLite (`finanzas_dev.db`) con las mismas tablas y datos para que puedas probar la aplicación de inmediato sin fricción.

---

### Paso 2: Configurar el Entorno Virtual de Python

1. Abre una terminal en la raíz del proyecto (`finansas/`):
   ```bash
   # Crear entorno virtual
   python -m venv venv
   ```

2. Activar el entorno virtual:
   - **En Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **En Windows (CMD)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **En Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. Instalar dependencias requeridas:
   ```bash
   pip install -r backend/requirements.txt
   ```

---

### Paso 3: Configurar Variables de Entorno (Opcional)

Puedes crear un archivo `.env` en la carpeta `backend/` si tus credenciales de MySQL son distintas a las predeterminadas:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=finanzas_db
PORT=5000
```

---

### Paso 4: Iniciar el Servidor Backend & Frontend

Inicia la aplicación ejecutando `app.py`:

```bash
cd backend
python app.py
```

El servidor iniciará en: **`http://127.0.0.1:5000`**

- **Dashboard Web**: Abre `http://127.0.0.1:5000` en tu navegador para interactuar con la interfaz completa.
- **API Healthcheck**: Consulta `http://127.0.0.1:5000/api/health` para verificar la conectividad de la base de datos.

*(Opcionalmente, si deseas servir el frontend de forma desacoplada con Live Server o HTTP Server, puedes ejecutar `python -m http.server 3000` dentro de la carpeta `frontend/` y la API responderá con soporte CORS activado).*

---

## 📡 4. Referencia de Endpoints REST de la API

| Método | Endpoint | Parámetros / Query Params | Descripción |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/usuarios` | - | Lista todos los usuarios registrados |
| `POST` | `/api/usuarios` | Body: `{ nombre, email, moneda }` | Crea un nuevo usuario |
| `GET` | `/api/categorias` | `?id_usuario=&tipo=` | Lista categorías del sistema y del usuario |
| `POST` | `/api/categorias` | Body: `{ nombre, tipo, icono, color, id_usuario }` | Registra una nueva categoría |
| `GET` | `/api/movimientos` | `?id_usuario=&mes=&tipo=&id_categoria=&busqueda=` | Lista transacciones filtradas |
| `POST` | `/api/movimientos` | Body: `{ id_usuario, id_categoria, monto, tipo, fecha, descripcion, metodo_pago }` | Registra una nueva transacción |
| `PUT` | `/api/movimientos/<id>`| Body: `{ id_categoria, monto, tipo, fecha, descripcion, metodo_pago }` | Actualiza un movimiento existente |
| `DELETE`| `/api/movimientos/<id>`| - | Elimina un movimiento |
| `GET` | `/api/resumen` | `?id_usuario=&mes=` | Resumen de KPIs, comparativa vs mes anterior y dona de gastos |
| `GET` | `/api/analitica/prediccion` | `?id_usuario=` | Predicción con Regresión Lineal del próximo mes |
| `GET` | `/api/analitica/anomalias` | `?id_usuario=&umbral=2.0` | Detección de transacciones atípicas con Z-Score |
| `GET` | `/api/analitica/historico-comparativo` | `?id_usuario=` | Serie temporal de ingresos, gastos y balance |

---

## 🧪 5. Verificación de la Detección de Anomalías

En el dataset `seed.sql`, el usuario **Kaleth García** posee el siguiente registro en Enero 2024:
- **Categoría**: `Ocio & Entretenimiento` (Promedio habitual: ~$80.00)
- **Monto Anómalo**: `$2,850.00` ("Paquete de viaje imprevisto crucero VIP")
- **Resultado del Motor**: $Z \ge 3.4\sigma$, activando automáticamente la alerta visual en el dashboard con severidad crítica y destacando la fila en la tabla de transacciones.
