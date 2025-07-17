#!/usr/bin/env python3
"""
Script de pruebas completo para validar todos los handlers del bot refactorizado.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import get_db
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido
from app.models.conversation_state import ConversationState
from app.services.bot_service_refactored import BotService

# Configurar base de datos de prueba
DATABASE_URL = "sqlite:///./test_handlers.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido
from app.models.conversation_state import ConversationState

# Crear todas las tablas
Cliente.metadata.create_all(bind=engine)

class TestResult:
    def __init__(self, test_name: str, success: bool, message: str = ""):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.timestamp = datetime.now()

class HandlerTester:
    def __init__(self):
        self.results = []
        self.db = SessionLocal()
        self.bot_service = BotService(self.db)
        self.test_phone = "+1234567890"
        
    def add_result(self, test_name: str, success: bool, message: str = ""):
        result = TestResult(test_name, success, message)
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        
    def setup_test_data(self):
        """Configurar datos de prueba"""
        try:
            # Limpiar datos previos
            self.db.query(ConversationState).delete()
            self.db.query(Pedido).delete()
            self.db.query(Cliente).delete()
            self.db.query(Pizza).delete()
            
            # Crear pizzas de prueba
            pizzas = [
                Pizza(
                    nombre="Margherita",
                    descripcion="Tomate, mozzarella y albahaca",
                    precio_pequena=12.99,
                    precio_mediana=16.99,
                    precio_grande=20.99,
                    disponible=True,
                    emoji="🍕"
                ),
                Pizza(
                    nombre="Pepperoni",
                    descripcion="Pepperoni y mozzarella",
                    precio_pequena=14.99,
                    precio_mediana=18.99,
                    precio_grande=22.99,
                    disponible=True,
                    emoji="🍕"
                ),
                Pizza(
                    nombre="Hawaiana",
                    descripcion="Jamón, piña y mozzarella",
                    precio_pequena=15.99,
                    precio_mediana=19.99,
                    precio_grande=23.99,
                    disponible=True,
                    emoji="🍕"
                )
            ]
            
            for pizza in pizzas:
                self.db.add(pizza)
            
            self.db.commit()
            self.add_result("Setup Test Data", True, "Datos de prueba creados correctamente")
            
        except Exception as e:
            self.add_result("Setup Test Data", False, f"Error: {str(e)}")
    
    async def test_registration_handler(self):
        """Probar el handler de registro"""
        try:
            # Test 1: Primer contacto (pedir nombre)
            response = await self.bot_service.process_message(self.test_phone, "hola")
            if "nombre completo" in response.lower():
                self.add_result("Registration - First Contact", True, "Pide nombre correctamente")
            else:
                self.add_result("Registration - First Contact", False, f"Respuesta inesperada: {response[:100]}")
                
            # Test 2: Proporcionar nombre inválido
            response = await self.bot_service.process_message(self.test_phone, "A")
            if "al menos 3 caracteres" in response.lower() or "nombre válido" in response.lower():
                self.add_result("Registration - Invalid Name", True, "Valida nombre correctamente")
            else:
                self.add_result("Registration - Invalid Name", False, f"No validó nombre: {response[:100]}")
                
            # Test 3: Proporcionar nombre válido
            response = await self.bot_service.process_message(self.test_phone, "Juan Pérez")
            if "dirección" in response.lower():
                self.add_result("Registration - Valid Name", True, "Acepta nombre y pide dirección")
            else:
                self.add_result("Registration - Valid Name", False, f"No pidió dirección: {response[:100]}")
                
            # Test 4: Proporcionar dirección inválida
            response = await self.bot_service.process_message(self.test_phone, "Casa")
            if "dirección completa" in response.lower():
                self.add_result("Registration - Invalid Address", True, "Valida dirección correctamente")
            else:
                self.add_result("Registration - Invalid Address", False, f"No validó dirección: {response[:100]}")
                
            # Test 5: Proporcionar dirección válida
            response = await self.bot_service.process_message(self.test_phone, "Calle 123, Colonia Centro, Ciudad, CP 12345")
            if "registro ha sido completado" in response.lower():
                self.add_result("Registration - Valid Address", True, "Completa registro exitosamente")
            else:
                self.add_result("Registration - Valid Address", False, f"No completó registro: {response[:100]}")
                
        except Exception as e:
            self.add_result("Registration Handler", False, f"Error: {str(e)}")
    
    async def test_menu_handler(self):
        """Probar el handler de menú"""
        try:
            # Test 1: Mostrar menú principal
            response = await self.bot_service.process_message(self.test_phone, "menu")
            if "menú principal" in response.lower() and "ver menú de pizzas" in response.lower():
                self.add_result("Menu - Main Menu", True, "Muestra menú principal correctamente")
            else:
                self.add_result("Menu - Main Menu", False, f"No muestra menú principal: {response[:100]}")
            
            # Test 2: Mostrar menú de pizzas
            response = await self.bot_service.process_message(self.test_phone, "1")
            if "menú de pizzas" in response.lower() and "margherita" in response.lower():
                self.add_result("Menu - Pizza Menu", True, "Muestra menú de pizzas correctamente")
            else:
                self.add_result("Menu - Pizza Menu", False, f"No muestra menú de pizzas: {response[:100]}")
                
        except Exception as e:
            self.add_result("Menu Handler", False, f"Error: {str(e)}")
    
    async def test_order_handler(self):
        """Probar el handler de pedidos"""
        try:
            # Test 1: Iniciar proceso de pedido
            response = await self.bot_service.process_message(self.test_phone, "2")
            if "nuevo pedido" in response.lower() and "qué pizza" in response.lower():
                self.add_result("Order - Start Process", True, "Inicia proceso de pedido correctamente")
            else:
                self.add_result("Order - Start Process", False, f"No inició proceso: {response[:100]}")
                
            # Test 2: Seleccionar pizza válida
            response = await self.bot_service.process_message(self.test_phone, "margherita")
            if "margherita" in response.lower() and "confirmas" in response.lower():
                self.add_result("Order - Valid Pizza Selection", True, "Selecciona pizza correctamente")
            else:
                self.add_result("Order - Valid Pizza Selection", False, f"No seleccionó pizza: {response[:100]}")
                
            # Test 3: Confirmar pizza
            response = await self.bot_service.process_message(self.test_phone, "si")
            if "tamaño" in response.lower() and "pequeña" in response.lower():
                self.add_result("Order - Confirm Pizza", True, "Confirma pizza correctamente")
            else:
                self.add_result("Order - Confirm Pizza", False, f"No confirmó pizza: {response[:100]}")
                
            # Test 4: Seleccionar tamaño
            response = await self.bot_service.process_message(self.test_phone, "mediana")
            if "cantidad" in response.lower() or "cuántas" in response.lower():
                self.add_result("Order - Size Selection", True, "Selecciona tamaño correctamente")
            else:
                self.add_result("Order - Size Selection", False, f"No seleccionó tamaño: {response[:100]}")
                
        except Exception as e:
            self.add_result("Order Handler", False, f"Error: {str(e)}")
    
    async def test_info_handler(self):
        """Probar el handler de información"""
        try:
            # Limpiar estado antes de probar info
            self.bot_service.clear_conversation_data(self.test_phone)
            
            # Test 1: Ayuda (usar comando especial)
            response = await self.bot_service.process_message(self.test_phone, "ayuda")
            if "ayuda" in response.lower() and "comandos" in response.lower():
                self.add_result("Info - Help", True, "Muestra ayuda correctamente")
            else:
                self.add_result("Info - Help", False, f"No muestra ayuda: {response[:100]}")
                
            # Test 2: Estado de pedidos (sin pedidos)
            response = await self.bot_service.process_message(self.test_phone, "pedido")
            if "no tienes pedidos" in response.lower() or "pedidos" in response.lower():
                self.add_result("Info - No Orders", True, "Maneja estado sin pedidos")
            else:
                self.add_result("Info - No Orders", False, f"No manejó estado sin pedidos: {response[:100]}")
                
        except Exception as e:
            self.add_result("Info Handler", False, f"Error: {str(e)}")
    
    async def test_base_handler_utilities(self):
        """Probar utilidades del handler base"""
        try:
            # Test 1: Estados de conversación
            self.bot_service.set_conversation_state(self.test_phone, "TEST_STATE")
            state = self.bot_service.get_conversation_state(self.test_phone)
            
            if state == "TEST_STATE":
                self.add_result("Base Handler - Conversation State", True, "Maneja estados correctamente")
            else:
                self.add_result("Base Handler - Conversation State", False, f"Estado incorrecto: {state}")
            
            # Test 2: Limpiar datos de conversación
            self.bot_service.clear_conversation_data(self.test_phone)
            state_after_clear = self.bot_service.get_conversation_state(self.test_phone)
            
            if state_after_clear == "inicio":
                self.add_result("Base Handler - Clear Data", True, "Limpia datos correctamente")
            else:
                self.add_result("Base Handler - Clear Data", False, f"No limpió datos: {state_after_clear}")
                
        except Exception as e:
            self.add_result("Base Handler Utilities", False, f"Error: {str(e)}")
    
    async def test_full_flow(self):
        """Probar flujo completo de pedido"""
        try:
            # Limpiar datos de prueba
            self.db.query(ConversationState).filter(
                ConversationState.numero_whatsapp == "+test_full_flow"
            ).delete()
            self.db.query(Cliente).filter(
                Cliente.numero_whatsapp == "+test_full_flow"
            ).delete()
            self.db.commit()
            
            phone = "+test_full_flow"
            
            # Paso 1: Registro
            await self.bot_service.process_message(phone, "hola")
            await self.bot_service.process_message(phone, "María García")
            response = await self.bot_service.process_message(phone, "Av. Principal 456, Colonia Sur, México, CP 67890")
            
            if "registro ha sido completado" in response.lower():
                self.add_result("Full Flow - Registration", True, "Registro completo exitoso")
            else:
                self.add_result("Full Flow - Registration", False, f"Fallo en registro: {response[:100]}")
                return
                
            # Paso 2: Ver menú principal
            response = await self.bot_service.process_message(phone, "menu")
            if "menú principal" in response.lower():
                self.add_result("Full Flow - Main Menu", True, "Menú principal mostrado correctamente")
            else:
                self.add_result("Full Flow - Main Menu", False, f"Fallo en menú: {response[:100]}")
                return
                
            # Paso 3: Iniciar proceso de pedido
            response = await self.bot_service.process_message(phone, "2")
            if "nuevo pedido" in response.lower():
                self.add_result("Full Flow - Start Order", True, "Proceso de pedido iniciado correctamente")
            else:
                self.add_result("Full Flow - Start Order", False, f"Fallo en iniciar pedido: {response[:100]}")
                return
                
            # Paso 4: Seleccionar pizza
            response = await self.bot_service.process_message(phone, "margherita")
            if "margherita" in response.lower() and "confirmas" in response.lower():
                self.add_result("Full Flow - Pizza Selection", True, "Pizza seleccionada correctamente")
            else:
                self.add_result("Full Flow - Pizza Selection", False, f"Fallo en selección: {response[:100]}")
                return
                
            # Paso 5: Confirmar pizza
            response = await self.bot_service.process_message(phone, "si")
            if "tamaño" in response.lower():
                self.add_result("Full Flow - Confirm Pizza", True, "Pizza confirmada correctamente")
            else:
                self.add_result("Full Flow - Confirm Pizza", False, f"Fallo en confirmación: {response[:100]}")
                return
                
            # Paso 6: Seleccionar tamaño
            response = await self.bot_service.process_message(phone, "grande")
            if "cantidad" in response.lower() or "cuántas" in response.lower():
                self.add_result("Full Flow - Size Selection", True, "Tamaño seleccionado correctamente")
            else:
                self.add_result("Full Flow - Size Selection", False, f"Fallo en tamaño: {response[:100]}")
                
        except Exception as e:
            self.add_result("Full Flow Test", False, f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🧪 INICIANDO PRUEBAS COMPLETAS DE HANDLERS")
        print("=" * 50)
        
        # Configurar datos de prueba
        self.setup_test_data()
        
        # Ejecutar pruebas individuales
        await self.test_registration_handler()
        await self.test_menu_handler()
        await self.test_order_handler()
        await self.test_info_handler()
        await self.test_base_handler_utilities()
        
        # Ejecutar prueba de flujo completo
        await self.test_full_flow()
        
        # Mostrar resumen
        self.show_summary()
        
        # Limpiar
        self.cleanup()
    
    def show_summary(self):
        """Mostrar resumen de resultados"""
        print("\n" + "=" * 50)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        print(f"Total de pruebas: {total_tests}")
        print(f"✅ Exitosas: {passed_tests}")
        print(f"❌ Fallidas: {failed_tests}")
        print(f"📊 Porcentaje de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 PRUEBAS FALLIDAS:")
            for result in self.results:
                if not result.success:
                    print(f"   • {result.test_name}: {result.message}")
        
        print("\n" + "=" * 50)
        if failed_tests == 0:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON! Los handlers están listos para usar.")
        else:
            print("⚠️  Algunas pruebas fallaron. Revisa los handlers antes de continuar.")
    
    def cleanup(self):
        """Limpiar recursos"""
        self.db.close()
        print("🧹 Limpieza completada")

async def main():
    """Función principal"""
    tester = HandlerTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
