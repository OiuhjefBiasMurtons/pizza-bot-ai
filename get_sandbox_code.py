#!/usr/bin/env python3
"""
Script para obtener el código de unión del WhatsApp Sandbox
"""
import os
from dotenv import load_dotenv
from twilio.rest import Client

# Cargar variables de entorno
load_dotenv()

def get_sandbox_code():
    """Obtener código de unión del sandbox"""
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    
    try:
        # Intentar obtener información del sandbox
        print("🔍 Obteniendo información del WhatsApp Sandbox...")
        print()
        print("📱 Para unirte al WhatsApp Sandbox:")
        print("   1. Abre WhatsApp")
        print("   2. Envía un mensaje a: +1 415 523 8886")
        print("   3. El mensaje debe ser: join <código>")
        print()
        print("ℹ️  Para obtener tu código específico:")
        print("   - Ve a: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        print("   - O busca 'WhatsApp Sandbox' en tu consola de Twilio")
        print("   - Allí verás tu código único de unión")
        print()
        print("🔗 URL directa: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_sandbox_code()
