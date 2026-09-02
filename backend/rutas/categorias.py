"""
Rutas API para Gestión de Categorías (/api/categorias)
"""

from flask import Blueprint, request, jsonify
from modelos.database import execute_query

bp_categorias = Blueprint("categorias", __name__, url_prefix="/api/categorias")


@bp_categorias.route("", methods=["GET"])
def listar_categorias():
    """
    Retorna categorías del sistema y personalizadas para el usuario especificado.
    Query params:
        id_usuario: (opcional) ID del usuario para filtrar categorías propias + globales.
        tipo: (opcional) 'ingreso' o 'gasto'
    """
    try:
        id_usuario = request.args.get("id_usuario")
        tipo = request.args.get("tipo")

        filtros = []
        params = []

        if id_usuario:
            filtros.append("(id_usuario IS NULL OR id_usuario = %s)")
            params.append(int(id_usuario))
        else:
            filtros.append("id_usuario IS NULL")

        if tipo in ["ingreso", "gasto"]:
            filtros.append("tipo = %s")
            params.append(tipo)

        where_clause = " AND ".join(filtros)
        sql = f"""
        SELECT id_categoria, id_usuario, nombre, tipo, icono, color, fecha_creacion
        FROM categorias
        WHERE {where_clause}
        ORDER BY tipo ASC, nombre ASC
        """
        categorias = execute_query(sql, tuple(params), fetch_all=True)
        return jsonify({"status": "success", "data": categorias}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al obtener categorías: {str(e)}"}), 500


@bp_categorias.route("", methods=["POST"])
def crear_categoria():
    """Crea una nueva categoría de ingreso o gasto."""
    try:
        datos = request.get_json() or {}
        nombre = datos.get("nombre", "").strip()
        tipo = datos.get("tipo", "").strip().lower()
        icono = datos.get("icono", "tag").strip()
        color = datos.get("color", "#6366f1").strip()
        id_usuario = datos.get("id_usuario")

        if not nombre:
            return jsonify({"status": "error", "message": "El nombre de la categoría es requerido"}), 400

        if tipo not in ["ingreso", "gasto"]:
            return jsonify({"status": "error", "message": "El tipo debe ser 'ingreso' o 'gasto'"}), 400

        sql = """
        INSERT INTO categorias (id_usuario, nombre, tipo, icono, color)
        VALUES (%s, %s, %s, %s, %s)
        """
        res = execute_query(sql, (id_usuario, nombre, tipo, icono, color), commit=True)
        nuevo_id = res.get("last_id")

        return jsonify({
            "status": "success",
            "message": "Categoría creada con éxito",
            "data": {
                "id_categoria": nuevo_id,
                "id_usuario": id_usuario,
                "nombre": nombre,
                "tipo": tipo,
                "icono": icono,
                "color": color
            }
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al crear categoría: {str(e)}"}), 500
