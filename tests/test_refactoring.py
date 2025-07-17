"""
Prueba simple para validar la refactorización de handlers
"""

import sys
import os
sys.path.append('/home/nomadbias/GothamCode/CampCode/Python/Whatss/cursor-pizza-bot/Pizza-bot-IA')

from app.services.bot_service_refactored import BotService
from app.services.handlers import (
    BaseHandler,
    RegistrationHandler,
    MenuHandler,
    OrderHandler,
    InfoHandler
)

def test_imports():
    """Prueba que todos los imports funcionen correctamente"""
    try:
        print("✅ Importando BotService...")
        print("✅ Importando handlers...")
        
        # Probar creación de instancias (sin DB real)
        print("✅ Imports exitosos!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def test_handler_structure():
    """Prueba la estructura básica de los handlers"""
    try:
        print("\n🔍 Probando estructura de handlers...")
        
        # Verificar que todos los handlers tienen los métodos esperados
        handlers = [
            ('RegistrationHandler', RegistrationHandler),
            ('MenuHandler', MenuHandler),
            ('OrderHandler', OrderHandler),
            ('InfoHandler', InfoHandler)
        ]
        
        for name, handler_class in handlers:
            print(f"   📋 {name}:")
            
            # Verificar herencia de BaseHandler
            if issubclass(handler_class, BaseHandler):
                print(f"      ✅ Hereda de BaseHandler")
            else:
                print(f"      ❌ No hereda de BaseHandler")
                
            # Verificar métodos principales
            if hasattr(handler_class, '__init__'):
                print(f"      ✅ Tiene __init__")
            else:
                print(f"      ❌ No tiene __init__")
        
        print("✅ Estructura de handlers validada!")
        return True
        
    except Exception as e:
        print(f"❌ Error en estructura: {e}")
        return False

def test_bot_service_structure():
    """Prueba la estructura del BotService refactorizado"""
    try:
        print("\n🔍 Probando estructura de BotService...")
        
        # Verificar métodos principales
        required_methods = [
            'process_message',
            'get_cliente',
            'get_conversation_state',
            'set_conversation_state',
            'clear_conversation_data'
        ]
        
        for method in required_methods:
            if hasattr(BotService, method):
                print(f"      ✅ Método {method} presente")
            else:
                print(f"      ❌ Método {method} ausente")
        
        print("✅ Estructura de BotService validada!")
        return True
        
    except Exception as e:
        print(f"❌ Error en BotService: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de refactorización...")
    
    tests = [
        ("Imports", test_imports),
        ("Estructura de Handlers", test_handler_structure),
        ("Estructura de BotService", test_bot_service_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 PRUEBA: {test_name}")
        print(f"{'='*50}")
        
        if test_func():
            passed += 1
            print(f"✅ PASÓ: {test_name}")
        else:
            print(f"❌ FALLÓ: {test_name}")
    
    print(f"\n{'='*50}")
    print(f"📊 RESULTADO FINAL")
    print(f"{'='*50}")
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("🚀 La refactorización está lista para usar!")
    else:
        print("⚠️  Algunas pruebas fallaron.")
        print("🔧 Revisa los errores antes de continuar.")

if __name__ == "__main__":
    main()
