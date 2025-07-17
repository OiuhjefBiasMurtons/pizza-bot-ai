#!/usr/bin/env python3
"""
Test para verificar las funcionalidades de modificación de carrito
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_bot_service import EnhancedBotService
from app.services.ai_service import AIService
from database.connection import SessionLocal
from app.models.cliente import Cliente

async def test_carrito_modification():
    """Test completo de modificación de carrito"""
    
    print("🧪 Iniciando test de modificación de carrito...")
    
    # Configurar servicios
    db_session = SessionLocal()
    
    try:
        ai_service = AIService(db_session)
        bot_service = EnhancedBotService(db_session)
        bot_service.ai_service = ai_service
        
        test_phone = "+1234567890"
        
        # Limpiar estado inicial
        bot_service.clear_conversation_data(test_phone)
        
        # Obtener o crear cliente de prueba
        cliente = db_session.query(Cliente).filter(Cliente.numero_whatsapp == test_phone).first()
        if not cliente:
            cliente = Cliente(
                numero_whatsapp=test_phone,
                nombre="Test User",
                direccion="Test Address 123"
            )
            db_session.add(cliente)
            db_session.commit()
            db_session.refresh(cliente)
        
        print(f"✅ Cliente configurado: {cliente.nombre}")
        
        # Paso 1: Agregar pizzas al carrito inicial
        print("\n1️⃣ Agregando pizzas iniciales al carrito...")
        
        # Simular que ya hay pizzas en el carrito
        carrito_inicial = [
            {
                'pizza_id': 1,
                'pizza_nombre': 'Pepperoni',
                'pizza_emoji': '🍕',
                'tamano': 'pequeña',
                'precio': 14.99,
                'cantidad': 1
            },
            {
                'pizza_id': 1,
                'pizza_nombre': 'Pepperoni', 
                'pizza_emoji': '🍕',
                'tamano': 'pequeña',
                'precio': 14.99,
                'cantidad': 1
            },
            {
                'pizza_id': 2,
                'pizza_nombre': 'Margherita',
                'pizza_emoji': '🍅',
                'tamano': 'grande',
                'precio': 20.99,
                'cantidad': 1
            }
        ]
        
        bot_service.set_temporary_value(test_phone, 'carrito', carrito_inicial)
        bot_service.set_conversation_state(test_phone, bot_service.ESTADOS['PEDIDO'])
        
        carrito = bot_service.get_temporary_value(test_phone, 'carrito') or []
        total_inicial = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
        print(f"   Carrito inicial: {len(carrito)} items, total: ${total_inicial:.2f}")
        
        # Paso 2: Test del mensaje problemático
        print("\n2️⃣ Probando mensaje: 'Solo quiero la pepperoni grande'")
        
        response = await bot_service.process_message(test_phone, "Solo quiero la pepperoni grande")
        print(f"   Respuesta del bot: {response[:100]}...")
        
        # Verificar estado del carrito después
        carrito_final = bot_service.get_temporary_value(test_phone, 'carrito') or []
        if carrito_final:
            total_final = sum(item['precio'] * item.get('cantidad', 1) for item in carrito_final)
            print(f"   Carrito final: {len(carrito_final)} items, total: ${total_final:.2f}")
            
            for item in carrito_final:
                print(f"      • {item['pizza_emoji']} {item['pizza_nombre']} - {item['tamano']}")
            
            # Verificar que solo hay una pizza pepperoni grande
            if len(carrito_final) == 1 and carrito_final[0]['pizza_nombre'] == 'Pepperoni' and carrito_final[0]['tamano'] == 'grande':
                print("   ✅ SUCCESS: Carrito modificado correctamente!")
            else:
                print("   ❌ FAILED: Carrito no se modificó como esperado")
        else:
            print("   ❌ FAILED: Carrito está vacío")
        
        # Paso 3: Test adicional - limpiar carrito
        print("\n3️⃣ Probando limpiar carrito...")
        
        # Agregar algo al carrito primero
        bot_service.set_temporary_value(test_phone, 'carrito', carrito_inicial.copy())
        
        response = await bot_service.process_message(test_phone, "Cancela todo mi pedido")
        carrito_limpio = bot_service.get_temporary_value(test_phone, 'carrito') or []
        
        if not carrito_limpio or len(carrito_limpio) == 0:
            print("   ✅ SUCCESS: Carrito limpiado correctamente!")
        else:
            print("   ❌ FAILED: Carrito no se limpió")
        
        print("\n🎉 Test completado!")
        
    except Exception as e:
        print(f"❌ Error durante el test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_session.close()

if __name__ == "__main__":
    asyncio.run(test_carrito_modification())
