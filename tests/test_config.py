"""Configuración para pruebas"""

# Números de teléfono de prueba válidos para WhatsApp
VALID_PHONE_NUMBERS = {
    'customer': 'whatsapp:+14155238886',  # Número de sandbox de Twilio
    'business': 'whatsapp:+14155551234'   # Número de prueba del negocio
}

# Configuración de Twilio para pruebas
TWILIO_TEST_CONFIG = {
    'account_sid': 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',  # Placeholder for Twilio Account SID
    'auth_token': 'your_test_auth_token',
    'phone_number': '+14155238886',
    'webhook_url': 'https://example.com/webhook',
    'test_signature': 'valid_signature'
}

# Mensajes de prueba
TEST_MESSAGES = {
    'greeting': 'hola',
    'menu': 'menu',
    'order': '1 mediana',
    'address': 'Calle 123, Ciudad, CP 12345',
    'confirm': 'si',
    'cancel': 'no'
}

# URLs de prueba
TEST_URLS = {
    'webhook': '/webhook/whatsapp',
    'send_message': '/webhook/send-message',
    'test': '/webhook/test',
    'image': 'http://example.com/test-image.jpg'
}

# Respuestas esperadas
EXPECTED_RESPONSES = {
    'greeting': '¡Hola!',
    'menu': 'MENÚ DE PIZZAS',
    'order_summary': 'RESUMEN DEL PEDIDO',
    'confirmation': '¿Confirmas tu pedido?'
}

# Códigos de estado HTTP esperados
HTTP_STATUS = {
    'success': 200,
    'bad_request': 400,
    'unauthorized': 401,
    'not_found': 404,
    'validation_error': 422,
    'server_error': 500
}

# Datos de prueba para la base de datos
TEST_DATA = {
    'pizza': {
        'nombre': 'Test Pizza',
        'descripcion': 'Pizza de prueba',
        'precio_pequena': 10.0,
        'precio_mediana': 15.0,
        'precio_grande': 20.0,
        'disponible': True,
        'emoji': '🍕'
    },
    'cliente': {
        'numero_whatsapp': VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', ''),
        'nombre': 'Cliente de Prueba',
        'direccion': TEST_MESSAGES['address'],
        'activo': True
    }
} 