"""Pruebas para el servicio de WhatsApp"""
import pytest
from unittest.mock import Mock, patch
from twilio.base.exceptions import TwilioRestException
from app.services.whatsapp_service import WhatsAppService
from tests.test_config import VALID_PHONE_NUMBERS, TEST_URLS, TWILIO_TEST_CONFIG

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_format_phone_number_valid():
    """Test phone number formatting with valid number"""
    service = WhatsAppService()
    number = VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', '')
    formatted = service._format_phone_number(number)
    assert formatted == VALID_PHONE_NUMBERS['customer']

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_format_phone_number_invalid():
    """Test phone number formatting with invalid number"""
    service = WhatsAppService()
    with pytest.raises(ValueError):
        service._format_phone_number("invalid")

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_validate_webhook_success():
    """Test successful webhook validation"""
    with patch('twilio.request_validator.RequestValidator.validate') as mock_validate:
        mock_validate.return_value = True
        service = WhatsAppService()
        result = service.validate_webhook(
            request_url=TWILIO_TEST_CONFIG['webhook_url'],
            post_data={
                "From": VALID_PHONE_NUMBERS['customer'],
                "Body": "test"
            },
            signature=TWILIO_TEST_CONFIG['test_signature']
        )
        assert result is True

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_validate_webhook_missing_data():
    """Test webhook validation with missing data"""
    service = WhatsAppService()
    result = service.validate_webhook(
        request_url="",
        post_data={},
        signature=""
    )
    assert result is False

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_send_message_success(mock_twilio_client):
    """Test successful message sending"""
    service = WhatsAppService(twilio_client=mock_twilio_client)
    message_id = await service.send_message(
        VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', ''),
        "Test message"
    )
    assert message_id == "test_message_sid"
    mock_twilio_client.messages.create.assert_called_once()

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_send_message_invalid_number():
    """Test message sending with invalid number"""
    service = WhatsAppService()
    with pytest.raises(ValueError):
        await service.send_message("invalid", "Test message")

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_send_message_twilio_error(mock_twilio_client):
    """Test message sending with Twilio error"""
    mock_twilio_client.messages.create.side_effect = TwilioRestException(
        status=400,
        uri="test"
    )
    service = WhatsAppService(twilio_client=mock_twilio_client)
    with pytest.raises(TwilioRestException):
        await service.send_message(
            VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', ''),
            "Test message"
        )

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_send_image_success():
    """Test successful image sending"""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid"
    mock_client.messages.create.return_value = mock_message
    
    service = WhatsAppService(twilio_client=mock_client)
    message_id = await service.send_image(
        VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', ''),
        TEST_URLS['image'],
        "Test caption"
    )
    assert message_id == "test_message_sid"

@pytest.mark.unit
@pytest.mark.twilio
@pytest.mark.asyncio
async def test_send_image_without_caption():
    """Test image sending without caption"""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid"
    mock_client.messages.create.return_value = mock_message
    
    service = WhatsAppService(twilio_client=mock_client)
    message_id = await service.send_image(
        VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', ''),
        TEST_URLS['image']
    )
    assert message_id == "test_message_sid" 