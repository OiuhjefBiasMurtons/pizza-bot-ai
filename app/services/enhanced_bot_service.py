"""
Servicio de bot mejorado con integración de IA
"""

from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido, DetallePedido
from app.models.conversation_state import ConversationState
from app.services.pedido_service import PedidoService
from app.services.ai_service import AIService
from app.services.ambiguity_resolver import AmbiguityResolver
import re
import logging
import json
from datetime import datetime
from typing import Optional, Dict, List

# Configurar logger
logger = logging.getLogger(__name__)

class EnhancedBotService:
    """
    Servicio de bot mejorado que combina IA con flujo tradicional
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.pedido_service = PedidoService(db)
        self.ai_service = AIService(db)
        self.ambiguity_resolver = AmbiguityResolver()
        
        # Estados de conversación
        self.ESTADOS = {
            'INICIO': 'inicio',
            'REGISTRO_NOMBRE': 'registro_nombre',
            'REGISTRO_DIRECCION': 'registro_direccion',
            'MENU': 'menu',
            'PEDIDO': 'pedido',
            'DIRECCION': 'direccion',
            'CONFIRMACION': 'confirmacion',
            'FINALIZADO': 'finalizado'
        }
        
        # Comandos que siempre usan flujo tradicional
        self.COMANDOS_TRADICIONALES = [
            'hola', 'hello', 'buenas', 'inicio', 'empezar',
            'menu', 'menú', 'carta', 'ayuda', 'help',
            'pedido', 'mis pedidos', 'estado'
        ]
        
        # Almacenar el último mensaje del bot para contexto
        self.last_bot_messages = {}
    
    async def process_message(self, numero_whatsapp: str, mensaje: str) -> str:
        """
        Procesador principal que decide entre IA y flujo tradicional
        """
        
        # Limpiar mensaje
        mensaje = mensaje.strip()
        mensaje_lower = mensaje.lower()
        
        # Verificar si el cliente está registrado
        cliente = self.get_cliente(numero_whatsapp)
        
        # Obtener estado actual de la conversación
        estado_actual = self.get_conversation_state(numero_whatsapp)
        
        # Obtener contexto de la conversación
        contexto = self.get_conversation_context(numero_whatsapp)
        
        # Log del estado actual
        logger.info(f"🔍 Usuario: {numero_whatsapp}, Estado: {estado_actual}, Mensaje: '{mensaje}'")
        
        # Si el cliente no está registrado, usar flujo tradicional
        if not cliente or cliente.nombre is None or cliente.direccion is None:
            return await self.handle_registration_flow(numero_whatsapp, mensaje, cliente)
        
        # Determinar si usar IA o flujo tradicional
        should_use_ai = await self.should_use_ai_processing(mensaje, estado_actual, contexto)
        
        if should_use_ai:
            return await self.process_with_ai(numero_whatsapp, mensaje, cliente, contexto)
        else:
            return await self.process_with_traditional_flow(numero_whatsapp, mensaje, cliente)
    
    async def should_use_ai_processing(self, mensaje: str, estado_actual: str, contexto: Dict) -> bool:
        """
        Determinar si usar procesamiento con IA
        """
        
        mensaje_lower = mensaje.lower().strip()
        
        # Comandos simples siempre usan flujo tradicional
        if mensaje_lower in self.COMANDOS_TRADICIONALES:
            return False
        
        # Si es un número simple en estado menu, usar flujo tradicional
        if mensaje_lower.isdigit() and estado_actual == self.ESTADOS['MENU']:
            return False
        
        # Si es confirmación simple, usar flujo tradicional
        if mensaje_lower in ['si', 'sí', 'no', 'confirmar', 'cancelar']:
            return False
        
        # Para preguntas complejas, modificaciones, o lenguaje natural, usar IA
        return True
    
    def _store_last_bot_message(self, numero_whatsapp: str, message: str):
        """Almacenar el último mensaje del bot para contexto"""
        self.last_bot_messages[numero_whatsapp] = message
    
    def _get_last_bot_message(self, numero_whatsapp: str) -> str:
        """Obtener el último mensaje del bot"""
        return self.last_bot_messages.get(numero_whatsapp, "")
    
    def _send_response_with_context(self, numero_whatsapp: str, response: str) -> str:
        """Enviar respuesta y almacenar para contexto futuro"""
        self._store_last_bot_message(numero_whatsapp, response)
        return response
    
    async def _handle_ambiguous_message(self, 
                                  numero_whatsapp: str, 
                                  mensaje: str, 
                                  cliente: Cliente, 
                                  current_state: str) -> Optional[str]:
        """
        Manejar mensajes ambiguos usando el AmbiguityResolver
        """
        last_bot_message = self._get_last_bot_message(numero_whatsapp)
        context = {
            'state': current_state,
            'carrito': self.get_temporary_value(numero_whatsapp, 'carrito'),
            'direccion': self.get_temporary_value(numero_whatsapp, 'direccion'),
            'cliente': cliente
        }
        
        # Resolver el mensaje ambiguo
        resolution = self.ambiguity_resolver.resolve_ambiguous_message(
            message=mensaje,
            last_bot_message=last_bot_message,
            conversation_state=current_state,
            context=context
        )
        
        logger.info(f"🔍 Ambiguity resolution: {resolution}")
        
        # Si se resolvió con alta confianza, actuar en consecuencia
        if resolution['confidence'] >= 0.7:
            intent = resolution['intent']
            
            if intent == 'confirm':
                if current_state == self.ESTADOS['PEDIDO']:
                    # Usuario quiere confirmar/continuar con el pedido
                    return self._proceed_to_address_or_confirmation(numero_whatsapp, cliente)
                elif current_state == self.ESTADOS['CONFIRMACION']:
                    # Usuario confirma el pedido final
                    return await self.handle_confirmacion(numero_whatsapp, "confirmar", cliente)
                elif current_state == self.ESTADOS['DIRECCION']:
                    # Usuario confirma usar dirección registrada
                    return await self.handle_direccion(numero_whatsapp, "si", cliente)
            
            elif intent == 'deny':
                if current_state == self.ESTADOS['CONFIRMACION']:
                    return self._send_response_with_context(
                        numero_whatsapp,
                        "Pedido cancelado. ¿Te gustaría hacer otro pedido? 🍕"
                    )
                elif current_state == self.ESTADOS['DIRECCION']:
                    return self._send_response_with_context(
                        numero_whatsapp,
                        "Por favor, ingresa tu nueva dirección de entrega:\n\n"
                        "Asegúrate de incluir calle, número, ciudad y código postal."
                    )
            
            elif intent == 'cancel':
                self.clear_conversation_data(numero_whatsapp)
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
                return self._send_response_with_context(
                    numero_whatsapp,
                    "Pedido cancelado. ¡Esperamos verte pronto! 👋\n\n"
                    "Escribe 'menú' cuando quieras hacer un nuevo pedido."
                )
            
            elif intent == 'finish':
                if current_state == self.ESTADOS['PEDIDO']:
                    return self._proceed_to_address_or_confirmation(numero_whatsapp, cliente)
            
            elif intent == 'add_more':
                if current_state == self.ESTADOS['PEDIDO']:
                    return self._send_response_with_context(
                        numero_whatsapp,
                        "¿Qué pizza más te gustaría agregar? 🍕\n\n"
                        "Escribe el nombre de la pizza o su número del menú."
                    )
        
        # Si se resolvió con confianza media, pedir clarificación pero sugerir
        elif resolution['confidence'] >= 0.5:
            suggestion = resolution.get('suggestion', '')
            return self._send_response_with_context(
                numero_whatsapp,
                f"Creo que entiendo lo que quieres decir, pero permíteme confirmarlo:\n\n{suggestion}"
            )
        
        # Si no se pudo resolver, pedir clarificación específica
        else:
            return await self._handle_unclear_message_with_guidance(numero_whatsapp, mensaje, current_state, context)
    
    def _proceed_to_address_or_confirmation(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Proceder a dirección o confirmación según corresponda"""
        # Si el cliente tiene dirección registrada, mostrarla y preguntar si quiere usarla
        if cliente.direccion is not None and cliente.direccion.strip():
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['DIRECCION'])
            return self._send_response_with_context(
                numero_whatsapp,
                f"Perfecto! 🎉\n\n"
                f"¿Deseas usar tu dirección registrada?\n\n"
                f"📍 {cliente.direccion}\n\n"
                f"• Escribe 'sí' para usar esta dirección\n"
                f"• Escribe 'no' para ingresar otra dirección"
            )
        else:
            # Si no tiene dirección registrada, pedirla
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['DIRECCION'])
            return self._send_response_with_context(
                numero_whatsapp,
                "Perfecto! 🎉\n\n"
                "Por favor, envía tu dirección de entrega:"
            )
    
    async def _handle_unclear_message_with_guidance(self, 
                                              numero_whatsapp: str, 
                                              mensaje: str, 
                                              current_state: str, 
                                              context: Dict) -> str:
        """
        Manejar mensajes que no se pudieron resolver, proporcionando guía específica
        """
        # Verificar si es solo emojis
        if self.ambiguity_resolver.is_emoji_only_message(mensaje):
            emoji_result = self.ambiguity_resolver.interpret_emoji_response(mensaje, context)
            if emoji_result['confidence'] > 0.7:
                # Recursivamente manejar la interpretación del emoji
                return await self._handle_ambiguous_message(numero_whatsapp, emoji_result['intent'], context['cliente'], current_state) or ""
        
        # Generar respuesta de clarificación contextual
        suggestions = self.ambiguity_resolver.suggest_response_alternatives(mensaje, {'state': current_state})
        
        clarification = f"No estoy seguro de entender '{mensaje}'. "
        
        # Agregar contexto específico
        if current_state == self.ESTADOS['PEDIDO']:
            carrito = context.get('carrito', [])
            if carrito:
                total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
                clarification += f"\n\n📋 *Tu pedido actual:*\n"
                for item in carrito:
                    emoji = item.get('pizza_emoji', '🍕')
                    cantidad = item.get('cantidad', 1)
                    clarification += f"• {emoji} {item['pizza_nombre']} - {item['tamano'].title()} x{cantidad}\n"
                clarification += f"\n*Total: ${total:.2f}*\n"
        
        clarification += "\n🤔 ¿Podrías ser más específico?\n"
        for suggestion in suggestions:
            clarification += f"• {suggestion}\n"
        
        return self._send_response_with_context(numero_whatsapp, clarification)
    
    async def process_with_ai(self, numero_whatsapp: str, mensaje: str, cliente: Cliente, contexto: Dict) -> str:
        """
        Procesar mensaje usando IA
        """
        
        try:
            # Obtener respuesta de IA
            ai_response = await self.ai_service.process_with_ai(
                numero_whatsapp=numero_whatsapp,
                mensaje=mensaje,
                cliente=cliente,
                contexto_conversacion=contexto
            )
            
            # Procesar la respuesta de IA
            return await self.handle_ai_response(numero_whatsapp, ai_response, cliente)
            
        except Exception as e:
            logger.error(f"Error procesando con IA: {str(e)}")
            # Intentar manejar solicitud parcial de pizza antes del fallback
            return await self.handle_partial_pizza_request(numero_whatsapp, mensaje, cliente)
    
    async def handle_ai_response(self, numero_whatsapp: str, ai_response: Dict, cliente: Cliente) -> str:
        """
        Manejar la respuesta de IA y ejecutar acciones necesarias
        """
        
        tipo_respuesta = ai_response.get('tipo_respuesta', 'informacion')
        requiere_accion = ai_response.get('requiere_accion', False)
        accion_sugerida = ai_response.get('accion_sugerida')
        mensaje = ai_response.get('mensaje', 'No entendí tu mensaje. ¿Puedes repetirlo?')
        datos_extraidos = ai_response.get('datos_extraidos', {})
        
        # Ejecutar acción si es necesario
        if requiere_accion and accion_sugerida:
            await self.execute_ai_action(numero_whatsapp, accion_sugerida, datos_extraidos, cliente)
        
        return mensaje
    
    async def execute_ai_action(self, numero_whatsapp: str, accion: str, datos: Dict, cliente: Cliente):
        """
        Ejecutar acciones sugeridas por la IA
        """
        
        if accion == 'mostrar_menu':
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['MENU'])
            
        elif accion == 'agregar_pizza':
            await self.handle_ai_pizza_selection(numero_whatsapp, datos, cliente)
            
        elif accion == 'confirmar_pedido':
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['CONFIRMACION'])
            
        elif accion == 'solicitar_direccion':
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['DIRECCION'])
            
        elif accion == 'limpiar_carrito':
            await self.handle_limpiar_carrito(numero_whatsapp, datos, cliente)
            
        elif accion == 'modificar_carrito':
            await self.handle_modificar_carrito(numero_whatsapp, datos, cliente)
            
        elif accion == 'reemplazar_pedido':
            await self.handle_reemplazar_pedido(numero_whatsapp, datos, cliente)
    
    async def handle_partial_pizza_request(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """
        Manejar solicitudes parciales de pizza cuando la IA falla
        Por ejemplo: 'Dame una de pepperoni' sin especificar tamaño
        """
        
        mensaje_lower = mensaje.lower()
        
        # Detectar solicitudes de pizza (patrones comunes)
        pizza_keywords = ['dame', 'quiero', 'pide', 'pedime', 'solicito']
        pizza_names = ['pepperoni', 'margarita', 'margherita', 'hawaiana', 'carnivora', 'carnicera', 'vegetariana']
        
        # Verificar si es una solicitud de pizza
        is_pizza_request = any(keyword in mensaje_lower for keyword in pizza_keywords)
        contains_pizza_name = any(name in mensaje_lower for name in pizza_names)
        
        if is_pizza_request and contains_pizza_name:
            # Intentar encontrar la pizza solicitada
            for name in pizza_names:
                if name in mensaje_lower:
                    # Buscar pizza en la base de datos
                    pizza = self.db.query(Pizza).filter(
                        Pizza.disponible == True,
                        Pizza.nombre.ilike(f'%{name}%')
                    ).first()
                    
                    if pizza:
                        # Guardar pizza en contexto temporal
                        self.set_temporary_value(numero_whatsapp, 'pizza_parcial', {
                            'id': pizza.id,
                            'nombre': pizza.nombre,
                            'emoji': pizza.emoji or '🍕'
                        })
                        
                        # Cambiar a estado de selección de tamaño
                        self.set_conversation_state(numero_whatsapp, 'seleccion_tamano_pizza')
                        
                        return (f"¡Perfecto! Pizza {pizza.emoji or '🍕'} {pizza.nombre} 👍\n\n"
                               f"¿Qué tamaño quieres?\n\n"
                               f"💰 Precios:\n"
                               f"• 1️⃣ Pequeña: ${pizza.precio_pequena:.2f}\n"
                               f"• 2️⃣ Mediana: ${pizza.precio_mediana:.2f}\n"
                               f"• 3️⃣ Grande: ${pizza.precio_grande:.2f}\n\n"
                               f"Escribe el número o el nombre del tamaño:")
            
        # Si no es una solicitud de pizza válida, usar fallback tradicional
        return await self.process_with_traditional_flow(numero_whatsapp, mensaje, cliente)
    
    #async def handle_reemplazar_pedido(self, numero_whatsapp: str, datos: Dict, cliente: Cliente):
        """
        Manejar reemplazo de pedido (funcionalidad existente)
        """
    #    pass  # TODO: Implementar según necesidad
    
    async def handle_ai_pizza_selection(self, numero_whatsapp: str, datos: Dict, cliente: Cliente):
        """
        Manejar selección de pizzas extraída por IA
        """
        
        pizzas_solicitadas = datos.get('pizzas_solicitadas', [])
        
        if not pizzas_solicitadas:
            return
        
        # Obtener pizzas disponibles
        pizzas_disponibles = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
        # Obtener carrito actual
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        
        # Procesar cada pizza solicitada
        for pizza_data in pizzas_solicitadas:
            numero_pizza = pizza_data.get('numero', 0)
            tamano = pizza_data.get('tamaño', 'mediana')
            cantidad = pizza_data.get('cantidad', 1)
            
            # Validar número de pizza
            if numero_pizza > 0 and numero_pizza <= len(pizzas_disponibles):
                pizza_seleccionada = pizzas_disponibles[numero_pizza - 1]
                
                # Obtener precio según tamaño
                precio = self.get_pizza_price(pizza_seleccionada, tamano)  # type: ignore
                
                # Agregar al carrito
                for _ in range(cantidad):
                    carrito.append({
                        'pizza_id': pizza_seleccionada.id,  # type: ignore
                        'pizza_nombre': pizza_seleccionada.nombre,  # type: ignore
                        'pizza_emoji': pizza_seleccionada.emoji,  # type: ignore
                        'tamano': tamano,
                        'precio': precio,
                        'cantidad': 1
                    })
        
        # Guardar carrito actualizado
        self.set_temporary_value(numero_whatsapp, 'carrito', carrito)
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['PEDIDO'])
    
    async def handle_limpiar_carrito(self, numero_whatsapp: str, datos: Dict, cliente: Cliente):
        """
        Limpiar completamente el carrito
        """
        # Limpiar carrito
        self.set_temporary_value(numero_whatsapp, 'carrito', [])
        logger.info(f"Carrito limpiado para {numero_whatsapp}")
    
    async def handle_modificar_carrito(self, numero_whatsapp: str, datos: Dict, cliente: Cliente):
        """
        Modificar elementos específicos del carrito
        """
        # Obtener carrito actual
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        
        # Implementar lógica de modificación específica
        # Por ahora, simplemente limpiar y agregar las nuevas pizzas
        await self.handle_limpiar_carrito(numero_whatsapp, datos, cliente)
        await self.handle_ai_pizza_selection(numero_whatsapp, datos, cliente)
    
    async def handle_reemplazar_pedido(self, numero_whatsapp: str, datos: Dict, cliente: Cliente):
        """
        Reemplazar completamente el pedido actual
        """
        # Limpiar carrito actual
        await self.handle_limpiar_carrito(numero_whatsapp, datos, cliente)
        
        # Agregar las nuevas pizzas
        await self.handle_ai_pizza_selection(numero_whatsapp, datos, cliente)
        
        logger.info(f"Pedido reemplazado para {numero_whatsapp}")
    
    def get_pizza_price(self, pizza: Pizza, tamano: str) -> float:
        """
        Obtener precio de pizza según tamaño
        """
        if tamano.lower() in ['pequeña', 'small']:
            return pizza.precio_pequena  # type: ignore
        elif tamano.lower() in ['mediana', 'medium']:
            return pizza.precio_mediana  # type: ignore
        else:  # grande
            return pizza.precio_grande  # type: ignore
    
    async def process_with_traditional_flow(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """
        Procesar con flujo tradicional (código existente)
        """
        
        mensaje_lower = mensaje.lower()
        estado_actual = self.get_conversation_state(numero_whatsapp)
        
        # Comandos especiales que reinician el flujo
        if mensaje_lower in ['hola', 'hello', 'buenas', 'inicio', 'empezar']:
            return self.handle_registered_greeting(numero_whatsapp, cliente)
        
        elif mensaje_lower in ['menu', 'menú', 'carta']:
            return await self.handle_menu(numero_whatsapp, cliente)
        
        elif mensaje_lower in ['ayuda', 'help']:
            return self.handle_ayuda(cliente)
        
        elif mensaje_lower in ['pedido', 'mis pedidos', 'estado']:
            return await self.handle_estado_pedido(numero_whatsapp, cliente)
        
        # Procesar según estado actual
        if estado_actual == self.ESTADOS['INICIO']:
            return self.handle_registered_greeting(numero_whatsapp, cliente)
        
        elif estado_actual == self.ESTADOS['MENU']:
            return await self.handle_seleccion_pizza(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == 'seleccion_tamano_pizza':
            return await self.handle_tamano_pizza_selection(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['PEDIDO']:
            return await self.handle_continuar_pedido(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['DIRECCION']:
            return await self.handle_direccion(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['CONFIRMACION']:
            return await self.handle_confirmacion(numero_whatsapp, mensaje, cliente)
        
        else:
            return self.handle_registered_greeting(numero_whatsapp, cliente)
    
    async def handle_tamano_pizza_selection(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """
        Manejar selección de tamaño para pizza parcialmente solicitada
        """
        
        mensaje_lower = mensaje.lower().strip()
        
        # Mapear opciones de tamaño
        tamanos = {
            '1': 'pequeña',
            '2': 'mediana', 
            '3': 'grande',
            'pequeña': 'pequeña',
            'pequena': 'pequeña',
            'small': 'pequeña',
            'chica': 'pequeña',
            'mediana': 'mediana',
            'medium': 'mediana',
            'grande': 'grande',
            'large': 'grande'
        }
        
        if mensaje_lower not in tamanos:
            return ("❓ Por favor, selecciona un tamaño válido:\n\n"
                   "• 1️⃣ Pequeña\n• 2️⃣ Mediana\n• 3️⃣ Grande\n\n"
                   "Escribe el número o el nombre del tamaño:")
        
        # Obtener pizza parcial del contexto temporal
        pizza_parcial = self.get_temporary_value(numero_whatsapp, 'pizza_parcial')
        if not pizza_parcial:
            return await self.handle_menu(numero_whatsapp, cliente)
        
        # Obtener pizza completa de la BD
        pizza = self.db.query(Pizza).filter(Pizza.id == pizza_parcial['id']).first()
        if not pizza:
            return await self.handle_menu(numero_whatsapp, cliente)
        
        # Obtener tamaño seleccionado y precio
        tamano_seleccionado = tamanos[mensaje_lower]
        precio = self.get_pizza_price(pizza, tamano_seleccionado)
        
        # Agregar al carrito
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        carrito.append({
            'pizza_id': pizza.id,
            'pizza_nombre': pizza.nombre,
            'pizza_emoji': pizza.emoji or '🍕',
            'tamano': tamano_seleccionado,
            'precio': float(precio),
            'cantidad': 1
        })
        
        self.set_temporary_value(numero_whatsapp, 'carrito', carrito)
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['PEDIDO'])
        
        # Limpiar datos temporales
        self.set_temporary_value(numero_whatsapp, 'pizza_parcial', None)
        
        # Calcular total
        total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
        
        return (f"✅ ¡Perfecto! Agregado al carrito:\n\n"
               f"{pizza.emoji or '🍕'} {pizza.nombre} - {tamano_seleccionado.title()}\n"
               f"💰 Precio: ${precio:.2f}\n\n"
               f"🛒 **Carrito actual:**\n"
               f"• {pizza.emoji or '🍕'} {pizza.nombre} - {tamano_seleccionado.title()} - ${precio:.2f}\n\n"
               f"**Total: ${total:.2f}**\n\n"
               f"¿Quieres agregar algo más?\n"
               f"• Escribe el nombre de otra pizza\n"
               f"• Escribe 'confirmar' para finalizar el pedido")
    
    # Métodos heredados del BotService original...
    
    # Métodos auxiliares (reutilizados del BotService original)
    def get_cliente(self, numero_whatsapp: str) -> Cliente:
        """Obtener cliente por número de WhatsApp"""
        return self.db.query(Cliente).filter(
            Cliente.numero_whatsapp == numero_whatsapp
        ).first()
    
    def get_conversation_state(self, numero_whatsapp: str) -> str:
        """Obtener estado de conversación persistente"""
        state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if state:
            return state.estado_actual  # type: ignore
        else:
            # Crear estado inicial
            new_state = ConversationState(
                numero_whatsapp=numero_whatsapp,
                estado_actual=self.ESTADOS['INICIO']
            )
            self.db.add(new_state)
            self.db.commit()
            return self.ESTADOS['INICIO']
    
    def set_conversation_state(self, numero_whatsapp: str, nuevo_estado: str):
        """Establecer nuevo estado de conversación"""
        state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if state:
            state.estado_actual = nuevo_estado  # type: ignore
        else:
            state = ConversationState(
                numero_whatsapp=numero_whatsapp,
                estado_actual=nuevo_estado
            )
            self.db.add(state)
        
        self.db.commit()
    
    def get_conversation_context(self, numero_whatsapp: str) -> Dict:
        """Obtener contexto completo de la conversación"""
        state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if state and state.datos_temporales:  # type: ignore
            try:
                return json.loads(state.datos_temporales)  # type: ignore
            except json.JSONDecodeError:
                return {}
        
        return {}
    
    def get_temporary_value(self, numero_whatsapp: str, key: str):
        """Obtener valor temporal de la conversación"""
        context = self.get_conversation_context(numero_whatsapp)
        return context.get(key)
    
    def set_temporary_value(self, numero_whatsapp: str, key: str, value):
        """Establecer valor temporal en la conversación"""
        context = self.get_conversation_context(numero_whatsapp)
        context[key] = value
        
        # Guardar en base de datos
        state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if state:
            state.datos_temporales = json.dumps(context)  # type: ignore
        else:
            state = ConversationState(
                numero_whatsapp=numero_whatsapp,
                datos_temporales=json.dumps(context)
            )
            self.db.add(state)
        
        self.db.commit()
    
    def clear_conversation_data(self, numero_whatsapp: str):
        """Limpiar datos de conversación"""
        try:
            # Eliminar estado de conversación de la base de datos
            self.db.query(ConversationState).filter(
                ConversationState.numero_whatsapp == numero_whatsapp
            ).delete()
            
            self.db.commit()
            
            logger.info(f"🧹 Conversación limpiada para {numero_whatsapp}")
            
        except Exception as e:
            logger.error(f"Error limpiando conversación para {numero_whatsapp}: {str(e)}")
            self.db.rollback()
    
    # Métodos del flujo tradicional (simplificados, implementar según necesidad)
    async def handle_registration_flow(self, numero_whatsapp: str, mensaje: str, cliente: Optional[Cliente]) -> str:
        """Manejar flujo de registro"""
        # Implementar lógica de registro aquí
        return "Flujo de registro (por implementar)"
    
    def handle_registered_greeting(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Manejar saludo para cliente registrado"""
        # Resetear estado de conversación al saludo inicial
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
        # Limpiar contexto de conversación
        self.clear_conversation_data(numero_whatsapp)
        
        return f"¡Hola {cliente.nombre}! 🍕 ¿Qué te gustaría ordenar hoy?"
    
    async def handle_menu(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Mostrar menú de pizzas"""
        # Implementar lógica de menú aquí
        return "Menú de pizzas (por implementar)"
    
    def handle_ayuda(self, cliente: Cliente) -> str:
        """Mostrar ayuda"""
        return "Ayuda del bot (por implementar)"
    
    async def handle_estado_pedido(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Mostrar estado de pedido"""
        return "Estado de pedido (por implementar)"
    
    async def handle_seleccion_pizza(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Manejar selección de pizza"""
        return "Selección de pizza (por implementar)"
    
    async def handle_continuar_pedido(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Continuar con pedido - Versión mejorada con resolución de ambigüedades"""
        
        # Limpiar mensaje de espacios y signos de puntuación
        mensaje_limpio = re.sub(r'[^\w\s]', '', mensaje).lower().strip()
        
        # Intentar resolución clara primero
        if mensaje_limpio in ['confirmar', 'confirm', 'ok', 'si', 'yes', 'sí']:
            return self._proceed_to_address_or_confirmation(numero_whatsapp, cliente)
        
        elif mensaje_limpio in ['cancelar', 'cancel', 'no']:
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
            return self._send_response_with_context(
                numero_whatsapp,
                "Pedido cancelado. ¡Esperamos verte pronto! 👋"
            )
        
        # Si no es una respuesta clara, intentar resolución de ambigüedad
        else:
            # Primero intentar con el resolvedor de ambigüedades
            ambiguity_result = await self._handle_ambiguous_message(
                numero_whatsapp, 
                mensaje, 
                cliente, 
                self.ESTADOS['PEDIDO']
            )
            
            if ambiguity_result is not None:
                return ambiguity_result
            
            # Si el resolvedor no pudo manejar el mensaje, intentar con IA
            try:
                # Procesar el mensaje con IA para extraer intención de pizza
                response = await self.ai_service.process_with_ai(
                    numero_whatsapp=numero_whatsapp,
                    mensaje=mensaje,
                    cliente=cliente,
                    contexto_conversacion=self.get_conversation_context(numero_whatsapp)
                )
                
                # Si la IA sugiere agregar pizza, ejecutar la acción
                if response.get('accion_sugerida') == 'agregar_pizza':
                    await self.execute_ai_action(numero_whatsapp, 'agregar_pizza', response.get('datos_extraidos', {}), cliente)
                    
                    # Mostrar carrito actualizado
                    carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
                    total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
                    
                    mensaje_respuesta = "✅ Pizza agregada al carrito!\n\n"
                    mensaje_respuesta += "*Carrito actual:*\n"
                    for item in carrito:
                        emoji = item.get('pizza_emoji', '🍕')
                        cantidad = item.get('cantidad', 1)
                        precio_total = item['precio'] * cantidad
                        mensaje_respuesta += f"• {emoji} {item['pizza_nombre']} - {item['tamano'].title()}\n"
                        mensaje_respuesta += f"  ${item['precio']:.2f} x {cantidad} = ${precio_total:.2f}\n"
                    
                    mensaje_respuesta += f"\n*Total: ${total:.2f}*\n\n"
                    mensaje_respuesta += "¿Quieres agregar algo más?\n"
                    mensaje_respuesta += "• Escribe el nombre de otra pizza\n"
                    mensaje_respuesta += "• Escribe 'confirmar' para finalizar el pedido\n"
                    mensaje_respuesta += "• Escribe 'cancelar' para cancelar"
                    
                    return self._send_response_with_context(numero_whatsapp, mensaje_respuesta)
                
                # Si la IA sugiere modificar o reemplazar el carrito
                elif response.get('accion_sugerida') in ['limpiar_carrito', 'modificar_carrito', 'reemplazar_pedido']:
                    accion = response.get('accion_sugerida', '')
                    if accion:
                        await self.execute_ai_action(numero_whatsapp, accion, response.get('datos_extraidos', {}), cliente)
                    
                    # Mostrar carrito actualizado
                    carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
                    
                    if not carrito:
                        return self._send_response_with_context(
                            numero_whatsapp,
                            "✅ Carrito limpiado. ¿Qué pizza te gustaría agregar?"
                        )
                    
                    total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
                    
                    mensaje_respuesta = "✅ Pedido actualizado!\n\n"
                    mensaje_respuesta += "*Tu nuevo pedido:*\n"
                    for item in carrito:
                        emoji = item.get('pizza_emoji', '🍕')
                        cantidad = item.get('cantidad', 1)
                        precio_total = item['precio'] * cantidad
                        mensaje_respuesta += f"• {emoji} {item['pizza_nombre']} - {item['tamano'].title()}\n"
                        mensaje_respuesta += f"  ${item['precio']:.2f} x {cantidad} = ${precio_total:.2f}\n"
                    
                    mensaje_respuesta += f"\n*Total: ${total:.2f}*\n\n"
                    mensaje_respuesta += "¿Está bien así?\n"
                    mensaje_respuesta += "• Escribe 'confirmar' para finalizar el pedido\n"
                    mensaje_respuesta += "• Escribe 'cancelar' para cancelar"
                    
                    return self._send_response_with_context(numero_whatsapp, mensaje_respuesta)
                else:
                    # Si la IA tampoco puede manejar el mensaje, dar respuesta de respaldo con contexto
                    return self._send_response_with_context(
                        numero_whatsapp,
                        response.get('mensaje', self._get_helpful_fallback_message(numero_whatsapp))
                    )
                    
            except Exception as e:
                logger.error(f"Error procesando mensaje con IA: {str(e)}")
                return self._send_response_with_context(
                    numero_whatsapp,
                    self._get_helpful_fallback_message(numero_whatsapp)
                )
    
    def _get_helpful_fallback_message(self, numero_whatsapp: str) -> str:
        """Obtener mensaje de respaldo útil cuando no se entiende el mensaje del usuario"""
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        
        fallback_msg = "🤔 No estoy seguro de entender tu mensaje.\n\n"
        
        if carrito:
            total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
            fallback_msg += "📋 *Tu pedido actual:*\n"
            for item in carrito:
                emoji = item.get('pizza_emoji', '🍕')
                cantidad = item.get('cantidad', 1)
                fallback_msg += f"• {emoji} {item['pizza_nombre']} - {item['tamano'].title()} x{cantidad}\n"
            fallback_msg += f"\n*Total: ${total:.2f}*\n\n"
        
        fallback_msg += "💡 *¿Qué quisieras hacer?*\n"
        fallback_msg += "• Escribe 'confirmar' para continuar con tu pedido\n"
        fallback_msg += "• Escribe el nombre de una pizza para agregar más\n"
        fallback_msg += "• Escribe 'cancelar' si quieres cancelar\n"
        fallback_msg += "• Escribe 'ayuda' si necesitas más opciones"
        
        return fallback_msg
    
    async def handle_direccion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Manejar dirección - Versión mejorada con resolución de ambigüedades"""
        
        mensaje_limpio = re.sub(r'[^\w\s]', '', mensaje).lower().strip()
        
        # Intentar resolución clara primero
        if cliente.direccion is not None and mensaje_limpio in ['si', 'sí', 'yes', 'usar', 'ok']:
            direccion_entrega = cliente.direccion
        elif cliente.direccion is not None and mensaje_limpio in ['no', 'otro', 'otra', 'nueva', 'cambiar']:
            return self._send_response_with_context(
                numero_whatsapp,
                "Por favor, ingresa tu nueva dirección de entrega:\n\n"
                "Asegúrate de incluir calle, número, ciudad y código postal."
            )
        elif len(mensaje.strip()) >= 10:
            # Es una dirección válida
            direccion_entrega = mensaje.strip()
        else:
            # La respuesta no es clara, intentar resolver ambigüedad
            ambiguity_result = await self._handle_ambiguous_message(
                numero_whatsapp,
                mensaje,
                cliente,
                self.ESTADOS['DIRECCION']
            )
            
            if ambiguity_result is not None:
                return ambiguity_result
            
            # Si no se pudo resolver, dar respuesta contextual
            if cliente.direccion is not None:
                return self._send_response_with_context(
                    numero_whatsapp,
                    f"🤔 No estoy seguro de entender '{mensaje}'.\n\n"
                    f"¿Deseas usar tu dirección registrada?\n\n"
                    f"📍 {cliente.direccion}\n\n"
                    "• Escribe 'sí' para usar esta dirección\n"
                    "• Escribe 'no' para ingresar otra dirección"
                )
            else:
                return self._send_response_with_context(
                    numero_whatsapp,
                    f"🤔 No estoy seguro de entender '{mensaje}'.\n\n"
                    "Por favor ingresa una dirección completa con:\n"
                    "• Calle y número\n"
                    "• Ciudad\n"
                    "• Código postal\n\n"
                    "Ejemplo: Calle 123 #45-67, Bogotá, 110111"
                )
        
        # Guardar dirección de entrega
        self.set_temporary_value(numero_whatsapp, 'direccion', direccion_entrega)
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['CONFIRMACION'])
        
        # Obtener carrito
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        
        # Calcular total
        total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
        
        # Generar resumen
        mensaje_respuesta = "📋 *RESUMEN DEL PEDIDO*\n\n"
        mensaje_respuesta += "*Pizzas:*\n"
        for item in carrito:
            emoji = item.get('pizza_emoji', '🍕')
            cantidad = item.get('cantidad', 1)
            precio_total = item['precio'] * cantidad
            mensaje_respuesta += f"• {emoji} {item['pizza_nombre']} - {item['tamano'].title()}\n"
            mensaje_respuesta += f"  ${item['precio']:.2f} x {cantidad} = ${precio_total:.2f}\n"
        
        mensaje_respuesta += f"\n*Dirección de entrega:*\n{direccion_entrega}\n"
        mensaje_respuesta += f"\n*Total a pagar: ${total:.2f}*\n\n"
        mensaje_respuesta += "¿Confirmas tu pedido?\n"
        mensaje_respuesta += "• Escribe 'sí' para confirmar\n"
        mensaje_respuesta += "• Escribe 'no' para cancelar"
        
        return self._send_response_with_context(numero_whatsapp, mensaje_respuesta)
    
    async def handle_confirmacion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Confirmar pedido - Versión mejorada con resolución de ambigüedades"""
        
        # Normalizar mensaje para eliminar acentos y signos de puntuación
        mensaje_limpio = mensaje.lower().strip()
        # Reemplazar caracteres con acentos
        mensaje_limpio = mensaje_limpio.replace('sí', 'si').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ó', 'o').replace('ú', 'u')
        # Eliminar signos de puntuación
        mensaje_limpio = re.sub(r'[^\w\s]', '', mensaje_limpio)
        
        # Intentar resolución clara primero
        if mensaje_limpio in ['si', 'yes', 'confirmar', 'ok', 'okay']:
            return await self._process_order_confirmation(numero_whatsapp, cliente)
        
        elif mensaje_limpio in ['no', 'cancelar', 'cancel']:
            return await self._process_order_cancellation(numero_whatsapp)
        
        else:
            # La respuesta no es clara, intentar resolver ambigüedad
            ambiguity_result = await self._handle_ambiguous_message(
                numero_whatsapp,
                mensaje,
                cliente,
                self.ESTADOS['CONFIRMACION']
            )
            
            if ambiguity_result is not None:
                return ambiguity_result
            
            # Si no se pudo resolver, mostrar contexto del pedido y pedir clarificación
            return await self._ask_for_confirmation_clarification(numero_whatsapp, mensaje, cliente)
    
    async def _process_order_confirmation(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Procesar confirmación del pedido"""
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        direccion = self.get_temporary_value(numero_whatsapp, 'direccion') or ""
        
        if not carrito:
            return "No hay productos en tu carrito. Comienza un nuevo pedido escribiendo 'menú'."
        
        try:
            # Crear el pedido usando el servicio de pedidos
            pedido_id = await self.pedido_service.crear_pedido(cliente, carrito, direccion)
            
            # Calcular total para mostrar en mensaje
            total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
            
            # Limpiar conversación
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['FINALIZADO'])
            
            mensaje = f"🎉 ¡Pedido confirmado!\n\n"
            mensaje += f"📋 Número de pedido: #{pedido_id}\n"
            mensaje += f"💰 Total: ${total:.2f}\n"
            mensaje += f"📍 Dirección: {direccion}\n"
            mensaje += f"⏰ Tiempo estimado: 30-45 minutos\n\n"
            mensaje += "📱 Te notificaremos cuando tu pedido esté listo.\n"
            mensaje += "¡Gracias por elegir Pizza Express! 🍕"
            
            return mensaje
            
        except Exception as e:
            logger.error(f"Error creando pedido: {str(e)}")
            return ("❌ Hubo un error al procesar tu pedido. Por favor intenta de nuevo.\n"
                   "Si el problema persiste, contacta a soporte.")
    
    async def _process_order_cancellation(self, numero_whatsapp: str) -> str:
        """Procesar cancelación del pedido"""
        self.clear_conversation_data(numero_whatsapp)
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
        
        return ("❌ Pedido cancelado. ¡Esperamos verte pronto! 👋\n\n"
               "Escribe 'menú' para hacer un nuevo pedido.")
    
    async def _ask_for_confirmation_clarification(self, numero_whatsapp: str, mensaje_original: str, cliente: Cliente) -> str:
        """Pedir clarificación cuando no se entiende la respuesta de confirmación"""
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        direccion = self.get_temporary_value(numero_whatsapp, 'direccion') or ""
        total = sum(item['precio'] * item.get('cantidad', 1) for item in carrito)
        
        clarification_msg = f"🤔 No estoy seguro de entender '{mensaje_original}'.\n\n"
        clarification_msg += "📋 *RESUMEN DE TU PEDIDO:*\n"
        for item in carrito:
            emoji = item.get('pizza_emoji', '🍕')
            cantidad = item.get('cantidad', 1)
            clarification_msg += f"• {emoji} {item['pizza_nombre']} - {item['tamano'].title()} x{cantidad}\n"
        
        clarification_msg += f"\n📍 *Dirección:* {direccion}\n"
        clarification_msg += f"💰 *Total:* ${total:.2f}\n\n"
        clarification_msg += "❓ *¿Quieres confirmar este pedido?*\n"
        clarification_msg += "• Escribe 'sí' para confirmar el pedido\n"
        clarification_msg += "• Escribe 'no' para cancelar el pedido"
        
        return self._send_response_with_context(numero_whatsapp, clarification_msg)
