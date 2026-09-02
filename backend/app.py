"""
Servidor Principal de la Aplicación Flask
Finanzas Personales con Dashboard Analítico y Machine Learning
"""

import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from modelos.database import test_connection
from rutas import bp_usuarios, bp_categorias, bp_movimientos, bp_analitica, bp_auth

def create_app() -> Flask:
    # Ruta estática hacia la carpeta frontend para servir opcionalmente todo integrado
    frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    app = Flask(__name__, static_folder=frontend_folder, static_url_path="")
    
    # Habilitar CORS para permitir peticiones desde cualquier origen (útil en desarrollo)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Registro de Blueprints
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_usuarios)
    app.register_blueprint(bp_categorias)
    app.register_blueprint(bp_movimientos)
    app.register_blueprint(bp_analitica)

    # Ruta raíz: sirve la aplicación frontend si existe, o información de la API
    @app.route("/", methods=["GET"])
    def index():
        index_path = os.path.join(frontend_folder, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(frontend_folder, "index.html")
        return jsonify({
            "nombre": "Fiskal - API de Finanzas Personales con Dashboard Analítico",
            "version": "1.0.0",
            "estado": "activo",
            "documentacion_endpoints": [
                "/api/auth/register",
                "/api/auth/login",
                "/api/auth/me",
                "/api/auth/logout",
                "/api/usuarios",
                "/api/categorias",
                "/api/movimientos",
                "/api/resumen",
                "/api/analitica/prediccion",
                "/api/analitica/anomalias",
                "/api/analitica/historico-comparativo"
            ]
        })

    # Servir archivos estáticos del frontend (css, js, etc.)
    @app.route("/<path:path>", methods=["GET"])
    def static_proxy(path):
        if os.path.exists(os.path.join(frontend_folder, path)):
            return send_from_directory(frontend_folder, path)
        return jsonify({"status": "error", "message": "Recurso no encontrado"}), 404

    # Endpoint de salud del sistema
    @app.route("/api/health", methods=["GET"])
    def health_check():
        db_status = test_connection()
        return jsonify({
            "app_status": "ok",
            "database": db_status
        }), 200

    # Manejo centralizado de errores HTTP
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"status": "error", "message": "Ruta o recurso no encontrado"}), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({"status": "error", "message": "Método HTTP no permitido"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    import sys
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    puerto = int(os.getenv("PORT", 5000))
    print("=" * 70)
    print(f"[*] Servidor de Finanzas Personales iniciado en: http://127.0.0.1:{puerto}")
    print("=" * 70)
    app.run(host="0.0.0.0", port=puerto, debug=True)

