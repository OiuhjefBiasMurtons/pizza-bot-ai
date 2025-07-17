"""
Nuevo BotService refactorizado que usa handlers separados
"""

from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.models.conversation_state import ConversationState
from app.services.handlers import (
    RegistrationHandler,
    MenuHandler,
    OrderHandler,
    InfoHandler
)
import logging
from typing import Optional

# Configurar logger
logger = logging.getLogger(__name__)

class BotService:
    """
    Servicio principal del bot que coordina diferentes handlers
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Inicializar handlers
        self.registration_handler = RegistrationHandler(db)
        self.menu_handler = MenuHandler(db)
        self.order_handler = OrderHandler(db)
        self.info_handler = InfoHandler(db)
        
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
    
    async def process_message(self, numero_whatsapp: str, mensaje: str) -> str:
        """
        Procesar mensaje del usuario y generar respuesta
        """
        try:
            # Limpiar mensaje
            mensaje = mensaje.strip()
            mensaje_lower = mensaje.lower()
            
            logger.info(f"📨 Procesando mensaje - Usuario: {numero_whatsapp}, Mensaje: '{mensaje}'")
            
            # Verificar si el cliente está registrado
            cliente = self.get_cliente(numero_whatsapp)
            
            # Obtener estado actual de la conversación
            estado_actual = self.get_conversation_state(numero_whatsapp)
            
            logger.info(f"🔍 Estado actual: {estado_actual}, Cliente registrado: {cliente is not None}")
            
            # Si el cliente no está registrado, usar registration handler
            if not cliente or not self._is_user_complete(cliente):
                result = self.registration_handler.handle_registration_flow(numero_whatsapp, mensaje)
                return result.get('response', 'Error en el proceso de registro')
            
            # Cliente registrado - manejar comandos especiales
            if self._is_special_command(mensaje_lower):
                return await self._handle_special_command(numero_whatsapp, mensaje_lower, cliente)
            
            # Procesar según estado actual usando handlers apropiados
            return await self._route_to_handler(numero_whatsapp, mensaje, cliente, estado_actual)
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            return "❌ Lo siento, ocurrió un error. Por favor, intenta nuevamente."
    
    def _is_user_complete(self, cliente: Cliente) -> bool:
        """
        Verificar si el usuario está completamente registrado
        """
        return cliente and cliente.nombre and cliente.direccion
    
    def _is_pizza_selection(self, mensaje: str) -> bool:
        """
        Verificar si el mensaje es una selección de pizza en formato original
        """
        import re
        # Buscar patrones como "1 mediana", "2 grande", "1 grande, 2 mediana"
        patrones = re.findall(r'(\d+)\s*(pequeña|mediana|grande|pequeña|small|medium|large)', mensaje.lower())
        return len(patrones) > 0
    
    def _is_special_command(self, mensaje_lower: str) -> bool:
        """
        Verificar si es un comando especial que reinicia el flujo
        """
        comandos_especiales = [
            'hola', 'hello', 'buenas', 'inicio', 'empezar',
            'menu', 'menú', 'carta',
            'ayuda', 'help',
            'pedido', 'mis pedidos', 'estado',
            'info', 'información', 'mi información',
            'cancelar', 'salir', 'reiniciar'
        ]
        return mensaje_lower in comandos_especiales
    
    async def _handle_special_command(self, numero_whatsapp: str, mensaje_lower: str, cliente: Cliente) -> str:
        """
        Manejar comandos especiales
        """
        if mensaje_lower in ['hola', 'hello', 'buenas', 'inicio', 'empezar']:
            return self._handle_registered_greeting(numero_whatsapp, cliente)
        
        elif mensaje_lower in ['menu', 'menú', 'carta']:
            result = self.menu_handler.handle_menu(numero_whatsapp, 'menu')
            # Si el resultado indica que debe establecer estado MENU, hacerlo
            if result.get('set_state') == 'MENU':
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['MENU'])
            return result.get('response', 'Error mostrando menú')
        
        elif mensaje_lower in ['ayuda', 'help']:
            result = self.info_handler.handle_info_request(numero_whatsapp, 'ayuda')
            return result.get('response', 'Error mostrando ayuda')
        
        elif mensaje_lower in ['pedido', 'mis pedidos', 'estado']:
            result = self.info_handler.handle_order_status(numero_whatsapp)
            return result.get('response', 'Error consultando pedidos')
        
        elif mensaje_lower in ['info', 'información', 'mi información']:
            result = self.info_handler.handle_info_request(numero_whatsapp, 'info')
            return result.get('response', 'Error mostrando información')
        
        elif mensaje_lower in ['cancelar', 'salir', 'reiniciar']:
            return self._handle_cancel_operation(numero_whatsapp, cliente)
        
        else:
            return self._handle_registered_greeting(numero_whatsapp, cliente)
    
    async def _route_to_handler(self, numero_whatsapp: str, mensaje: str, cliente: Cliente, estado_actual: str) -> str:
        """
        Enrutar el mensaje al handler apropiado según el estado
        """
        if estado_actual in [self.ESTADOS['INICIO']]:
            return self._handle_registered_greeting(numero_whatsapp, cliente)
        
        elif estado_actual in [self.ESTADOS['REGISTRO_NOMBRE'], self.ESTADOS['REGISTRO_DIRECCION']]:
            result = self.registration_handler.handle_registration_flow(numero_whatsapp, mensaje)
            return result.get('response', 'Error en el proceso de registro')
        
        elif estado_actual == self.ESTADOS['MENU']:
            # Si es una selección de pizza en formato original, enviarlo al order_handler
            if self._is_pizza_selection(mensaje):
                # Cambiar estado a PEDIDO y procesar
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['PEDIDO'])
                result = self.order_handler.handle_order_process(numero_whatsapp, mensaje)
                return result.get('response', 'Error procesando pedido')
            else:
                # Es navegación del menú principal
                result = self.menu_handler.handle_menu(numero_whatsapp, mensaje)
                return result.get('response', 'Error procesando menú')
        
        elif estado_actual == self.ESTADOS['PEDIDO']:
            result = self.order_handler.handle_order_process(numero_whatsapp, mensaje)
            return result.get('response', 'Error procesando pedido')
        
        elif estado_actual in [self.ESTADOS['DIRECCION'], self.ESTADOS['CONFIRMACION']]:
            result = self.order_handler.handle_order_process(numero_whatsapp, mensaje)
            return result.get('response', 'Error procesando pedido')
        
        else:
            # Estado desconocido, reiniciar
            logger.warning(f"⚠️ Estado desconocido: {estado_actual}, reiniciando...")
            return self._handle_registered_greeting(numero_whatsapp, cliente)
    
    def _handle_registered_greeting(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """
        Manejar saludo para usuario registrado
        """
        # Establecer estado en menú
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['MENU'])
        
        greeting = f"¡Hola {cliente.nombre}! 🍕 Bienvenido a Pizza Express.\n\n"
        greeting += "🍕 *MENÚ PRINCIPAL*\n\n"
        greeting += "1️⃣ Ver menú de pizzas\n"
        greeting += "2️⃣ Hacer un pedido\n"
        greeting += "3️⃣ Ver mi información\n"
        greeting += "4️⃣ Ayuda\n\n"
        greeting += "Escribe el número de la opción que deseas:"
        
        return greeting
    
    def _handle_cancel_operation(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """
        Cancelar operación actual y volver al menú principal
        """
        # Limpiar datos temporales
        self.clear_conversation_data(numero_whatsapp)
        
        # Volver al menú principal
        return self._handle_registered_greeting(numero_whatsapp, cliente)
    
    # Métodos de utilidad para manejo de estado y datos
    def get_cliente(self, numero_whatsapp: str) -> Optional[Cliente]:
        """
        Obtener cliente por número de WhatsApp
        """
        return self.db.query(Cliente).filter(
            Cliente.numero_whatsapp == numero_whatsapp
        ).first()
    
    def get_conversation_state(self, numero_whatsapp: str) -> str:
        """
        Obtener estado actual de la conversación
        """
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if conv_state:
            return getattr(conv_state, 'estado_actual', self.ESTADOS['INICIO'])
        
        return self.ESTADOS['INICIO']
    
    def set_conversation_state(self, numero_whatsapp: str, estado: str):
        """
        Establecer estado de la conversación
        """
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not conv_state:
            conv_state = ConversationState(numero_whatsapp=numero_whatsapp)
            self.db.add(conv_state)
        
        setattr(conv_state, 'estado_actual', estado)
        self.db.commit()
        
        logger.info(f"💾 Estado guardado - Usuario: {numero_whatsapp}, Estado: {estado}")
    
    def clear_conversation_data(self, numero_whatsapp: str):
        """
        Limpiar datos de conversación
        """
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if conv_state:
            setattr(conv_state, 'estado_actual', self.ESTADOS['INICIO'])
            setattr(conv_state, 'datos_temporales', None)
            self.db.commit()
            
            logger.info(f"🗑️ Datos de conversación limpiados - Usuario: {numero_whatsapp}")
    
    # Métodos para compatibilidad con el código existente
    async def handle_webhook(self, data: dict) -> str:
        """
        Manejar webhook de WhatsApp (mantener compatibilidad)
        """
        # Extraer información del webhook
        numero_whatsapp = data.get('from', '')
        mensaje = data.get('body', '')
        
        if not numero_whatsapp or not mensaje:
            logger.warning("⚠️ Webhook recibido con datos incompletos")
            return "Error: datos incompletos"
        
        # Procesar mensaje
        return await self.process_message(numero_whatsapp, mensaje)
    
    def get_menu_text(self) -> str:
        """
        Obtener texto del menú (para compatibilidad)
        """
        result = self.menu_handler._show_pizza_menu()
        return result.get('response', 'Error mostrando menú')
    
    def validate_pizza_selection(self, input_text: str) -> bool:
        """
        Validar selección de pizza (para compatibilidad)
        """
        pizza_encontrada = self.order_handler._find_pizza_by_input(input_text)
        return pizza_encontrada is not None
    
    def get_pizza_by_selection(self, input_text: str):
        """
        Obtener pizza por selección (para compatibilidad)
        """
        return self.order_handler._find_pizza_by_input(input_text)
