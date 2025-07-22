"""
Servicio para resolver mensajes ambiguos y hacer el bot más resiliente
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Union
from app.models.cliente import Cliente

logger = logging.getLogger(__name__)

class AmbiguityResolver:
    """
    Resuelve mensajes ambiguos, mal escritos o poco claros de los usuarios
    """
    
    def __init__(self):
        # Mapeos de respuestas ambiguas o mal escritas a intenciones claras
        self.confirmation_patterns = [
            # Confirmaciones positivas
            (r'^(si|sí|yes|ok|okay|okey|vale|va|asi|asÍ|así|perfecto|bien|correcto|exacto|claro)$', True),
            (r'^(👍|✅|🙂|😊|👌)$', True),
            # Variaciones mal escritas de "sí"
            (r'^(s|sy|si|zi|ci)$', True),
            # Confirmaciones en diferentes idiomas/jerga
            (r'^(yep|yup|yeah|seh|sep|see|aja|ajá|ujum|ujúm)$', True),
            # Frases de confirmación
            (r'(esta\s*bien|estabien|ta\s*bien|tabien|perfecto|correcto|exacto)', True),
            
            # Negaciones
            (r'^(no|nop|nope|nada|nunca|neg|negativo)$', False),
            (r'^(❌|👎|🚫|😕|😞)$', False),
            # Negaciones mal escritas
            (r'^(n|nn|noo|nooo)$', False),
            
            # Cancelaciones
            (r'^(cancel|cancelar|cancela|salir|exit|quit|para|parar|stop)$', 'cancel'),
            (r'^(ya\s*no|mejor\s*no|olvida|olvidalo|olvidalo)', 'cancel'),
        ]
        
        # Patrones para extraer intención de agregar más pizzas
        self.add_more_patterns = [
            (r'(otra|mas|más|tambien|también|adicional|agregar|agrega)', 'add_more'),
            (r'(quiero\s*(otra|mas|más)|me\s*das\s*(otra|mas|más))', 'add_more'),
            (r'(y\s*(otra|mas|más|tambien|también))', 'add_more'),
        ]
        
        # Patrones para detectar finalización de pedido
        self.finish_patterns = [
            (r'(confirmar|confirma|finalizar|finaliza|terminar|termina|listo|ya\s*esta)', 'finish'),
            (r'(proceder|procede|continuar|continua|seguir|sigue)', 'finish'),
            (r'(eso\s*es\s*todo|ya\s*termine|ya\s*termino|nada\s*mas)', 'finish'),
        ]
        
        # Patrones para corregir errores de escritura comunes
        self.typo_corrections = {
            'pizzza': 'pizza',
            'piza': 'pizza',
            'pissa': 'pizza',
            'pizzaa': 'pizza',
            'margarita': 'margarita',
            'margarida': 'margarita',
            'margherita': 'margarita',
            'peperoni': 'pepperoni',
            'peperony': 'pepperoni',
            'champiñon': 'champiñones',
            'champinon': 'champiñones',
            'champignon': 'champiñones',
            'grande': 'grande',
            'grnade': 'grande',
            'granade': 'grande',
            'mediana': 'mediana',
            'median': 'mediana',
            'pequena': 'pequeña',
            'pequeña': 'pequeña',
            'chica': 'pequeña',
            'confirmr': 'confirmar',
            'confiram': 'confirmar',
            'confimar': 'confirmar'
        }
        
        # Contexto de preguntas anteriores para entender respuestas ambiguas
        self.question_context_patterns = [
            ('confirmar.*pedido', ['confirmar', 'proceder']),
            ('agregar.*más', ['agregar', 'más']),
            ('dirección.*registrada', ['usar_direccion', 'direccion']),
            ('continuar.*pedido', ['continuar', 'seguir']),
            ('finalizar.*pedido', ['finalizar', 'terminar']),
        ]
    
    def resolve_ambiguous_message(self, 
                                 message: str, 
                                 last_bot_message: str = "", 
                                 conversation_state: str = "", 
                                 context: Optional[Dict] = None) -> Dict:
        """
        Resolver un mensaje ambiguo basado en el contexto
        
        Args:
            message: El mensaje del usuario
            last_bot_message: El último mensaje del bot
            conversation_state: Estado actual de la conversación
            context: Contexto adicional de la conversación
            
        Returns:
            Dict con la intención resuelta y confianza
        """
        if context is None:
            context = {}
            
        # Limpiar y normalizar el mensaje
        cleaned_message = self._clean_message(message)
        
        # Aplicar correcciones de errores tipográficos
        corrected_message = self._correct_typos(cleaned_message)
        
        # Intentar resolver basado en patrones de confirmación
        confirmation_result = self._resolve_confirmation(corrected_message)
        if confirmation_result['confidence'] > 0.7:
            return confirmation_result
        
        # Intentar resolver basado en contexto de la pregunta anterior
        context_result = self._resolve_from_context(corrected_message, last_bot_message, conversation_state)
        if context_result['confidence'] > 0.6:
            return context_result
        
        # Intentar detectar intención de agregar más elementos
        add_more_result = self._detect_add_more_intent(corrected_message)
        if add_more_result['confidence'] > 0.5:
            return add_more_result
        
        # Intentar detectar intención de finalizar
        finish_result = self._detect_finish_intent(corrected_message)
        if finish_result['confidence'] > 0.5:
            return finish_result
        
        # Si no se puede resolver, retornar baja confianza
        return {
            'intent': 'unclear',
            'confidence': 0.0,
            'original_message': message,
            'cleaned_message': corrected_message,
            'suggestion': self._generate_clarification_suggestion(conversation_state, context)
        }
    
    def _clean_message(self, message: str) -> str:
        """Limpiar y normalizar el mensaje"""
        # Convertir a minúsculas
        cleaned = message.lower().strip()
        
        # Remover múltiples espacios
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remover puntuación excesiva
        cleaned = re.sub(r'[.!?]{2,}', '', cleaned)
        
        # Remover emojis repetitivos pero mantener uno
        cleaned = re.sub(r'([😊🙂👍✅👌❌👎🚫😕😞])\1+', r'\1', cleaned)
        
        return cleaned
    
    def _correct_typos(self, message: str) -> str:
        """Corregir errores tipográficos comunes"""
        corrected = message
        
        for typo, correction in self.typo_corrections.items():
            # Usar word boundaries para evitar correcciones incorrectas
            pattern = r'\b' + re.escape(typo) + r'\b'
            corrected = re.sub(pattern, correction, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def _resolve_confirmation(self, message: str) -> Dict:
        """Resolver confirmaciones/negaciones"""
        for pattern, intent in self.confirmation_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                confidence = 0.9 if len(message.split()) <= 2 else 0.8
                return {
                    'intent': 'confirm' if intent is True else ('deny' if intent is False else intent),
                    'confidence': confidence,
                    'pattern_matched': pattern,
                    'resolved_to': intent
                }
        
        return {'intent': 'unclear', 'confidence': 0.0}
    
    def _resolve_from_context(self, message: str, last_bot_message: str, state: str) -> Dict:
        """Resolver basado en el contexto de la conversación"""
        if not last_bot_message:
            return {'intent': 'unclear', 'confidence': 0.0}
        
        # Analizar el último mensaje del bot para entender qué se preguntó
        for pattern, expected_responses in self.question_context_patterns:
            if re.search(pattern, last_bot_message.lower()):
                # Buscar respuestas relacionadas en el mensaje del usuario
                for expected in expected_responses:
                    if expected in message or self._fuzzy_match(message, expected):
                        return {
                            'intent': expected,
                            'confidence': 0.7,
                            'context_pattern': pattern,
                            'resolved_from_context': True
                        }
        
        # Contexto específico por estado
        if state == 'confirmacion' or 'confirmar' in last_bot_message.lower():
            if len(message) <= 5 and any(char in message for char in 'sísnoy'):
                return {
                    'intent': 'confirm' if any(char in message for char in 'sío') else 'deny',
                    'confidence': 0.8,
                    'context_state': state
                }
        
        return {'intent': 'unclear', 'confidence': 0.0}
    
    def _detect_add_more_intent(self, message: str) -> Dict:
        """Detectar intención de agregar más elementos"""
        for pattern, intent in self.add_more_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return {
                    'intent': intent,
                    'confidence': 0.6,
                    'pattern_matched': pattern
                }
        
        return {'intent': 'unclear', 'confidence': 0.0}
    
    def _detect_finish_intent(self, message: str) -> Dict:
        """Detectar intención de finalizar pedido"""
        for pattern, intent in self.finish_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return {
                    'intent': intent,
                    'confidence': 0.7,
                    'pattern_matched': pattern
                }
        
        return {'intent': 'unclear', 'confidence': 0.0}
    
    def _fuzzy_match(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Coincidencia difusa simple entre dos textos"""
        # Implementación simple de similitud por caracteres comunes
        if not text1 or not text2:
            return False
        
        # Si son muy diferentes en longitud, probablemente no coinciden
        if abs(len(text1) - len(text2)) > max(len(text1), len(text2)) * 0.5:
            return False
        
        # Contar caracteres comunes
        common_chars = sum(1 for c in text1 if c in text2)
        similarity = common_chars / max(len(text1), len(text2))
        
        return similarity >= threshold
    
    def _generate_clarification_suggestion(self, state: str, context: Dict) -> str:
        """Generar una sugerencia de clarificación basada en el contexto"""
        if state == 'pedido':
            return ("Parece que quieres continuar con tu pedido. ¿Podrías ser más específico?\n"
                   "• Escribe 'confirmar' para finalizar el pedido\n"
                   "• Escribe el nombre de otra pizza si quieres agregar más\n"
                   "• Escribe 'cancelar' para cancelar el pedido")
        
        elif state == 'confirmacion':
            return ("¿Te gustaría confirmar tu pedido?\n"
                   "• Escribe 'sí' para confirmar\n"
                   "• Escribe 'no' para cancelar")
        
        elif state == 'direccion':
            return ("¿Sobre la dirección de entrega?\n"
                   "• Escribe 'sí' para usar tu dirección registrada\n"
                   "• Escribe 'no' para ingresar una nueva dirección")
        
        else:
            return ("No entendí tu mensaje. ¿Podrías ser más específico?\n"
                   "Escribe 'ayuda' si necesitas asistencia.")
    
    def suggest_response_alternatives(self, unclear_message: str, context: Optional[Dict] = None) -> List[str]:
        """Sugerir alternativas de respuesta para mensajes poco claros"""
        if context is None:
            context = {}
            
        state = context.get('state', '')
        suggestions = []
        
        if state == 'pedido':
            suggestions = [
                "Escribe 'confirmar' para finalizar tu pedido",
                "Escribe el nombre de otra pizza para agregar más",
                "Escribe 'cancelar' para cancelar el pedido"
            ]
        elif state == 'confirmacion':
            suggestions = [
                "Escribe 'sí' para confirmar",
                "Escribe 'no' para cancelar"
            ]
        elif state == 'direccion':
            suggestions = [
                "Escribe 'sí' para usar tu dirección registrada",
                "Escribe 'no' para ingresar una nueva dirección"
            ]
        else:
            suggestions = [
                "Escribe 'menú' para ver nuestras pizzas",
                "Escribe 'ayuda' para obtener asistencia",
                "Escribe 'pedido' para revisar tu pedido actual"
            ]
        
        return suggestions

    def is_emoji_only_message(self, message: str) -> bool:
        """Detectar si el mensaje contiene solo emojis"""
        # Remover espacios en blanco
        cleaned = message.strip()
        if not cleaned:
            return False
        
        # Patrones comunes de emojis
        emoji_pattern = r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+$'
        return bool(re.match(emoji_pattern, cleaned))
    
    def interpret_emoji_response(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Interpretar respuestas que solo contienen emojis"""
        if context is None:
            context = {}
            
        # Emojis positivos
        if any(emoji in message for emoji in ['👍', '✅', '🙂', '😊', '👌', '🍕']):
            return {
                'intent': 'confirm',
                'confidence': 0.8,
                'emoji_interpretation': True,
                'original_emoji': message.strip()
            }
        
        # Emojis negativos
        if any(emoji in message for emoji in ['👎', '❌', '🚫', '😕', '😞']):
            return {
                'intent': 'deny',
                'confidence': 0.8,
                'emoji_interpretation': True,
                'original_emoji': message.strip()
            }
        
        # Emojis de confusión
        if any(emoji in message for emoji in ['🤔', '😕', '❓', '🤷']):
            return {
                'intent': 'confused',
                'confidence': 0.9,
                'emoji_interpretation': True,
                'original_emoji': message.strip()
            }
        
        return {
            'intent': 'unclear',
            'confidence': 0.3,
            'emoji_interpretation': True,
            'original_emoji': message.strip()
        }
