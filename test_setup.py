#!/usr/bin/env python3
"""
Script de prueba para verificar el setup del proyecto Pizza Bot
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Verificar versión de Python"""
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Se requiere Python 3.9+")
        return False

def check_dependencies():
    """Verificar dependencias instaladas"""
    print("\n📦 Verificando dependencias...")
    
    dependencies = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'psycopg2',
        'twilio',
        'python-dotenv'
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - OK")
        except ImportError:
            print(f"❌ {dep} - NO INSTALADO")
            all_ok = False
    
    return all_ok

def check_structure():
    """Verificar estructura del proyecto"""
    print("\n📁 Verificando estructura del proyecto...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'config/settings.py',
        'database/connection.py',
        'database/init_db.py',
        'app/models/__init__.py',
        'app/routers/__init__.py',
        'app/services/__init__.py',
        'README.md'
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - OK")
        else:
            print(f"❌ {file_path} - NO EXISTE")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Verificar archivo de configuración"""
    print("\n🔧 Verificando configuración...")
    
    if Path('.env').exists():
        print("✅ Archivo .env encontrado")
        return True
    elif Path('env_example.txt').exists():
        print("⚠️  Archivo .env no encontrado, pero env_example.txt existe")
        print("💡 Copia env_example.txt a .env y configura tus variables")
        return False
    else:
        print("❌ No se encontró archivo de configuración")
        return False

def main():
    """Función principal"""
    print("🍕 PIZZA BOT - VERIFICACIÓN DE SETUP")
    print("=" * 50)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_structure(),
        check_env_file()
    ]
    
    print("\n" + "=" * 50)
    if all(checks):
        print("🎉 ¡Todo está configurado correctamente!")
        print("\n🚀 Pasos siguientes:")
        print("1. Configura tu archivo .env con las credenciales de Twilio")
        print("2. Asegúrate de que PostgreSQL esté corriendo")
        print("3. Ejecuta: python database/init_db.py")
        print("4. Inicia el servidor: uvicorn main:app --reload")
        print("5. Expón el servidor con ngrok: ngrok http 8000")
    else:
        print("❌ Se encontraron problemas en la configuración")
        print("Por favor, revisa los errores mostrados arriba")
    
    print("\n📖 Para más información, consulta el README.md")

if __name__ == "__main__":
    main() 