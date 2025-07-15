#!/usr/bin/env python3
"""Test de debugging específico para el problema del pedido"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService
from app.models.cliente import Cliente
from app.models.pedido import Pedido

async def debug_pedido_creation():
    """Debug específico para la creación del pedido"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555debug{int(time.time() % 1000)}"
    
    print(f"🔍 DEBUG: Creación de pedido")
    print(f"📱 Número: {test_phone}")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # Registrar usuario
    await bot_service.process_message(test_phone, "hola")
    await bot_service.process_message(test_phone, "Debug User")
    await bot_service.process_message(test_phone, "Debug Street 123, Debug City")
    
    # Hacer pedido
    await bot_service.process_message(test_phone, "menu")
    await bot_service.process_message(test_phone, "1 grande")
    
    # Verificar carrito antes de confirmar
    carrito = bot_service.get_temporary_value(test_phone, 'carrito')
    print(f"🛒 Carrito antes de confirmar: {carrito}")
    
    # Confirmar pedido
    response = await bot_service.process_message(test_phone, "confirmar")
    print(f"📝 Respuesta al confirmar: {response[:100]}...")
    
    # Verificar estado
    estado = bot_service.get_conversation_state(test_phone)
    print(f"💬 Estado después de confirmar: {estado}")
    
    # Verificar si pide dirección
    if "dirección" in response.lower():
        print("✅ Pide dirección correctamente")
        
        # Confirmar dirección
        response = await bot_service.process_message(test_phone, "sí")
        print(f"📍 Respuesta al confirmar dirección: {response[:100]}...")
        
        # Verificar estado
        estado = bot_service.get_conversation_state(test_phone)
        print(f"💬 Estado después de dirección: {estado}")
        
        # Verificar datos temporales
        direccion = bot_service.get_temporary_value(test_phone, 'direccion')
        carrito = bot_service.get_temporary_value(test_phone, 'carrito')
        print(f"📍 Dirección guardada: {direccion}")
        print(f"🛒 Carrito guardado: {carrito}")
        
        if "confirmas tu pedido" in response.lower():
            print("✅ Muestra resumen del pedido")
            
            # Confirmar pedido final
            print("\n🎯 CONFIRMACIÓN FINAL")
            response = await bot_service.process_message(test_phone, "sí")
            print(f"🎉 Respuesta final: {response[:100]}...")
            
            # Verificar estado final
            estado = bot_service.get_conversation_state(test_phone)
            print(f"💬 Estado final: {estado}")
            
            # Verificar datos temporales después
            direccion = bot_service.get_temporary_value(test_phone, 'direccion')
            carrito = bot_service.get_temporary_value(test_phone, 'carrito')
            print(f"📍 Dirección después: {direccion}")
            print(f"🛒 Carrito después: {carrito}")
            
            # Verificar en base de datos
            cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == test_phone).first()
            if cliente:
                pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
                print(f"📦 Pedidos en BD: {len(pedidos)}")
                
                if pedidos:
                    pedido = pedidos[0]
                    print(f"✅ Pedido creado: #{pedido.id}")
                    print(f"   Cliente: {pedido.cliente.nombre}")
                    print(f"   Total: ${pedido.total}")
                    print(f"   Dirección: {pedido.direccion_entrega}")
                    print(f"   Detalles: {len(pedido.detalles)}")
                else:
                    print("❌ No se encontró pedido en BD")
            else:
                print("❌ Cliente no encontrado")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_pedido_creation())
