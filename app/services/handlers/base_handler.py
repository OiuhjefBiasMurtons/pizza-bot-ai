"""
Clase base para todos los handlers del bot
"""

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

class BaseHandler(ABC):
    """
    Clase base para todos los handlers del bot
    Proporciona funcionalidad común y interfaz consistente
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Estados de conversación (compartidos entre handlers)
        self.ESTADOS = {
            'INICIO': 'inicio',
            'REGISTRO_NOMBRE': 'registro_nombre', 
            'REGISTRO_DIRECCION': 'registro_direccion',
            'MENU': 'menu',
            'PEDIDO': 'pedido',
            'DIRECCION': 'direccion',
            'CONFIRMACION': 'confirmacion',
            'FINALIZADO': 'finalizado'
        }
    
    # Métodos de utilidad compartidos
    def get_temporary_data(self, numero_whatsapp: str) -> dict:
        """Obtener datos temporales de la conversación"""
        from app.models.conversation_state import ConversationState
        
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if conv_state and conv_state.datos_temporales is not None:
            try:
                return json.loads(str(conv_state.datos_temporales))
            except:
                return {}
        
        return {}

    def get_temporary_value(self, numero_whatsapp: str, key: str):
        """Obtener un valor específico de los datos temporales"""
        datos = self.get_temporary_data(numero_whatsapp)
        return datos.get(key)

    def set_temporary_value(self, numero_whatsapp: str, key: str, value):
        """Guardar un valor específico en los datos temporales"""
        datos = self.get_temporary_data(numero_whatsapp)
        datos[key] = value
        self.set_temporary_data(numero_whatsapp, datos)

    def set_temporary_data(self, numero_whatsapp: str, datos: dict):
        """Guardar datos temporales de la conversación"""
        from app.models.conversation_state import ConversationState
        
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not conv_state:
            conv_state = ConversationState(numero_whatsapp=numero_whatsapp)
            self.db.add(conv_state)
        
        setattr(conv_state, 'datos_temporales', json.dumps(datos))
        self.db.commit()

    def set_conversation_state(self, numero_whatsapp: str, estado: str):
        """Cambiar estado de la conversación"""
        from app.models.conversation_state import ConversationState
        
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not conv_state:
            conv_state = ConversationState(numero_whatsapp=numero_whatsapp)
            self.db.add(conv_state)
        
        setattr(conv_state, 'estado_actual', estado)
        self.db.commit()
        logger.info(f"💾 Estado guardado - Usuario: {numero_whatsapp}, Estado: {estado}")

    def clear_conversation_data(self, numero_whatsapp: str):
        """Limpiar datos de conversación"""
        from app.models.conversation_state import ConversationState
        
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if conv_state:
            setattr(conv_state, 'estado_actual', self.ESTADOS['INICIO'])
            setattr(conv_state, 'datos_temporales', None)
            self.db.commit()
