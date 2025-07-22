"""
Tests para el AmbiguityResolver - sistema de resolución de mensajes ambiguos
"""

import pytest
from app.services.ambiguity_resolver import AmbiguityResolver

class TestAmbiguityResolver:
    """Tests para el resolvedor de ambigüedades"""
    
    @pytest.fixture
    def resolver(self):
        return AmbiguityResolver()
    
    def test_resolve_clear_confirmation_positive(self, resolver):
        """Test resolución de confirmación positiva clara"""
        result = resolver.resolve_ambiguous_message("sí")
        
        assert result['intent'] == 'confirm'
        assert result['confidence'] >= 0.8
    
    def test_resolve_ambiguous_confirmation_positive(self, resolver):
        """Test resolución de confirmación positiva ambigua - como 'Así'"""
        result = resolver.resolve_ambiguous_message("así")
        
        assert result['intent'] == 'confirm'
        assert result['confidence'] >= 0.8
        assert result['pattern_matched'] is not None
    
    def test_resolve_emoji_confirmation(self, resolver):
        """Test resolución de confirmación con emojis"""
        result = resolver.resolve_ambiguous_message("👍")
        
        assert result['intent'] == 'confirm'
        assert result['confidence'] >= 0.8
    
    def test_resolve_negative_response(self, resolver):
        """Test resolución de respuesta negativa"""
        result = resolver.resolve_ambiguous_message("no")
        
        assert result['intent'] == 'deny'
        assert result['confidence'] >= 0.8
    
    def test_resolve_typo_corrections(self, resolver):
        """Test corrección de errores tipográficos"""
        # Test corrección de "pizzza" a "pizza"
        corrected = resolver._correct_typos("quiero una pizzza margarita")
        assert "pizza margarita" in corrected
        
        # Test corrección de "confiram" a "confirmar"
        corrected = resolver._correct_typos("confiram el pedido")
        assert "confirmar el pedido" in corrected
    
    def test_resolve_with_context_confirmation(self, resolver):
        """Test resolución con contexto de confirmación"""
        last_bot_message = "¿Te gustaría confirmar tu pedido?"
        result = resolver.resolve_ambiguous_message(
            "así",
            last_bot_message=last_bot_message,
            conversation_state="confirmacion"
        )
        
        assert result['intent'] == 'confirm'
        assert result['confidence'] >= 0.7
    
    def test_resolve_finish_intent(self, resolver):
        """Test detección de intención de finalizar"""
        result = resolver.resolve_ambiguous_message("listo")
        
        assert result['intent'] == 'finish'
        assert result['confidence'] >= 0.5
    
    def test_resolve_cancel_intent(self, resolver):
        """Test detección de intención de cancelar"""
        result = resolver.resolve_ambiguous_message("mejor no")
        
        assert result['intent'] == 'cancel'
        assert result['confidence'] >= 0.8
    
    def test_unclear_message_with_suggestion(self, resolver):
        """Test mensaje poco claro con sugerencia"""
        result = resolver.resolve_ambiguous_message(
            "asdfgh",
            conversation_state="pedido"
        )
        
        assert result['intent'] == 'unclear'
        assert result['confidence'] == 0.0
        assert 'suggestion' in result
    
    def test_emoji_only_detection(self, resolver):
        """Test detección de mensajes solo con emojis"""
        assert resolver.is_emoji_only_message("👍")
        assert resolver.is_emoji_only_message("🍕")
        assert not resolver.is_emoji_only_message("sí 👍")
        assert not resolver.is_emoji_only_message("hola")
    
    def test_interpret_positive_emoji(self, resolver):
        """Test interpretación de emoji positivo"""
        result = resolver.interpret_emoji_response("👍")
        
        assert result['intent'] == 'confirm'
        assert result['confidence'] >= 0.8
        assert result['emoji_interpretation'] is True
    
    def test_interpret_negative_emoji(self, resolver):
        """Test interpretación de emoji negativo"""
        result = resolver.interpret_emoji_response("👎")
        
        assert result['intent'] == 'deny'
        assert result['confidence'] >= 0.8
        assert result['emoji_interpretation'] is True
    
    def test_interpret_confused_emoji(self, resolver):
        """Test interpretación de emoji confuso"""
        result = resolver.interpret_emoji_response("🤔")
        
        assert result['intent'] == 'confused'
        assert result['confidence'] >= 0.8
        assert result['emoji_interpretation'] is True
    
    def test_generate_clarification_suggestions_pedido(self, resolver):
        """Test generación de sugerencias para estado de pedido"""
        suggestions = resolver.suggest_response_alternatives(
            "algo raro",
            context={'state': 'pedido'}
        )
        
        assert len(suggestions) > 0
        assert any("confirmar" in s.lower() for s in suggestions)
        assert any("pizza" in s.lower() for s in suggestions)
    
    def test_generate_clarification_suggestions_confirmacion(self, resolver):
        """Test generación de sugerencias para estado de confirmación"""
        suggestions = resolver.suggest_response_alternatives(
            "mmm",
            context={'state': 'confirmacion'}
        )
        
        assert len(suggestions) > 0
        assert any("sí" in s.lower() for s in suggestions)
        assert any("no" in s.lower() for s in suggestions)
    
    def test_fuzzy_matching(self, resolver):
        """Test coincidencia difusa"""
        assert resolver._fuzzy_match("confirmar", "confiram") is True
        assert resolver._fuzzy_match("pizza", "piza") is True
        assert resolver._fuzzy_match("hola", "adios") is False
    
    def test_message_cleaning(self, resolver):
        """Test limpieza de mensajes"""
        cleaned = resolver._clean_message("  Sí!!!  ")
        assert cleaned == "sí"
        
        cleaned = resolver._clean_message("😊😊😊")
        assert cleaned == "😊"
        
        cleaned = resolver._clean_message("hola    mundo")
        assert cleaned == "hola mundo"
    
    def test_context_based_resolution_address(self, resolver):
        """Test resolución basada en contexto para dirección"""
        last_bot_message = "¿Deseas usar tu dirección registrada?"
        result = resolver.resolve_ambiguous_message(
            "así",
            last_bot_message=last_bot_message,
            conversation_state="direccion"
        )
        
        # Debería resolverse como confirmación con contexto
        assert result['confidence'] >= 0.6
        
    def test_various_confirmation_patterns(self, resolver):
        """Test varios patrones de confirmación"""
        test_cases = [
            ("sí", 'confirm'),
            ("si", 'confirm'),
            ("así", 'confirm'),
            ("perfecto", 'confirm'),
            ("vale", 'confirm'),
            ("ok", 'confirm'),
            ("👍", 'confirm'),
            ("✅", 'confirm'),
            ("yep", 'confirm'),
            ("aja", 'confirm'),
        ]
        
        for message, expected_intent in test_cases:
            result = resolver.resolve_ambiguous_message(message)
            assert result['intent'] == expected_intent, f"Failed for '{message}'"
            assert result['confidence'] >= 0.7
    
    def test_various_negation_patterns(self, resolver):
        """Test varios patrones de negación"""
        test_cases = [
            ("no", 'deny'),
            ("nop", 'deny'),
            ("nada", 'deny'),
            ("👎", 'deny'),
            ("❌", 'deny'),
            ("nn", 'deny'),
        ]
        
        for message, expected_intent in test_cases:
            result = resolver.resolve_ambiguous_message(message)
            assert result['intent'] == expected_intent, f"Failed for '{message}'"
            assert result['confidence'] >= 0.7
    
    def test_real_world_scenario_order_confirmation(self, resolver):
        """Test escenario real - confirmación de pedido"""
        # Simular el escenario real mencionado por el usuario
        last_bot_message = ("El total de tu pedido actual, que incluye dos pizzas "
                           "Cuatro Quesos grandes, es de $49.98. ¿Te gustaría "
                           "proceder con el pedido o necesitas algo más? 🍕")
        
        # El usuario responde "Así" (que debería interpretarse como confirmación)
        result = resolver.resolve_ambiguous_message(
            "Así",
            last_bot_message=last_bot_message,
            conversation_state="pedido"
        )
        
        # Debería resolverse como confirmación
        assert result['intent'] == 'confirm'
        assert result['confidence'] >= 0.7
        
        # No debería reiniciar el flujo, sino proceder con el pedido
