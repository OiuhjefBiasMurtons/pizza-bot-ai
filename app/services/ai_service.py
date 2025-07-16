"""
Servicio de IA para manejar conversaciones inteligentes del bot de pizza
"""

import openai
import json
import logging
from typing import Dict, List, Optional, Tuple, cast
from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido
from app.services.bot_service import BotService
from config.settings import settings

logger = logging.getLogger(__name__)

# AIService para manejar la lógica de IA
# Este servicio se encarga de procesar mensajes, extraer intenciones y manejar el contexto
# Utiliza OpenAI para generar respuestas inteligentes basadas en el contexto del cliente y la conversación
class AIService:
    def __init__(self, db: Session):
        self.db = db
        self.bot_service = BotService(db)
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Configurar el contexto del sistema
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self) -> str:
        """Crear el prompt del sistema para la IA"""
        pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
        menu_info = "\n".join([
            f"- {pizza.nombre}: {pizza.descripcion} (Pequeña: ${pizza.precio_pequena}, Mediana: ${pizza.precio_mediana}, Grande: ${pizza.precio_grande})"
            for pizza in pizzas
        ])
        
        return f"""
Eres un asistente de ventas especializado en una pizzería que opera por WhatsApp.

INFORMACIÓN DEL NEGOCIO:
- Nombre: Pizza Bot
- Servicio: Entrega de pizzas a domicilio
- Método de pedido: WhatsApp
- Área de entrega: Ciudad local

MENÚ ACTUAL:
{menu_info}

PERSONALIDAD:
- Amigable y profesional
- Usa emojis apropiados 🍕
- Responde en español
- Mantén las respuestas concisas pero informativas

CAPACIDADES:
1. Responder preguntas sobre pizzas (ingredientes, precios, tamaños)
2. Ayudar con el proceso de pedido
3. Sugerir pizzas según preferencias
4. Manejar modificaciones de pedidos
5. Resolver dudas sobre entrega

RESTRICCIONES:
- Solo vendes pizzas del menú actual
- No puedes crear pizzas personalizadas
- No manejas pagos (solo tomas pedidos)
- No das información médica sobre alergias

FORMATO DE RESPUESTA:
- Siempre responde en formato JSON con esta estructura:
{{
    "tipo_respuesta": "informacion|pedido|menu|ayuda",
    "requiere_accion": true/false,
    "accion_sugerida": "mostrar_menu|agregar_pizza|confirmar_pedido|solicitar_direccion|null",
    "mensaje": "Tu respuesta al usuario",
    "datos_extraidos": {{
        "pizzas_solicitadas": [
            {{"numero": 1, "tamaño": "mediana", "cantidad": 1}}
        ],
        "direccion": "dirección si se menciona",
        "modificaciones": "cambios solicitados"
    }}
}}

EJEMPLO DE CONVERSACIÓN:
Usuario: "Quiero una pizza margarita grande"
Respuesta: {{
    "tipo_respuesta": "pedido",
    "requiere_accion": true,
    "accion_sugerida": "agregar_pizza",
    "mensaje": "¡Perfecto! Te agrego una pizza Margarita grande por $15.99. ¿Quieres agregar algo más a tu pedido? 🍕",
    "datos_extraidos": {{
        "pizzas_solicitadas": [{{"numero": 1, "tamaño": "grande", "cantidad": 1}}]
    }}
}}
"""
    # Procesar mensaje con IA y determinar la acción apropiada
    async def process_with_ai(self, 
                            numero_whatsapp: str, 
                            mensaje: str, 
                            cliente: Optional[Cliente] = None,
                            contexto_conversacion: Optional[Dict] = None) -> Dict:
        """
        Procesar mensaje con IA y determinar la acción apropiada
        """
        
        # Construir contexto de la conversación
        context = self._build_conversation_context(numero_whatsapp, cliente, contexto_conversacion)
        
        # Preparar mensajes para OpenAI con tipos correctos
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Contexto: {context}\n\nMensaje del usuario: {mensaje}"}
        ]
        
        try:
            # Llamar a OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,  # type: ignore
                temperature=0.7,
                max_tokens=500
            )
            
            # Verificar que el contenido no sea None
            content = response.choices[0].message.content
            if content is None:
                logger.error("OpenAI response content is None")
                return self._fallback_response(mensaje)
            
            # Parsear respuesta
            ai_response = json.loads(content)
            
            # Log para debugging
            logger.info(f"AI Response: {ai_response}")
            
            return ai_response
            
        except json.JSONDecodeError:
            logger.error(f"Error parseando respuesta de IA: {response.choices[0].message.content}")
            return self._fallback_response(mensaje)
            
        except Exception as e:
            logger.error(f"Error en llamada a OpenAI: {str(e)}")
            return self._fallback_response(mensaje)
    
    def _build_conversation_context(self, 
                                  numero_whatsapp: str, 
                                  cliente: Optional[Cliente],
                                  contexto_conversacion: Optional[Dict]) -> str:
        """Construir contexto de la conversación"""
        
        context = f"Cliente: {numero_whatsapp}\n"
        
        if cliente:
            context += f"Nombre: {cliente.nombre or 'No registrado'}\n"
            context += f"Dirección: {cliente.direccion or 'No registrada'}\n"
        
        if contexto_conversacion:
            context += f"Estado actual: {contexto_conversacion.get('estado', 'inicio')}\n"
            
            carrito = contexto_conversacion.get('carrito', [])
            if carrito:
                context += "Carrito actual:\n"
                for item in carrito:
                    context += f"- {item['pizza_nombre']} ({item['tamano']}): ${item['precio']}\n"
        
        return context
    
    def _fallback_response(self, mensaje: str) -> Dict:
        """Respuesta de respaldo cuando la IA falla"""
        return {
            "tipo_respuesta": "error",
            "requiere_accion": False,
            "accion_sugerida": None,
            "mensaje": "Disculpa, hay un problema técnico. ¿Puedes repetir tu mensaje? 🤖",
            "datos_extraidos": {}
        }
    
    async def should_use_ai(self, mensaje: str, estado_actual: str) -> bool:
        """
        Determinar si usar IA o el flujo tradicional
        """
        
        # Comandos simples que no requieren IA
        comandos_simples = [
            'hola', 'menu', 'ayuda', 'si', 'no', 'confirmar', 'cancelar'
        ]
        
        mensaje_lower = mensaje.lower().strip()
        
        # Si es un comando simple y estamos en estado apropiado, no usar IA
        if mensaje_lower in comandos_simples and estado_actual in ['inicio', 'menu']:
            return False
        
        # Si es un número simple (selección de pizza), no usar IA
        if mensaje_lower.isdigit() and estado_actual == 'menu':
            return False
        
        # Para todo lo demás, usar IA
        return True
    
    async def extract_intent(self, mensaje: str) -> Dict:
        """Extraer intención del mensaje usando IA"""
        
        intent_prompt = f"""
        Analiza el siguiente mensaje y determina la intención del usuario:
        
        Mensaje: "{mensaje}"
        
        Responde solo con un JSON:
        {{
            "intencion": "saludo|menu|pedido|pregunta|modificacion|confirmacion|cancelacion|ayuda",
            "confianza": 0.8,
            "entidades": {{
                "pizza_mencionada": "nombre de pizza si se menciona",
                "tamaño": "pequeña|mediana|grande",
                "cantidad": 1,
                "accion": "agregar|quitar|modificar"
            }}
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": intent_prompt}],  # type: ignore
                temperature=0.3,
                max_tokens=200
            )
            
            # Verificar que el contenido no sea None
            content = response.choices[0].message.content
            if content is None:
                logger.error("OpenAI response content is None in extract_intent")
                return {"intencion": "ayuda", "confianza": 0.1, "entidades": {}}
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error extrayendo intención: {str(e)}")
            return {"intencion": "ayuda", "confianza": 0.1, "entidades": {}}
