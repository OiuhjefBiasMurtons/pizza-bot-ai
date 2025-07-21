#!/usr/bin/env python3
"""
Test de flujo completo - Simulación real del problema solucionado
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from database.connection import get_db
from app.services.enhanced_bot_service import EnhancedBotService

async def test_fixed_flow():
    """Test del flujo completo solucionado"""
    
    print("🎉 Test: Flujo solucionado - Dame una de pepperoni")
    print("=" * 60)
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        bot = EnhancedBotService(db)
        
        # Usar número de test existente (cliente ya registrado)
        test_phone = "+1234567890"  # Cliente de prueba existente
        
        print("📱 Simulación del flujo reportado:")
        print("1. Usuario pregunta sobre pizzas con pepperoni")
        print("2. Bot muestra pizzas con pepperoni")
        print("3. Usuario dice: 'Dame una de pepperoni' (SIN tamaño)")
        print()
        
        # STEP 1: Pregunta inicial
        response1 = await bot.process_message(test_phone, "¿Qué pizzas tienen pepperoni?")
        print(f"🤖 Bot: {response1[:150]}...\n")
        
        # STEP 2: El mensaje problemático
        print("🔥 MOMENTO CRÍTICO - Usuario dice: 'Dame una de pepperoni'")
        response2 = await bot.process_message(test_phone, "Dame una de pepperoni")
        print(f"🤖 Bot: {response2[:200]}...")
        
        # Verificar que no sea el mensaje de bienvenida
        if "Hola" in response2 and "¿Qué te gustaría ordenar hoy?" in response2:
            print("\n❌ PROBLEMA AÚN EXISTE: Bot reinicia conversación")
        else:
            print("\n✅ PROBLEMA SOLUCIONADO: Bot maneja correctamente la solicitud")
            
            # STEP 3: Continuar el flujo - selección de tamaño
            if "tamaño" in response2.lower() or "precio" in response2.lower():
                print("\n📏 Usuario selecciona tamaño: 'grande'")
                response3 = await bot.process_message(test_phone, "grande")
                print(f"🤖 Bot: {response3[:150]}...")
                
                if "agregado" in response3.lower() or "carrito" in response3.lower():
                    print("\n🎉 FLUJO COMPLETO EXITOSO!")
                    print("   ✅ Detectó solicitud parcial")
                    print("   ✅ Preguntó por tamaño")
                    print("   ✅ Agregó pizza al carrito")
                else:
                    print("\n⚠️  Problema en paso final")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_fixed_flow())
