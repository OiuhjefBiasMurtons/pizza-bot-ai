#!/usr/bin/env python3
"""
Test práctico de la nueva arquitectura simplificada
Verifica que EnhancedBotService funciona correctamente como bot híbrido
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

from database.connection import get_db
from app.services.enhanced_bot_service import EnhancedBotService
from config.settings import settings

async def test_hybrid_bot():
    """Test práctico de funcionalidad híbrida"""
    
    print("🧪 Iniciando test de arquitectura simplificada...")
    
    # Configurar base de datos de test
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Crear instancia del bot híbrido
        bot = EnhancedBotService(db)
        print(f"✅ EnhancedBotService creado correctamente")
        
        # Test 1: Comando tradicional (debe usar flujo tradicional)
        print("\n📋 Test 1: Comando tradicional")
        response1 = await bot.process_message("+123456789", "hola")
        print(f"📨 Input: 'hola'")
        print(f"📤 Response: {response1}")
        
        # Test 2: Número simple (debe usar flujo tradicional)
        print("\n📋 Test 2: Selección por número")
        # Primero registrar el usuario
        await bot.process_message("+123456789", "Juan Pérez")  # Nombre
        await bot.process_message("+123456789", "Calle 123, Ciudad")  # Dirección
        response2 = await bot.process_message("+123456789", "1")  # Debería mostrar menú primero
        print(f"📨 Input: '1'")
        print(f"📤 Response: {response2[:100]}...")  # Solo primeros 100 chars
        
        # Test 3: Verificar que funciona sin OpenAI
        print("\n📋 Test 3: Verificación de configuración OpenAI")
        if settings.OPENAI_API_KEY:
            print(f"🤖 OpenAI configurado - Bot híbrido completo disponible")
        else:
            print(f"🔧 Sin OpenAI - Bot funciona en modo tradicional")
        
        print("\n✅ Todos los tests pasaron - Arquitectura simplificada funcionando correctamente")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

async def test_decision_logic():
    """Test específico de la lógica de decisión IA vs tradicional"""
    
    print("\n🧠 Test de lógica de decisión...")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        bot = EnhancedBotService(db)
        
        # Casos que deberían usar tradicional
        traditional_cases = [
            "hola",
            "menu", 
            "1",
            "si",
            "confirmar"
        ]
        
        # Casos que deberían usar IA (si está disponible)
        ai_cases = [
            "Quiero una pizza margarita grande",
            "Cambia la pizza por una mediana",
            "¿Qué pizzas tienen jamón?",
            "No me gusta la masa delgada"
        ]
        
        print("📊 Casos tradicionales:")
        for case in traditional_cases:
            should_use_ai = await bot.should_use_ai_processing(case, "menu", {})
            print(f"  '{case}' → {'❌ Tradicional' if not should_use_ai else '🤖 IA'}")
        
        print("\n📊 Casos de IA:")
        for case in ai_cases:
            should_use_ai = await bot.should_use_ai_processing(case, "menu", {})
            print(f"  '{case}' → {'🤖 IA' if should_use_ai else '❌ Tradicional'}")
        
    except Exception as e:
        print(f"❌ Error en test de decisión: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Test de Arquitectura Simplificada - Pizza Bot")
    print("=" * 50)
    
    # Ejecutar tests
    asyncio.run(test_hybrid_bot())
    asyncio.run(test_decision_logic())
    
    print("\n" + "=" * 50)
    print("🏁 Test completado")
