"""
Rutas API para Analítica Avanzada, Machine Learning y Detección de Anomalías (/api/analitica)
"""

from flask import Blueprint, request, jsonify
from analitica.engine import (
    predecir_gasto_proximo_mes,
    detectar_anomalias,
    obtener_historico_mensual,
    InsuficientesDatosException
)

bp_analitica = Blueprint("analitica", __name__, url_prefix="/api/analitica")


@bp_analitica.route("/prediccion", methods=["GET"])
def obtener_prediccion_gasto():
    """
    Endpoint para predecir el gasto del próximo mes mediante Regresión Lineal.
    Query param:
        id_usuario: ID del usuario (requerido)
    """
    try:
        id_usuario = request.args.get("id_usuario")
        if not id_usuario:
            return jsonify({"status": "error", "message": "El parámetro 'id_usuario' es requerido"}), 400

        resultado = predecir_gasto_proximo_mes(int(id_usuario))
        return jsonify({
            "status": "success",
            "data": resultado
        }), 200

    except InsuficientesDatosException as e:
        return jsonify({
            "status": "warning",
            "message": str(e),
            "meses_disponibles": e.meses_disponibles,
            "meses_requeridos": e.meses_requeridos
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al procesar modelo de predicción: {str(e)}"
        }), 500


@bp_analitica.route("/anomalias", methods=["GET"])
def obtener_anomalias():
    """
    Endpoint para detectar gastos atípicos / anómalos usando Z-score por categoría.
    Query params:
        id_usuario: ID del usuario (requerido)
        umbral: Umbral de Z-score (opcional, default: 2.0)
    """
    try:
        id_usuario = request.args.get("id_usuario")
        umbral = request.args.get("umbral", 2.0)

        if not id_usuario:
            return jsonify({"status": "error", "message": "El parámetro 'id_usuario' es requerido"}), 400

        try:
            umbral_float = float(umbral)
        except ValueError:
            umbral_float = 2.0

        resultado = detectar_anomalias(int(id_usuario), umbral_z=umbral_float)
        return jsonify({
            "status": "success",
            "data": resultado
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al calcular anomalías: {str(e)}"
        }), 500


@bp_analitica.route("/historico-comparativo", methods=["GET"])
def obtener_historico():
    """
    Endpoint que retorna la serie temporal mensual consolidada (Ingresos, Gastos, Balance)
    para alimentar el gráfico de tendencias multilínea/barras.
    """
    try:
        id_usuario = request.args.get("id_usuario")
        if not id_usuario:
            return jsonify({"status": "error", "message": "El parámetro 'id_usuario' es requerido"}), 400

        datos = obtener_historico_mensual(int(id_usuario))
        return jsonify({
            "status": "success",
            "data": datos
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al generar histórico comparativo: {str(e)}"
        }), 500
