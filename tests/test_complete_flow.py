#!/usr/bin/env python3

"""
Test completo del flujo process_message para detectar el bug
"""

import asyncio
import sys
import os
import logging

# Configurar logging para ver los mensajes de debug
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Agregar el directorio raíz al path para poder importar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_bot_service import EnhancedBotService
from database.connection import get_db

async def test_complete_flow():
    """Test completo del flujo process_message"""
    
    # Crear una sesión de base de datos
    db = next(get_db())
    
    try:
        # Crear instancia del servicio
        enhanced_service = EnhancedBotService(db)
        
        numero_test = "+573137479005"
        mensaje = "Hola"
        
        print("🔬 EJECUTANDO FLUJO COMPLETO...")
        print("=" * 60)
        print(f"📱 Número: {numero_test}")
        print(f"💬 Mensaje: '{mensaje}'")
        print()
        
        # Ejecutar el flujo completo
        print("🏃‍♂️ Ejecutando enhanced_service.process_message()...")
        resultado = await enhanced_service.process_message(numero_test, mensaje)
        
        print(f"📨 RESULTADO: {resultado}")
        print()
        print("✅ Test completado - revisar logs arriba para ver la decisión real")
        
    except Exception as e:
        print(f"❌ ERROR durante el test: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
