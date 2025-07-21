"""
Servicio de IA para manejar conversaciones inteligentes del bot de pizza
"""

import openai
import json
import logging
from typing import Dict, List, Optional, Tuple, cast
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido, DetallePedido
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
        """Crear el prompt del sistema para la IA con contexto completo de la base de datos"""
        
        # Obtener información de pizzas
        pizzas_info = self._get_pizzas_context()
        
        # Obtener estadísticas de la base de datos
        db_stats = self._get_database_stats()
        
        # Obtener pizzas más populares
        popular_pizzas = self._get_popular_pizzas()
        
        return f"""
Eres un asistente de ventas especializado en una pizzería que opera por WhatsApp.

INFORMACIÓN DEL NEGOCIO:
- Nombre: Pizza Bias
- Servicio: Entrega de pizzas a domicilio
- Método de pedido: WhatsApp
- Área de entrega: Sur de Cali

MENÚ ACTUAL:
{pizzas_info}

ESTADÍSTICAS DE LA BASE DE DATOS:
{db_stats}

PIZZAS MÁS POPULARES:
{popular_pizzas}

PERSONALIDAD:
- Amigable y profesional
- Usa emojis apropiados 🍕
- Responde en español
- Mantén las respuestas concisas pero informativas

CAPACIDADES:
1. Responder preguntas sobre pizzas (ingredientes, precios, tamaños)
2. Ayudar con el proceso de pedido
3. Sugerir pizzas según preferencias
4. Manejar modificaciones de pedidos (agregar, quitar, reemplazar)
5. Limpiar y modificar el carrito de compras
6. Resolver dudas sobre entrega
7. Hacer recomendaciones basadas en popularidad
8. Detectar intenciones de cambio como "solo quiero", "cambia mi pedido", "quita las otras"

RESTRICCIONES:
- Solo vendes pizzas del menú actual
- No puedes crear pizzas personalizadas
- No manejas pagos (solo tomas pedidos)
- No das información médica sobre alergias

FORMATO DE RESPUESTA:
- Siempre responde en formato JSON con esta estructura:
{{
    "tipo_respuesta": "informacion|pedido|menu|ayuda|recomendacion|modificacion",
    "requiere_accion": true/false,
    "accion_sugerida": "mostrar_menu|agregar_pizza|confirmar_pedido|solicitar_direccion|recomendar_pizza|limpiar_carrito|modificar_carrito|reemplazar_pedido|null",
    "mensaje": "Tu respuesta al usuario",
    "datos_extraidos": {{
        "pizzas_solicitadas": [
            {{"numero": 1, "tamaño": "mediana", "cantidad": 1}}
        ],
        "direccion": "dirección si se menciona",
        "modificaciones": "cambios solicitados",
        "accion_carrito": "limpiar|modificar|reemplazar"
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

EJEMPLO DE MODIFICACIÓN:
Usuario: "Solo quiero la pepperoni grande"
Respuesta: {{
    "tipo_respuesta": "modificacion",
    "requiere_accion": true,
    "accion_sugerida": "reemplazar_pedido",
    "mensaje": "Entendido, reemplazaré tu pedido actual por una pizza Pepperoni grande por $22.99. ¿Está bien así? 🍕",
    "datos_extraidos": {{
        "pizzas_solicitadas": [{{"numero": 2, "tamaño": "grande", "cantidad": 1}}],
        "accion_carrito": "reemplazar"
    }}
}}

PALABRAS CLAVE PARA MODIFICACIÓN:
- "Solo quiero" → reemplazar_pedido
- "Cambia mi pedido" → reemplazar_pedido  
- "Mejor haz" → reemplazar_pedido
- "Quita las otras" → reemplazar_pedido
- "En su lugar" → reemplazar_pedido
- "Cancela todo y" → reemplazar_pedido
- "Únicamente" → reemplazar_pedido
- "Solamente" → reemplazar_pedido

IMPORTANTE: Cuando el usuario dice "Solo quiero X" significa que quiere REEMPLAZAR todo el carrito actual con únicamente X.
"""
    
    def _get_pizzas_context(self) -> str:
        """Obtener contexto completo de pizzas desde la base de datos"""
        try:
            pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
            
            if not pizzas:
                return "No hay pizzas disponibles en este momento."
            
            pizzas_info = []
            for i, pizza in enumerate(pizzas, 1):
                emoji = pizza.emoji or "🍕"
                info = (
                    f"{i}. {emoji} {pizza.nombre}: {pizza.descripcion}\n"
                    f"   - Pequeña: ${pizza.precio_pequena:.2f}\n"
                    f"   - Mediana: ${pizza.precio_mediana:.2f}\n"
                    f"   - Grande: ${pizza.precio_grande:.2f}"
                )
                pizzas_info.append(info)
            
            return "\n".join(pizzas_info)
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto de pizzas: {str(e)}")
            return "Error al cargar información de pizzas."
    
    def _get_database_stats(self) -> str:
        """Obtener estadísticas de la base de datos"""
        try:
            # Contar clientes registrados
            total_clientes = self.db.query(Cliente).count()
            
            # Contar pedidos realizados
            total_pedidos = self.db.query(Pedido).count()
            
            # Contar pizzas disponibles
            total_pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).count()
            
            # Calcular valor promedio de pedido
            avg_pedido = self.db.query(func.avg(Pedido.total)).scalar() or 0
            
            stats = f"""- Total de clientes registrados: {total_clientes}
- Total de pedidos realizados: {total_pedidos}
- Pizzas disponibles en menú: {total_pizzas}
- Valor promedio de pedido: ${avg_pedido:.2f}"""
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return "- Estadísticas no disponibles"
    
    def _get_popular_pizzas(self) -> str:
        """Obtener pizzas más populares basadas en pedidos"""
        try:
            # Consulta para obtener pizzas más vendidas
            popular_query = (
                self.db.query(
                    Pizza.nombre,
                    Pizza.emoji,
                    func.sum(DetallePedido.cantidad).label('total_vendidas'),
                    func.count(DetallePedido.id).label('veces_pedida')
                )
                .join(DetallePedido, Pizza.id == DetallePedido.pizza_id)
                .join(Pedido, DetallePedido.pedido_id == Pedido.id)
                .filter(Pizza.disponible == True)
                .group_by(Pizza.id, Pizza.nombre, Pizza.emoji)
                .order_by(func.sum(DetallePedido.cantidad).desc())
                .limit(3)
                .all()
            )
            
            if not popular_query:
                return "No hay datos de ventas disponibles aún."
            
            popular_info = []
            for i, (nombre, emoji, total_vendidas, veces_pedida) in enumerate(popular_query, 1):
                emoji_display = emoji or "🍕"
                info = f"{i}. {emoji_display} {nombre} - {total_vendidas} pizzas vendidas en {veces_pedida} pedidos"
                popular_info.append(info)
            
            return "\n".join(popular_info)
            
        except Exception as e:
            logger.error(f"Error obteniendo pizzas populares: {str(e)}")
            return "Información de popularidad no disponible."
    
    def _get_client_context(self, cliente: Cliente) -> str:
        """Obtener contexto específico del cliente"""
        try:
            if not cliente:
                return "Cliente nuevo (no registrado)"
            
            # Obtener últimos pedidos del cliente
            ultimos_pedidos = (
                self.db.query(Pedido)
                .filter(Pedido.cliente_id == cliente.id)
                .order_by(Pedido.fecha_pedido.desc())
                .limit(3)
                .all()
            )
            
            context = f"""INFORMACIÓN DEL CLIENTE:
- Nombre: {cliente.nombre or 'No registrado'}
- Número: {cliente.numero_whatsapp}
- Dirección: {cliente.direccion or 'No registrada'}
- Fecha de registro: {cliente.fecha_registro.strftime('%Y-%m-%d') if cliente.fecha_registro is not None else 'No disponible'}
- Último pedido: {cliente.ultimo_pedido.strftime('%Y-%m-%d') if cliente.ultimo_pedido is not None else 'Nunca'}"""
            
            if ultimos_pedidos:
                context += "\n\nÚLTIMOS PEDIDOS:"
                for pedido in ultimos_pedidos:
                    context += f"\n- {pedido.fecha_pedido.strftime('%Y-%m-%d')}: ${pedido.total:.2f} ({pedido.estado})"
                    
                    # Obtener detalles del pedido
                    detalles = (
                        self.db.query(DetallePedido, Pizza.nombre)
                        .join(Pizza, DetallePedido.pizza_id == Pizza.id)
                        .filter(DetallePedido.pedido_id == pedido.id)
                        .all()
                    )
                    
                    for detalle, pizza_nombre in detalles:
                        context += f"\n  • {pizza_nombre} ({detalle.tamano}) x{detalle.cantidad}"
            
            return context
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto del cliente: {str(e)}")
            return "Información del cliente no disponible."
    
    async def process_with_ai(self, 
                            numero_whatsapp: str, 
                            mensaje: str, 
                            cliente: Optional[Cliente] = None,
                            contexto_conversacion: Optional[Dict] = None) -> Dict:
        """
        Procesar mensaje con IA y determinar la acción apropiada
        """
        
        # Obtener contexto dinámico actualizado
        contexto_dinamico = self.get_dynamic_context(numero_whatsapp)
        
        # Usar el cliente del contexto dinámico si no se proporcionó
        if not cliente and contexto_dinamico.get('cliente'):
            cliente = contexto_dinamico['cliente']
        
        # Construir contexto de la conversación
        context = self._build_conversation_context(numero_whatsapp, cliente, contexto_conversacion)
        
        # Agregar contexto dinámico
        if contexto_dinamico:
            context += f"\n\nCONTEXTO DINÁMICO:\n"
            context += f"- Pedidos recientes (30 días): {contexto_dinamico.get('pedidos_recientes_30_dias', 0)}\n"
            context += f"- Pizzas disponibles: {contexto_dinamico.get('pizzas_disponibles', 0)}\n"
            if contexto_dinamico.get('recomendaciones'):
                context += f"\nRECOMENDACIONES:\n{contexto_dinamico['recomendaciones']}\n"
        
        # Preparar mensajes para OpenAI con tipos correctos
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Contexto: {context}\n\nMensaje del usuario: {mensaje}"}
        ]
        
        try:
            # Llamar a OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,  # type: ignore
                temperature=0.7,
                max_tokens=500
            )
            
            # Verificar que el contenido no sea None
            content = response.choices[0].message.content
            if content is None:
                logger.error("OpenAI response content is None")
                return self._fallback_response(mensaje)
            
            # Limpiar markdown code blocks si existen
            content = content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
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
        """Construir contexto completo de la conversación"""
        
        context = f"CONVERSACIÓN CON: {numero_whatsapp}\n\n"
        
        # Agregar contexto del cliente si existe
        if cliente:
            context += self._get_client_context(cliente) + "\n\n"
        else:
            context += "CLIENTE NUEVO (no registrado)\n\n"
        
        # Agregar contexto de la conversación actual
        if contexto_conversacion:
            context += f"ESTADO ACTUAL DE LA CONVERSACIÓN:\n"
            context += f"- Estado: {contexto_conversacion.get('estado', 'inicio')}\n"
            
            carrito = contexto_conversacion.get('carrito', [])
            if carrito:
                context += "- Carrito actual:\n"
                total_carrito = 0
                for item in carrito:
                    context += f"  • {item['pizza_nombre']} ({item['tamano']}): ${item['precio']:.2f}\n"
                    total_carrito += item['precio']
                context += f"- Total del carrito: ${total_carrito:.2f}\n"
            else:
                context += "- Carrito: vacío\n"
            
            # Agregar información de entrega si existe
            if contexto_conversacion.get('direccion_entrega'):
                context += f"- Dirección de entrega: {contexto_conversacion['direccion_entrega']}\n"
        
        return context
    
    def get_personalized_recommendations(self, cliente: Optional[Cliente]) -> str:
        """Obtener recomendaciones personalizadas para el cliente"""
        try:
            if not cliente:
                # Para clientes nuevos, recomendar pizzas populares
                popular_pizzas = self._get_popular_pizzas()
                return f"Como cliente nuevo, te recomendamos nuestras pizzas más populares:\n{popular_pizzas}"
            
            # Obtener pizzas que el cliente ha pedido antes
            pizzas_cliente = (
                self.db.query(Pizza.nombre, Pizza.emoji, func.count(DetallePedido.id).label('veces_pedida'))
                .join(DetallePedido, Pizza.id == DetallePedido.pizza_id)
                .join(Pedido, DetallePedido.pedido_id == Pedido.id)
                .filter(Pedido.cliente_id == cliente.id)
                .group_by(Pizza.id, Pizza.nombre, Pizza.emoji)
                .order_by(func.count(DetallePedido.id).desc())
                .limit(3)
                .all()
            )
            
            if not pizzas_cliente:
                return "No tienes historial de pedidos. Te recomendamos nuestras pizzas más populares."
            
            recomendaciones = "Basado en tus pedidos anteriores:\n"
            for nombre, emoji, veces in pizzas_cliente:
                emoji_display = emoji or "🍕"
                recomendaciones += f"- {emoji_display} {nombre} (pedida {veces} {'vez' if veces == 1 else 'veces'})\n"
            
            return recomendaciones
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones: {str(e)}")
            return "No se pudieron cargar las recomendaciones."
    
    def get_dynamic_context(self, numero_whatsapp: str) -> Dict:
        """Obtener contexto dinámico actualizado de la base de datos"""
        try:
            # Obtener cliente
            cliente = self.db.query(Cliente).filter(Cliente.numero_whatsapp == numero_whatsapp).first()
            
            # Obtener pedidos recientes (últimos 30 días)
            from datetime import datetime, timedelta
            fecha_limite = datetime.now() - timedelta(days=30)
            
            pedidos_recientes = (
                self.db.query(Pedido)
                .filter(Pedido.fecha_pedido >= fecha_limite)
                .count()
            )
            
            # Obtener pizzas con stock bajo (simulado - podrías agregar un campo stock a Pizza)
            pizzas_disponibles = self.db.query(Pizza).filter(Pizza.disponible == True).count()
            
            return {
                "cliente": cliente,
                "pedidos_recientes_30_dias": pedidos_recientes,
                "pizzas_disponibles": pizzas_disponibles,
                "recomendaciones": self.get_personalized_recommendations(cliente)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo contexto dinámico: {str(e)}")
            return {}
    
    def refresh_system_context(self):
        """Refrescar el contexto del sistema cuando hay cambios en la base de datos"""
        try:
            self.system_prompt = self._create_system_prompt()
            logger.info("Sistema de IA actualizado con nuevo contexto de base de datos")
        except Exception as e:
            logger.error(f"Error refrescando contexto del sistema: {str(e)}")
    
    def get_pizza_by_name_or_number(self, identifier: str) -> Optional[Pizza]:
        """Obtener pizza por nombre o número de menú"""
        try:
            # Intentar como número primero
            if identifier.isdigit():
                pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
                pizza_num = int(identifier)
                if 1 <= pizza_num <= len(pizzas):
                    return pizzas[pizza_num - 1]
            
            # Buscar por nombre (case insensitive)
            pizza = (
                self.db.query(Pizza)
                .filter(Pizza.disponible == True)
                .filter(Pizza.nombre.ilike(f"%{identifier}%"))
                .first()
            )
            
            return pizza
            
        except Exception as e:
            logger.error(f"Error buscando pizza: {str(e)}")
            return None
    
    def validate_pizza_order(self, pizza_data: Dict) -> Dict:
        """Validar datos de pedido de pizza"""
        try:
            errors = []
            
            # Validar pizza
            if "numero" in pizza_data:
                pizza = self.get_pizza_by_name_or_number(str(pizza_data["numero"]))
                if not pizza:
                    errors.append(f"Pizza número {pizza_data['numero']} no encontrada")
            
            # Validar tamaño
            tamanos_validos = ["pequeña", "mediana", "grande"]
            if pizza_data.get("tamaño") not in tamanos_validos:
                errors.append(f"Tamaño inválido. Opciones: {', '.join(tamanos_validos)}")
            
            # Validar cantidad
            cantidad = pizza_data.get("cantidad", 1)
            if not isinstance(cantidad, int) or cantidad < 1 or cantidad > 10:
                errors.append("Cantidad debe ser entre 1 y 10")
            
            return {
                "valido": len(errors) == 0,
                "errores": errors,
                "pizza": pizza if len(errors) == 0 else None
            }
            
        except Exception as e:
            logger.error(f"Error validando pedido: {str(e)}")
            return {
                "valido": False,
                "errores": ["Error interno de validación"],
                "pizza": None
            }
    
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
        
        # Validar que el mensaje no sea None o vacío
        if not mensaje or not isinstance(mensaje, str):
            return False
        
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
                model="gpt-3.5-turbo-0125",
                messages=[{"role": "user", "content": intent_prompt}],  # type: ignore
                temperature=0.3,
                max_tokens=200
            )
            
            # Verificar que el contenido no sea None
            content = response.choices[0].message.content
            if content is None:
                logger.error("OpenAI response content is None in extract_intent")
                return {"intencion": "ayuda", "confianza": 0.1, "entidades": {}}
            
            # Limpiar markdown code blocks si existen
            content = content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error extrayendo intención: {str(e)}")
            return {"intencion": "ayuda", "confianza": 0.1, "entidades": {}}
