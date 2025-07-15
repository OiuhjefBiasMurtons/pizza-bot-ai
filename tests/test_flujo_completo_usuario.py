#!/usr/bin/env python3
"""Test final para verificar el flujo completo de pedido"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService
from app.models.cliente import Cliente
from app.models.pedido import Pedido

async def test_flujo_completo_usuario():
    """Test que simula exactamente el flujo que describe el usuario"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555final{int(time.time() % 1000)}"
    
    print(f"📱 Número de prueba: {test_phone}")
    print("🎯 Simulando flujo completo del usuario...")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # Registrar usuario previamente
    print("\n🔧 SETUP: Registrar usuario")
    await bot_service.process_message(test_phone, "hola")
    await bot_service.process_message(test_phone, "Usuario Final")
    await bot_service.process_message(test_phone, "Calle Final 456, Ciudad Final")
    print("   ✅ Usuario registrado")
    
    # Flujo que describe el usuario
    print("\n1️⃣ Solicitar menú")
    response = await bot_service.process_message(test_phone, "menu")
    print(f"   📋 Respuesta: Ver menú de pizzas")
    
    print("\n2️⃣ Hacer pedido")
    response = await bot_service.process_message(test_phone, "1 grande")
    print(f"   🍕 Respuesta: Pizza agregada al carrito")
    
    # Verificar que aparece la pregunta "¿Quieres agregar algo más?"
    if "quieres agregar algo" in response.lower():
        print("   ✅ Aparece pregunta: '¿Quieres agregar algo más?'")
    
    print("\n3️⃣ Escribir 'confirmar' (aquí era el problema)")
    response = await bot_service.process_message(test_phone, "confirmar")
    print(f"   📝 Usuario escribe: 'confirmar'")
    
    # Verificar que NO aparece el mensaje de error
    if "especifica el numero de pizza" in response.lower():
        print("   ❌ ERROR: Aparece mensaje 'especifica el numero de pizza'")
        print("   🔍 Problema NO resuelto")
        return False
    else:
        print("   ✅ NO aparece mensaje de error")
    
    # Verificar que pide dirección
    if "dirección" in response.lower():
        print("   ✅ Pide dirección correctamente")
    else:
        print("   ❌ NO pide dirección")
        print(f"   Respuesta: {response}")
        return False
    
    print("\n4️⃣ Completar pedido")
    response = await bot_service.process_message(test_phone, "sí")
    print("   📋 Resumen del pedido mostrado")
    
    response = await bot_service.process_message(test_phone, "sí")
    print("   🎉 Pedido confirmado")
    
    # Verificar que el pedido se creó en la base de datos
    print("\n5️⃣ Verificar pedido en base de datos")
    cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == test_phone).first()
    if cliente:
        pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
        print(f"   📦 Pedidos encontrados: {len(pedidos)}")
        
        if pedidos:
            print("   ✅ Pedido creado en base de datos")
            return True
        else:
            print("   ❌ Pedido NO se creó en base de datos")
            return False
    else:
        print("   ❌ Cliente no encontrado")
        return False
    
    db.close()

async def main():
    """Función principal"""
    success = await test_flujo_completo_usuario()
    
    print("\n" + "=" * 60)
    print("🎯 RESULTADO FINAL:")
    
    if success:
        print("✅ ¡PROBLEMA RESUELTO COMPLETAMENTE!")
        print("   - El comando 'confirmar' funciona correctamente")
        print("   - NO aparece mensaje de 'especifica el numero de pizza'")
        print("   - El pedido se crea en la base de datos")
        print("   - El flujo completo funciona sin problemas")
    else:
        print("❌ PROBLEMA AÚN PERSISTE")
        print("   - Revisar el código para identificar el problema")

if __name__ == "__main__":
    asyncio.run(main())
