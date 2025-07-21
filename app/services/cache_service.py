import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
from config.settings import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Servicio de caché para optimizar acceso a datos frecuentes"""
    
    def __init__(self):
        self.redis: Optional[Any] = None
        self.enabled = settings.REDIS_ENABLED
        self.default_ttl = timedelta(hours=2)  # TTL por defecto de 2 horas
        self.redis_available = False
        
    async def connect(self):
        """Conectar al servidor Redis"""
        if not self.enabled:
            logger.info("🔧 Caché Redis deshabilitado - usando solo memoria local")
            return
            
        try:
            # Intentar importar aioredis de forma segura
            try:
                import aioredis
            except ImportError as e:
                logger.warning(f"⚠️ aioredis no disponible: {e}. Continuando sin Redis.")
                self.enabled = False
                return
            
            self.redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Probar conexión
            await self.redis.ping()
            self.redis_available = True
            logger.info("✅ Conectado a Redis para caché")
            
        except ImportError as e:
            logger.warning(f"⚠️ Módulos de Redis no disponibles: {e}. Continuando sin caché distribuido.")
            self.enabled = False
            self.redis = None
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar a Redis: {e}. Continuando sin caché distribuido.")
            self.enabled = False
            self.redis = None
            self.redis_available = False
    
    async def disconnect(self):
        """Desconectar del servidor Redis"""
        if self.redis:
            try:
                await self.redis.close()
                logger.info("🔌 Desconectado de Redis")
            except Exception as e:
                logger.warning(f"⚠️ Error desconectando Redis: {e}")
            finally:
                self.redis = None
                self.redis_available = False
    
    async def get_conversation_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de conversación desde caché"""
        if not self.enabled or not self.redis:
            return None
            
        try:
            key = f"conversation:{user_id}"
            cached_data = await self.redis.get(key)
            
            if cached_data:
                logger.debug(f"🎯 Estado de conversación encontrado en caché para {user_id}")
                return json.loads(cached_data)
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de caché para {user_id}: {e}")
            
        return None
    
    async def set_conversation_state(
        self, 
        user_id: str, 
        state_data: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ):
        """Guardar estado de conversación en caché"""
        if not self.enabled or not self.redis:
            return
            
        try:
            key = f"conversation:{user_id}"
            ttl_seconds = int((ttl or self.default_ttl).total_seconds())
            
            await self.redis.setex(
                key,
                ttl_seconds,
                json.dumps(state_data, default=str)
            )
            
            logger.debug(f"💾 Estado de conversación guardado en caché para {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando estado en caché para {user_id}: {e}")
    
    async def delete_conversation_state(self, user_id: str):
        """Eliminar estado de conversación del caché"""
        if not self.enabled or not self.redis:
            return
            
        try:
            key = f"conversation:{user_id}"
            await self.redis.delete(key)
            logger.debug(f"🗑️ Estado de conversación eliminado del caché para {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error eliminando estado de caché para {user_id}: {e}")
    
    async def get_user_data(self, user_id: str, data_key: str) -> Optional[Any]:
        """Obtener datos de usuario específicos desde caché"""
        if not self.enabled or not self.redis:
            return None
            
        try:
            key = f"user:{user_id}:{data_key}"
            cached_data = await self.redis.get(key)
            
            if cached_data:
                return json.loads(cached_data)
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de usuario {user_id}:{data_key}: {e}")
            
        return None
    
    async def set_user_data(
        self, 
        user_id: str, 
        data_key: str, 
        data: Any,
        ttl: Optional[timedelta] = None
    ):
        """Guardar datos de usuario en caché"""
        if not self.enabled or not self.redis:
            return
            
        try:
            key = f"user:{user_id}:{data_key}"
            ttl_seconds = int((ttl or self.default_ttl).total_seconds())
            
            await self.redis.setex(
                key,
                ttl_seconds,
                json.dumps(data, default=str)
            )
            
        except Exception as e:
            logger.error(f"❌ Error guardando datos de usuario {user_id}:{data_key}: {e}")
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidar todo el caché de un usuario"""
        if not self.enabled or not self.redis:
            return
            
        try:
            # Buscar todas las claves relacionadas al usuario
            patterns = [f"conversation:{user_id}", f"user:{user_id}:*"]
            
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            
            logger.debug(f"🧹 Caché invalidado para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error invalidando caché para {user_id}: {e}")

# Instancia global del servicio de caché
cache_service = CacheService()
