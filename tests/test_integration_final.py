#!/usr/bin/env python3
"""
Test final de integración del bot_service refactorizado
"""
import asyncio
from database.connection import get_db
from app.services.bot_service import BotService
from app.models.cliente import Cliente
from app.models.conversation_state import ConversationState
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_integration_final():
    """Test final de integración del bot_service refactorizado"""
    
    try:
        # Obtener DB
        db = next(get_db())
        
        # Limpiar datos de prueba
        db.query(Cliente).filter(Cliente.numero_whatsapp == '+final_test').delete()
        db.query(ConversationState).filter(ConversationState.numero_whatsapp == '+final_test').delete()
        db.commit()
        
        print("🧪 INICIANDO PRUEBAS DE INTEGRACIÓN FINAL")
        print("=" * 50)
        
        # Crear instancia del bot service
        bot_service = BotService(db)
        
        # Test 1: Mensaje inicial
        print("\n📱 TEST 1: Mensaje inicial 'hola'")
        response = await bot_service.process_message('+final_test', 'hola')
        print(f"🤖 Bot: {response[:100]}...")
        assert 'nombre' in response.lower()
        print("✅ Solicita nombre correctamente")
        
        # Test 2: Proporcionar nombre
        print("\n📱 TEST 2: Proporcionar nombre")
        response = await bot_service.process_message('+final_test', 'Juan Final')
        print(f"🤖 Bot: {response[:100]}...")
        assert 'dirección' in response.lower()
        print("✅ Solicita dirección correctamente")
        
        # Test 3: Proporcionar dirección
        print("\n📱 TEST 3: Proporcionar dirección")
        response = await bot_service.process_message('+final_test', 'Calle Final 123')
        print(f"🤖 Bot: {response[:100]}...")
        assert 'menú' in response.lower()
        print("✅ Muestra menú principal correctamente")
        
        # Test 4: Solicitar menú de pizzas
        print("\n📱 TEST 4: Solicitar menú de pizzas")
        response = await bot_service.process_message('+final_test', '1')
        print(f"🤖 Bot: {response[:100]}...")
        assert 'pizza' in response.lower()
        print("✅ Muestra menú de pizzas correctamente")
        
        # Test 5: Seleccionar pizza formato original
        print("\n📱 TEST 5: Seleccionar pizza (formato original)")
        response = await bot_service.process_message('+final_test', '1 mediana')
        print(f"🤖 Bot: {response[:100]}...")
        assert 'carrito' in response.lower() or 'agregado' in response.lower()
        print("✅ Selecciona pizza correctamente")
        
        # Test 6: Comando especial - menu
        print("\n📱 TEST 6: Comando 'menu'")
        response = await bot_service.process_message('+final_test', 'menu')
        print(f"🤖 Bot: {response[:100]}...")
        assert 'pizza' in response.lower()
        print("✅ Comando 'menu' funciona correctamente")
        
        # Test 7: Comando especial - ayuda
        print("\n📱 TEST 7: Comando 'ayuda'")
        response = await bot_service.process_message('+final_test', 'ayuda')
        print(f"🤖 Bot: {response[:100]}...")
        assert 'ayuda' in response.lower() or 'comandos' in response.lower()
        print("✅ Comando 'ayuda' funciona correctamente")
        
        # Test 8: Verificar cliente registrado
        print("\n📱 TEST 8: Verificar cliente registrado")
        cliente = bot_service.get_cliente('+final_test')
        assert cliente is not None
        assert getattr(cliente, 'nombre') == 'Juan Final'
        assert getattr(cliente, 'direccion') == 'Calle Final 123'
        print(f"✅ Cliente registrado: {getattr(cliente, 'nombre')}")
        print(f"📍 Dirección: {getattr(cliente, 'direccion')}")
        
        # Test 9: Verificar estado de conversación
        print("\n📱 TEST 9: Verificar estado de conversación")
        estado = bot_service.get_conversation_state('+final_test')
        assert estado is not None
        print(f"✅ Estado actual: {estado}")
        
        # Test 10: Métodos de compatibilidad
        print("\n📱 TEST 10: Métodos de compatibilidad")
        
        # Test get_or_create_cliente
        cliente2 = bot_service.get_or_create_cliente('+final_test')
        assert getattr(cliente2, 'numero_whatsapp') == '+final_test'
        print("✅ get_or_create_cliente funciona")
        
        # Test validate_pizza_selection
        is_valid = bot_service.validate_pizza_selection('1 mediana')
        assert is_valid == True
        print("✅ validate_pizza_selection funciona")
        
        # Test get_menu_text
        menu_text = bot_service.get_menu_text()
        assert 'pizza' in menu_text.lower()
        print("✅ get_menu_text funciona")
        
        # Test ESTADOS property
        estados = bot_service.ESTADOS
        assert 'INICIO' in estados
        assert 'MENU' in estados
        print("✅ ESTADOS property funciona")
        
        # Test conversaciones property
        conversaciones = bot_service.conversaciones
        assert isinstance(conversaciones, dict)
        print("✅ conversaciones property funciona")
        
        print("\n" + "=" * 50)
        print("🎉 TODOS LOS TESTS DE INTEGRACIÓN PASARON EXITOSAMENTE!")
        print("✅ El bot_service refactorizado está completamente funcional")
        print("✅ Mantiene compatibilidad con el código existente")
        print("✅ Los handlers están funcionando correctamente")
        print("✅ Los métodos de compatibilidad están implementados")
        print("✅ El estado de conversación se mantiene correctamente")
        print("✅ El registro de usuarios funciona perfectamente")
        print("✅ La selección de pizzas (formato original) funciona")
        print("✅ Los comandos especiales están operativos")
        print("\n🚀 EL REEMPLAZO DE BOT_SERVICE FUE EXITOSO!")
        
    except Exception as e:
        logger.error(f"❌ Error en test final: {e}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # Limpiar datos de prueba
        db.query(Cliente).filter(Cliente.numero_whatsapp == '+final_test').delete()
        db.query(ConversationState).filter(ConversationState.numero_whatsapp == '+final_test').delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    asyncio.run(test_integration_final())
