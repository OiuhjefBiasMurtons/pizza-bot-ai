"""
Ejemplo de uso del servicio optimizado de conversaciones
Demuestra cómo integrar el nuevo sistema de caché
"""
import asyncio
import logging
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from app.services.optimized_conversation_service import OptimizedConversationService
from app.services.cache_service import cache_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ejemplo_uso_optimizado():
    """Ejemplo de uso del servicio optimizado"""
    
    # Intentar conectar a Redis (opcional)
    try:
        await cache_service.connect()
        if cache_service.redis_available:
            print("✅ Redis conectado - usando caché distribuido")
        else:
            print("⚠️ Redis no disponible - usando solo caché en memoria")
    except Exception as e:
        print(f"⚠️ Error conectando Redis: {e} - usando solo caché en memoria")
    
    # Crear sesión de base de datos
    db: Session = SessionLocal()
    
    try:
        # Inicializar servicio optimizado
        service = OptimizedConversationService(db)
        
        # Usuario de ejemplo
        numero_test = "+1234567890"
        
        print("\n🧪 Probando servicio optimizado de conversaciones...")
        
        # 1. Obtener estado inicial (creará nuevo estado si no existe)
        estado1 = await service.get_conversation_state(numero_test)
        print(f"📍 Estado inicial: {estado1}")
        
        # 2. Cambiar estado
        success = await service.set_conversation_state(numero_test, "MENU")
        print(f"✅ Estado cambiado: {success}")
        
        # 3. Verificar desde caché (debería ser más rápido)
        estado2 = await service.get_conversation_state(numero_test)
        print(f"🎯 Estado desde caché: {estado2}")
        
        # 4. Obtener estadísticas
        stats = await service.get_cache_stats()
        print(f"📊 Estadísticas de caché: {stats}")
        
        # 5. Limpiar caché en memoria
        service.cleanup_memory_cache()
        print("🧹 Caché en memoria limpiado")
        
        # 6. Invalidar estado específico
        await service.invalidate_user_state(numero_test)
        print("❌ Estado invalidado en caché")
        
        # 7. Verificar que se obtiene desde BD
        estado3 = await service.get_conversation_state(numero_test)
        print(f"🗃️ Estado desde BD después de invalidar: {estado3}")
        
        print("\n🎉 ¡Optimizaciones funcionando correctamente!")
        
    finally:
        db.close()
        try:
            await cache_service.disconnect()
        except Exception as e:
            print(f"⚠️ Error desconectando Redis: {e}")

if __name__ == "__main__":
    asyncio.run(ejemplo_uso_optimizado())
