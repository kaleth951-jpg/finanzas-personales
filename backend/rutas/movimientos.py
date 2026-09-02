"""
Rutas API para Transacciones y Resumen Financiero (/api/movimientos y /api/resumen)
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from modelos.database import execute_query

bp_movimientos = Blueprint("movimientos", __name__)


@bp_movimientos.route("/api/movimientos", methods=["GET"])
def listar_movimientos():
    """
    Lista transacciones con filtros dinámicos (usuario, fecha, categoría, tipo y texto de búsqueda).
    """
    try:
        id_usuario = request.args.get("id_usuario")
        mes = request.args.get("mes")           # Formato 'YYYY-MM' o número 'MM'
        anio = request.args.get("anio")         # Formato 'YYYY'
        tipo = request.args.get("tipo")         # 'ingreso' o 'gasto'
        id_categoria = request.args.get("id_categoria")
        busqueda = request.args.get("busqueda", "").strip()

        if not id_usuario:
            return jsonify({"status": "error", "message": "El parámetro 'id_usuario' es requerido"}), 400

        filtros = ["m.id_usuario = %s"]
        params = [int(id_usuario)]

        if tipo in ["ingreso", "gasto"]:
            filtros.append("m.tipo = %s")
            params.append(tipo)

        if id_categoria:
            filtros.append("m.id_categoria = %s")
            params.append(int(id_categoria))

        if mes:
            # Si mes viene como YYYY-MM
            if len(mes) == 7 and "-" in mes:
                filtros.append("DATE_FORMAT(m.fecha, '%Y-%m') = %s")
                params.append(mes)
            else:
                filtros.append("MONTH(m.fecha) = %s")
                params.append(int(mes))

        if anio:
            filtros.append("YEAR(m.fecha) = %s")
            params.append(int(anio))

        if busqueda:
            filtros.append("(m.descripcion LIKE %s OR c.nombre LIKE %s)")
            termino = f"%{busqueda}%"
            params.extend([termino, termino])

        where_clause = " AND ".join(filtros)
        sql = f"""
        SELECT 
            m.id_movimiento,
            m.id_usuario,
            m.id_categoria,
            c.nombre AS categoria,
            c.color AS categoria_color,
            c.icono AS categoria_icono,
            m.monto,
            m.tipo,
            m.fecha,
            m.descripcion,
            m.metodo_pago,
            m.fecha_registro
        FROM ingresos_gastos m
        INNER JOIN categorias c ON m.id_categoria = c.id_categoria
        WHERE {where_clause}
        ORDER BY m.fecha DESC, m.id_movimiento DESC
        """
        movimientos = execute_query(sql, tuple(params), fetch_all=True)

        return jsonify({
            "status": "success",
            "total_registros": len(movimientos),
            "data": movimientos
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al listar movimientos: {str(e)}"}), 500


@bp_movimientos.route("/api/movimientos/<int:id_movimiento>", methods=["GET"])
def obtener_movimiento(id_movimiento: int):
    """Obtiene el detalle de un movimiento específico."""
    try:
        sql = """
        SELECT 
            m.id_movimiento,
            m.id_usuario,
            m.id_categoria,
            c.nombre AS categoria,
            c.color AS categoria_color,
            c.icono AS categoria_icono,
            m.monto,
            m.tipo,
            m.fecha,
            m.descripcion,
            m.metodo_pago,
            m.fecha_registro
        FROM ingresos_gastos m
        INNER JOIN categorias c ON m.id_categoria = c.id_categoria
        WHERE m.id_movimiento = %s
        """
        movimiento = execute_query(sql, (id_movimiento,), fetch_one=True)
        if not movimiento:
            return jsonify({"status": "error", "message": "Movimiento no encontrado"}), 404
        return jsonify({"status": "success", "data": movimiento}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_movimientos.route("/api/movimientos", methods=["POST"])
def crear_movimiento():
    """Registra una nueva transacción (ingreso o gasto) con validaciones estrictas."""
    try:
        datos = request.get_json() or {}
        id_usuario = datos.get("id_usuario")
        id_categoria = datos.get("id_categoria")
        monto_raw = datos.get("monto")
        tipo = datos.get("tipo", "").strip().lower()
        fecha = datos.get("fecha", "").strip()
        descripcion = datos.get("descripcion", "").strip()
        metodo_pago = datos.get("metodo_pago", "efectivo").strip().lower()

        # Validaciones
        if not id_usuario or not id_categoria:
            return jsonify({"status": "error", "message": "id_usuario e id_categoria son obligatorios"}), 400

        try:
            monto = float(monto_raw)
            if monto <= 0:
                return jsonify({"status": "error", "message": "El monto debe ser estrictamente mayor a 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "El monto ingresado no es un número válido"}), 400

        if tipo not in ["ingreso", "gasto"]:
            return jsonify({"status": "error", "message": "El tipo debe ser 'ingreso' o 'gasto'"}), 400

        if not fecha:
            fecha = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                return jsonify({"status": "error", "message": "Formato de fecha inválido (use AAAA-MM-DD)"}), 400

        if not descripcion:
            return jsonify({"status": "error", "message": "La descripción es obligatoria"}), 400

        metodos_validos = ["efectivo", "tarjeta_debito", "tarjeta_credito", "transferencia", "otro"]
        if metodo_pago not in metodos_validos:
            metodo_pago = "efectivo"

        sql_insert = """
        INSERT INTO ingresos_gastos 
        (id_usuario, id_categoria, monto, tipo, fecha, descripcion, metodo_pago)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        res = execute_query(sql_insert, (id_usuario, id_categoria, monto, tipo, fecha, descripcion, metodo_pago), commit=True)
        nuevo_id = res.get("last_id")

        return jsonify({
            "status": "success",
            "message": "Movimiento registrado exitosamente",
            "data": {
                "id_movimiento": nuevo_id,
                "id_usuario": id_usuario,
                "id_categoria": id_categoria,
                "monto": monto,
                "tipo": tipo,
                "fecha": fecha,
                "descripcion": descripcion,
                "metodo_pago": metodo_pago
            }
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al crear movimiento: {str(e)}"}), 500


@bp_movimientos.route("/api/movimientos/<int:id_movimiento>", methods=["PUT"])
def actualizar_movimiento(id_movimiento: int):
    """Actualiza una transacción existente."""
    try:
        # Verificar existencia
        sql_check = "SELECT id_movimiento FROM ingresos_gastos WHERE id_movimiento = %s"
        existente = execute_query(sql_check, (id_movimiento,), fetch_one=True)
        if not existente:
            return jsonify({"status": "error", "message": "Movimiento no encontrado"}), 404

        datos = request.get_json() or {}
        id_categoria = datos.get("id_categoria")
        monto_raw = datos.get("monto")
        tipo = datos.get("tipo", "").strip().lower()
        fecha = datos.get("fecha", "").strip()
        descripcion = datos.get("descripcion", "").strip()
        metodo_pago = datos.get("metodo_pago", "efectivo").strip().lower()

        try:
            monto = float(monto_raw)
            if monto <= 0:
                return jsonify({"status": "error", "message": "El monto debe ser mayor a 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Monto no válido"}), 400

        if tipo not in ["ingreso", "gasto"]:
            return jsonify({"status": "error", "message": "Tipo no válido ('ingreso' o 'gasto')"}), 400

        sql_update = """
        UPDATE ingresos_gastos
        SET id_categoria = %s,
            monto = %s,
            tipo = %s,
            fecha = %s,
            descripcion = %s,
            metodo_pago = %s
        WHERE id_movimiento = %s
        """
        execute_query(sql_update, (id_categoria, monto, tipo, fecha, descripcion, metodo_pago, id_movimiento), commit=True)

        return jsonify({
            "status": "success",
            "message": "Movimiento actualizado correctamente",
            "data": {
                "id_movimiento": id_movimiento,
                "id_categoria": id_categoria,
                "monto": monto,
                "tipo": tipo,
                "fecha": fecha,
                "descripcion": descripcion,
                "metodo_pago": metodo_pago
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al actualizar movimiento: {str(e)}"}), 500


@bp_movimientos.route("/api/movimientos/<int:id_movimiento>", methods=["DELETE"])
def eliminar_movimiento(id_movimiento: int):
    """Elimina una transacción por ID."""
    try:
        sql_check = "SELECT id_movimiento FROM ingresos_gastos WHERE id_movimiento = %s"
        existente = execute_query(sql_check, (id_movimiento,), fetch_one=True)
        if not existente:
            return jsonify({"status": "error", "message": "Movimiento no encontrado"}), 404

        sql_delete = "DELETE FROM ingresos_gastos WHERE id_movimiento = %s"
        execute_query(sql_delete, (id_movimiento,), commit=True)

        return jsonify({
            "status": "success",
            "message": "Movimiento eliminado satisfactoriamente",
            "id_eliminado": id_movimiento
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al eliminar movimiento: {str(e)}"}), 500


@bp_movimientos.route("/api/resumen", methods=["GET"])
def obtener_resumen_financiero():
    """
    Retorna métricas ejecutivas:
    - Total Ingresos, Total Gastos, Balance Neto, Tasa de Ahorro
    - Distribución de Gastos por Categoría (para gráfico de dona)
    - Comparativa porcentual con el mes anterior
    """
    try:
        id_usuario = request.args.get("id_usuario")
        mes_filtro = request.args.get("mes")  # Formato 'YYYY-MM'

        if not id_usuario:
            return jsonify({"status": "error", "message": "El parámetro 'id_usuario' es requerido"}), 400

        id_u = int(id_usuario)

        # Si no se envía mes, seleccionar el mes más reciente con datos o el actual
        if not mes_filtro:
            sql_latest = "SELECT DATE_FORMAT(MAX(fecha), '%Y-%m') AS max_mes FROM ingresos_gastos WHERE id_usuario = %s"
            latest_res = execute_query(sql_latest, (id_u,), fetch_one=True)
            if latest_res and latest_res.get("max_mes"):
                mes_filtro = latest_res["max_mes"]
            else:
                mes_filtro = datetime.now().strftime("%Y-%m")

        # 1. Totales del mes seleccionado
        sql_totales = """
        SELECT 
            tipo, 
            COALESCE(SUM(monto), 0) AS total 
        FROM ingresos_gastos 
        WHERE id_usuario = %s AND DATE_FORMAT(fecha, '%Y-%m') = %s 
        GROUP BY tipo
        """
        totales_rows = execute_query(sql_totales, (id_u, mes_filtro), fetch_all=True)
        totales = {r["tipo"]: float(r["total"]) for r in totales_rows}
        ingresos_mes = totales.get("ingreso", 0.0)
        gastos_mes = totales.get("gasto", 0.0)
        balance_mes = round(ingresos_mes - gastos_mes, 2)
        tasa_ahorro = round((balance_mes / ingresos_mes) * 100, 1) if ingresos_mes > 0 else 0.0

        # 2. Distribución de gastos por categoría para el mes
        sql_cat = """
        SELECT 
            c.nombre AS categoria,
            c.color,
            c.icono,
            SUM(m.monto) AS total
        FROM ingresos_gastos m
        INNER JOIN categorias c ON m.id_categoria = c.id_categoria
        WHERE m.id_usuario = %s 
          AND m.tipo = 'gasto' 
          AND DATE_FORMAT(m.fecha, '%Y-%m') = %s
        GROUP BY c.id_categoria, c.nombre, c.color, c.icono
        ORDER BY total DESC
        """
        distribucion = execute_query(sql_cat, (id_u, mes_filtro), fetch_all=True)
        for item in distribucion:
            item["total"] = round(float(item["total"]), 2)
            item["porcentaje"] = round((item["total"] / gastos_mes) * 100, 1) if gastos_mes > 0 else 0.0

        # 3. Datos del mes anterior para comparativa
        dt_actual = datetime.strptime(mes_filtro, "%Y-%m")
        if dt_actual.month == 1:
            mes_prev = f"{dt_actual.year - 1}-12"
        else:
            mes_prev = f"{dt_actual.year}-{dt_actual.month - 1:02d}"

        totales_prev_rows = execute_query(sql_totales, (id_u, mes_prev), fetch_all=True)
        totales_prev = {r["tipo"]: float(r["total"]) for r in totales_prev_rows}
        ingresos_prev = totales_prev.get("ingreso", 0.0)
        gastos_prev = totales_prev.get("gasto", 0.0)

        dif_ingresos_pct = round(((ingresos_mes - ingresos_prev) / ingresos_prev) * 100, 1) if ingresos_prev > 0 else 0.0
        dif_gastos_pct = round(((gastos_mes - gastos_prev) / gastos_prev) * 100, 1) if gastos_prev > 0 else 0.0

        return jsonify({
            "status": "success",
            "periodo": mes_filtro,
            "periodo_anterior": mes_prev,
            "resumen": {
                "ingresos": round(ingresos_mes, 2),
                "gastos": round(gastos_mes, 2),
                "balance": balance_mes,
                "tasa_ahorro_pct": tasa_ahorro,
                "comparativa": {
                    "dif_ingresos_pct": dif_ingresos_pct,
                    "dif_gastos_pct": dif_gastos_pct
                }
            },
            "distribucion_gastos": distribucion
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al generar resumen: {str(e)}"}), 500
