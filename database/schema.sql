-- ==============================================================================
-- SISTEMA DE FINANZAS PERSONALES CON DASHBOARD ANALÍTICO
-- Esquema de Base de Datos en Tercera Forma Normal (3FN)
-- Motor: MySQL 8.0+
-- ==============================================================================

-- Creación de la base de datos si no existe
CREATE DATABASE IF NOT EXISTS finanzas_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finanzas_db;

-- ------------------------------------------------------------------------------
-- 1. TABLA: usuarios
-- Entidad independiente que almacena los usuarios del sistema.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS ingresos_gastos;
DROP TABLE IF EXISTS categorias;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    moneda VARCHAR(10) NOT NULL DEFAULT 'USD',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_email_formato CHECK (email LIKE '%_@__%.__%')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. TABLA: categorias
-- Categorías clasificatorias para ingresos y gastos.
-- Puede tener categorías globales (id_usuario IS NULL) o personalizadas por usuario.
-- ------------------------------------------------------------------------------
CREATE TABLE categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL,
    nombre VARCHAR(60) NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    icono VARCHAR(50) DEFAULT 'tag',
    color VARCHAR(20) DEFAULT '#6366f1',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_categoria_tipo CHECK (tipo IN ('ingreso', 'gasto')),
    CONSTRAINT fk_categorias_usuario 
        FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario) 
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. TABLA: ingresos_gastos (Movimientos Transaccionales)
-- Cumple 3FN: no contiene dependencias transitivas ni grupos repetitivos.
-- ------------------------------------------------------------------------------
CREATE TABLE ingresos_gastos (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_categoria INT NOT NULL,
    monto DECIMAL(12, 2) NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    fecha DATE NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL DEFAULT 'efectivo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monto_positivo CHECK (monto > 0),
    CONSTRAINT chk_movimiento_tipo CHECK (tipo IN ('ingreso', 'gasto')),
    CONSTRAINT chk_metodo_pago CHECK (metodo_pago IN ('efectivo', 'tarjeta_debito', 'tarjeta_credito', 'transferencia', 'otro')),
    CONSTRAINT fk_movimientos_usuario 
        FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario) 
        ON DELETE CASCADE,
    CONSTRAINT fk_movimientos_categoria 
        FOREIGN KEY (id_categoria) 
        REFERENCES categorias(id_categoria) 
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- ÍNDICES DE OPTIMIZACIÓN
-- Optimizan consultas analíticas, filtros por fecha y agrupaciones por categoría
-- ------------------------------------------------------------------------------
CREATE INDEX idx_movimientos_usuario_fecha ON ingresos_gastos (id_usuario, fecha);
CREATE INDEX idx_movimientos_categoria ON ingresos_gastos (id_categoria);
CREATE INDEX idx_movimientos_tipo ON ingresos_gastos (tipo);
CREATE INDEX idx_movimientos_usuario_tipo_fecha ON ingresos_gastos (id_usuario, tipo, fecha);
CREATE INDEX idx_categorias_usuario ON categorias (id_usuario, tipo);
