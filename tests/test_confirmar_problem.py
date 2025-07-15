#!/usr/bin/env python3
"""Test específico para el problema de 'confirmar' en el pedido"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService
from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.models.conversation_state import ConversationState

async def test_confirmar_problem():
    """Test específico para el problema de 'confirmar'"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555confirm{int(time.time() % 1000)}"
    
    print(f"📱 Número de prueba: {test_phone}")
    print("🔍 Test específico para problema de 'confirmar'...")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # PASO 1: Registrar usuario
    print("\n1️⃣ REGISTRO DE USUARIO")
    await bot_service.process_message(test_phone, "hola")
    await bot_service.process_message(test_phone, "Juan Pérez")
    await bot_service.process_message(test_phone, "Calle Principal 123, Ciudad, CP 12345")
    print("   ✅ Usuario registrado")
    
    # PASO 2: Pedir menú
    print("\n2️⃣ SOLICITAR MENÚ")
    response = await bot_service.process_message(test_phone, "menu")
    print(f"   📋 Respuesta: {response[:50]}...")
    
    # Verificar estado
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   💬 Estado actual: {estado}")
    
    # PASO 3: Hacer pedido
    print("\n3️⃣ HACER PEDIDO")
    response = await bot_service.process_message(test_phone, "1 grande")
    print(f"   🍕 Respuesta: {response[:100]}...")
    
    # Verificar estado después del pedido
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   💬 Estado después del pedido: {estado}")
    
    # Verificar carrito
    carrito = bot_service.get_temporary_value(test_phone, 'carrito')
    print(f"   🛒 Carrito: {len(carrito) if carrito else 0} items")
    
    # PASO 4: CONFIRMAR (aquí está el problema)
    print("\n4️⃣ CONFIRMAR PEDIDO (PROBLEMA)")
    print("   📝 Usuario escribe: 'confirmar'")
    response = await bot_service.process_message(test_phone, "confirmar")
    print(f"   🤖 Respuesta: {response[:100]}...")
    
    # Verificar estado después de confirmar
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   💬 Estado después de confirmar: {estado}")
    
    # Verificar si aparece el mensaje de error
    if "especifica el numero de pizza" in response.lower():
        print("   ❌ ERROR: Aparece mensaje de 'especifica el numero de pizza'")
        print("   🔍 ANÁLISIS: El bot está tratando 'confirmar' como selección de pizza")
        
        # Verificar qué método se está llamando
        print("\n🔍 DEBUGGING:")
        print(f"   - Estado actual: {estado}")
        print(f"   - Mensaje enviado: 'confirmar'")
        print(f"   - Respuesta recibida: {response[:150]}...")
        
    elif "dirección" in response.lower():
        print("   ✅ CORRECTO: El bot pide dirección")
        
        # Continuar con el flujo correcto
        print("\n5️⃣ CONTINUAR FLUJO CORRECTO")
        response = await bot_service.process_message(test_phone, "sí")
        print(f"   📋 Resumen: {response[:100]}...")
        
        response = await bot_service.process_message(test_phone, "sí")
        print(f"   🎉 Confirmación: {response[:100]}...")
        
        # Verificar pedido en BD
        cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == test_phone).first()
        if cliente:
            pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
            print(f"   📦 Pedidos en BD: {len(pedidos)}")
    
    else:
        print("   ⚠️  RESPUESTA INESPERADA")
        print(f"   Respuesta completa: {response}")
    
    print("\n" + "=" * 60)
    print("🎯 RESULTADO DEL TEST")
    
    # Verificar resultado final
    if "especifica el numero de pizza" in response.lower():
        print("❌ PROBLEMA CONFIRMADO: 'confirmar' no funciona correctamente")
        print("   - El bot interpreta 'confirmar' como selección de pizza")
        print("   - No avanza al siguiente estado (DIRECCION)")
        print("   - El pedido no se crea en la base de datos")
    else:
        print("✅ PROBLEMA RESUELTO: 'confirmar' funciona correctamente")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_confirmar_problem())
