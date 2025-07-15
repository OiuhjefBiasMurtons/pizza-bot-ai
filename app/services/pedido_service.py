from sqlalchemy.orm import Session
from app.models.pedido import Pedido, DetallePedido
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.sql import func

# Servicio de pedidos
class PedidoService:
    def __init__(self, db: Session):
        self.db = db
    
    # Crear un nuevo pedido en la base de datos
    async def crear_pedido(self, cliente: Cliente, carrito: List[Dict[str, Any]], direccion: str) -> int:
        """Crear un nuevo pedido en la base de datos"""
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        
        # Crear pedido
        pedido = Pedido(
            cliente_id=cliente.id,
            total=total,
            direccion_entrega=direccion,
            estado="pendiente"
        )
        
        self.db.add(pedido)
        self.db.commit()
        self.db.refresh(pedido)
        
        # Crear detalles del pedido
        for item in carrito:
            detalle = DetallePedido(
                pedido_id=pedido.id,
                pizza_id=item['pizza_id'],
                tamano=item['tamano'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio'],
                subtotal=item['precio'] * item['cantidad']
            )
            self.db.add(detalle)
        
        self.db.commit()
        
        # Actualizar última fecha de pedido del cliente
        self.db.query(Cliente).filter(Cliente.id == cliente.id).update(
            {"ultimo_pedido": func.now()},
            synchronize_session=False
        )
        self.db.commit()
        
        return self.db.query(Pedido.id).filter(Pedido.id == pedido.id).scalar()
    
    async def obtener_pedido(self, pedido_id: int) -> Pedido:
        """Obtener pedido por ID"""
        return self.db.query(Pedido).filter(Pedido.id == pedido_id).first()
    
    async def obtener_pedidos_cliente(self, cliente_id: int) -> List[Pedido]:
        """Obtener todos los pedidos de un cliente"""
        return self.db.query(Pedido).filter(
            Pedido.cliente_id == cliente_id
        ).order_by(Pedido.fecha_pedido.desc()).all()
    
    async def actualizar_estado_pedido(self, pedido_id: int, nuevo_estado: str) -> bool:
        """Actualizar estado de un pedido"""
        pedido = self.db.query(Pedido).filter(Pedido.id == pedido_id).first()
        
        if not pedido:
            return False
        
        self.db.query(Pedido).filter(Pedido.id == pedido_id).update(
            {"estado": nuevo_estado},
            synchronize_session=False
        )
        self.db.commit()
        
        return True
    
    async def obtener_pedidos_por_estado(self, estado: str) -> List[Pedido]:
        """Obtener pedidos por estado"""
        return self.db.query(Pedido).filter(Pedido.estado == estado).all()
    
    async def calcular_total_carrito(self, carrito: List[Dict[str, Any]]) -> float:
        """Calcular total del carrito"""
        return sum(item['precio'] * item['cantidad'] for item in carrito)
    
    async def validar_pizza_disponible(self, pizza_id: int) -> bool:
        """Validar que una pizza esté disponible"""
        pizza = self.db.query(Pizza).filter(
            Pizza.id == pizza_id,
            Pizza.disponible == True
        ).first()
        
        return pizza is not None 