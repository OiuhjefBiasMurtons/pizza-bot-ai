#!/usr/bin/env python3
"""Debug detallado del flujo de registro"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from app.services.bot_service import BotService
from app.models.cliente import Cliente

async def debug_registration_flow():
    """Debug paso a paso del flujo de registro"""
    
    db = SessionLocal()
    bot_service = BotService(db)
    
    import time
    test_phone = f"+555777666{int(time.time() % 1000)}"
    
    print(f"📱 Usando número: {test_phone}")
    print("🔍 Debug detallado del flujo de registro...")
    print("=" * 60)
    
    # Paso 1: Primer mensaje
    print("\n1️⃣ PRIMER MENSAJE: 'hola'")
    print("   Verificando estado antes:")
    cliente = bot_service.get_cliente(test_phone)
    estado = bot_service.conversaciones.get(test_phone, 'ninguno')
    print(f"   - Cliente: {cliente}")
    print(f"   - Estado: {estado}")
    
    response = await bot_service.process_message(test_phone, "hola")
    print(f"   Bot response: {response[:100]}...")
    
    print("   Verificando estado después:")
    cliente = bot_service.get_cliente(test_phone)
    estado = bot_service.conversaciones.get(test_phone, 'ninguno')
    print(f"   - Cliente: {cliente}")
    print(f"   - Cliente.nombre: {cliente.nombre if cliente else 'N/A'}")
    print(f"   - Cliente.direccion: {cliente.direccion if cliente else 'N/A'}")
    print(f"   - Estado: {estado}")
    
    # Paso 2: Enviar nombre
    print("\n2️⃣ SEGUNDO MENSAJE: 'andre philips'")
    print("   Verificando estado antes:")
    cliente = bot_service.get_cliente(test_phone)
    estado = bot_service.conversaciones.get(test_phone, 'ninguno')
    print(f"   - Cliente: {cliente}")
    print(f"   - Cliente.nombre: {cliente.nombre if cliente else 'N/A'}")
    print(f"   - Cliente.direccion: {cliente.direccion if cliente else 'N/A'}")
    print(f"   - Estado: {estado}")
    
    response = await bot_service.process_message(test_phone, "andre philips")
    print(f"   Bot response: {response[:100]}...")
    
    print("   Verificando estado después:")
    cliente = bot_service.get_cliente(test_phone)
    estado = bot_service.conversaciones.get(test_phone, 'ninguno')
    print(f"   - Cliente: {cliente}")
    print(f"   - Cliente.nombre: {cliente.nombre if cliente else 'N/A'}")
    print(f"   - Cliente.direccion: {cliente.direccion if cliente else 'N/A'}")
    print(f"   - Estado: {estado}")
    
    # Paso 3: Enviar dirección
    print("\n3️⃣ TERCER MENSAJE: 'Calle 123, Ciudad, CP 12345'")
    print("   Verificando estado antes:")
    cliente = bot_service.get_cliente(test_phone)
    estado = bot_service.conversaciones.get(test_phone, 'ninguno')
    print(f"   - Cliente: {cliente}")
    print(f"   - Cliente.nombre: {cliente.nombre if cliente else 'N/A'}")
    print(f"   - Cliente.direccion: {cliente.direccion if cliente else 'N/A'}")
    print(f"   - Estado: {estado}")
    
    response = await bot_service.process_message(test_phone, "Calle 123, Ciudad, CP 12345")
    print(f"   Bot response: {response[:100]}...")
    
    print("   Verificando estado después:")
    cliente = bot_service.get_cliente(test_phone)
    estado = bot_service.conversaciones.get(test_phone, 'ninguno')
    print(f"   - Cliente: {cliente}")
    print(f"   - Cliente.nombre: {cliente.nombre if cliente else 'N/A'}")
    print(f"   - Cliente.direccion: {cliente.direccion if cliente else 'N/A'}")
    print(f"   - Estado: {estado}")
    
    print("\n" + "=" * 60)
    print("🎉 Debug completado!")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_registration_flow())
