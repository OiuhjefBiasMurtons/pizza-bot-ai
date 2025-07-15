#!/usr/bin/env python3
"""Debug específico para el problema de 'andre philips'"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from app.services.bot_service import BotService
from app.models.cliente import Cliente

def debug_name_validation():
    """Debug de la validación de nombres"""
    
    test_names = [
        "andre philips",
        "Andre Philips", 
        "Andrew Philips",
        "Juan Pérez",
        "María González"
    ]
    
    print("🔍 Debug de validación de nombres:")
    print("=" * 50)
    
    for nombre in test_names:
        print(f"\n📝 Testing: '{nombre}'")
        nombre_limpio = nombre.strip()
        palabras = nombre_limpio.split()
        
        print(f"   - Longitud: {len(nombre_limpio)}")
        print(f"   - Palabras: {palabras}")
        print(f"   - Cantidad palabras: {len(palabras)}")
        
        # Test cada palabra
        for i, palabra in enumerate(palabras):
            sin_guion = palabra.replace('-', '')
            es_alpha = sin_guion.isalpha()
            print(f"   - Palabra {i+1}: '{palabra}' -> sin guión: '{sin_guion}' -> isalpha(): {es_alpha}")
        
        # Test validación completa
        validacion_alpha = all(palabra.replace('-', '').isalpha() for palabra in palabras)
        print(f"   - Validación completa: {validacion_alpha}")
        
        # Condiciones finales
        longitud_ok = len(nombre_limpio) >= 2
        palabras_ok = len(palabras) >= 2
        letras_ok = validacion_alpha
        
        print(f"   - Longitud OK: {longitud_ok}")
        print(f"   - Palabras OK: {palabras_ok}")
        print(f"   - Letras OK: {letras_ok}")
        print(f"   - RESULTADO: {'✅ VÁLIDO' if (longitud_ok and palabras_ok and letras_ok) else '❌ INVÁLIDO'}")

async def test_specific_name():
    """Test específico para 'andre philips'"""
    
    db = SessionLocal()
    bot_service = BotService(db)
    
    import time
    test_phone = f"+555999888{int(time.time() % 1000)}"
    
    print(f"\n📱 Usando número: {test_phone}")
    print("🧪 Test específico para 'andre philips'...")
    print("=" * 50)
    
    # Iniciar proceso
    print("\n1. 👤 Iniciando proceso:")
    response = await bot_service.process_message(test_phone, "hola")
    print(f"Bot: {response}")
    
    # Probar el nombre problemático
    print("\n2. 📝 Enviando 'andre philips':")
    response = await bot_service.process_message(test_phone, "andre philips")
    print(f"Bot: {response}")
    
    # Verificar base de datos
    print("\n3. 🔍 Verificando base de datos:")
    user = db.query(Cliente).filter(Cliente.numero_whatsapp == test_phone).first()
    if user:
        print(f"   - Usuario existe: {user.numero_whatsapp}")
        print(f"   - Nombre: '{user.nombre}'")
        print(f"   - Dirección: '{user.direccion}'")
    else:
        print("   - Usuario no encontrado")
    
    db.close()

if __name__ == "__main__":
    debug_name_validation()
    asyncio.run(test_specific_name())
