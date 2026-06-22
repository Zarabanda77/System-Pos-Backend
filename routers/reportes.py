from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from database import get_db
from models import Venta, DetalleVenta, Producto, Categoria
from datetime import datetime, timedelta, timezone
from typing import Optional
from routers.auth import get_usuario_actual

router = APIRouter()

@router.get("/hoy")
def ventas_hoy(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    ahora = datetime.now()
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_hoy = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)
    ventas = db.query(Venta).filter(
        Venta.fecha >= inicio_hoy,
        Venta.fecha <= fin_hoy,
        Venta.estado == "completada"
    ).all()
    total = sum(v.total for v in ventas) if ventas else 0
    return {
        "fecha": str(ahora.date()),
        "cantidad_ventas": len(ventas),
        "total": total
    }
    
    
@router.get("/semana")
def ventas_semana(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    hace7 = datetime.now() - timedelta(days=7)
    ventas = db.query(Venta).filter(
        Venta.fecha >= hace7,
        Venta.estado == "completada"
    ).all()
    total = sum(v.total for v in ventas)
    return {"cantidad_ventas": len(ventas), "total": total}

@router.get("/productos-mas-vendidos")
def mas_vendidos(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    resultado = db.query(
        DetalleVenta.nombre_producto,
        func.sum(DetalleVenta.cantidad).label("total_vendido"),
        func.sum(DetalleVenta.subtotal).label("total_ingresos")
    ).group_by(DetalleVenta.nombre_producto)\
     .order_by(func.sum(DetalleVenta.cantidad).desc())\
     .limit(10).all()
    return [{"producto": r[0], "cantidad": r[1], "ingresos": r[2]} for r in resultado]

@router.get("/metodos-pago")
def metodos_pago(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    resultado = db.query(
        Venta.metodo_pago,
        func.sum(Venta.total).label("total")
    ).filter(Venta.estado == "completada")\
     .group_by(Venta.metodo_pago).all()
    return [{"metodo": r[0], "total": r[1]} for r in resultado]

@router.get("/ventas-por-dia")
def ventas_por_dia(db: Session = Depends(get_db), _=Depends(get_usuario_actual)):
    hace7 = datetime.now() - timedelta(days=7)
    resultado = db.query(
        func.date(Venta.fecha).label("dia"),
        func.sum(Venta.total).label("total")
    ).filter(
        Venta.fecha >= hace7,
        Venta.estado == "completada"
    ).group_by(func.date(Venta.fecha))\
     .order_by(func.date(Venta.fecha)).all()
    return [{"dia": str(r[0]), "total": r[1]} for r in resultado]


@router.get("/exportar")
def exportar_reporte(
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_usuario_actual),
):
    """Datos completos para el reporte de ventas en Excel.

    Calcula toda la analítica del lado del servidor (ingresos, costos, utilidad,
    márgenes, desgloses por producto/categoría/método/día/hora) sobre las ventas
    completadas dentro del rango [desde, hasta]. Sin fechas usa los últimos 90 días.
    """
    def _num(x):
        return x if isinstance(x, (int, float)) else 0

    ahora = datetime.now()
    # Rango: fin = 'hasta' (fin del día) o ahora; inicio = 'desde' o hace 90 días.
    fin = ahora
    if hasta:
        try:
            d = datetime.strptime(hasta, "%Y-%m-%d")
            fin = d.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            pass
    if desde:
        try:
            inicio = datetime.strptime(desde, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            inicio = fin - timedelta(days=90)
    else:
        inicio = fin - timedelta(days=90)

    ventas = (
        db.query(Venta)
        .options(joinedload(Venta.detalles))
        .filter(
            Venta.fecha >= inicio,
            Venta.fecha <= fin,
            Venta.estado == "completada",
        )
        .order_by(Venta.fecha.asc())
        .all()
    )

    productos = {p.id: p for p in db.query(Producto).all()}
    categorias = {c.id: c.nombre for c in db.query(Categoria).all()}

    def cat_de(prod):
        if not prod:
            return "Sin categoría"
        return categorias.get(prod.categoria_id, "Sin categoría")

    ventas_list = []
    items_list = []
    por_producto = {}
    por_categoria = {}
    por_metodo = {}
    por_dia = {}
    por_hora = {}

    ingresos_totales = 0.0
    costo_total = 0.0
    unidades_totales = 0.0

    for v in ventas:
        costo_venta = 0.0
        unidades_venta = 0.0
        for d in v.detalles:
            prod = productos.get(d.producto_id)
            costo_unit = _num(prod.costo) if prod else 0.0
            cantidad = _num(d.cantidad)
            subtotal = _num(d.subtotal)
            costo_linea = costo_unit * cantidad
            util_linea = subtotal - costo_linea
            categoria = cat_de(prod)

            costo_venta += costo_linea
            unidades_venta += cantidad

            items_list.append({
                "fecha": v.fecha.isoformat() if v.fecha else None,
                "venta_id": v.id,
                "producto": d.nombre_producto,
                "categoria": categoria,
                "cantidad": cantidad,
                "precio_unitario": _num(d.precio_unitario),
                "subtotal": subtotal,
                "costo_unitario": costo_unit,
                "costo_total": costo_linea,
                "utilidad": util_linea,
            })

            p = por_producto.setdefault(d.nombre_producto, {
                "producto": d.nombre_producto, "categoria": categoria,
                "unidades": 0.0, "ingresos": 0.0, "costo": 0.0, "utilidad": 0.0,
            })
            p["unidades"] += cantidad
            p["ingresos"] += subtotal
            p["costo"] += costo_linea
            p["utilidad"] += util_linea

            c = por_categoria.setdefault(categoria, {
                "categoria": categoria, "unidades": 0.0, "ingresos": 0.0, "costo": 0.0, "utilidad": 0.0,
            })
            c["unidades"] += cantidad
            c["ingresos"] += subtotal
            c["costo"] += costo_linea
            c["utilidad"] += util_linea

        total_v = _num(v.total)
        util_venta = total_v - costo_venta
        ingresos_totales += total_v
        costo_total += costo_venta
        unidades_totales += unidades_venta

        ventas_list.append({
            "id": v.id,
            "fecha": v.fecha.isoformat() if v.fecha else None,
            "cliente": v.nombre_cliente or "Consumidor final",
            "metodo_pago": v.metodo_pago or "—",
            "lineas": len(v.detalles),
            "unidades": unidades_venta,
            "total": total_v,
            "costo": costo_venta,
            "utilidad": util_venta,
            "margen_pct": round((util_venta / total_v * 100), 2) if total_v else 0,
        })

        metodo = v.metodo_pago or "—"
        m = por_metodo.setdefault(metodo, {"metodo": metodo, "ventas": 0, "total": 0.0})
        m["ventas"] += 1
        m["total"] += total_v

        if v.fecha:
            dia = str(v.fecha.date())
            dd = por_dia.setdefault(dia, {"dia": dia, "ventas": 0, "ingresos": 0.0})
            dd["ventas"] += 1
            dd["ingresos"] += total_v

            hora = v.fecha.hour
            hh = por_hora.setdefault(hora, {"hora": hora, "ventas": 0, "ingresos": 0.0})
            hh["ventas"] += 1
            hh["ingresos"] += total_v

    utilidad_total = ingresos_totales - costo_total
    num_ventas = len(ventas_list)
    dias_con_ventas = len(por_dia)

    # Redondeos y campos derivados para los desgloses
    for p in por_producto.values():
        p["margen_pct"] = round((p["utilidad"] / p["ingresos"] * 100), 2) if p["ingresos"] else 0
        p["participacion_pct"] = round((p["ingresos"] / ingresos_totales * 100), 2) if ingresos_totales else 0
    for c in por_categoria.values():
        c["margen_pct"] = round((c["utilidad"] / c["ingresos"] * 100), 2) if c["ingresos"] else 0
        c["participacion_pct"] = round((c["ingresos"] / ingresos_totales * 100), 2) if ingresos_totales else 0
    for m in por_metodo.values():
        m["participacion_pct"] = round((m["total"] / ingresos_totales * 100), 2) if ingresos_totales else 0
    for dd in por_dia.values():
        dd["ticket_promedio"] = round((dd["ingresos"] / dd["ventas"]), 2) if dd["ventas"] else 0

    productos_lista = sorted(por_producto.values(), key=lambda x: x["ingresos"], reverse=True)
    categorias_lista = sorted(por_categoria.values(), key=lambda x: x["ingresos"], reverse=True)
    metodos_lista = sorted(por_metodo.values(), key=lambda x: x["total"], reverse=True)
    dias_lista = sorted(por_dia.values(), key=lambda x: x["dia"])
    horas_lista = sorted(por_hora.values(), key=lambda x: x["hora"])

    mejor_dia = max(dias_lista, key=lambda x: x["ingresos"]) if dias_lista else None
    mejor_hora = max(horas_lista, key=lambda x: x["ingresos"]) if horas_lista else None

    # Inventario: valoración y productos bajos en stock (apoyo a "qué mejorar")
    todos_productos = list(productos.values())
    valor_costo = sum(_num(p.costo) * _num(p.stock_actual) for p in todos_productos)
    valor_venta = sum(
        (_num(p.precio_por_kilo) if p.es_por_peso else _num(p.precio_unitario)) * _num(p.stock_actual)
        for p in todos_productos
    )
    bajos = [
        {
            "producto": p.nombre,
            "stock_actual": _num(p.stock_actual),
            "stock_minimo": _num(p.stock_minimo),
            "unidad": p.unidad_medida,
            "categoria": categorias.get(p.categoria_id, "Sin categoría"),
        }
        for p in todos_productos
        if _num(p.stock_minimo) > 0 and _num(p.stock_actual) <= _num(p.stock_minimo)
    ]

    return {
        "generado_en": ahora.isoformat(),
        "rango": {"desde": str(inicio.date()), "hasta": str(fin.date())},
        "resumen": {
            "num_ventas": num_ventas,
            "ingresos_totales": round(ingresos_totales, 2),
            "costo_total": round(costo_total, 2),
            "utilidad_total": round(utilidad_total, 2),
            "margen_pct": round((utilidad_total / ingresos_totales * 100), 2) if ingresos_totales else 0,
            "ticket_promedio": round((ingresos_totales / num_ventas), 2) if num_ventas else 0,
            "unidades_vendidas": round(unidades_totales, 3),
            "dias_con_ventas": dias_con_ventas,
            "ingreso_diario_promedio": round((ingresos_totales / dias_con_ventas), 2) if dias_con_ventas else 0,
            "mejor_dia": mejor_dia,
            "mejor_hora": mejor_hora,
            "valor_inventario_costo": round(valor_costo, 2),
            "valor_inventario_venta": round(valor_venta, 2),
            "productos_bajos": len(bajos),
        },
        "ventas": ventas_list,
        "items": items_list,
        "por_producto": productos_lista,
        "por_categoria": categorias_lista,
        "por_metodo": metodos_lista,
        "por_dia": dias_lista,
        "por_hora": horas_lista,
        "inventario_bajo": bajos,
    }