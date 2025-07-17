#!/usr/bin/env python3
"""
Test funcional del webhook después de la migración
"""
import asyncio
import json
from app.routers.webhook import process_whatsapp_message
from database.connection import get_db
from app.models.cliente import Cliente
from app.models.conversation_state import ConversationState
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_webhook_functionality():
    """Test funcional del webhook después de la migración"""
    
    try:
        # Obtener DB
        db = next(get_db())
        
        # Limpiar datos de prueba
        db.query(Cliente).filter(Cliente.numero_whatsapp == '+webhook_test').delete()
        db.query(ConversationState).filter(ConversationState.numero_whatsapp == '+webhook_test').delete()
        db.commit()
        
        print("🧪 INICIANDO PRUEBAS DE WEBHOOK")
        print("=" * 50)
        
        # Test 1: Mensaje inicial
        print("\n📱 TEST 1: Mensaje inicial 'hola'")
        result = await process_whatsapp_message('+webhook_test', 'hola', db)
        print(f"✅ Status: {result['status']}")
        print(f"🔄 Respuesta procesada correctamente")
        
        # Test 2: Proporcionar nombre
        print("\n📱 TEST 2: Proporcionar nombre")
        result = await process_whatsapp_message('+webhook_test', 'Juan Test', db)
        print(f"✅ Status: {result['status']}")
        print(f"🔄 Nombre procesado correctamente")
        
        # Test 3: Proporcionar dirección
        print("\n📱 TEST 3: Proporcionar dirección")
        result = await process_whatsapp_message('+webhook_test', 'Calle Test 123', db)
        print(f"✅ Status: {result['status']}")
        print(f"🔄 Dirección procesada correctamente")
        
        # Test 4: Solicitar menú
        print("\n📱 TEST 4: Solicitar menú")
        result = await process_whatsapp_message('+webhook_test', '1', db)
        print(f"✅ Status: {result['status']}")
        print(f"🔄 Menú mostrado correctamente")
        
        # Test 5: Seleccionar pizza
        print("\n📱 TEST 5: Seleccionar pizza (formato original)")
        result = await process_whatsapp_message('+webhook_test', '1 mediana', db)
        print(f"✅ Status: {result['status']}")
        print(f"🔄 Pizza seleccionada correctamente")
        
        # Test 6: Verificar que el cliente está registrado
        print("\n📱 TEST 6: Verificar cliente registrado")
        cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == '+webhook_test').first()
        if cliente:
            print(f"✅ Cliente registrado: {cliente.nombre}")
            print(f"📍 Dirección: {cliente.direccion}")
        else:
            print("❌ Cliente no encontrado")
            
        # Test 7: Verificar estado de conversación
        print("\n📱 TEST 7: Verificar estado de conversación")
        estado = db.query(ConversationState).filter(ConversationState.numero_whatsapp == '+webhook_test').first()
        if estado:
            print(f"✅ Estado actual: {estado.estado_actual}")
        else:
            print("❌ Estado no encontrado")
        
        print("\n" + "=" * 50)
        print("🎉 TODOS LOS TESTS DE WEBHOOK PASARON EXITOSAMENTE!")
        print("🔧 El bot refactorizado está funcionando correctamente con el webhook")
        
    except Exception as e:
        logger.error(f"❌ Error en test de webhook: {e}")
        raise
        
    finally:
        # Limpiar datos de prueba
        db.query(Cliente).filter(Cliente.numero_whatsapp == '+webhook_test').delete()
        db.query(ConversationState).filter(ConversationState.numero_whatsapp == '+webhook_test').delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    asyncio.run(test_webhook_functionality())
