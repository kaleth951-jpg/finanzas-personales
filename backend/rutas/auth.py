"""
Rutas API para Autenticación Segura (/api/auth)
Manejo de Login, Registro, Verificación de Sesión y Logout.
"""

import re
import secrets
from flask import Blueprint, request, jsonify
from modelos.database import execute_query, hash_password, verify_password

bp_auth = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp_auth.route("/register", methods=["POST"])
def register():
    """
    Registra un nuevo usuario con contraseña cifrada de manera segura.
    Payload: { nombre, email, password, moneda }
    """
    try:
        datos = request.get_json() or {}
        nombre = datos.get("nombre", "").strip()
        email = datos.get("email", "").strip().lower()
        password = datos.get("password", "").strip()
        moneda = datos.get("moneda", "USD").strip().upper()

        # 1. Validaciones de entrada
        if not nombre or len(nombre) < 2:
            return jsonify({
                "status": "error",
                "message": "El nombre completo es obligatorio (mínimo 2 caracteres)"
            }), 400

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_regex, email):
            return jsonify({
                "status": "error",
                "message": "Por favor ingresa un correo electrónico válido"
            }), 400

        if not password or len(password) < 6:
            return jsonify({
                "status": "error",
                "message": "La contraseña debe tener al menos 6 caracteres"
            }), 400

        if moneda not in ["USD", "EUR", "COP", "MXN"]:
            moneda = "USD"

        # 2. Verificar si el usuario ya existe
        sql_check = "SELECT id_usuario FROM usuarios WHERE email = %s"
        existente = execute_query(sql_check, (email,), fetch_one=True)
        if existente:
            return jsonify({
                "status": "error",
                "message": "Ya existe una cuenta registrada con este correo electrónico"
            }), 409

        # 3. Cifrado seguro de contraseña
        hashed_pw = hash_password(password)

        # 4. Inserción en la base de datos
        sql_insert = """
        INSERT INTO usuarios (nombre, email, password_hash, moneda)
        VALUES (%s, %s, %s, %s)
        """
        res = execute_query(sql_insert, (nombre, email, hashed_pw, moneda), commit=True)
        nuevo_id = res.get("last_id") if res else None

        # Generar token de sesión
        session_token = secrets.token_hex(24)

        return jsonify({
            "status": "success",
            "message": "¡Cuenta creada exitosamente! Bienvenido a Fiskal.",
            "data": {
                "usuario": {
                    "id_usuario": nuevo_id,
                    "nombre": nombre,
                    "email": email,
                    "moneda": moneda
                },
                "token": session_token
            }
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error en el servidor al registrar usuario: {str(e)}"
        }), 500


@bp_auth.route("/login", methods=["POST"])
def login():
    """
    Inicia sesión validando credenciales contra el hash seguro en la base de datos.
    Payload: { email, password }
    """
    try:
        datos = request.get_json() or {}
        email = datos.get("email", "").strip().lower()
        password = datos.get("password", "").strip()

        if not email or not password:
            return jsonify({
                "status": "error",
                "message": "Debes ingresar tu correo electrónico y contraseña"
            }), 400

        # Buscar usuario por correo
        sql = """
        SELECT id_usuario, nombre, email, password_hash, moneda, fecha_creacion
        FROM usuarios
        WHERE email = %s
        """
        usuario = execute_query(sql, (email,), fetch_one=True)

        if not usuario:
            return jsonify({
                "status": "error",
                "message": "Credenciales incorrectas. Verifica tu correo o regístrate si no tienes cuenta."
            }), 401

        # Validar contraseña con verificación criptográfica
        stored_hash = usuario.get("password_hash") or ""
        if not verify_password(stored_hash, password):
            return jsonify({
                "status": "error",
                "message": "Contraseña incorrecta. Por favor intenta de nuevo."
            }), 401

        # Generar token de sesión
        session_token = secrets.token_hex(24)

        return jsonify({
            "status": "success",
            "message": f"¡Bienvenido de nuevo, {usuario['nombre']}!",
            "data": {
                "usuario": {
                    "id_usuario": usuario["id_usuario"],
                    "nombre": usuario["nombre"],
                    "email": usuario["email"],
                    "moneda": usuario["moneda"],
                    "fecha_creacion": usuario.get("fecha_creacion")
                },
                "token": session_token
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error en el servidor al iniciar sesión: {str(e)}"
        }), 500


@bp_auth.route("/me", methods=["GET"])
def me():
    """
    Retorna el perfil del usuario autenticado a partir de su id_usuario.
    """
    try:
        id_usuario = request.args.get("id_usuario")
        if not id_usuario:
            return jsonify({"status": "error", "message": "ID de usuario requerido"}), 400

        sql = """
        SELECT id_usuario, nombre, email, moneda, fecha_creacion
        FROM usuarios
        WHERE id_usuario = %s
        """
        usuario = execute_query(sql, (int(id_usuario),), fetch_one=True)
        if not usuario:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

        return jsonify({"status": "success", "data": usuario}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_auth.route("/logout", methods=["POST"])
def logout():
    """
    Cierra la sesión del usuario.
    """
    return jsonify({
        "status": "success",
        "message": "Sesión cerrada correctamente"
    }), 200
