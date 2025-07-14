#!/usr/bin/env python3
"""
Script para verificar la configuración de Twilio (cuenta Trial)
"""
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Cargar variables de entorno
load_dotenv()

# Configuración de Twilio
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

def check_twilio_config():
    """Verificar configuración básica de Twilio"""
    print("🔍 Verificando configuración de Twilio...")
    print(f"Account SID: {ACCOUNT_SID}")
    print(f"Phone Number: {PHONE_NUMBER}")
    print(f"Auth Token: {'*' * len(AUTH_TOKEN) if AUTH_TOKEN else 'NO CONFIGURADO'}")
    print()

def test_twilio_connection():
    """Probar conexión con Twilio"""
    print("🔗 Probando conexión con Twilio...")
    
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        
        # Obtener información de la cuenta
        account = client.api.account.fetch()
        print(f"✅ Conexión exitosa!")
        print(f"   Tipo de cuenta: {account.type}")
        print(f"   Estado: {account.status}")
        print(f"   Nombre: {account.friendly_name}")
        print()
        
        return client
        
    except TwilioRestException as e:
        print(f"❌ Error de Twilio: {e}")
        print(f"   Código de error: {e.code}")
        print(f"   Mensaje: {e.msg}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def check_phone_numbers(client):
    """Verificar números de teléfono disponibles"""
    print("📱 Verificando números de teléfono...")
    
    try:
        # Obtener números de teléfono de la cuenta
        phone_numbers = client.incoming_phone_numbers.list()
        
        if phone_numbers:
            print(f"✅ Números disponibles ({len(phone_numbers)}):")
            for number in phone_numbers:
                print(f"   📞 {number.phone_number}")
                print(f"      Capabilities: SMS={number.capabilities.get('sms', False)}, "
                      f"Voice={number.capabilities.get('voice', False)}")
                if number.sms_url:
                    print(f"      Webhook SMS: {number.sms_url}")
        else:
            print("⚠️  No se encontraron números de teléfono")
            
    except Exception as e:
        print(f"❌ Error obteniendo números: {e}")
    
    print()

def check_whatsapp_senders(client):
    """Verificar números de WhatsApp disponibles"""
    print("💬 Verificando números de WhatsApp...")
    
    try:
        # Para cuentas Trial, generalmente usan el Sandbox
        print("ℹ️  Para cuentas Trial, WhatsApp funciona a través del Sandbox")
        print("   Número del Sandbox: +1 415 523 8886")
        print("   Para probarlo, envía el código de unión desde tu WhatsApp")
        print()
        
        # Intentar obtener senders de WhatsApp (puede no estar disponible en Trial)
        try:
            senders = client.messaging.services.list()
            if senders:
                print(f"✅ Servicios de mensajería encontrados: {len(senders)}")
            else:
                print("ℹ️  No hay servicios de mensajería configurados (normal en Trial)")
        except:
            print("ℹ️  API de servicios de mensajería no disponible en Trial")
            
    except Exception as e:
        print(f"❌ Error verificando WhatsApp: {e}")
    
    print()

def test_sms_send(client):
    """Probar envío de SMS (solo a números verificados en Trial)"""
    print("📧 Información sobre envío de mensajes en cuenta Trial...")
    print("⚠️  IMPORTANTE: En cuentas Trial solo puedes enviar mensajes a:")
    print("   1. Números verificados en tu cuenta")
    print("   2. Tu propio número de teléfono")
    print("   3. WhatsApp Sandbox (para WhatsApp)")
    print()
    
    # No enviamos SMS real para evitar costos/errores
    print("ℹ️  Para probar SMS, usa este código:")
    print(f"""
    message = client.messages.create(
        body="¡Hola desde Pizza Bot!",
        from_="{PHONE_NUMBER}",
        to="+1234567890"  # Debe ser un número verificado
    )
    print(f"Mensaje enviado: {{message.sid}}")
    """)
    print()

def show_trial_limitations():
    """Mostrar limitaciones de cuenta Trial"""
    print("⚠️  LIMITACIONES DE CUENTA TRIAL:")
    print("=" * 50)
    print("📱 SMS:")
    print("   • Solo a números verificados en tu cuenta")
    print("   • Prefijo automático en mensajes: '[Sent from your Twilio trial account]'")
    print("   • Límite de mensajes por día")
    print()
    print("💬 WhatsApp:")
    print("   • Solo funciona con WhatsApp Sandbox")
    print("   • Número del Sandbox: +1 415 523 8886")
    print("   • Debes unirte al sandbox enviando el código")
    print("   • Solo tú puedes recibir mensajes")
    print()
    print("💰 Créditos:")
    print("   • $15.50 USD de crédito inicial")
    print("   • SMS: ~$0.0075 por mensaje")
    print("   • WhatsApp: ~$0.005 por mensaje")
    print()
    print("🔧 Para producción necesitarás:")
    print("   • Verificar tu cuenta (tarjeta de crédito)")
    print("   • Comprar un número de teléfono dedicado")
    print("   • Configurar WhatsApp Business API")
    print()

def main():
    print("🍕 Pizza Bot - Verificador de Twilio")
    print("=" * 50)
    
    # Verificar configuración
    check_twilio_config()
    
    # Probar conexión
    client = test_twilio_connection()
    
    if client:
        check_phone_numbers(client)
        check_whatsapp_senders(client)
        test_sms_send(client)
    
    # Mostrar limitaciones
    show_trial_limitations()
    
    print("✅ Verificación completada")
    print()
    print("🚀 Próximos pasos:")
    print("   1. Si todo está bien, configura el webhook en Twilio")
    print("   2. Para WhatsApp: únete al Sandbox")
    print("   3. Prueba enviando mensajes a números verificados")

if __name__ == "__main__":
    main()
