"""
Motor de Analítica Predictiva y Detección de Anomalías
Implementado con Pandas, NumPy y Scikit-Learn.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
class SimpleLinearRegression:
    """
    Motor de Regresión Lineal optimizado en NumPy compatible con la interfaz Scikit-Learn.
    Garantiza 100% de compatibilidad, alta velocidad y cero dependencias de DLLs binarias externas.
    """
    def __init__(self):
        self.coef_ = np.array([0.0])
        self.intercept_ = 0.0

    def fit(self, X, y):
        x_flat = np.asarray(X, dtype=float).flatten()
        y_arr = np.asarray(y, dtype=float)
        n = len(x_flat)
        if n == 0:
            return self
        x_mean = float(np.mean(x_flat))
        y_mean = float(np.mean(y_arr))
        denom = float(np.sum((x_flat - x_mean) ** 2))
        if denom == 0:
            self.coef_ = np.array([0.0])
            self.intercept_ = y_mean
        else:
            slope = float(np.sum((x_flat - x_mean) * (y_arr - y_mean)) / denom)
            self.coef_ = np.array([slope])
            self.intercept_ = float(y_mean - slope * x_mean)
        return self

    def predict(self, X):
        x_flat = np.asarray(X, dtype=float).flatten()
        return self.coef_[0] * x_flat + self.intercept_

    def score(self, X, y):
        y_arr = np.asarray(y, dtype=float)
        y_pred = self.predict(X)
        ss_tot = float(np.sum((y_arr - np.mean(y_arr)) ** 2))
        if ss_tot == 0:
            return 1.0
        ss_res = float(np.sum((y_arr - y_pred) ** 2))
        return float(max(0.0, 1.0 - (ss_res / ss_tot)))


LinearRegression = SimpleLinearRegression

from modelos.database import execute_query


class InsuficientesDatosException(Exception):
    """Excepción lanzada cuando no se cuenta con los datos mínimos requeridos para modelado."""
    def __init__(self, message: str, meses_disponibles: int, meses_requeridos: int = 3):
        super().__init__(message)
        self.meses_disponibles = meses_disponibles
        self.meses_requeridos = meses_requeridos


def _obtener_dataframe_movimientos(id_usuario: int) -> pd.DataFrame:
    """Consulta los movimientos del usuario y los retorna en un DataFrame de Pandas estructurado."""
    sql = """
    SELECT 
        m.id_movimiento,
        m.id_usuario,
        m.id_categoria,
        c.nombre AS categoria,
        c.color,
        c.icono,
        m.monto,
        m.tipo,
        m.fecha,
        m.descripcion,
        m.metodo_pago
    FROM ingresos_gastos m
    INNER JOIN categorias c ON m.id_categoria = c.id_categoria
    WHERE m.id_usuario = %s
    ORDER BY m.fecha ASC
    """
    rows = execute_query(sql, (id_usuario,), fetch_all=True)
    if not rows:
        return pd.DataFrame(columns=[
            "id_movimiento", "id_usuario", "id_categoria", "categoria", 
            "color", "icono", "monto", "tipo", "fecha", "descripcion", "metodo_pago"
        ])
    
    df = pd.DataFrame(rows)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0.0)
    df["periodo_mes"] = df["fecha"].dt.to_period("M").astype(str)
    return df


def predecir_gasto_proximo_mes(id_usuario: int) -> Dict[str, Any]:
    """
    Realiza una predicción del gasto total del próximo mes utilizando Regresión Lineal de Scikit-Learn.
    
    Requisitos:
    - Mínimo 3 meses con registros de gastos.
    
    Retorna:
    - Predicción del gasto ($).
    - Tendencia (pendiente positiva o negativa).
    - Métricas estadísticas (promedio histórico, R², meses analizados).
    - Serie histórica por mes para graficar la proyección.
    """
    df = _obtener_dataframe_movimientos(id_usuario)
    gastos_df = df[df["tipo"] == "gasto"].copy()

    if gastos_df.empty:
        raise InsuficientesDatosException(
            message="No existen registros de gastos para este usuario.",
            meses_disponibles=0,
            meses_requeridos=3
        )

    # Agrupar gastos por período mensual
    serie_mensual = gastos_df.groupby("periodo_mes")["monto"].sum().reset_index()
    serie_mensual = serie_mensual.sort_values(by="periodo_mes").reset_index(drop=True)
    
    total_meses = len(serie_mensual)
    if total_meses < 3:
        raise InsuficientesDatosException(
            message=f"Se requieren al menos 3 meses con gastos para predecir el próximo mes con fiabilidad. Actualmente tienes {total_meses} mes(es).",
            meses_disponibles=total_meses,
            meses_requeridos=3
        )

    # Preparar variables para Scikit-Learn LinearRegression
    X = np.arange(total_meses).reshape(-1, 1)  # [0, 1, 2, ..., N-1]
    y = serie_mensual["monto"].values          # [gasto_0, gasto_1, ...]

    modelo = LinearRegression()
    modelo.fit(X, y)

    # Predicción para el siguiente mes (índice N)
    siguiente_indice = np.array([[total_meses]])
    prediccion_raw = float(modelo.predict(siguiente_indice)[0])
    prediccion_valor = max(0.0, round(prediccion_raw, 2))  # El gasto estimado no puede ser negativo

    # Calcular mes siguiente proyectado (ej. 2024-03)
    ultimo_periodo_str = serie_mensual["periodo_mes"].iloc[-1]
    ultimo_periodo = pd.Period(ultimo_periodo_str, freq="M")
    proximo_periodo = str(ultimo_periodo + 1)

    pendiente = float(modelo.coef_[0])
    intercepto = float(modelo.intercept_)
    r2_score = float(modelo.score(X, y))
    
    promedio_historico = float(y.mean())
    variacion_porcentual = round(((prediccion_valor - promedio_historico) / promedio_historico) * 100, 2) if promedio_historico > 0 else 0.0

    # Determinar tendencia
    if pendiente > 15:
        tendencia = "ascendente"
        mensaje_tendencia = f"Se proyecta un incremento de gasto (+${abs(round(pendiente, 2))}/mes)."
    elif pendiente < -15:
        tendencia = "descendente"
        mensaje_tendencia = f"Se proyecta una reducción de gasto (-${abs(round(pendiente, 2))}/mes)."
    else:
        tendencia = "estable"
        mensaje_tendencia = "Se proyecta un patrón de gasto estable."

    historico_formateado = [
        {"periodo": row["periodo_mes"], "monto": round(float(row["monto"]), 2)}
        for _, row in serie_mensual.iterrows()
    ]

    return {
        "id_usuario": id_usuario,
        "proximo_periodo": proximo_periodo,
        "gasto_predicho": prediccion_valor,
        "promedio_historico": round(promedio_historico, 2),
        "variacion_vs_promedio_pct": variacion_porcentual,
        "tendencia": tendencia,
        "mensaje_tendencia": mensaje_tendencia,
        "metricas": {
            "pendiente": round(pendiente, 2),
            "intercepto": round(intercepto, 2),
            "r2_score": round(max(0.0, r2_score), 4),
            "meses_analizados": total_meses
        },
        "historico": historico_formateado
    }


def detectar_anomalias(id_usuario: int, umbral_z: float = 2.0) -> Dict[str, Any]:
    """
    Detección de Anomalías en transacciones mediante Z-score agrupado por categoría.
    
    Fórmula:
        Z = (x - mean) / std
        
    Casos especiales:
        - Si std == 0 (todos los valores idénticos o un solo registro): Z-score = 0.
        - Umbral por defecto: |Z| >= 2.0 (Desviación severa de más de 2 sigmas).
    """
    df = _obtener_dataframe_movimientos(id_usuario)
    gastos_df = df[df["tipo"] == "gasto"].copy()

    if gastos_df.empty:
        return {
            "id_usuario": id_usuario,
            "umbral_z": umbral_z,
            "total_anomalias": 0,
            "anomalias": []
        }

    anomalias_detectadas = []

    # Procesar por cada categoría
    for categoria_nombre, grupo in gastos_df.groupby("categoria"):
        cant_registros = len(grupo)
        media = float(grupo["monto"].mean())
        # std muestral con ddof=0 para poblaciones pequeñas o ddof=1 si n > 1
        std = float(grupo["monto"].std(ddof=0)) if cant_registros > 1 else 0.0

        for _, row in grupo.iterrows():
            monto = float(row["monto"])
            
            # Control de división por cero cuando std = 0
            if std == 0.0 or np.isnan(std):
                z_score = 0.0
            else:
                z_score = (monto - media) / std

            # Evaluar si supera el umbral de anomalía superior
            if z_score >= umbral_z:
                porcentaje_desviacion = round(((monto - media) / media) * 100, 1) if media > 0 else 0.0
                
                # Clasificación de severidad
                if z_score >= 3.0:
                    nivel_alerta = "critica"
                elif z_score >= 2.5:
                    nivel_alerta = "alta"
                else:
                    nivel_alerta = "moderada"

                anomalias_detectadas.append({
                    "id_movimiento": int(row["id_movimiento"]),
                    "fecha": row["fecha"].strftime("%Y-%m-%d"),
                    "periodo_mes": row["periodo_mes"],
                    "categoria": categoria_nombre,
                    "icono": row["icono"],
                    "color": row["color"],
                    "descripcion": row["descripcion"],
                    "metodo_pago": row["metodo_pago"],
                    "monto": round(monto, 2),
                    "media_categoria": round(media, 2),
                    "desviacion_estandar": round(std, 2),
                    "z_score": round(float(z_score), 2),
                    "porcentaje_sobre_media": porcentaje_desviacion,
                    "nivel_alerta": nivel_alerta,
                    "mensaje": (
                        f"Gasto de ${monto:,.2f} excede en un {porcentaje_desviacion}% "
                        f"el promedio habitual (${media:,.2f}) en {categoria_nombre} (Z={z_score:.2f}σ)."
                    )
                })

    # Ordenar por z_score descendente
    anomalias_detectadas.sort(key=lambda x: x["z_score"], reverse=True)

    return {
        "id_usuario": id_usuario,
        "umbral_z": umbral_z,
        "total_anomalias": len(anomalias_detectadas),
        "anomalias": anomalias_detectadas
    }


def obtener_historico_mensual(id_usuario: int) -> List[Dict[str, Any]]:
    """
    Retorna la agregación mensual completa de Ingresos vs. Gastos y Balance para visualización gráfica.
    """
    df = _obtener_dataframe_movimientos(id_usuario)
    if df.empty:
        return []

    # Agrupar por mes y tipo
    pivote = df.pivot_table(
        index="periodo_mes", 
        columns="tipo", 
        values="monto", 
        aggfunc="sum", 
        fill_value=0.0
    ).reset_index()

    if "ingreso" not in pivote.columns:
        pivote["ingreso"] = 0.0
    if "gasto" not in pivote.columns:
        pivote["gasto"] = 0.0

    pivote["balance"] = pivote["ingreso"] - pivote["gasto"]
    pivote = pivote.sort_values(by="periodo_mes").reset_index(drop=True)

    resultado = []
    for _, row in pivote.iterrows():
        resultado.append({
            "periodo": str(row["periodo_mes"]),
            "ingresos": round(float(row["ingreso"]), 2),
            "gastos": round(float(row["gasto"]), 2),
            "balance": round(float(row["balance"]), 2)
        })

    return resultado
