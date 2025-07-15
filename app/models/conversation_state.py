from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database.connection import Base

class ConversationState(Base):
    __tablename__ = "conversation_states"
    
    id = Column(Integer, primary_key=True, index=True)
    numero_whatsapp = Column(String(20), unique=True, nullable=False, index=True)
    estado_actual = Column(String(50), default='inicio')
    datos_temporales = Column(Text)  # JSON string para guardar datos temporales
    ultimo_mensaje = Column(String(500))
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ConversationState(numero_whatsapp='{self.numero_whatsapp}', estado='{self.estado_actual}')>"
