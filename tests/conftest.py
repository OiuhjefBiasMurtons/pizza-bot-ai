"""Configuración de pruebas"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database.connection import Base, get_db
from main import app
from unittest.mock import Mock, patch, AsyncMock
from app.models.pizza import Pizza
from app.models.cliente import Cliente
from app.models.pedido import Pedido, DetallePedido
from datetime import datetime

# URLs de prueba
TEST_URLS = {
    'webhook': '/webhook/whatsapp',
    'send_message': '/webhook/send-message'
}

# Mensajes de prueba
TEST_MESSAGES = {
    'greeting': 'hola',
    'menu': 'menu',
    'address': 'Calle 123, Ciudad, CP 12345'
}

# Respuestas esperadas
EXPECTED_RESPONSES = {
    'greeting': '¡Hola!',
    'menu': 'MENÚ DE PIZZAS',
    'order_summary': 'RESUMEN DEL PEDIDO',
    'confirmation': '¿Confirmas tu pedido?'
}

# Números de teléfono válidos
VALID_PHONE_NUMBERS = {
    'customer': 'whatsapp:+14155238886',
    'bot': 'whatsapp:+14155238886'
}

# Códigos de estado HTTP
HTTP_STATUS = {
    'success': 200,
    'bad_request': 400,
    'unauthorized': 401,
    'forbidden': 403,
    'not_found': 404,
    'validation_error': 422,
    'too_many_requests': 429,
    'server_error': 500
}

# Base de datos en memoria para pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Fixture para base de datos de prueba"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Fixture para cliente de prueba"""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def mock_whatsapp_service():
    """Mock para WhatsAppService"""
    mock = Mock()
    mock.send_message = AsyncMock(return_value="test_message_sid")
    return mock

@pytest.fixture
def mock_bot_service():
    """Mock para BotService"""
    mock = Mock()
    mock.process_message = AsyncMock(return_value="Test response")
    return mock 

@pytest.fixture
def sample_pizza(db):
    """Fixture para pizza de ejemplo"""
    pizza = Pizza(
        nombre="Margherita",
        descripcion="Salsa de tomate, mozzarella, albahaca fresca",
        precio_pequena=12.0,
        precio_mediana=15.0,
        precio_grande=18.0,
        disponible=True,
        emoji="🍕"
    )
    db.add(pizza)
    db.commit()
    db.refresh(pizza)
    return pizza

@pytest.fixture
def sample_cliente(db):
    """Fixture para cliente de ejemplo"""
    cliente = Cliente(
        numero_whatsapp="+14155238886",
        nombre="Cliente Test",
        direccion="Calle 123, Ciudad Test",
        activo=True
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

@pytest.fixture
def sample_pedido(db, sample_cliente, sample_pizza):
    """Fixture para pedido de ejemplo"""
    pedido = Pedido(
        cliente_id=sample_cliente.id,
        estado="pendiente",
        total=15.0,
        direccion_entrega="Calle 123, Ciudad Test",
        notas="Sin cebolla"
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    
    # Agregar detalle de pedido
    detalle = DetallePedido(
        pedido_id=pedido.id,
        pizza_id=sample_pizza.id,
        tamano="mediana",
        cantidad=1,
        precio_unitario=15.0,
        subtotal=15.0
    )
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    
    return pedido

@pytest.fixture
def mock_twilio_client():
    """Mock para cliente de Twilio"""
    with patch('app.services.whatsapp_service.Client') as mock_client:
        mock_instance = Mock()
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        mock_instance.messages.create.return_value = mock_message
        mock_client.return_value = mock_instance
        yield mock_instance