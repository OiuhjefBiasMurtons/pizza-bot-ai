#!/usr/bin/env python3
"""
Test simple para depurar el problema de registro
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.services.bot_service_refactored import BotService

# Configurar base de datos de prueba
DATABASE_URL = "sqlite:///./test_debug.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas
Cliente.metadata.create_all(bind=engine)

async def test_debug():
    """
    Test de depuración
    """
    print("🔍 DEPURANDO PROBLEMA DE REGISTRO")
    
    db = SessionLocal()
    bot_service = BotService(db)
    test_phone = "+debug"
    
    # Limpiar datos previos
    from app.models.conversation_state import ConversationState
    
    db.query(ConversationState).filter(ConversationState.numero_whatsapp == test_phone).delete()
    db.query(Cliente).filter(Cliente.numero_whatsapp == test_phone).delete()
    db.query(Pizza).delete()
    db.commit()
    
    # Crear pizzas de prueba
    pizzas = [
        Pizza(
            nombre="Margherita",
            descripcion="Tomate, mozzarella y albahaca",
            precio_pequena=12.99,
            precio_mediana=16.99,
            precio_grande=20.99,
            disponible=True,
            emoji="🍕"
        ),
        Pizza(
            nombre="Pepperoni",
            descripcion="Pepperoni y mozzarella",
            precio_pequena=14.99,
            precio_mediana=18.99,
            precio_grande=22.99,
            disponible=True,
            emoji="🍕"
        )
    ]
    
    for pizza in pizzas:
        db.add(pizza)
    db.commit()
    
    print("✅ Pizzas creadas")
    
    try:
        # Verificar estado inicial
        cliente = bot_service.get_cliente(test_phone)
        estado = bot_service.get_conversation_state(test_phone)
        print(f"Estado inicial: {estado}, Cliente: {cliente}")
        
        # Test registro paso a paso
        print("\n1. Primer mensaje:")
        response1 = await bot_service.process_message(test_phone, "hola")
        print(f"✅ Respuesta: {response1}")
        
        # Verificar estado después del primer mensaje
        estado_after = bot_service.get_conversation_state(test_phone)
        print(f"Estado después de 'hola': {estado_after}")
        
        print("\n2. Enviar nombre:")
        response2 = await bot_service.process_message(test_phone, "Juan Pérez")
        print(f"✅ Respuesta: {response2}")
        
        # Verificar estado después del nombre
        estado_after_name = bot_service.get_conversation_state(test_phone)
        print(f"Estado después del nombre: {estado_after_name}")
        
        print("\n3. Enviar dirección:")
        response3 = await bot_service.process_message(test_phone, "Calle 123, Ciudad")
        print(f"✅ Respuesta: {response3}")
        
        # Verificar estado y cliente después de completar registro
        cliente_final = bot_service.get_cliente(test_phone)
        estado_final = bot_service.get_conversation_state(test_phone)
        print(f"Estado final: {estado_final}, Cliente completo: {bot_service._is_user_complete(cliente_final)}")
        
        print("\n4. Comando menu:")
        response4 = await bot_service.process_message(test_phone, "menu")
        print(f"✅ Respuesta: {response4[:200]}...")
        
        print("\n5. Seleccionar pizza '1 mediana':")
        response5 = await bot_service.process_message(test_phone, "1 mediana")
        print(f"✅ Respuesta: {response5[:200]}...")
        
        print("\n6. Múltiples pizzas '1 grande, 2 pequeña':")
        response6 = await bot_service.process_message(test_phone, "1 grande, 2 pequeña")
        print(f"✅ Respuesta: {response6[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_debug())
