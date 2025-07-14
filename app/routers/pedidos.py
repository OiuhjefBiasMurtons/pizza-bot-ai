from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from app.models.pedido import Pedido, DetallePedido
from app.models.cliente import Cliente

# Router de pedidos
router = APIRouter()

# Obtener todos los pedidos
@router.get("/")
async def get_pedidos(db: Session = Depends(get_db)):
    """Obtener todos los pedidos"""
    pedidos = db.query(Pedido).all()
    return [
        {
            "id": pedido.id,
            "cliente_id": pedido.cliente_id,
            "estado": pedido.estado,
            "total": pedido.total,
            "fecha_pedido": pedido.fecha_pedido,
            "direccion_entrega": pedido.direccion_entrega
        }
        for pedido in pedidos
    ]

# Obtener un pedido específico
@router.get("/{pedido_id}")
async def get_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """Obtener un pedido específico"""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Obtener detalles del pedido
    detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido_id).all()
    
    return {
        "id": pedido.id,
        "cliente_id": pedido.cliente_id,
        "estado": pedido.estado,
        "total": pedido.total,
        "fecha_pedido": pedido.fecha_pedido,
        "direccion_entrega": pedido.direccion_entrega,
        "notas": pedido.notas,
        "detalles": [
            {
                "pizza_id": detalle.pizza_id,
                "tamano": detalle.tamano,
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario,
                "subtotal": detalle.subtotal
            }
            for detalle in detalles
        ]
    }

# Actualizar el estado de un pedido
@router.put("/{pedido_id}/estado")
async def update_pedido_estado(
    pedido_id: int, 
    nuevo_estado: str, 
    db: Session = Depends(get_db)
):
    """Actualizar el estado de un pedido"""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    estados_validos = ["pendiente", "confirmado", "preparando", "enviado", "entregado", "cancelado"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=400, 
            detail=f"Estado no válido. Estados válidos: {', '.join(estados_validos)}"
        )
    
    pedido.estado = nuevo_estado
    db.commit()
    
    return {"message": f"Estado del pedido {pedido_id} actualizado a {nuevo_estado}"}

# Obtener pedidos de un cliente específico
@router.get("/cliente/{numero_whatsapp}")
async def get_pedidos_cliente(numero_whatsapp: str, db: Session = Depends(get_db)):
    """Obtener pedidos de un cliente específico"""
    cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == numero_whatsapp).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
    return [
        {
            "id": pedido.id,
            "estado": pedido.estado,
            "total": pedido.total,
            "fecha_pedido": pedido.fecha_pedido
        }
        for pedido in pedidos
    ] 