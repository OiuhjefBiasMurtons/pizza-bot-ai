#!/usr/bin/env python3
"""
Test comprensivo para diferentes casos de modificación de carrito
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_bot_service import EnhancedBotService
from app.services.ai_service import AIService
from database.connection import SessionLocal
from app.models.cliente import Cliente

async def test_comprehensive_cart_modification():
    """Test comprensivo de todas las funcionalidades de modificación"""
    
    print("🧪 Test Comprensivo de Modificación de Carrito")
    print("=" * 50)
    
    db_session = SessionLocal()
    
    try:
        ai_service = AIService(db_session)
        bot_service = EnhancedBotService(db_session)
        bot_service.ai_service = ai_service
        
        test_phone = "+1234567890"
        
        # Obtener o crear cliente
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
        
        # Test cases con diferentes frases
        test_cases = [
            {
                "frase": "Solo quiero la pepperoni grande",
                "descripcion": "Caso original - 'Solo quiero'",
                "esperado": "reemplazo"
            },
            {
                "frase": "Cambia mi pedido a una margherita mediana",
                "descripcion": "Usando 'Cambia mi pedido'",
                "esperado": "reemplazo"
            },
            {
                "frase": "Mejor haz una hawaiana grande",
                "descripcion": "Usando 'Mejor haz'", 
                "esperado": "reemplazo"
            },
            {
                "frase": "Quita las otras pizzas y solo déjame una pepperoni",
                "descripcion": "Usando 'Quita las otras'",
                "esperado": "reemplazo"
            },
            {
                "frase": "Únicamente quiero una margherita",
                "descripcion": "Usando 'Únicamente'",
                "esperado": "reemplazo"
            },
            {
                "frase": "También quiero una hawaiana mediana",
                "descripcion": "Caso de agregar (no modificar)",
                "esperado": "agregar"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}️⃣ {test_case['descripcion']}")
            print(f"   Frase: '{test_case['frase']}'")
            
            # Limpiar y configurar estado inicial
            bot_service.clear_conversation_data(test_phone)
            
            # Carrito inicial con varias pizzas
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
                    'pizza_id': 2,
                    'pizza_nombre': 'Margherita',
                    'pizza_emoji': '🍅',
                    'tamano': 'mediana',
                    'precio': 16.99,
                    'cantidad': 1
                }
            ]
            
            bot_service.set_temporary_value(test_phone, 'carrito', carrito_inicial.copy())
            bot_service.set_conversation_state(test_phone, bot_service.ESTADOS['PEDIDO'])
            
            print(f"   Carrito inicial: {len(carrito_inicial)} items")
            
            # Procesar mensaje
            try:
                response = await bot_service.process_message(test_phone, test_case['frase'])
                
                carrito_final = bot_service.get_temporary_value(test_phone, 'carrito') or []
                
                if test_case['esperado'] == 'reemplazo':
                    if len(carrito_final) == 1:
                        print(f"   ✅ SUCCESS: Carrito reemplazado correctamente")
                        print(f"      Nueva pizza: {carrito_final[0]['pizza_nombre']} - {carrito_final[0]['tamano']}")
                    else:
                        print(f"   ❌ FAILED: Esperaba 1 pizza, encontré {len(carrito_final)}")
                
                elif test_case['esperado'] == 'agregar':
                    if len(carrito_final) > len(carrito_inicial):
                        print(f"   ✅ SUCCESS: Pizza agregada correctamente")
                        print(f"      Carrito final: {len(carrito_final)} items")
                    else:
                        print(f"   ❌ FAILED: No se agregó pizza. Items: {len(carrito_final)}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Test comprensivo completado!")
        
    except Exception as e:
        print(f"❌ Error durante el test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_session.close()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_cart_modification())
