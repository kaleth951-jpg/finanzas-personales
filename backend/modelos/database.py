"""
Módulo de Gestión de Conexión a Base de Datos
Soporta MySQL (por defecto) con pymysql/mysql-connector y fallback inteligente a SQLite para desarrollo local.
"""

import os
import time
import sqlite3
from decimal import Decimal
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

# Cargar variables de entorno si existe archivo .env de forma nativa
def _cargar_env_local():
    """Carga variables desde archivo .env sin requerir librerías externas."""
    for base in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), ".."), os.path.join(os.path.dirname(__file__), "..", "..")]:
        env_file = os.path.abspath(os.path.join(base, ".env"))
        if os.path.isfile(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

_cargar_env_local()

# Configuración de Base de Datos
DB_ENGINE = os.getenv("DB_ENGINE", "mysql").lower()  # 'mysql' o 'sqlite'
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "finanzas_db")
DB_PORT = int(os.getenv("DB_PORT", 3306))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "finanzas_dev.db"))

_DRIVER = None

def _get_mysql_driver():
    """Intenta cargar el driver PyMySQL."""
    global _DRIVER
    if _DRIVER is not None:
        return _DRIVER

    try:
        import pymysql
        import pymysql.cursors
        _DRIVER = ("pymysql", pymysql)
        return _DRIVER
    except Exception:
        _DRIVER = None
        return None


def serialize_row(row: Union[Dict[str, Any], tuple, list]) -> Any:
    """Convierte tipos especiales como Decimal, date o datetime en tipos serializables JSON."""
    if isinstance(row, dict):
        clean = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                clean[k] = float(v)
            elif isinstance(v, (date, datetime)):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        return clean
    elif isinstance(row, (list, tuple)):
        return [serialize_row(item) for item in row]
    return row


def _sqlite_date_format(val, fmt):
    """Polyfill de DATE_FORMAT de MySQL para SQLite."""
    if val is None:
        return None
    val_str = str(val)[:19]
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(val_str, pattern)
            res = fmt
            res = res.replace("%Y", f"{dt.year:04d}")
            res = res.replace("%m", f"{dt.month:02d}")
            res = res.replace("%d", f"{dt.day:02d}")
            res = res.replace("%H", f"{dt.hour:02d}")
            res = res.replace("%i", f"{dt.minute:02d}")
            res = res.replace("%s", f"{dt.second:02d}")
            return res
        except ValueError:
            continue
    if fmt == "%Y-%m" and len(val_str) >= 7:
        return val_str[:7]
    return str(val)


def _sqlite_month(val):
    """Polyfill de MONTH() de MySQL para SQLite."""
    if val is None:
        return None
    val_str = str(val)[:10]
    try:
        dt = datetime.strptime(val_str, "%Y-%m-%d")
        return dt.month
    except Exception:
        return int(val_str[5:7]) if len(val_str) >= 7 and val_str[5:7].isdigit() else None


def _sqlite_year(val):
    """Polyfill de YEAR() de MySQL para SQLite."""
    if val is None:
        return None
    val_str = str(val)[:4]
    return int(val_str) if val_str.isdigit() else None


def _register_sqlite_functions(conn: sqlite3.Connection):
    """Registra funciones compatibles con MySQL en la conexión SQLite activa."""
    conn.create_function("DATE_FORMAT", 2, _sqlite_date_format)
    conn.create_function("MONTH", 1, _sqlite_month)
    conn.create_function("YEAR", 1, _sqlite_year)
    conn.create_function("IFNULL", 2, lambda a, b: a if a is not None else b)
    conn.create_function("NOW", 0, lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


_MYSQL_AVAILABLE: Optional[bool] = None
_LAST_MYSQL_CHECK_TIME: float = 0.0
_MYSQL_RETRY_INTERVAL: float = 30.0  # Reintentar conexión a MySQL cada 30 segundos si está apagado


def get_db_connection():
    """
    Retorna una conexión activa a la base de datos configurada.
    Si MySQL no responde o no está disponible, conmuta instantáneamente a SQLite local.
    """
    global _MYSQL_AVAILABLE, _LAST_MYSQL_CHECK_TIME

    driver_info = _get_mysql_driver()
    now = time.time()

    should_try_mysql = (
        DB_ENGINE == "mysql"
        and driver_info is not None
        and (_MYSQL_AVAILABLE is not False or (now - _LAST_MYSQL_CHECK_TIME) > _MYSQL_RETRY_INTERVAL)
    )

    if should_try_mysql:
        _, driver = driver_info
        try:
            conn = driver.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                charset="utf8mb4",
                cursorclass=driver.cursors.DictCursor,
                autocommit=False,
                connect_timeout=1
            )
            _MYSQL_AVAILABLE = True
            return ("mysql", conn)
        except Exception:
            _MYSQL_AVAILABLE = False
            _LAST_MYSQL_CHECK_TIME = now

    # Conexión SQLite Fallback/Dev ultra rápida
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _register_sqlite_functions(conn)
    _init_sqlite_if_needed(conn)
    return ("sqlite", conn)


try:
    from werkzeug.security import generate_password_hash, check_password_hash

    def hash_password(password: str) -> str:
        """Genera un hash seguro para la contraseña."""
        return generate_password_hash(password)

    def verify_password(stored_hash: str, password: str) -> bool:
        """Verifica una contraseña contra su hash almacenado."""
        if not stored_hash or not password:
            return False
        try:
            return check_password_hash(stored_hash, password)
        except Exception:
            # Compatibilidad con contraseñas planas legacy
            return stored_hash == password
except Exception:
    import hashlib
    import secrets

    def hash_password(password: str) -> str:
        salt = secrets.token_hex(8)
        hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return f"sha256:{salt}:{hashed}"

    def verify_password(stored_hash: str, password: str) -> bool:
        if not stored_hash or not password:
            return False
        if stored_hash.startswith("sha256:"):
            try:
                _, salt, hashed = stored_hash.split(":", 2)
                return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == hashed
            except Exception:
                return False
        return stored_hash == password


def _init_sqlite_if_needed(conn: sqlite3.Connection):
    """Inicializa automáticamente las tablas y semillas en SQLite si no existen y asegura migraciones."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios';")
    default_hash = hash_password("password123")
    
    if not cursor.fetchone():
        schema_sql = f"""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL DEFAULT '',
            moneda TEXT NOT NULL DEFAULT 'USD',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categorias (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NULL,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('ingreso', 'gasto')),
            icono TEXT DEFAULT 'tag',
            color TEXT DEFAULT '#6366f1',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ingresos_gastos (
            id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_categoria INTEGER NOT NULL,
            monto REAL NOT NULL CHECK (monto > 0),
            tipo TEXT NOT NULL CHECK (tipo IN ('ingreso', 'gasto')),
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            metodo_pago TEXT NOT NULL DEFAULT 'efectivo',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
            FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria) ON DELETE RESTRICT
        );

        CREATE INDEX IF NOT EXISTS idx_mov_user_fecha ON ingresos_gastos (id_usuario, fecha);
        CREATE INDEX IF NOT EXISTS idx_mov_cat ON ingresos_gastos (id_categoria);
        CREATE INDEX IF NOT EXISTS idx_mov_tipo ON ingresos_gastos (tipo);
        """
        cursor.executescript(schema_sql)

        # Semilla básica de prueba en SQLite
        seed_sql = f"""
        INSERT OR IGNORE INTO usuarios (id_usuario, nombre, email, password_hash, moneda) VALUES
        (1, 'Kaleth García', 'kaleth@example.com', '{default_hash}', 'USD'),
        (2, 'Elena Morales', 'elena.morales@example.com', '{default_hash}', 'EUR');

        INSERT OR IGNORE INTO categorias (id_categoria, id_usuario, nombre, tipo, icono, color) VALUES
        (1, NULL, 'Salario Principal', 'ingreso', 'briefcase', '#10b981'),
        (2, NULL, 'Freelance & Consultoría', 'ingreso', 'laptop', '#06b6d4'),
        (3, NULL, 'Inversiones & Dividendos', 'ingreso', 'trending-up', '#8b5cf6'),
        (4, NULL, 'Otros Ingresos', 'ingreso', 'plus-circle', '#14b8a6'),
        (5, NULL, 'Alimentación & Supermercado', 'gasto', 'shopping-cart', '#f59e0b'),
        (6, NULL, 'Vivienda & Servicios', 'gasto', 'home', '#3b82f6'),
        (7, NULL, 'Transporte & Combustible', 'gasto', 'car', '#6366f1'),
        (8, NULL, 'Ocio & Entretenimiento', 'gasto', 'film', '#ec4899'),
        (9, NULL, 'Salud & Medicamentos', 'gasto', 'heart-pulse', '#ef4444'),
        (10, NULL, 'Educación & Cursos', 'gasto', 'book-open', '#84cc16'),
        (11, NULL, 'Tecnología & Gadgets', 'gasto', 'cpu', '#a855f7');

        -- =====================================================================
        -- MOVIMIENTOS HISTÓRICOS DESDE 2024 HASTA FECHA ACTUAL (2026)
        -- =====================================================================
        INSERT OR IGNORE INTO ingresos_gastos (id_usuario, id_categoria, monto, tipo, fecha, descripcion, metodo_pago) VALUES
        -- === 2024 ===
        -- Enero 2024 (Con gasto anómalo evidente en Ocio)
        (1, 1, 3200.00, 'ingreso', '2024-01-02', 'Nómina mensual Enero', 'transferencia'),
        (1, 2, 600.00,  'ingreso', '2024-01-18', 'Consultoría técnica cloud', 'transferencia'),
        (1, 6, 650.00,  'gasto',   '2024-01-03', 'Pago de arriendo apartamento', 'transferencia'),
        (1, 6, 115.00,  'gasto',   '2024-01-05', 'Factura servicios públicos', 'tarjeta_debito'),
        (1, 5, 410.00,  'gasto',   '2024-01-09', 'Mercado mensual supermercado', 'tarjeta_debito'),
        (1, 7, 105.00,  'gasto',   '2024-01-15', 'Combustible vehículo', 'efectivo'),
        (1, 9, 80.00,   'gasto',   '2024-01-22', 'Farmacia y vitaminas', 'tarjeta_debito'),
        (1, 8, 2850.00, 'gasto',   '2024-01-20', 'Paquete de viaje imprevisto crucero VIP todo incluido', 'tarjeta_credito'),
        (1, 8, 75.00,   'gasto',   '2024-01-28', 'Salida casual a restaurante', 'tarjeta_debito'),

        -- Febrero 2024
        (1, 1, 3200.00, 'ingreso', '2024-02-01', 'Nómina mensual Febrero', 'transferencia'),
        (1, 2, 350.00,  'ingreso', '2024-02-14', 'Auditoría de código freelance', 'transferencia'),
        (1, 6, 650.00,  'gasto',   '2024-02-02', 'Pago de arriendo apartamento', 'transferencia'),
        (1, 6, 118.00,  'gasto',   '2024-02-06', 'Factura luz, gas e internet', 'tarjeta_debito'),
        (1, 5, 435.00,  'gasto',   '2024-02-11', 'Mercado y provisiones', 'tarjeta_debito'),
        (1, 7, 115.00,  'gasto',   '2024-02-17', 'Gasolina mensual', 'efectivo'),
        (1, 8, 90.00,   'gasto',   '2024-02-21', 'Entradas concierto y cena', 'tarjeta_credito'),
        (1, 8, 60.00,   'gasto',   '2024-02-27', 'Suscripciones mensuales', 'tarjeta_credito'),
        (1, 10, 120.00, 'gasto',   '2024-02-24', 'Certificación AWS Cloud Practitioner', 'tarjeta_credito'),

        -- Junio 2024
        (1, 1, 3300.00, 'ingreso', '2024-06-01', 'Nómina mensual Junio', 'transferencia'),
        (1, 2, 500.00,  'ingreso', '2024-06-15', 'Desarrollo API clientes', 'transferencia'),
        (1, 6, 680.00,  'gasto',   '2024-06-02', 'Pago de arriendo', 'transferencia'),
        (1, 5, 450.00,  'gasto',   '2024-06-10', 'Mercado quincenal', 'tarjeta_debito'),
        (1, 7, 120.00,  'gasto',   '2024-06-16', 'Combustible y peajes', 'efectivo'),
        (1, 8, 110.00,  'gasto',   '2024-06-22', 'Cenas de fin de semana', 'tarjeta_credito'),

        -- Diciembre 2024
        (1, 1, 3400.00, 'ingreso', '2024-12-01', 'Nómina mensual Diciembre', 'transferencia'),
        (1, 1, 1000.00, 'ingreso', '2024-12-15', 'Bono fin de año', 'transferencia'),
        (1, 6, 680.00,  'gasto',   '2024-12-02', 'Pago de arriendo', 'transferencia'),
        (1, 5, 520.00,  'gasto',   '2024-12-12', 'Compras navideñas supermercado', 'tarjeta_debito'),
        (1, 8, 180.00,  'gasto',   '2024-12-24', 'Celebración fin de año', 'tarjeta_credito'),

        -- === 2025 ===
        -- Junio 2025
        (1, 1, 3500.00, 'ingreso', '2025-06-01', 'Nómina mensual Junio', 'transferencia'),
        (1, 2, 600.00,  'ingreso', '2025-06-18', 'Proyecto web React & Python', 'transferencia'),
        (1, 6, 700.00,  'gasto',   '2025-06-02', 'Pago arriendo apartamento', 'transferencia'),
        (1, 5, 470.00,  'gasto',   '2025-06-08', 'Mercado mensual', 'tarjeta_debito'),
        (1, 7, 130.00,  'gasto',   '2025-06-14', 'Gasolina y mantenimiento auto', 'tarjeta_debito'),
        (1, 8, 120.00,  'gasto',   '2025-06-20', 'Cine y restaurantes', 'tarjeta_credito'),

        -- Diciembre 2025
        (1, 1, 3600.00, 'ingreso', '2025-12-01', 'Nómina mensual Diciembre', 'transferencia'),
        (1, 6, 700.00,  'gasto',   '2025-12-02', 'Pago arriendo apartamento', 'transferencia'),
        (1, 5, 540.00,  'gasto',   '2025-12-15', 'Cena navidad y compras', 'tarjeta_debito'),
        (1, 8, 150.00,  'gasto',   '2025-12-22', 'Salidas y regalos', 'tarjeta_credito'),

        -- === 2026 (AÑO ACTUAL) ===
        -- Julio 2026
        (1, 1, 3700.00, 'ingreso', '2026-07-01', 'Nómina mensual Julio', 'transferencia'),
        (1, 2, 450.00,  'ingreso', '2026-07-15', 'Consultoría DevOps', 'transferencia'),
        (1, 6, 720.00,  'gasto',   '2026-07-02', 'Pago arriendo apartamento', 'transferencia'),
        (1, 5, 480.00,  'gasto',   '2026-07-10', 'Supermercado mensual', 'tarjeta_debito'),
        (1, 7, 135.00,  'gasto',   '2026-07-16', 'Combustible y parqueadero', 'efectivo'),
        (1, 8, 130.00,  'gasto',   '2026-07-25', 'Restaurantes y ocio', 'tarjeta_credito'),

        -- Agosto 2026
        (1, 1, 3700.00, 'ingreso', '2026-08-01', 'Nómina mensual Agosto', 'transferencia'),
        (1, 2, 550.00,  'ingreso', '2026-08-18', 'Mantenimiento plataforma web', 'transferencia'),
        (1, 6, 720.00,  'gasto',   '2026-08-02', 'Pago arriendo apartamento', 'transferencia'),
        (1, 5, 490.00,  'gasto',   '2026-08-09', 'Mercado mensual', 'tarjeta_debito'),
        (1, 7, 140.00,  'gasto',   '2026-08-14', 'Gasolina mensual', 'efectivo'),
        (1, 8, 145.00,  'gasto',   '2026-08-22', 'Cine y conciertos', 'tarjeta_credito'),
        (1, 11, 180.00, 'gasto',   '2026-08-28', 'Accesorios de computación', 'tarjeta_credito'),

        -- Septiembre 2026 (Mes Actual)
        (1, 1, 3800.00, 'ingreso', '2026-09-01', 'Nómina mensual Septiembre', 'transferencia'),
        (1, 6, 720.00,  'gasto',   '2026-09-02', 'Pago arriendo apartamento', 'transferencia'),
        (1, 5, 230.00,  'gasto',   '2026-09-02', 'Mercado de inicio de mes', 'tarjeta_debito');
        """
        cursor.executescript(seed_sql)
        conn.commit()
    else:
        # Migración automática si la tabla usuarios ya existía sin password_hash
        try:
            cursor.execute("PRAGMA table_info(usuarios);")
            columns = [row[1] for row in cursor.fetchall()]
            if "password_hash" not in columns:
                cursor.execute("ALTER TABLE usuarios ADD COLUMN password_hash TEXT NOT NULL DEFAULT '';")
                cursor.execute("UPDATE usuarios SET password_hash = ? WHERE password_hash IS NULL OR password_hash = '';", (default_hash,))
                conn.commit()
        except Exception:
            pass

    cursor.close()


def execute_query(
    query: str, 
    params: Optional[Union[tuple, list, dict]] = None, 
    fetch_all: bool = True, 
    fetch_one: bool = False, 
    commit: bool = False
) -> Any:
    """
    Ejecuta una consulta SQL de forma segura y devuelve resultados serializables.
    """
    engine_type, conn = get_db_connection()
    cursor = None
    try:
        if engine_type == "mysql":
            # Si el driver es pymysql con DictCursor
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
                return {"last_id": last_id, "affected_rows": rowcount}
            
            if fetch_one:
                row = cursor.fetchone()
                return serialize_row(row)
            if fetch_all:
                rows = cursor.fetchall()
                return [serialize_row(r) for r in rows]
            return None
        else:
            # SQLite: Reemplaza marcadores %s por ? para compatibilidad
            sqlite_query = query.replace("%s", "?")
            cursor = conn.cursor()
            cursor.execute(sqlite_query, params or ())
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
                return {"last_id": last_id, "affected_rows": rowcount}

            if fetch_one:
                row = cursor.fetchone()
                if row is None:
                    return None
                return serialize_row(dict(row))
            if fetch_all:
                rows = cursor.fetchall()
                return [serialize_row(dict(r)) for r in rows]
            return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_connection() -> Dict[str, Any]:
    """Verifica el estado de la conexión a la base de datos."""
    try:
        engine_type, conn = get_db_connection()
        conn.close()
        return {"status": "ok", "engine": engine_type, "database": DB_NAME if engine_type == "mysql" else "sqlite"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
