-- ==============================================================================
-- SISTEMA DE FINANZAS PERSONALES CON DASHBOARD ANALÍTICO
-- Dataset Inicial de Pruebas (Seeds)
-- Incluye >4 meses de historial con un gasto anómalo evidente para Machine Learning
-- ==============================================================================

USE finanzas_db;

-- Limpieza preventiva
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE ingresos_gastos;
TRUNCATE TABLE categorias;
TRUNCATE TABLE usuarios;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------------------------
-- 1. USUARIOS DE PRUEBA
-- ------------------------------------------------------------------------------
INSERT INTO usuarios (id_usuario, nombre, email, moneda) VALUES
(1, 'Kaleth García', 'kaleth@example.com', 'USD'),
(2, 'Elena Morales', 'elena.morales@example.com', 'EUR');

-- ------------------------------------------------------------------------------
-- 2. CATEGORÍAS (Ingresos y Gastos)
-- ------------------------------------------------------------------------------
INSERT INTO categorias (id_categoria, id_usuario, nombre, tipo, icono, color) VALUES
-- Categorías de Ingresos
(1, NULL, 'Salario Principal', 'ingreso', 'briefcase', '#10b981'),
(2, NULL, 'Freelance & Consultoría', 'ingreso', 'laptop', '#06b6d4'),
(3, NULL, 'Inversiones & Dividendos', 'ingreso', 'trending-up', '#8b5cf6'),
(4, NULL, 'Otros Ingresos', 'ingreso', 'plus-circle', '#14b8a6'),

-- Categorías de Gastos
(5, NULL, 'Alimentación & Supermercado', 'gasto', 'shopping-cart', '#f59e0b'),
(6, NULL, 'Vivienda & Servicios', 'gasto', 'home', '#3b82f6'),
(7, NULL, 'Transporte & Combustible', 'gasto', 'car', '#6366f1'),
(8, NULL, 'Ocio & Entretenimiento', 'gasto', 'film', '#ec4899'),
(9, NULL, 'Salud & Medicamentos', 'gasto', 'heart-pulse', '#ef4444'),
(10, NULL, 'Educación & Cursos', 'gasto', 'book-open', '#84cc16'),
(11, NULL, 'Tecnología & Gadgets', 'gasto', 'cpu', '#a855f7');

-- ------------------------------------------------------------------------------
-- 3. MOVIMIENTOS HISTÓRICOS DESDE 2024 HASTA FECHA ACTUAL (2026)
-- Mínimo 6 atributos: id_usuario, id_categoria, monto, tipo, fecha, descripcion, metodo_pago
-- ------------------------------------------------------------------------------

-- === 2024 ===
-- Enero 2024 (Con gasto anómalo evidente en Ocio)
INSERT INTO ingresos_gastos (id_usuario, id_categoria, monto, tipo, fecha, descripcion, metodo_pago) VALUES
(1, 1, 3200.00, 'ingreso', '2024-01-02', 'Nómina mensual Enero', 'transferencia'),
(1, 2, 600.00,  'ingreso', '2024-01-18', 'Consultoría técnica cloud', 'transferencia'),
(1, 6, 650.00,  'gasto',   '2024-01-03', 'Pago de arriendo apartamento', 'transferencia'),
(1, 6, 115.00,  'gasto',   '2024-01-05', 'Factura servicios públicos', 'tarjeta_debito'),
(1, 5, 410.00,  'gasto',   '2024-01-09', 'Mercado mensual supermercado', 'tarjeta_debito'),
(1, 7, 105.00,  'gasto',   '2024-01-15', 'Combustible vehículo', 'efectivo'),
(1, 9, 80.00,   'gasto',   '2024-01-22', 'Farmacia y vitaminas', 'tarjeta_debito'),
-- !!! GASTO ANÓMALO CLARO: En Ocio el promedio habitual es ~$80. Este gasto es de $2,850.00 (Z-score > 3.0)
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

-- === DATOS PARA USUARIO 2 (Elena Morales) ===
INSERT INTO ingresos_gastos (id_usuario, id_categoria, monto, tipo, fecha, descripcion, metodo_pago) VALUES
(2, 1, 2800.00, 'ingreso', '2024-01-01', 'Nómina mensual', 'transferencia'),
(2, 6, 500.00,  'gasto',   '2024-01-05', 'Alquiler estudio', 'transferencia'),
(2, 5, 350.00,  'gasto',   '2024-01-10', 'Supermercado', 'tarjeta_debito'),
(2, 8, 120.00,  'gasto',   '2024-01-15', 'Cena gourmet', 'tarjeta_credito'),
(2, 1, 2800.00, 'ingreso', '2024-02-01', 'Nómina mensual', 'transferencia'),
(2, 6, 500.00,  'gasto',   '2024-02-05', 'Alquiler estudio', 'transferencia'),
(2, 5, 360.00,  'gasto',   '2024-02-12', 'Supermercado', 'tarjeta_debito');
