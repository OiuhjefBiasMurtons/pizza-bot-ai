"""
Servicio para gestionar el lifecycle de conexiones y caché
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class AppLifecycleManager:
    """Gestor del ciclo de vida de la aplicación"""
    
    def __init__(self):
        self.cache_cleanup_task = None
        self.cleanup_interval = 3600  # 1 hora en segundos
    
    async def startup(self):
        """Inicialización de servicios al arrancar la app"""
        try:
            logger.info("🚀 Iniciando servicios de la aplicación...")
            
            # Conectar a Redis
            await cache_service.connect()
            
            # Iniciar tarea de limpieza periódica
            self.cache_cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            logger.info("✅ Servicios iniciados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando servicios: {e}")
            raise
    
    async def shutdown(self):
        """Limpieza de servicios al cerrar la app"""
        try:
            logger.info("🛑 Cerrando servicios de la aplicación...")
            
            # Cancelar tarea de limpieza
            if self.cache_cleanup_task and not self.cache_cleanup_task.done():
                self.cache_cleanup_task.cancel()
                try:
                    await self.cache_cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Desconectar Redis
            await cache_service.disconnect()
            
            logger.info("✅ Servicios cerrados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error cerrando servicios: {e}")
    
    async def _periodic_cleanup(self):
        """Tarea de limpieza periódica"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                logger.debug("🧹 Ejecutando limpieza periódica de caché...")
                
                # Aquí se pueden agregar más tareas de limpieza
                # Por ejemplo: limpiar sesiones expiradas, logs antiguos, etc.
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en limpieza periódica: {e}")

# Instancia global del gestor
lifecycle_manager = AppLifecycleManager()

@asynccontextmanager
async def lifespan(app):
    """
    Context manager para gestionar el lifecycle de FastAPI
    Uso en main.py:
    
    from app.services.lifecycle_service import lifespan
    app = FastAPI(lifespan=lifespan)
    """
    # Startup
    await lifecycle_manager.startup()
    
    try:
        yield
    finally:
        # Shutdown
        await lifecycle_manager.shutdown()
