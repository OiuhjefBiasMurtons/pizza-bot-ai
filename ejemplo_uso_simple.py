"""
Ejemplo de uso del servicio optimizado de conversaciones (versión sin Redis)
Demuestra el funcionamiento con solo caché en memoria
"""
import asyncio
import logging
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from app.services.optimized_conversation_service import OptimizedConversationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ejemplo_uso_sin_redis():
    """Ejemplo de uso sin Redis - solo caché en memoria"""
    
    # Crear sesión de base de datos
    db: Session = SessionLocal()
    
    try:
        # Inicializar servicio optimizado
        service = OptimizedConversationService(db)
        
        # Usuario de ejemplo
        numero_test = "+1234567890"
        
        print("🧪 Probando servicio optimizado (solo caché en memoria)...")
        
        # 1. Obtener estado inicial (creará nuevo estado si no existe)
        print("1️⃣ Obteniendo estado inicial...")
        estado1 = await service.get_conversation_state(numero_test)
        print(f"📍 Estado inicial: {estado1}")
        
        # 2. Cambiar estado
        print("\n2️⃣ Cambiando estado a MENU...")
        success = await service.set_conversation_state(numero_test, "MENU")
        print(f"✅ Estado cambiado: {success}")
        
        # 3. Verificar desde caché (debería ser más rápido - segunda vez)
        print("\n3️⃣ Obteniendo estado desde caché...")
        estado2 = await service.get_conversation_state(numero_test)
        print(f"🧠 Estado desde caché en memoria: {estado2}")
        
        # 4. Obtener estadísticas
        print("\n4️⃣ Obteniendo estadísticas...")
        try:
            stats = await service.get_cache_stats()
            print(f"📊 Estadísticas de caché: {stats}")
        except Exception as e:
            print(f"⚠️ Error obteniendo estadísticas: {e}")
            # Mostrar estadísticas básicas
            print(f"📊 Tamaño caché en memoria: {len(service._memory_cache)} entradas")
        
        # 5. Probar múltiples accesos para ver la diferencia de rendimiento
        print("\n5️⃣ Probando rendimiento...")
        import time
        
        # Primer acceso (desde BD)
        service._memory_cache.clear()  # Limpiar caché
        start_time = time.time()
        estado_bd = await service.get_conversation_state(numero_test)
        bd_time = time.time() - start_time
        print(f"⏱️ Tiempo desde BD: {bd_time*1000:.2f}ms")
        
        # Segundo acceso (desde caché)
        start_time = time.time()
        estado_cache = await service.get_conversation_state(numero_test)
        cache_time = time.time() - start_time
        print(f"⏱️ Tiempo desde caché: {cache_time*1000:.2f}ms")
        
        if bd_time > cache_time:
            mejora = ((bd_time - cache_time) / bd_time) * 100
            print(f"🚀 Mejora de rendimiento: {mejora:.1f}%")
        
        # 6. Limpiar caché en memoria
        print("\n6️⃣ Limpiando caché...")
        service.cleanup_memory_cache()
        print(f"🧹 Caché limpiado - Tamaño actual: {len(service._memory_cache)}")
        
        # 7. Invalidar estado específico
        print("\n7️⃣ Invalidando estado...")
        await service.invalidate_user_state(numero_test)
        print("❌ Estado invalidado")
        
        # 8. Verificar que se obtiene desde BD
        print("\n8️⃣ Verificando acceso post-invalidación...")
        estado3 = await service.get_conversation_state(numero_test)
        print(f"🗃️ Estado desde BD después de invalidar: {estado3}")
        
        print("\n🎉 ¡Prueba completada exitosamente!")
        print("💡 El sistema funciona perfectamente sin Redis, usando caché en memoria.")
        
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(ejemplo_uso_sin_redis())
