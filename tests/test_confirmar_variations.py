#!/usr/bin/env python3
"""Test para diferentes variaciones de 'confirmar'"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.services.bot_service import BotService

async def test_confirmar_variations():
    """Test diferentes variaciones de 'confirmar'"""
    
    db = SessionLocal()
    
    variations = [
        "confirmar",
        "Confirmar", 
        "CONFIRMAR",
        " confirmar ",
        "confirmar.",
        "Confirmar!",
        "confirm",
        "ok",
        "si",
        "sí",
        "yes"
    ]
    
    print("🔍 Test de variaciones de 'confirmar'...")
    print("=" * 60)
    
    for i, variation in enumerate(variations):
        import time
        test_phone = f"+555var{i}{int(time.time() % 100)}"
        
        print(f"\n{i+1}️⃣ Probando: '{variation}'")
        
        bot_service = BotService(db)
        
        # Registrar usuario
        await bot_service.process_message(test_phone, "hola")
        await bot_service.process_message(test_phone, "Test User")
        await bot_service.process_message(test_phone, "Calle Test 123, Ciudad")
        
        # Hacer pedido
        await bot_service.process_message(test_phone, "menu")
        await bot_service.process_message(test_phone, "1 grande")
        
        # Probar variación de confirmar
        response = await bot_service.process_message(test_phone, variation)
        
        # Verificar resultado
        if "dirección" in response.lower():
            print(f"   ✅ FUNCIONA: '{variation}' → Pide dirección")
        elif "especifica el numero de pizza" in response.lower():
            print(f"   ❌ FALLA: '{variation}' → Pide número de pizza")
        else:
            print(f"   ⚠️  OTRO: '{variation}' → {response[:50]}...")
    
    print("\n" + "=" * 60)
    print("🎯 Todas las variaciones deberían funcionar correctamente")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_confirmar_variations())
