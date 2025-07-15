#!/usr/bin/env python3
"""Test paso a paso para ver dónde se pierde el carrito"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService

async def debug_carrito_loss():
    """Debug para ver dónde se pierde el carrito"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555carrito{int(time.time() % 1000)}"
    
    print(f"🔍 DEBUG: Pérdida del carrito")
    print(f"📱 Número: {test_phone}")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # Registrar usuario
    print("\n1️⃣ Registrar usuario")
    await bot_service.process_message(test_phone, "hola")
    await bot_service.process_message(test_phone, "Carrito User")
    await bot_service.process_message(test_phone, "Carrito Street 123, Carrito City")
    
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado después del registro: {estado}")
    
    # Solicitar menú
    print("\n2️⃣ Solicitar menú")
    response = await bot_service.process_message(test_phone, "menu")
    
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado después del menú: {estado}")
    
    # Hacer pedido
    print("\n3️⃣ Hacer pedido")
    response = await bot_service.process_message(test_phone, "1 grande")
    
    estado = bot_service.get_conversation_state(test_phone)
    carrito = bot_service.get_temporary_value(test_phone, 'carrito')
    print(f"   Estado después del pedido: {estado}")
    print(f"   Carrito después del pedido: {carrito}")
    
    if carrito:
        print(f"   ✅ Carrito contiene {len(carrito)} items")
        for item in carrito:
            print(f"      • {item['pizza_nombre']} - {item['tamano']}")
    else:
        print("   ❌ Carrito está vacío o es None")
    
    # Confirmar pedido
    print("\n4️⃣ Confirmar pedido")
    response = await bot_service.process_message(test_phone, "confirmar")
    
    estado = bot_service.get_conversation_state(test_phone)
    carrito = bot_service.get_temporary_value(test_phone, 'carrito')
    print(f"   Estado después de confirmar: {estado}")
    print(f"   Carrito después de confirmar: {carrito}")
    print(f"   Respuesta: {response[:100]}...")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_carrito_loss())
