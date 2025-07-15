#!/usr/bin/env python3
"""Test para verificar el nuevo flujo de direcciones"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService

async def test_direccion_registrada():
    """Test del nuevo flujo con dirección registrada"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555direccion{int(time.time() % 1000)}"
    
    print(f"🏠 TEST: Flujo con dirección registrada")
    print(f"📱 Número: {test_phone}")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # Registro completo
    print("\n🔧 SETUP: Registro completo")
    await bot_service.process_message(test_phone, "hola")
    await bot_service.process_message(test_phone, "María García")
    direccion_registrada = "Avenida Principal 456, Colonia Roma, Ciudad, CP 54321"
    await bot_service.process_message(test_phone, direccion_registrada)
    
    cliente = bot_service.get_cliente(test_phone)
    print(f"   ✅ Cliente registrado: {cliente.nombre}")
    print(f"   ✅ Dirección registrada: {cliente.direccion}")
    
    # Hacer pedido
    print("\n1️⃣ HACER PEDIDO")
    await bot_service.process_message(test_phone, "menu")
    await bot_service.process_message(test_phone, "1 grande")
    
    # Confirmar pedido - aquí debería mostrar la dirección registrada
    print("\n2️⃣ CONFIRMAR PEDIDO (mostrar dirección registrada)")
    response = await bot_service.process_message(test_phone, "confirmar")
    print(f"   📱 Respuesta del bot:")
    print(f"   {response}")
    
    # Verificar que muestra la dirección registrada
    if direccion_registrada in response:
        print("   ✅ CORRECTO: Muestra la dirección registrada")
    else:
        print("   ❌ ERROR: No muestra la dirección registrada")
    
    # Confirmar usar la dirección registrada
    print("\n3️⃣ CONFIRMAR USAR DIRECCIÓN REGISTRADA")
    response = await bot_service.process_message(test_phone, "sí")
    print(f"   📱 Respuesta del bot:")
    print(f"   {response[:150]}...")
    
    # Verificar que va al resumen
    if "RESUMEN DEL PEDIDO" in response:
        print("   ✅ CORRECTO: Va al resumen del pedido")
    else:
        print("   ❌ ERROR: No va al resumen")
    
    # Confirmar pedido final
    print("\n4️⃣ CONFIRMAR PEDIDO FINAL")
    response = await bot_service.process_message(test_phone, "sí")
    print(f"   📱 Respuesta del bot:")
    print(f"   {response[:100]}...")
    
    # Verificar pedido en BD
    if "Pedido confirmado" in response:
        print("   ✅ CORRECTO: Pedido confirmado")
        
        # Verificar que usó la dirección registrada
        from app.models.pedido import Pedido
        pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
        if pedidos:
            pedido = pedidos[0]
            print(f"   📍 Dirección del pedido: {pedido.direccion_entrega}")
            if str(pedido.direccion_entrega) == direccion_registrada:
                print("   ✅ CORRECTO: Usó la dirección registrada")
            else:
                print("   ❌ ERROR: No usó la dirección registrada")
    else:
        print("   ❌ ERROR: Pedido no confirmado")
    
    print("\n" + "=" * 60)
    print("✨ Test completado")
    
    db.close()

async def test_cambiar_direccion():
    """Test para cambiar dirección"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555cambiar{int(time.time() % 1000)}"
    
    print(f"\n🔄 TEST: Cambiar dirección")
    print(f"📱 Número: {test_phone}")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # Registro completo
    print("\n🔧 SETUP: Registro completo")
    await bot_service.process_message(test_phone, "hola")
    await bot_service.process_message(test_phone, "Carlos López")
    direccion_registrada = "Calle Antigua 123, Barrio Viejo, Ciudad, CP 12345"
    await bot_service.process_message(test_phone, direccion_registrada)
    
    # Hacer pedido
    await bot_service.process_message(test_phone, "menu")
    await bot_service.process_message(test_phone, "2 mediana")
    
    # Confirmar pedido
    print("\n1️⃣ CONFIRMAR PEDIDO")
    response = await bot_service.process_message(test_phone, "confirmar")
    print(f"   📱 Respuesta: {response[:100]}...")
    
    # Decir NO para cambiar dirección
    print("\n2️⃣ DECIR NO PARA CAMBIAR DIRECCIÓN")
    response = await bot_service.process_message(test_phone, "no")
    print(f"   📱 Respuesta: {response[:100]}...")
    
    # Verificar que pide nueva dirección
    if "nueva dirección" in response:
        print("   ✅ CORRECTO: Pide nueva dirección")
    else:
        print("   ❌ ERROR: No pide nueva dirección")
    
    # Proporcionar nueva dirección
    print("\n3️⃣ PROPORCIONAR NUEVA DIRECCIÓN")
    nueva_direccion = "Avenida Nueva 789, Colonia Moderna, Ciudad, CP 67890"
    response = await bot_service.process_message(test_phone, nueva_direccion)
    print(f"   📱 Respuesta: {response[:100]}...")
    
    # Verificar que va al resumen con nueva dirección
    if "RESUMEN DEL PEDIDO" in response and nueva_direccion in response:
        print("   ✅ CORRECTO: Usa la nueva dirección")
    else:
        print("   ❌ ERROR: No usa la nueva dirección")
    
    print("\n" + "=" * 60)
    print("✨ Test completado")
    
    db.close()

async def main():
    """Ejecutar todos los tests"""
    await test_direccion_registrada()
    await test_cambiar_direccion()

if __name__ == "__main__":
    asyncio.run(main())
