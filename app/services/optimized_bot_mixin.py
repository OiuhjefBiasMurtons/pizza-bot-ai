"""
Mixin para integrar el servicio optimizado de conversaciones en bots existentes
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.optimized_conversation_service import OptimizedConversationService

logger = logging.getLogger(__name__)

class OptimizedBotMixin:
    """Mixin que proporciona funcionalidades optimizadas de conversación a los bots existentes"""
    
    def __init__(self, db: Session):
        # Asegurar que el bot tenga acceso a la DB
        if not hasattr(self, 'db'):
            self.db = db
        
        # Inicializar servicio optimizado
        self._optimized_service = OptimizedConversationService(db)
    
    async def get_conversation_state_optimized(self, numero_whatsapp: str) -> str:
        """
        Versión optimizada de get_conversation_state que usa caché multi-nivel
        Reemplaza la versión original del bot
        """
        return await self._optimized_service.get_conversation_state(numero_whatsapp)
    
    async def set_conversation_state_optimized(self, numero_whatsapp: str, nuevo_estado: str) -> bool:
        """
        Versión optimizada de set_conversation_state que usa caché multi-nivel
        Reemplaza la versión original del bot
        """
        return await self._optimized_service.set_conversation_state(numero_whatsapp, nuevo_estado)
    
    async def invalidate_conversation_state(self, numero_whatsapp: str):
        """
        Invalidar caché de conversación para un usuario
        Útil cuando se necesita forzar una recarga desde BD
        """
        await self._optimized_service.invalidate_user_state(numero_whatsapp)
    
    def cleanup_conversation_cache(self):
        """
        Limpiar caché en memoria de conversaciones expiradas
        Debe ser llamado periódicamente (ej: cada hora)
        """
        self._optimized_service.cleanup_memory_cache()
    
    async def get_conversation_cache_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de rendimiento del caché
        Útil para monitoreo y debugging
        """
        return await self._optimized_service.get_cache_stats()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas de rendimiento del bot
        """
        return {
            'cache_service_enabled': self._optimized_service._memory_cache is not None,
            'memory_cache_size': len(self._optimized_service._memory_cache),
            'optimization_version': '1.0'
        }
