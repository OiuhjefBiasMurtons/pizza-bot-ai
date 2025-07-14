"""Pruebas para el servicio del bot"""
import pytest
from app.services.bot_service import BotService
from tests.test_config import VALID_PHONE_NUMBERS, TEST_MESSAGES, EXPECTED_RESPONSES

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_or_create_cliente(db):
    """Test cliente creation and retrieval"""
    bot_service = BotService(db)
    phone = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')
    
    # Should create new cliente
    cliente = bot_service.get_or_create_cliente(phone)
    assert str(cliente.numero_whatsapp) == phone
    assert cliente.id is not None

@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_greeting(db):
    """Test greeting message handling"""
    bot_service = BotService(db)
    phone = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')
    
    response = await bot_service.process_message(phone, TEST_MESSAGES['greeting'])
    assert EXPECTED_RESPONSES['greeting'] in response
    assert 'menu' in response.lower()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_menu(db):
    """Test menu request handling"""
    bot_service = BotService(db)
    phone = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')
    
    response = await bot_service.process_message(phone, TEST_MESSAGES['menu'])
    assert EXPECTED_RESPONSES['menu'] in response

@pytest.mark.unit
@pytest.mark.asyncio
async def test_address_validation_valid(db, sample_pizza):
    """Test valid address processing"""
    bot_service = BotService(db)
    phone = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')

    # Setup cart and state
    bot_service.conversaciones[f"{phone}_carrito"] = [{
        'pizza': sample_pizza,
        'tamano': 'mediana',
        'precio': 15.0,
        'cantidad': 1
    }]
    bot_service.conversaciones[phone] = bot_service.ESTADOS['DIRECCION']

    response = await bot_service.process_message(phone, TEST_MESSAGES['address'])
    assert EXPECTED_RESPONSES['order_summary'] in response
    # Verificar que al menos parte de la dirección aparezca (considerando posible truncado)
    assert "calle 123" in response.lower() or TEST_MESSAGES['address'] in response
    assert "15.00" in response

@pytest.mark.unit
@pytest.mark.asyncio
async def test_address_validation_invalid(db):
    """Test invalid address processing"""
    bot_service = BotService(db)
    phone = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')
    
    bot_service.conversaciones[phone] = bot_service.ESTADOS['DIRECCION']
    response = await bot_service.process_message(phone, "123")
    
    assert "dirección completa" in response.lower()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_order_confirmation(db, sample_pizza):
    """Test order confirmation"""
    bot_service = BotService(db)
    phone = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')

    # Setup cart and address
    bot_service.conversaciones[f"{phone}_carrito"] = [{
        'pizza': sample_pizza,
        'tamano': 'mediana',
        'precio': 15.0,
        'cantidad': 1
    }]
    bot_service.conversaciones[f"{phone}_direccion"] = TEST_MESSAGES['address']
    bot_service.conversaciones[phone] = bot_service.ESTADOS['CONFIRMACION']

    response = await bot_service.process_message(phone, TEST_MESSAGES['confirm'])
    assert "pedido confirmado" in response.lower() or "procesando" in response.lower()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_order_cancellation(db, sample_pizza):
    """Test order cancellation"""
    bot_service = BotService(db)
    phone = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')

    # Setup cart and address
    bot_service.conversaciones[f"{phone}_carrito"] = [{
        'pizza': sample_pizza,
        'tamano': 'mediana',
        'precio': 15.0,
        'cantidad': 1
    }]
    bot_service.conversaciones[f"{phone}_direccion"] = TEST_MESSAGES['address']
    bot_service.conversaciones[phone] = bot_service.ESTADOS['CONFIRMACION']

    response = await bot_service.process_message(phone, TEST_MESSAGES['cancel'])
    assert "cancelado" in response.lower() 