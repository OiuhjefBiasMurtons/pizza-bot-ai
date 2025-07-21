#!/usr/bin/env python3
"""
Test específico para el problema reportado:
"Dame una de pepperoni" → Bot reinicia en lugar de preguntar tamaño
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

from database.connection import get_db
from app.services.enhanced_bot_service import EnhancedBotService
from app.models.pizza import Pizza
from app.models.cliente import Cliente

async def test_incomplete_pizza_request():
    """Test del caso específico reportado"""
    
    print("🧪 Test: Pedido incompleto de pizza")
    print("=" * 50)
    
    # Configurar base de datos de test
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Crear bot híbrido
        bot = EnhancedBotService(db)
        
        # Crear pizzas de prueba
        pizza_pepperoni = Pizza(
            nombre="Pepperoni",
            descripcion="Pepperoni y mozzarella",
            precio_pequena=14.99,
            precio_mediana=18.99,
            precio_grande=22.99,
            disponible=True,
            emoji="🍕"
        )
        
        pizza_carnivora = Pizza(
            nombre="Carnívora",
            descripcion="Pepperoni, salchicha y jamón",
            precio_pequena=16.99,
            precio_mediana=20.99,
            precio_grande=24.99,
            disponible=True,
            emoji="🥩"
        )
        
        db.add(pizza_pepperoni)
        db.add(pizza_carnivora)
        db.commit()
        
        # Crear cliente de prueba (usar número único)
        import time
        unique_phone = f"+123456{int(time.time() % 10000)}"
        
        cliente = Cliente(
            numero_whatsapp=unique_phone,
            nombre="Andrés",
            direccion="Calle Test 123"
        )
        db.add(cliente)
        db.commit()
        
        test_phone = unique_phone
        
        print("✅ Datos de test creados")
        
        # STEP 1: Cliente pregunta qué pizzas tienen pepperoni
        print(f"\n📱 Usuario pregunta: '¿Qué pizzas tienen pepperoni?'")
        response1 = await bot.process_message(test_phone, "¿Qué pizzas tienen pepperoni?")
        print(f"🤖 Bot responde: {response1[:200]}...")
        
        # STEP 2: El problema - usuario dice "Dame una de pepperoni" sin tamaño
        print(f"\n📱 Usuario responde: 'Dame una de pepperoni'")
        response2 = await bot.process_message(test_phone, "Dame una de pepperoni")
        print(f"🤖 Bot responde: {response2[:200]}...")
        
        # Verificar estado actual
        estado = bot.get_conversation_state(test_phone)
        print(f"📊 Estado actual: {estado}")
        
        # Verificar contexto de conversación
        contexto = bot.get_conversation_context(test_phone)
        print(f"📋 Contexto: {contexto}")
        
        # Verificar si hay carrito temporal
        carrito = bot.get_temporary_value(test_phone, 'carrito')
        print(f"🛒 Carrito: {carrito}")
        
        # Análisis del problema
        print(f"\n🔍 ANÁLISIS:")
        if "Hola andres" in response2.lower() or "que te gustaria ordenar" in response2.lower():
            print("❌ PROBLEMA CONFIRMADO: Bot reinicia conversación")
            print("   Debería preguntar por el tamaño de la pizza")
        else:
            print("✅ Bot manejó correctamente la solicitud incompleta")
        
        # Test de detección de IA
        should_use_ai = await bot.should_use_ai_processing("Dame una de pepperoni", estado, contexto)
        print(f"🧠 ¿Debería usar IA?: {should_use_ai}")
        
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpiar datos de test
        db.query(Pizza).delete()
        db.query(Cliente).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    asyncio.run(test_incomplete_pizza_request())
