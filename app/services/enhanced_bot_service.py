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
    
    # Métodos del flujo tradicional (simplificados, implementar según necesidad)
    async def handle_registration_flow(self, numero_whatsapp: str, mensaje: str, cliente: Optional[Cliente]) -> str:
        """Manejar flujo de registro"""
        # Implementar lógica de registro aquí
        return "Flujo de registro (por implementar)"
    
    def handle_registered_greeting(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Manejar saludo para cliente registrado"""
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
        return "Continuar pedido (por implementar)"
    
    async def handle_direccion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Manejar dirección"""
        return "Manejo de dirección (por implementar)"
    
    async def handle_confirmacion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Confirmar pedido"""
        return "Confirmación de pedido (por implementar)"
