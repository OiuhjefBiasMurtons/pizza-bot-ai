#!/usr/bin/env python3
"""
Script para actualizar los imports en todos los archivos de test movidos
"""

import os
import re

def update_test_imports():
    """Actualizar imports en todos los archivos de test"""
    
    tests_dir = "/home/nomadbias/GothamCode/CampCode/Python/Whatss/cursor-pizza-bot/Pizza-bot/tests"
    
    # Patrón para encontrar la línea que necesita cambiar
    pattern = r"sys\.path\.append\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)"
    replacement = "sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))"
    
    # Obtener todos los archivos de test
    test_files = []
    for file in os.listdir(tests_dir):
        if file.startswith(('test_', 'debug_')) and file.endswith('.py'):
            test_files.append(os.path.join(tests_dir, file))
    
    print(f"📁 Actualizando imports en {len(test_files)} archivos de test...")
    print("=" * 60)
    
    updated_count = 0
    
    for file_path in test_files:
        print(f"🔄 Procesando: {os.path.basename(file_path)}")
        
        try:
            # Leer contenido del archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reemplazar el patrón
            new_content = re.sub(pattern, replacement, content)
            
            # Solo escribir si hubo cambios
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"   ✅ Actualizado")
                updated_count += 1
            else:
                print(f"   ⚪ Sin cambios necesarios")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Proceso completado: {updated_count}/{len(test_files)} archivos actualizados")

if __name__ == "__main__":
    update_test_imports()
