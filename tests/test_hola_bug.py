#!/usr/bin/env python3

"""
Test específico para simular el escenario del bug reportado
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path para poder importar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.enhanced_bot_service import EnhancedBotService
from database.connection import get_db
from app.models.cliente import Cliente
from datetime import datetime

async def test_hola_finalizado_scenario():
    """Test específico para el escenario: cliente registrado, estado finalizado, mensaje 'Hola'"""
    
    # Crear una sesión de base de datos
    db = next(get_db())
    
    try:
        # Crear instancia del servicio
        enhanced_service = EnhancedBotService(db)
        
        # Simular un cliente registrado
        numero_test = "+573137479005"
        
        print("🔬 Simulando escenario específico del bug...")
        print("=" * 60)
        print(f"📱 Número: {numero_test}")
        print(f"💬 Mensaje: 'Hola'")
        print(f"📊 Estado esperado: finalizado")
        print()
        
        # Verificar si el cliente existe en la BD
        cliente = enhanced_service.get_cliente(numero_test)
        if cliente:
            print(f"👤 Cliente encontrado: {cliente.nombre}")
            print(f"📍 Dirección: {cliente.direccion}")
            print(f"✅ Cliente registrado: {cliente.nombre is not None and cliente.direccion is not None}")
        else:
            print("👤 Cliente no encontrado en BD")
            
        # Obtener estado actual
        estado_actual = enhanced_service.get_conversation_state(numero_test)
        print(f"📊 Estado actual: {estado_actual}")
        
        # Obtener contexto
        contexto = enhanced_service.get_conversation_context(numero_test)
        print(f"🔍 Contexto: {contexto}")
        print()
        
        # Test 1: Verificar should_use_ai_processing
        should_use_ai = await enhanced_service.should_use_ai_processing("Hola", estado_actual, contexto)
        print(f"🤖 should_use_ai_processing('Hola', '{estado_actual}') = {should_use_ai}")
        
        # Test 2: Verificar condición de cliente registrado
        cliente_registrado = cliente and cliente.nombre is not None and cliente.direccion is not None
        print(f"👤 Cliente registrado: {cliente_registrado}")
        
        # Test 3: Simular el flujo completo
        print("\n🏃‍♂️ Simulando flujo completo de process_message...")
        
        if not cliente_registrado:
            print("   → Iría a handle_registration_flow (flujo tradicional)")
        else:
            print("   → Cliente registrado, verificando should_use_ai...")
            if should_use_ai:
                print("   → IRÍA A IA ❌")
            else:
                print("   → IRÍA A FLUJO TRADICIONAL ✅")
                print("   → Llamaría a process_with_traditional_flow")
                print("   → Detectaría 'hola' como comando especial")
                print("   → Llamaría a handle_registered_greeting")
        
        print("\n🎯 ANÁLISIS:")
        if not cliente_registrado:
            print("   ✅ El flujo es correcto (registro)")
        elif not should_use_ai:
            print("   ✅ El flujo es correcto (tradicional)")
        else:
            print("   ❌ PROBLEMA DETECTADO: debería ir a flujo tradicional")
            print("   🔧 La función should_use_ai_processing está retornando True incorrectamente")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_hola_finalizado_scenario())
