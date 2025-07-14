from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from database.connection import Base

# Modelo de pizza
class Pizza(Base):
    __tablename__ = "pizzas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio_pequena = Column(Float, nullable=False)
    precio_mediana = Column(Float, nullable=False)
    precio_grande = Column(Float, nullable=False)
    disponible = Column(Boolean, default=True)
    emoji = Column(String(10), default="🍕")
    
    def __repr__(self):
        return f"<Pizza(nombre='{self.nombre}', precio_pequena={self.precio_pequena})>" 