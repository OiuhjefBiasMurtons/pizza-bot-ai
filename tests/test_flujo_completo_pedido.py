#!/usr/bin/env python3
"""Test del flujo completo de pedido para verificar creación en BD"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService

async def test_flujo_completo_pedido():
    """Test completo del flujo de pedido hasta la creación en BD"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555pedido{int(time.time() % 1000)}"
    
    print(f"🎯 TEST: Flujo completo de pedido")
    print(f"📱 Número: {test_phone}")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # Registro completo
    print("\n🔧 SETUP: Registro completo")
    await bot_service.process_message(test_phone, "hola")
    await bot_service.process_message(test_phone, "Juan Pérez")
    response = await bot_service.process_message(test_phone, "Calle 123, Colonia Centro, Ciudad, CP 12345")
    print(f"   Estado después del registro: {bot_service.get_conversation_state(test_phone)}")
    
    # Menú
    print("\n1️⃣ PASO 1: Solicitar menú")
    response = await bot_service.process_message(test_phone, "menu")
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado: {estado}")
    
    # Hacer pedido
    print("\n2️⃣ PASO 2: Hacer pedido")
    response = await bot_service.process_message(test_phone, "1 mediana")
    estado = bot_service.get_conversation_state(test_phone)
    carrito = bot_service.get_temporary_value(test_phone, 'carrito')
    print(f"   Estado: {estado}")
    print(f"   Carrito: {carrito}")
    
    # Confirmar pedido
    print("\n3️⃣ PASO 3: Confirmar pedido")
    response = await bot_service.process_message(test_phone, "confirmar")
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado: {estado}")
    print(f"   Respuesta: {response[:100]}...")
    
    # Confirmar dirección
    print("\n4️⃣ PASO 4: Confirmar dirección")
    response = await bot_service.process_message(test_phone, "si")
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado: {estado}")
    print(f"   Respuesta: {response[:100]}...")
    
    # Confirmar pedido final
    print("\n5️⃣ PASO 5: Confirmar pedido final")
    response = await bot_service.process_message(test_phone, "si")
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado: {estado}")
    print(f"   Respuesta: {response[:100]}...")
    
    # Verificar pedido en BD
    print("\n6️⃣ PASO 6: Verificar pedido en BD")
    cliente = bot_service.get_cliente(test_phone)
    if cliente:
        from app.models.pedido import Pedido
        pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
        print(f"   Pedidos en BD: {len(pedidos)}")
        for pedido in pedidos:
            print(f"   - Pedido {pedido.id}: {pedido.estado}")
            print(f"     Dirección: {pedido.direccion_entrega}")
            print(f"     Total: ${pedido.total}")
    else:
        print("   ❌ Cliente no encontrado")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_flujo_completo_pedido())
