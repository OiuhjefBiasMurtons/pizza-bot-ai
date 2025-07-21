"""
Servicio optimizado para gestión de estados de conversación
Combina caché en memoria con persistencia en base de datos
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.conversation_state import ConversationState
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class OptimizedConversationService:
    """Servicio optimizado para gestión de estados de conversación"""
    
    def __init__(self, db: Session):
        self.db = db
        self._memory_cache = {}  # Caché en memoria como fallback
        self._cache_ttl = timedelta(minutes=30)
    
    async def get_conversation_state(self, numero_whatsapp: str) -> str:
        """
        Obtener estado de conversación con caché multi-nivel:
        1. Caché Redis (si está disponible)
        2. Caché en memoria
        3. Base de datos
        """
        try:
            # Nivel 1: Intentar caché Redis
            cached_data = await cache_service.get_conversation_state(numero_whatsapp)
            if cached_data and cached_data.get('estado'):
                logger.debug(f"🎯 Estado desde Redis: {numero_whatsapp}")
                return cached_data['estado']
            
            # Nivel 2: Caché en memoria
            if numero_whatsapp in self._memory_cache:
                cache_entry = self._memory_cache[numero_whatsapp]
                if datetime.now() - cache_entry['timestamp'] < self._cache_ttl:
                    logger.debug(f"🧠 Estado desde memoria: {numero_whatsapp}")
                    return cache_entry['estado']
                else:
                    # Limpiar entrada expirada
                    del self._memory_cache[numero_whatsapp]
            
            # Nivel 3: Base de datos
            estado = self._get_state_from_db(numero_whatsapp)
            
            # Actualizar cachés con el resultado
            await self._update_caches(numero_whatsapp, estado)
            
            return estado
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado para {numero_whatsapp}: {e}")
            # Fallback a estado por defecto
            return 'SALUDO'
    
    async def set_conversation_state(self, numero_whatsapp: str, nuevo_estado: str) -> bool:
        """
        Actualizar estado de conversación en todos los niveles:
        1. Base de datos (fuente de verdad)
        2. Caché Redis
        3. Caché en memoria
        """
        try:
            # Actualizar en base de datos primero
            success = self._update_state_in_db(numero_whatsapp, nuevo_estado)
            
            if success:
                # Actualizar cachés
                await self._update_caches(numero_whatsapp, nuevo_estado)
                logger.debug(f"✅ Estado actualizado para {numero_whatsapp}: {nuevo_estado}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estado para {numero_whatsapp}: {e}")
            return False
    
    def _get_state_from_db(self, numero_whatsapp: str) -> str:
        """Obtener estado desde la base de datos con manejo de errores"""
        try:
            state = self.db.query(ConversationState).filter(
                ConversationState.numero_whatsapp == numero_whatsapp
            ).first()
            
            if state:
                logger.debug(f"🗃️ Estado desde BD: {numero_whatsapp}")
                return str(state.estado_actual)  # Convertir a string explícitamente
            else:
                # Crear nuevo estado por defecto
                logger.info(f"🆕 Creando nuevo estado para {numero_whatsapp}")
                new_state = ConversationState(
                    numero_whatsapp=numero_whatsapp,
                    estado_actual='SALUDO',
                    fecha_actualizacion=datetime.now()
                )
                self.db.add(new_state)
                self.db.commit()
                return 'SALUDO'
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Error de BD obteniendo estado para {numero_whatsapp}: {e}")
            self.db.rollback()
            return 'SALUDO'
    
    def _update_state_in_db(self, numero_whatsapp: str, nuevo_estado: str) -> bool:
        """Actualizar estado en la base de datos con manejo de errores"""
        try:
            state = self.db.query(ConversationState).filter(
                ConversationState.numero_whatsapp == numero_whatsapp
            ).first()
            
            if state:
                # Actualizar estado existente
                state.estado_actual = nuevo_estado  # type: ignore
                state.fecha_actualizacion = datetime.now()  # type: ignore
            else:
                # Crear nuevo estado
                state = ConversationState(
                    numero_whatsapp=numero_whatsapp,
                    estado_actual=nuevo_estado,
                    fecha_actualizacion=datetime.now()
                )
                self.db.add(state)
            
            self.db.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Error de BD actualizando estado para {numero_whatsapp}: {e}")
            self.db.rollback()
            return False
    
    async def _update_caches(self, numero_whatsapp: str, estado: str):
        """Actualizar todos los cachés con el nuevo estado"""
        try:
            # Preparar datos para caché
            cache_data = {
                'estado': estado,
                'timestamp': datetime.now().isoformat(),
                'numero_whatsapp': numero_whatsapp
            }
            
            # Actualizar caché Redis
            await cache_service.set_conversation_state(
                numero_whatsapp, 
                cache_data,
                ttl=self._cache_ttl
            )
            
            # Actualizar caché en memoria
            self._memory_cache[numero_whatsapp] = {
                'estado': estado,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando cachés para {numero_whatsapp}: {e}")
    
    async def invalidate_user_state(self, numero_whatsapp: str):
        """Invalidar estado de conversación en todos los cachés"""
        try:
            # Limpiar caché Redis
            await cache_service.delete_conversation_state(numero_whatsapp)
            
            # Limpiar caché en memoria
            if numero_whatsapp in self._memory_cache:
                del self._memory_cache[numero_whatsapp]
            
            logger.debug(f"🧹 Estado invalidado para {numero_whatsapp}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error invalidando estado para {numero_whatsapp}: {e}")
    
    def cleanup_memory_cache(self):
        """Limpiar entradas expiradas del caché en memoria"""
        try:
            now = datetime.now()
            expired_keys = [
                key for key, value in self._memory_cache.items()
                if now - value['timestamp'] > self._cache_ttl
            ]
            
            for key in expired_keys:
                del self._memory_cache[key]
            
            if expired_keys:
                logger.debug(f"🧹 Limpiadas {len(expired_keys)} entradas expiradas del caché")
                
        except Exception as e:
            logger.warning(f"⚠️ Error limpiando caché en memoria: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de caché para monitoreo"""
        stats = {
            'memory_cache_size': len(self._memory_cache),
            'redis_enabled': cache_service.enabled,
            'redis_connected': cache_service.redis is not None
        }
        
        try:
            if cache_service.redis:
                info = await cache_service.redis.info()
                stats['redis_memory_used'] = info.get('used_memory_human', 'Unknown')
                stats['redis_connected_clients'] = info.get('connected_clients', 0)
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo stats de Redis: {e}")
            stats['redis_error'] = str(e)
        
        return stats
