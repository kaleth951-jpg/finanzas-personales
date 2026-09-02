"""
Rutas API para Gestión de Usuarios (/api/usuarios)
"""

import re
from flask import Blueprint, request, jsonify
from modelos.database import execute_query

bp_usuarios = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")


@bp_usuarios.route("", methods=["GET"])
def listar_usuarios():
    """Retorna la lista de usuarios registrados con conteo de movimientos."""
    try:
        sql = """
        SELECT 
            u.id_usuario, 
            u.nombre, 
            u.email, 
            u.moneda, 
            u.fecha_creacion,
            COUNT(m.id_movimiento) AS total_movimientos
        FROM usuarios u
        LEFT JOIN ingresos_gastos m ON u.id_usuario = m.id_usuario
        GROUP BY u.id_usuario, u.nombre, u.email, u.moneda, u.fecha_creacion
        ORDER BY u.id_usuario ASC
        """
        usuarios = execute_query(sql, fetch_all=True)
        return jsonify({"status": "success", "data": usuarios}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al listar usuarios: {str(e)}"}), 500


@bp_usuarios.route("/<int:id_usuario>", methods=["GET"])
def obtener_usuario(id_usuario: int):
    """Obtiene el detalle de un usuario por su ID."""
    try:
        sql = "SELECT id_usuario, nombre, email, moneda, fecha_creacion FROM usuarios WHERE id_usuario = %s"
        usuario = execute_query(sql, (id_usuario,), fetch_one=True)
        if not usuario:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
        return jsonify({"status": "success", "data": usuario}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_usuarios.route("", methods=["POST"])
def crear_usuario():
    """Registra un nuevo usuario en la base de datos."""
    try:
        datos = request.get_json() or {}
        nombre = datos.get("nombre", "").strip()
        email = datos.get("email", "").strip().lower()
        moneda = datos.get("moneda", "USD").strip().upper()

        if not nombre:
            return jsonify({"status": "error", "message": "El nombre es obligatorio"}), 400
        
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_regex, email):
            return jsonify({"status": "error", "message": "Formato de correo electrónico no válido"}), 400

        # Verificar duplicidad de correo
        sql_check = "SELECT id_usuario FROM usuarios WHERE email = %s"
        existente = execute_query(sql_check, (email,), fetch_one=True)
        if existente:
            return jsonify({"status": "error", "message": "El correo ya se encuentra registrado"}), 409

        sql_insert = "INSERT INTO usuarios (nombre, email, moneda) VALUES (%s, %s, %s)"
        res = execute_query(sql_insert, (nombre, email, moneda), commit=True)
        nuevo_id = res.get("last_id")

        return jsonify({
            "status": "success",
            "message": "Usuario creado exitosamente",
            "data": {
                "id_usuario": nuevo_id,
                "nombre": nombre,
                "email": email,
                "moneda": moneda
            }
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al crear usuario: {str(e)}"}), 500
