"""
Módulo de rutas y controladores REST de la API.
"""
from .usuarios import bp_usuarios
from .categorias import bp_categorias
from .movimientos import bp_movimientos
from .analitica import bp_analitica
from .auth import bp_auth

__all__ = [
    "bp_usuarios",
    "bp_categorias",
    "bp_movimientos",
    "bp_analitica",
    "bp_auth"
]
