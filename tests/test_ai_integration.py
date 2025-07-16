"""
Pruebas para el sistema de IA del bot de pizza
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from app.services.enhanced_bot_service import EnhancedBotService
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.conversation_state import ConversationState

class TestAIService:
    """Pruebas para el servicio de IA"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de la base de datos"""
        db = Mock(spec=Session)
        
        # Mock de pizzas
        pizza1 = Mock(spec=Pizza)
        pizza1.id = 1
        pizza1.nombre = "Margarita"
        pizza1.descripcion = "Pizza clásica con tomate, mozzarella y albahaca"
        pizza1.precio_pequena = 12.99
        pizza1.precio_mediana = 15.99
        pizza1.precio_grande = 18.99
        pizza1.disponible = True
        
        pizza2 = Mock(spec=Pizza)
        pizza2.id = 2
        pizza2.nombre = "Pepperoni"
        pizza2.descripcion = "Pizza con pepperoni y mozzarella"
        pizza2.precio_pequena = 14.99
        pizza2.precio_mediana = 17.99
        pizza2.precio_grande = 20.99
        pizza2.disponible = True
        
        db.query().filter().all.return_value = [pizza1, pizza2]
        
        return db
    
    @pytest.fixture
    def ai_service(self, mock_db):
        """Fixture del servicio de IA"""
        with patch('app.services.ai_service.settings.OPENAI_API_KEY', 'test_key'):
            return AIService(mock_db)
    
    @patch('app.services.ai_service.openai.OpenAI')
    async def test_process_with_ai_simple_order(self, mock_openai, ai_service):
        """Probar procesamiento de pedido simple con IA"""
        
        # Mock de respuesta de OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "tipo_respuesta": "pedido",
            "requiere_accion": True,
            "accion_sugerida": "agregar_pizza",
            "mensaje": "¡Perfecto! Te agrego una pizza Margarita grande por $18.99.",
            "datos_extraidos": {
                "pizzas_solicitadas": [{"numero": 1, "tamaño": "grande", "cantidad": 1}]
            }
        })
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        # Ejecutar prueba
        result = await ai_service.process_with_ai(
            numero_whatsapp="123456789",
            mensaje="Quiero una pizza margarita grande",
            cliente=None,
            contexto_conversacion={}
        )
        
        # Verificar resultado
        assert result["tipo_respuesta"] == "pedido"
        assert result["requiere_accion"] == True
        assert result["accion_sugerida"] == "agregar_pizza"
        assert "margarita" in result["mensaje"].lower()
        assert len(result["datos_extraidos"]["pizzas_solicitadas"]) == 1
    
    @patch('app.services.ai_service.openai.OpenAI')
    async def test_process_with_ai_complex_order(self, mock_openai, ai_service):
        """Probar procesamiento de pedido complejo con IA"""
        
        # Mock de respuesta de OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "tipo_respuesta": "pedido",
            "requiere_accion": True,
            "accion_sugerida": "agregar_pizza",
            "mensaje": "Te agrego: 2 pizzas Margarita medianas y 1 pizza Pepperoni grande.",
            "datos_extraidos": {
                "pizzas_solicitadas": [
                    {"numero": 1, "tamaño": "mediana", "cantidad": 2},
                    {"numero": 2, "tamaño": "grande", "cantidad": 1}
                ]
            }
        })
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        # Ejecutar prueba
        result = await ai_service.process_with_ai(
            numero_whatsapp="123456789",
            mensaje="Quiero 2 margaritas medianas y una pepperoni grande",
            cliente=None,
            contexto_conversacion={}
        )
        
        # Verificar resultado
        assert result["tipo_respuesta"] == "pedido"
        assert len(result["datos_extraidos"]["pizzas_solicitadas"]) == 2
    
    @patch('app.services.ai_service.openai.OpenAI')
    async def test_process_with_ai_question(self, mock_openai, ai_service):
        """Probar procesamiento de pregunta con IA"""
        
        # Mock de respuesta de OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "tipo_respuesta": "informacion",
            "requiere_accion": False,
            "accion_sugerida": None,
            "mensaje": "La pizza Margarita es nuestra clásica con tomate, mozzarella y albahaca. Pequeña $12.99, mediana $15.99, grande $18.99.",
            "datos_extraidos": {}
        })
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        # Ejecutar prueba
        result = await ai_service.process_with_ai(
            numero_whatsapp="123456789",
            mensaje="¿Qué ingredientes tiene la pizza margarita?",
            cliente=None,
            contexto_conversacion={}
        )
        
        # Verificar resultado
        assert result["tipo_respuesta"] == "informacion"
        assert result["requiere_accion"] == False
        assert "margarita" in result["mensaje"].lower()
    
    async def test_should_use_ai_complex_message(self, ai_service):
        """Probar decisión de usar IA para mensaje complejo"""
        
        should_use = await ai_service.should_use_ai(
            "Quiero modificar mi pedido, cambiar la pizza grande por dos medianas",
            "pedido"
        )
        
        assert should_use == True
    
    async def test_should_use_ai_simple_command(self, ai_service):
        """Probar decisión de NO usar IA para comando simple"""
        
        should_use = await ai_service.should_use_ai("menu", "inicio")
        
        assert should_use == False
    
    def test_fallback_response(self, ai_service):
        """Probar respuesta de respaldo cuando IA falla"""
        
        result = ai_service._fallback_response("cualquier mensaje")
        
        assert result["tipo_respuesta"] == "error"
        assert result["requiere_accion"] == False
        assert "problema técnico" in result["mensaje"]


class TestEnhancedBotService:
    """Pruebas para el servicio de bot mejorado"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de la base de datos"""
        db = Mock(spec=Session)
        
        # Mock de cliente
        cliente = Mock(spec=Cliente)
        cliente.numero_whatsapp = "123456789"
        cliente.nombre = "Juan Pérez"
        cliente.direccion = "Calle 123"
        
        db.query().filter().first.return_value = cliente
        
        return db
    
    @pytest.fixture
    def enhanced_bot_service(self, mock_db):
        """Fixture del servicio de bot mejorado"""
        with patch('app.services.enhanced_bot_service.AIService'):
            return EnhancedBotService(mock_db)
    
    async def test_should_use_ai_processing_complex(self, enhanced_bot_service):
        """Probar decisión de usar IA para mensaje complejo"""
        
        should_use = await enhanced_bot_service.should_use_ai_processing(
            "Quiero cambiar mi pizza grande por dos medianas",
            "pedido",
            {}
        )
        
        assert should_use == True
    
    async def test_should_use_ai_processing_simple(self, enhanced_bot_service):
        """Probar decisión de NO usar IA para comando simple"""
        
        should_use = await enhanced_bot_service.should_use_ai_processing(
            "menu",
            "inicio",
            {}
        )
        
        assert should_use == False
    
    async def test_should_use_ai_processing_number(self, enhanced_bot_service):
        """Probar decisión de NO usar IA para número simple"""
        
        should_use = await enhanced_bot_service.should_use_ai_processing(
            "1",
            "menu",
            {}
        )
        
        assert should_use == False
    
    @patch('app.services.enhanced_bot_service.AIService')
    async def test_process_with_ai_success(self, mock_ai_service, enhanced_bot_service):
        """Probar procesamiento exitoso con IA"""
        
        # Mock de respuesta de IA
        mock_ai_response = {
            "tipo_respuesta": "pedido",
            "requiere_accion": True,
            "accion_sugerida": "agregar_pizza",
            "mensaje": "¡Pizza agregada al carrito!",
            "datos_extraidos": {"pizzas_solicitadas": [{"numero": 1, "tamaño": "grande"}]}
        }
        
        mock_ai_service.return_value.process_with_ai.return_value = mock_ai_response
        
        # Mock de cliente
        cliente = Mock(spec=Cliente)
        cliente.nombre = "Juan"
        
        # Ejecutar prueba
        result = await enhanced_bot_service.process_with_ai(
            "123456789",
            "Quiero una pizza grande",
            cliente,
            {}
        )
        
        # Verificar resultado
        assert result == "¡Pizza agregada al carrito!"


# Configuración de pruebas
@pytest.fixture
def sample_ai_responses():
    """Respuestas de ejemplo para las pruebas"""
    return {
        "simple_order": {
            "tipo_respuesta": "pedido",
            "requiere_accion": True,
            "accion_sugerida": "agregar_pizza",
            "mensaje": "¡Perfecto! Te agrego una pizza Margarita grande por $18.99.",
            "datos_extraidos": {
                "pizzas_solicitadas": [{"numero": 1, "tamaño": "grande", "cantidad": 1}]
            }
        },
        "question": {
            "tipo_respuesta": "informacion",
            "requiere_accion": False,
            "accion_sugerida": None,
            "mensaje": "La pizza Margarita tiene tomate, mozzarella y albahaca.",
            "datos_extraidos": {}
        },
        "error": {
            "tipo_respuesta": "error",
            "requiere_accion": False,
            "accion_sugerida": None,
            "mensaje": "Disculpa, hay un problema técnico. ¿Puedes repetir?",
            "datos_extraidos": {}
        }
    }
