from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

# Modelo de pedido
class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    estado = Column(String(50), default="pendiente")  # pendiente, confirmado, preparando, enviado, entregado, cancelado
    total = Column(Float, nullable=False)
    direccion_entrega = Column(String(200))
    notas = Column(Text)
    fecha_pedido = Column(DateTime(timezone=True), server_default=func.now())
    fecha_entrega = Column(DateTime(timezone=True))
    
    # Relación con cliente
    cliente = relationship("Cliente")
    
    def __repr__(self):
        return f"<Pedido(id={self.id}, cliente_id={self.cliente_id}, total={self.total})>"

# Modelo de detalle de pedido
class DetallePedido(Base):
    __tablename__ = "detalle_pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    pizza_id = Column(Integer, ForeignKey("pizzas.id"), nullable=False)
    tamano = Column(String(20), nullable=False)  # pequeña, mediana, grande
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Relaciones
    pedido = relationship("Pedido")
    pizza = relationship("Pizza")
    
    def __repr__(self):
        return f"<DetallePedido(pedido_id={self.pedido_id}, pizza_id={self.pizza_id}, cantidad={self.cantidad})>" 