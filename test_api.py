#!/usr/bin/env python3
"""
Script para probar el API de Pizza Bot
"""
import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
NGROK_URL = "https://f72857ff1728.ngrok-free.app"

def test_health():
    """Probar endpoint de salud"""
    print("🔍 Probando endpoint de salud...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_root():
    """Probar endpoint raíz"""
    print("🔍 Probando endpoint raíz...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_pizzas():
    """Probar obtener pizzas"""
    print("🔍 Probando obtener pizzas...")
    response = requests.get(f"{BASE_URL}/pizzas/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_menu():
    """Probar obtener menú en texto"""
    print("🔍 Probando obtener menú en texto...")
    response = requests.get(f"{BASE_URL}/pizzas/menu")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_webhook_simulation():
    """Simular un webhook de WhatsApp"""
    print("🔍 Simulando webhook de WhatsApp...")
    
    # Simular mensaje de saludo
    data = {
        "From": "whatsapp:+1234567890",
        "Body": "hola"
    }
    
    response = requests.post(f"{BASE_URL}/webhook/whatsapp", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_send_message():
    """Probar endpoint de envío de mensajes"""
    print("🔍 Probando endpoint de envío de mensajes...")
    
    data = {
        "to_number": "+1234567890",
        "message": "¡Hola! Este es un mensaje de prueba desde el Pizza Bot."
    }
    
    response = requests.post(f"{BASE_URL}/webhook/send-message", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("🍕 Pizza Bot - Script de Pruebas")
    print("="*50)
    
    try:
        test_health()
        test_root()
        test_get_pizzas()
        test_get_menu()
        test_webhook_simulation()
        test_send_message()
        
        print("✅ Todas las pruebas completadas")
        print()
        print("🌐 URLs disponibles:")
        print(f"   Local: {BASE_URL}")
        print(f"   Público (ngrok): {NGROK_URL}")
        print(f"   Documentación: {BASE_URL}/docs")
        print(f"   Webhook para Twilio: {NGROK_URL}/webhook/whatsapp/form")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté ejecutándose con: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
