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
            # Fallback al flujo tradicional
            return await self.process_with_traditional_flow(numero_whatsapp, mensaje, cliente)
    
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
        
        elif estado_actual == self.ESTADOS['PEDIDO']:
            return await self.handle_continuar_pedido(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['DIRECCION']:
            return await self.handle_direccion(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['CONFIRMACION']:
            return await self.handle_confirmacion(numero_whatsapp, mensaje, cliente)
        
        else:
            return self.handle_registered_greeting(numero_whatsapp, cliente)
    
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
        """Continuar con pedido"""
        
        # Limpiar mensaje de espacios y signos de puntuación
        mensaje_limpio = re.sub(r'[^\w\s]', '', mensaje).lower().strip()
        
        if mensaje_limpio in ['confirmar', 'confirm', 'ok', 'si', 'yes']:
            # Si el cliente tiene dirección registrada, mostrarla y preguntar si quiere usarla
            if cliente.direccion is not None and cliente.direccion.strip():
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['DIRECCION'])
                return (f"Perfecto! 🎉\n\n"
                       f"¿Deseas usar tu dirección registrada?\n\n"
                       f"📍 {cliente.direccion}\n\n"
                       f"• Escribe 'sí' para usar esta dirección\n"
                       f"• Escribe 'no' para ingresar otra dirección")
            else:
                # Si no tiene dirección registrada, pedirla
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['DIRECCION'])
                return "Perfecto! 🎉\n\nPor favor, envía tu dirección de entrega:"
        
        elif mensaje_limpio in ['cancelar', 'cancel', 'no']:
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
            return "Pedido cancelado. ¡Esperamos verte pronto! 👋"
        
        else:
            # Intentar agregar otra pizza usando IA
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
                    
                    return mensaje_respuesta
                
                # Si la IA sugiere modificar o reemplazar el carrito
                elif response.get('accion_sugerida') in ['limpiar_carrito', 'modificar_carrito', 'reemplazar_pedido']:
                    accion = response.get('accion_sugerida', '')
                    if accion:
                        await self.execute_ai_action(numero_whatsapp, accion, response.get('datos_extraidos', {}), cliente)
                    
                    # Mostrar carrito actualizado
                    carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
                    
                    if not carrito:
                        return "✅ Carrito limpiado. ¿Qué pizza te gustaría agregar?"
                    
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
                    
                    return mensaje_respuesta
                else:
                    # Si no es para agregar pizza, devolver la respuesta de la IA
                    return response.get('mensaje', "No entendí tu mensaje. ¿Quieres agregar otra pizza o confirmar el pedido?")
                    
            except Exception as e:
                logger.error(f"Error procesando mensaje con IA: {str(e)}")
                return ("No entendí tu mensaje. ¿Quieres agregar otra pizza o confirmar el pedido?\n"
                       "• Escribe 'confirmar' para finalizar\n"
                       "• Escribe 'cancelar' para cancelar")
    
    async def handle_direccion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Manejar dirección"""
        
        mensaje_limpio = re.sub(r'[^\w\s]', '', mensaje).lower().strip()
        
        # Si el usuario confirma usar la dirección registrada
        if cliente.direccion is not None and mensaje_limpio in ['si', 'sí', 'yes', 'usar', 'ok']:
            direccion_entrega = cliente.direccion
        # Si el usuario dice no, pedir nueva dirección
        elif cliente.direccion is not None and mensaje_limpio in ['no', 'otro', 'otra', 'nueva', 'cambiar']:
            return ("Por favor, ingresa tu nueva dirección de entrega:\n\n"
                   "Asegúrate de incluir calle, número, ciudad y código postal.")
        # Si proporciona una nueva dirección (mínimo 10 caracteres)
        elif len(mensaje.strip()) >= 10:
            direccion_entrega = mensaje.strip()
        else:
            # Si no tiene dirección registrada o la respuesta no es clara
            if cliente.direccion is not None:
                return (f"¿Deseas usar tu dirección registrada?\n\n"
                       f"📍 {cliente.direccion}\n\n"
                       "• Escribe 'sí' para usar esta dirección\n"
                       "• Escribe 'no' para ingresar otra dirección")
            else:
                return "Por favor ingresa una dirección completa con calle, número, ciudad y código postal."
        
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
        
        return mensaje_respuesta
    
    async def handle_confirmacion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Confirmar pedido"""
        
        # Normalizar mensaje para eliminar acentos y signos de puntuación
        mensaje_limpio = mensaje.lower().strip()
        # Reemplazar caracteres con acentos
        mensaje_limpio = mensaje_limpio.replace('sí', 'si').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ó', 'o').replace('ú', 'u')
        # Eliminar signos de puntuación
        mensaje_limpio = re.sub(r'[^\w\s]', '', mensaje_limpio)
        
        if mensaje_limpio in ['si', 'yes', 'confirmar', 'ok', 'okay']:
            # Crear pedido en base de datos
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
                mensaje += "¡Gracias por elegir Pizza Bias! 🍕"
                
                return mensaje
                
            except Exception as e:
                logger.error(f"Error creando pedido: {str(e)}")
                return ("❌ Hubo un error al procesar tu pedido. Por favor intenta de nuevo.\n"
                       "Si el problema persiste, contacta a soporte.")
        
        else:
            # Cancelar pedido
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
            
            return "❌ Pedido cancelado. ¡Esperamos verte pronto! 👋\n\nEscribe 'menú' para hacer un nuevo pedido."
