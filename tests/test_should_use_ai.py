#!/usr/bin/env python3

"""
Test rápido para verificar la lógica should_use_ai_processing
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path para poder importar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_bot_service import EnhancedBotService
from database.connection import get_db

async def test_should_use_ai():
    """Test de la función should_use_ai_processing"""
    
    # Crear una sesión de base de datos
    db = next(get_db())
    
    try:
        # Crear instancia del servicio
        enhanced_service = EnhancedBotService(db)
        
        # Casos de prueba
        test_cases = [
            {"mensaje": "Hola", "estado": "finalizado", "expected": False, "description": "Saludo básico"},
            {"mensaje": "HOLA", "estado": "inicio", "expected": False, "description": "Saludo en mayúsculas"},
            {"mensaje": "hola", "estado": "inicio", "expected": False, "description": "Saludo en minúsculas"},
            {"mensaje": "buenas", "estado": "inicio", "expected": False, "description": "Saludo informal"},
            {"mensaje": "menu", "estado": "inicio", "expected": False, "description": "Comando menú"},
            {"mensaje": "si", "estado": "confirmacion", "expected": False, "description": "Confirmación simple"},
            {"mensaje": "Así está bien", "estado": "pedido", "expected": True, "description": "Confirmación compleja"},
            {"mensaje": "Solo quiero la pepperoni grande", "estado": "pedido", "expected": True, "description": "Modificación compleja"},
            {"mensaje": "1", "estado": "menu", "expected": False, "description": "Número en menú"},
            {"mensaje": "Quiero pizza", "estado": "inicio", "expected": True, "description": "Lenguaje natural"},
        ]
        
        print("🧪 Iniciando tests de should_use_ai_processing...")
        print("=" * 60)
        
        for i, test_case in enumerate(test_cases, 1):
            mensaje = test_case["mensaje"]
            estado = test_case["estado"]
            expected = test_case["expected"]
            description = test_case["description"]
            
            # Ejecutar la función
            resultado = await enhanced_service.should_use_ai_processing(mensaje, estado, {})
            
            # Verificar resultado
            status = "✅ PASS" if resultado == expected else "❌ FAIL"
            ai_method = "IA" if resultado else "Tradicional"
            expected_method = "IA" if expected else "Tradicional"
            
            print(f"{i:2d}. {status} {description}")
            print(f"    Mensaje: '{mensaje}' (estado: {estado})")
            print(f"    Resultado: {ai_method} | Esperado: {expected_method}")
            if resultado != expected:
                print(f"    ⚠️  ERROR: Se esperaba {expected_method} pero se obtuvo {ai_method}")
            print()
        
        print("🏁 Tests completados!")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_should_use_ai())
