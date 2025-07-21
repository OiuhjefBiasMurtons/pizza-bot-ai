from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from database.connection import get_db
from app.models.pedido import Pedido, DetallePedido
from app.models.cliente import Cliente
from app.models.pizza import Pizza

router = APIRouter(prefix="/admin", tags=["admin"])

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Panel de administración principal - Dashboard de pedidos"""
    
    # Obtener pedidos activos (no entregados ni cancelados)
    pedidos_activos = db.query(Pedido).filter(
        Pedido.estado.in_(["pendiente", "confirmado", "preparando", "enviado"])
    ).order_by(desc(Pedido.fecha_pedido)).all()
    
    # Enriquecer pedidos con información del cliente y detalles
    pedidos_enriquecidos = []
    for pedido in pedidos_activos:
        cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
        detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).all()
        
        # Enriquecer detalles con información de pizzas
        detalles_enriquecidos = []
        for detalle in detalles:
            pizza = db.query(Pizza).filter(Pizza.id == detalle.pizza_id).first()
            detalles_enriquecidos.append({
                "pizza_nombre": pizza.nombre if pizza else "Pizza no encontrada",
                "tamano": detalle.tamano,
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario,
                "subtotal": detalle.subtotal
            })
        
        pedidos_enriquecidos.append({
            "id": pedido.id,
            "cliente_nombre": cliente.nombre if cliente else "Cliente desconocido",
            "cliente_whatsapp": cliente.numero_whatsapp if cliente else "Sin número",
            "estado": pedido.estado,
            "total": pedido.total,
            "direccion_entrega": pedido.direccion_entrega,
            "fecha_pedido": pedido.fecha_pedido,
            "detalles": detalles_enriquecidos
        })
    
    # Estadísticas básicas
    pendientes = db.query(Pedido).filter(Pedido.estado == "pendiente").count()
    preparando = db.query(Pedido).filter(Pedido.estado == "preparando").count()
    en_reparto = db.query(Pedido).filter(Pedido.estado == "enviado").count()
    
    stats = {
        "total_activos": len(pedidos_activos),
        "pendientes": pendientes,
        "preparando": preparando,
        "en_reparto": en_reparto
    }
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "pedidos": pedidos_enriquecidos,
        "stats": stats,
        "estados_disponibles": ["pendiente", "confirmado", "preparando", "enviado", "entregado", "cancelado"]
    })

@router.get("/pedidos", response_class=HTMLResponse)
async def admin_pedidos(
    request: Request, 
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Vista de todos los pedidos con filtros"""
    
    query = db.query(Pedido)
    
    # Aplicar filtro de estado si se especifica
    if estado:
        query = query.filter(Pedido.estado == estado)
    
    pedidos = query.order_by(desc(Pedido.fecha_pedido)).all()
    
    # Enriquecer pedidos
    pedidos_enriquecidos = []
    for pedido in pedidos:
        cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
        detalles_count = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).count()
        
        pedidos_enriquecidos.append({
            "id": pedido.id,
            "cliente_nombre": cliente.nombre if cliente else "Cliente desconocido",
            "cliente_whatsapp": cliente.numero_whatsapp if cliente else "Sin número",
            "estado": pedido.estado,
            "total": pedido.total,
            "direccion_entrega": pedido.direccion_entrega,
            "fecha_pedido": pedido.fecha_pedido,
            "items_count": detalles_count
        })
    
    return templates.TemplateResponse("admin/pedidos.html", {
        "request": request,
        "pedidos": pedidos_enriquecidos,
        "estado_filtro": estado,
        "estados_disponibles": ["pendiente", "confirmado", "preparando", "enviado", "entregado", "cancelado"]
    })

@router.post("/pedido/{pedido_id}/estado")
async def cambiar_estado_pedido(
    pedido_id: int, 
    nuevo_estado: str = Form(...),
    db: Session = Depends(get_db)
):
    """API endpoint para cambiar el estado de un pedido"""
    
    estados_validos = ["pendiente", "confirmado", "preparando", "enviado", "entregado", "cancelado"]
    
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=400, 
            detail=f"Estado no válido. Estados válidos: {', '.join(estados_validos)}"
        )
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Actualizar estado
    db.query(Pedido).filter(Pedido.id == pedido_id).update(
        {"estado": nuevo_estado}
    )
    
    # Si se marca como entregado, actualizar fecha de entrega
    if nuevo_estado == "entregado":
        db.query(Pedido).filter(Pedido.id == pedido_id).update(
            {"fecha_entrega": datetime.now()}
        )
    
    db.commit()
    
    return {"success": True, "message": f"Estado actualizado a {nuevo_estado}"}

@router.get("/pedido/{pedido_id}", response_class=HTMLResponse)
async def ver_pedido_detalle(
    pedido_id: int, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Ver detalles completos de un pedido"""
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Obtener información del cliente
    cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
    
    # Obtener detalles del pedido
    detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido_id).all()
    
    # Enriquecer detalles con información de pizzas
    detalles_enriquecidos = []
    for detalle in detalles:
        pizza = db.query(Pizza).filter(Pizza.id == detalle.pizza_id).first()
        detalles_enriquecidos.append({
            "pizza_nombre": pizza.nombre if pizza else "Pizza no encontrada",
            "pizza_descripcion": pizza.descripcion if pizza else "",
            "tamano": detalle.tamano,
            "cantidad": detalle.cantidad,
            "precio_unitario": detalle.precio_unitario,
            "subtotal": detalle.subtotal
        })
    
    pedido_detallado = {
        "id": pedido.id,
        "cliente_nombre": cliente.nombre if cliente else "Cliente desconocido",
        "cliente_whatsapp": cliente.numero_whatsapp if cliente else "Sin número",
        "estado": pedido.estado,
        "total": pedido.total,
        "direccion_entrega": pedido.direccion_entrega,
        "notas": pedido.notas,
        "fecha_pedido": pedido.fecha_pedido,
        "fecha_entrega": pedido.fecha_entrega,
        "detalles": detalles_enriquecidos
    }
    
    return templates.TemplateResponse("admin/pedido_detalle.html", {
        "request": request,
        "pedido": pedido_detallado,
        "estados_disponibles": ["pendiente", "confirmado", "preparando", "enviado", "entregado", "cancelado"]
    })
