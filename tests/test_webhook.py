"""Tests para el router de webhook"""
import pytest
from fastapi.testclient import TestClient
from twilio.base.exceptions import TwilioRestException
from tests.conftest import TEST_URLS, TEST_MESSAGES, VALID_PHONE_NUMBERS, HTTP_STATUS
from unittest.mock import patch, Mock, AsyncMock
import asyncio

@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_whatsapp_form(client):
    """Test webhook handling via form data"""
    with patch('app.routers.webhook.WhatsAppService') as mock_whatsapp, \
         patch('app.routers.webhook.BotService') as mock_bot:
        
        # Configurar mocks
        mock_bot_instance = Mock()
        mock_bot_instance.process_message = AsyncMock(return_value="Test response")
        mock_bot.return_value = mock_bot_instance
        
        mock_whatsapp_instance = Mock()
        mock_whatsapp_instance.send_message = AsyncMock(return_value="test_message_sid")
        mock_whatsapp.return_value = mock_whatsapp_instance
        
        response = client.post(
            TEST_URLS['webhook'] + "/form",
            data={
                "From": VALID_PHONE_NUMBERS['customer'],
                "Body": TEST_MESSAGES['greeting']
            }
        )
        assert response.status_code == HTTP_STATUS['success']
        assert response.json()["status"] == "success"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_whatsapp_json(client):
    """Test webhook handling via JSON"""
    with patch('app.routers.webhook.WhatsAppService') as mock_whatsapp, \
         patch('app.routers.webhook.BotService') as mock_bot:
        
        # Configurar mocks
        mock_bot_instance = Mock()
        mock_bot_instance.process_message = AsyncMock(return_value="Test response")
        mock_bot.return_value = mock_bot_instance
        
        mock_whatsapp_instance = Mock()
        mock_whatsapp_instance.send_message = AsyncMock(return_value="test_message_sid")
        mock_whatsapp.return_value = mock_whatsapp_instance
        
        response = client.post(
            TEST_URLS['webhook'],
            json={
                "From": VALID_PHONE_NUMBERS['customer'],
                "Body": TEST_MESSAGES['greeting']
            }
        )
        assert response.status_code == HTTP_STATUS['success']
        assert response.json()["status"] == "success"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_whatsapp_error_handling(client):
    """Test webhook error handling"""
    with patch('app.routers.webhook.WhatsAppService') as mock_whatsapp, \
         patch('app.routers.webhook.BotService') as mock_bot:
        
        # Simular error en el procesamiento
        mock_bot_instance = Mock()
        mock_bot_instance.process_message = AsyncMock(side_effect=Exception("Test error"))
        mock_bot.return_value = mock_bot_instance
        
        mock_whatsapp_instance = Mock()
        mock_whatsapp_instance.send_message = AsyncMock(return_value="test_message_sid")
        mock_whatsapp.return_value = mock_whatsapp_instance
        
        response = client.post(
            TEST_URLS['webhook'],
            json={
                "From": VALID_PHONE_NUMBERS['customer'],
                "Body": "error"
            }
        )
        assert response.status_code == HTTP_STATUS['server_error']

@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_send_message_success(client):
    """Test send message endpoint success"""
    with patch('app.routers.webhook.WhatsAppService') as mock_whatsapp:
        # Configurar mock
        mock_whatsapp_instance = Mock()
        mock_whatsapp_instance.send_message = AsyncMock(return_value="test_message_sid")
        mock_whatsapp.return_value = mock_whatsapp_instance
        
        response = client.post(
            TEST_URLS['send_message'],
            json={
                "to_number": VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', ''),
                "message": "Test message"
            }
        )
        assert response.status_code == HTTP_STATUS['success']
        assert response.json()["status"] == "success"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_send_message_twilio_error(client):
    """Test send message endpoint with Twilio error"""
    with patch('app.routers.webhook.WhatsAppService') as mock_whatsapp:
        # Simular error de Twilio
        mock_whatsapp_instance = Mock()
        mock_whatsapp_instance.send_message = AsyncMock(side_effect=TwilioRestException(
            status=429,
            uri="test"
        ))
        mock_whatsapp.return_value = mock_whatsapp_instance
        
        response = client.post(
            TEST_URLS['send_message'],
            json={
                "to_number": VALID_PHONE_NUMBERS['customer'].replace('whatsapp:', ''),
                "message": "Test message"
            }
        )
        assert response.status_code == HTTP_STATUS['too_many_requests']

@pytest.mark.integration
def test_webhook_missing_data(client):
    """Test webhook with missing data"""
    response = client.post(
        TEST_URLS['webhook'] + "/form",
        data={}
    )
    assert response.status_code == HTTP_STATUS['validation_error']