from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from database.connection import Base

# Modelo de cliente
class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_whatsapp = Column(String(20), unique=True, nullable=False, index=True)
    nombre = Column(String(100))
    direccion = Column(String(200))
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_pedido = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Cliente(numero_whatsapp='{self.numero_whatsapp}', nombre='{self.nombre}')>" 