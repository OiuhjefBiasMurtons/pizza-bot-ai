#!/usr/bin/env python3
"""
Prueba del flujo de confirmación de pedido
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database.connection import get_db
from app.services.enhanced_bot_service import EnhancedBotService
from app.models.cliente import Cliente
from app.models.pizza import Pizza

async def test_confirmation_flow():
    """Probar el flujo de confirmación de pedido"""
    
    # Obtener sesión de base de datos
    db = next(get_db())
    
    # Crear servicio
    bot_service = EnhancedBotService(db)
    
    # Número de prueba
    numero_whatsapp = "+573001234567"
    
    print("🧪 PRUEBA DEL FLUJO DE CONFIRMACIÓN")
    print("=" * 50)
    
    # Paso 1: Simular que hay un cliente registrado
    cliente = db.query(Cliente).filter(Cliente.numero_whatsapp == numero_whatsapp).first()
    if not cliente:
        cliente = Cliente(
            numero_whatsapp=numero_whatsapp,
            nombre="Andrés Test",
            direccion="Cra 73 #13a-236 apto 707"
        )
        db.add(cliente)
        db.commit()
        print(f"✅ Cliente creado: {cliente.nombre}")
    else:
        print(f"✅ Cliente encontrado: {cliente.nombre}")
    
    # Paso 2: Simular un carrito con pizzas
    carrito = [
        {
            "pizza_id": 1,
            "pizza_nombre": "Pepperoni",
            "pizza_emoji": "🍕",
            "tamano": "pequeña",
            "precio": 14.99,
            "cantidad": 2
        },
        {
            "pizza_id": 2,
            "pizza_nombre": "Margherita",
            "pizza_emoji": "🍕",
            "tamano": "grande",
            "precio": 20.99,
            "cantidad": 1
        }
    ]
    
    # Configurar el carrito en la conversación
    bot_service.set_temporary_value(numero_whatsapp, 'carrito', carrito)
    bot_service.set_temporary_value(numero_whatsapp, 'direccion', "Cra 73 #13a-236 apto 707")
    bot_service.set_conversation_state(numero_whatsapp, bot_service.ESTADOS['CONFIRMACION'])
    
    total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
    print(f"🛒 Carrito configurado con {len(carrito)} items - Total: ${total:.2f}")
    
    # Paso 3: Probar diferentes respuestas de confirmación
    test_cases = [
        ("Si", "✅ Confirmación positiva"),
        ("sí", "✅ Confirmación con acento"),
        ("no", "❌ Cancelación"),
        ("confirmar", "✅ Confirmación explícita"),
        ("cancelar", "❌ Cancelación explícita"),
        ("okay", "✅ Confirmación informal"),
        ("texto random", "❌ Respuesta no reconocida -> cancelación")
    ]
    
    print("\n🔄 PROBANDO DIFERENTES RESPUESTAS:")
    print("-" * 40)
    
    for i, (mensaje, descripcion) in enumerate(test_cases, 1):
        print(f"\n{i}. {descripcion}")
        print(f"   Usuario: '{mensaje}'")
        
        # Restaurar el estado para cada prueba
        bot_service.set_temporary_value(numero_whatsapp, 'carrito', carrito)
        bot_service.set_temporary_value(numero_whatsapp, 'direccion', "Cra 73 #13a-236 apto 707")
        bot_service.set_conversation_state(numero_whatsapp, bot_service.ESTADOS['CONFIRMACION'])
        
        try:
            respuesta = await bot_service.handle_confirmacion(numero_whatsapp, mensaje, cliente)
            print(f"   Bot: {respuesta[:100]}...")
            
            # Verificar estado después de la respuesta
            estado_final = bot_service.get_conversation_state(numero_whatsapp)
            print(f"   Estado final: {estado_final}")
            
            if "confirmado" in respuesta.lower():
                print(f"   ✅ ÉXITO: Pedido confirmado")
            elif "cancelado" in respuesta.lower():
                print(f"   ❌ CANCELADO: Pedido cancelado")
            else:
                print(f"   ⚠️  RESPUESTA INESPERADA")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    # Paso 4: Verificar que el pedido se guarde en la base de datos
    print("\n📊 VERIFICANDO PEDIDOS EN BASE DE DATOS:")
    print("-" * 40)
    
    # Restaurar estado y confirmar un pedido real
    bot_service.set_temporary_value(numero_whatsapp, 'carrito', carrito)
    bot_service.set_temporary_value(numero_whatsapp, 'direccion', "Cra 73 #13a-236 apto 707")
    bot_service.set_conversation_state(numero_whatsapp, bot_service.ESTADOS['CONFIRMACION'])
    
    respuesta_final = await bot_service.handle_confirmacion(numero_whatsapp, "sí", cliente)
    print(f"Respuesta final: {respuesta_final}")
    
    # Verificar pedidos en la base de datos
    from app.models.pedido import Pedido
    pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
    print(f"\n📦 Pedidos en la base de datos: {len(pedidos)}")
    
    if pedidos:
        ultimo_pedido = pedidos[-1]
        print(f"   - Último pedido ID: {ultimo_pedido.id}")
        print(f"   - Total: ${ultimo_pedido.total:.2f}")
        print(f"   - Estado: {ultimo_pedido.estado}")
        print(f"   - Dirección: {ultimo_pedido.direccion_entrega}")
        
        # Verificar detalles del pedido
        print(f"   - Detalles: {len(ultimo_pedido.detalles)} items")
        for detalle in ultimo_pedido.detalles:
            print(f"     • {detalle.pizza.nombre} ({detalle.tamano}) x{detalle.cantidad} - ${detalle.subtotal:.2f}")
    
    # Limpiar datos de prueba
    db.close()
    
    print("\n✅ PRUEBA COMPLETADA")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_confirmation_flow())
