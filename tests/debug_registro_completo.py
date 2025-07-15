#!/usr/bin/env python3
"""Test específico para el problema de registro"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService

async def debug_registro_completo():
    """Debug para el proceso de registro completo"""
    
    db = SessionLocal()
    
    import time
    test_phone = f"+555registro{int(time.time() % 1000)}"
    
    print(f"🔍 DEBUG: Proceso de registro")
    print(f"📱 Número: {test_phone}")
    print("=" * 60)
    
    bot_service = BotService(db)
    
    # Paso 1: Inicial
    print("\n1️⃣ Mensaje inicial")
    response = await bot_service.process_message(test_phone, "hola")
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado: {estado}")
    print(f"   Respuesta: {response[:100]}...")
    
    # Paso 2: Nombre
    print("\n2️⃣ Enviar nombre")
    response = await bot_service.process_message(test_phone, "Test Usuario")
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado: {estado}")
    print(f"   Respuesta: {response[:100]}...")
    
    # Paso 3: Dirección (aquí puede estar el problema)
    print("\n3️⃣ Enviar dirección")
    direccion = "Calle Principal 123, Ciudad, CP 12345"
    response = await bot_service.process_message(test_phone, direccion)
    estado = bot_service.get_conversation_state(test_phone)
    print(f"   Estado: {estado}")
    print(f"   Respuesta: {response[:100]}...")
    
    # Verificar si el registro se completó
    if estado == "inicio":
        print("   ✅ Registro completado correctamente")
        
        # Ahora probar el menú
        print("\n4️⃣ Probar menú")
        response = await bot_service.process_message(test_phone, "menu")
        estado = bot_service.get_conversation_state(test_phone)
        print(f"   Estado: {estado}")
        print(f"   Respuesta: {response[:50]}...")
        
        if estado == "menu":
            print("   ✅ Menú funciona correctamente")
        else:
            print("   ❌ Menú no funciona")
            
    else:
        print("   ❌ Registro NO completado")
        print(f"   Estado actual: {estado}")
        
        # Intentar diferentes direcciones
        print("\n🔄 Intentando direcciones alternativas:")
        
        direcciones = [
            "Calle 456, Colonia Centro, Ciudad, CP 12345",
            "Avenida 789, Barrio Norte, Ciudad, CP 54321",
            "Carrera 123, Zona Sur, Ciudad, CP 67890"
        ]
        
        for i, dir_alt in enumerate(direcciones):
            print(f"\n   Intento {i+1}: {dir_alt}")
            response = await bot_service.process_message(test_phone, dir_alt)
            estado = bot_service.get_conversation_state(test_phone)
            print(f"   Estado: {estado}")
            
            if estado == "inicio":
                print("   ✅ Registro completado con esta dirección")
                break
            else:
                print(f"   ❌ Sigue en estado: {estado}")
                print(f"   Respuesta: {response[:100]}...")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_registro_completo())
