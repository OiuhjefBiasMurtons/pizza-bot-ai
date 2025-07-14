# 🧪 Guía de Testing - Pizza Bot

## Descripción General

El proyecto Pizza Bot incluye una suite completa de tests que cubren todas las funcionalidades principales. Los tests están organizados en diferentes categorías y utilizan mocks para aislar las dependencias externas como Twilio.

## Estructura de Tests

```
tests/
├── conftest.py           # Configuración y fixtures
├── test_models.py        # Tests para modelos de BD
├── test_whatsapp_service.py # Tests para servicio WhatsApp
├── test_bot_service.py   # Tests para lógica del bot
├── test_webhook.py       # Tests de integración webhook
└── test_api_endpoints.py # Tests para endpoints API
```

## Configuración de Testing

### Fixtures Disponibles

El archivo `conftest.py` proporciona las siguientes fixtures:

- `db`: Sesión de base de datos en memoria para testing
- `client`: Cliente de test de FastAPI
- `sample_pizza`: Pizza de ejemplo para tests
- `sample_cliente`: Cliente de ejemplo para tests
- `sample_pedido`: Pedido de ejemplo para tests
- `mock_twilio_client`: Cliente Twilio mockeado
- `mock_whatsapp_form_data`: Datos de formulario WhatsApp simulados

### Base de Datos de Test

Los tests utilizan SQLite en memoria para aislar completamente las pruebas:

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
```

## Categorías de Tests

### 1. Tests Unitarios (`@pytest.mark.unit`)

Prueban componentes individuales de forma aislada:

```bash
# Ejecutar solo tests unitarios
pytest -m unit
```

**Cobertura:**
- Modelos de base de datos
- Lógica de servicios
- Validaciones individuales

### 2. Tests de Integración (`@pytest.mark.integration`)

Prueban la interacción entre componentes:

```bash
# Ejecutar solo tests de integración
pytest -m integration
```

**Cobertura:**
- Webhook completo
- API endpoints
- Flujo de datos entre servicios

### 3. Tests Twilio (`@pytest.mark.twilio`)

Tests específicos para funcionalidad de Twilio:

```bash
# Ejecutar solo tests de Twilio
pytest -m twilio
```

**Cobertura:**
- Envío de mensajes
- Validación de webhooks
- Manejo de errores de Twilio

## Estrategia de Mocking

### 1. Twilio Client Mock

```python
@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing"""
    from unittest.mock import Mock
    
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid"
    mock_client.messages.create.return_value = mock_message
    
    return mock_client
```

### 2. WhatsApp Service Mock

```python
@patch('app.services.whatsapp_service.Client')
async def test_send_message_success(mock_client_class, mock_twilio_client):
    # Setup mock
    mock_client_class.return_value = mock_twilio_client
    
    # Test functionality
    # ...
```

### 3. Database Mock

Los tests utilizan una base de datos en memoria completamente separada de la base de datos de producción.

## Ejecutar Tests

### Comandos Básicos

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con verbose output
pytest -v

# Ejecutar tests específicos
pytest tests/test_models.py

# Ejecutar test específico
pytest tests/test_models.py::test_pizza_model
```

### Con Coverage

```bash
# Ejecutar con coverage
pytest --cov=app tests/

# Generar reporte HTML
pytest --cov=app --cov-report=html tests/

# Coverage con detalles
pytest --cov=app --cov-report=term-missing tests/
```

### Por Marcadores

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Solo tests de Twilio
pytest -m twilio

# Excluir tests lentos
pytest -m "not slow"
```

## Casos de Test Importantes

### 1. Modelo de Datos

```python
def test_pizza_model(db):
    """Test Pizza model creation and attributes"""
    pizza = Pizza(nombre="Margherita", ...)
    db.add(pizza)
    db.commit()
    
    assert pizza.id is not None
    assert pizza.disponible == True
```

### 2. Servicio WhatsApp

```python
@patch('app.services.whatsapp_service.Client')
async def test_send_message_success(mock_client_class, mock_twilio_client):
    """Test successful message sending"""
    # Mock setup
    mock_client_class.return_value = mock_twilio_client
    
    # Test
    whatsapp_service = WhatsAppService()
    result = await whatsapp_service.send_message("+1234567890", "Test")
    
    # Verify
    mock_twilio_client.messages.create.assert_called_once()
    assert result == "test_message_sid"
```

### 3. Lógica del Bot

```python
async def test_bot_service_saludo(db, sample_pizza):
    """Test bot greeting functionality"""
    bot_service = BotService(db)
    
    response = await bot_service.process_message("+1234567890", "hola")
    
    assert "¡Hola!" in response
    assert "Pizza Bot" in response
```

### 4. Webhook de Integración

```python
@patch('app.services.whatsapp_service.WhatsAppService.send_message')
async def test_webhook_whatsapp_greeting(mock_send_message, client, db):
    """Test WhatsApp webhook with greeting message"""
    mock_send_message.return_value = "test_message_sid"
    
    response = client.post("/webhook/whatsapp", data={
        "From": "whatsapp:+1234567890",
        "Body": "hola"
    })
    
    assert response.status_code == 200
    mock_send_message.assert_called_once()
```

## Configuración de CI/CD

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=app tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Debugging Tests

### 1. Verbose Output

```bash
# Mostrar print statements
pytest -s

# Mostrar detalles de failures
pytest -v --tb=short
```

### 2. Debugging Específico

```bash
# Parar en primer fallo
pytest -x

# Parar después de N fallos
pytest --maxfail=2

# Ejecutar test específico con debugging
pytest -s -v tests/test_models.py::test_pizza_model
```

### 3. Logging en Tests

```python
import logging

def test_something():
    logger = logging.getLogger(__name__)
    logger.debug("Debug info")
    # ...
```

## Mocks Avanzados

### 1. Mock de Tiempo

```python
from unittest.mock import patch
import datetime

@patch('app.services.bot_service.datetime')
def test_order_timing(mock_datetime):
    mock_datetime.now.return_value = datetime.datetime(2023, 1, 1, 12, 0, 0)
    # Test logic
```

### 2. Mock de Base de Datos

```python
@patch('app.services.bot_service.sessionmaker')
def test_database_error(mock_session):
    mock_session.side_effect = Exception("Database error")
    # Test error handling
```

### 3. Mock de Requests HTTP

```python
@patch('requests.post')
def test_external_api(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"success": True}
    # Test external API integration
```

## Mejores Prácticas

### 1. Aislamiento de Tests

- Cada test debe ser independiente
- Usar fixtures para setup/teardown
- No compartir estado entre tests

### 2. Nombres Descriptivos

```python
# Bueno
def test_pizza_selection_with_valid_size():

# Malo
def test_pizza():
```

### 3. Arrange-Act-Assert

```python
def test_create_pedido():
    # Arrange
    cliente = Cliente(numero_whatsapp="+1234567890")
    
    # Act
    pedido = create_pedido(cliente, items)
    
    # Assert
    assert pedido.total == expected_total
```

### 4. Mocks Específicos

```python
# Bueno - mock específico
@patch('app.services.whatsapp_service.Client')

# Malo - mock muy amplio
@patch('app.services')
```

## Datos de Test

### Fixtures Reutilizables

```python
@pytest.fixture
def pizza_margherita():
    return Pizza(
        nombre="Margherita",
        precio_pequena=12.99,
        precio_mediana=16.99,
        precio_grande=20.99
    )
```

### Factories

```python
def create_test_cliente(**kwargs):
    defaults = {
        "numero_whatsapp": "+1234567890",
        "nombre": "Test Cliente",
        "activo": True
    }
    defaults.update(kwargs)
    return Cliente(**defaults)
```

## Troubleshooting

### Problemas Comunes

1. **Tests fallan por orden**: Usar fixtures independientes
2. **Mocks no funcionan**: Verificar path del mock
3. **Base de datos sucia**: Asegurar rollback en fixtures
4. **Async tests**: Usar `pytest-asyncio`

### Herramientas de Debugging

- `pytest --pdb` - Debugger interactivo
- `pytest --trace` - Trace de ejecución
- `pytest-html` - Reportes HTML
- `pytest-xdist` - Ejecución paralela

## Métricas y Reporting

### Coverage Target

- **Mínimo**: 80% coverage
- **Objetivo**: 90% coverage
- **Crítico**: 95% para servicios core

### Reportes

```bash
# Generar reporte de coverage
pytest --cov=app --cov-report=html

# Ver en navegador
open htmlcov/index.html
```

## Mantenimiento

### Actualizaciones Regulares

1. Revisar tests obsoletos
2. Actualizar mocks cuando cambien APIs
3. Agregar tests para nuevas funcionalidades
4. Refactorizar tests duplicados

### Monitoreo

- Tiempo de ejecución de tests
- Tasa de fallo
- Coverage por módulo
- Tests flaky (inestables) 