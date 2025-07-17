"""
Handler para manejar el flujo de registro de usuarios
"""

from .base_handler import BaseHandler
from typing import Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)

class RegistrationHandler(BaseHandler):
    """
    Handler para manejar el registro de usuarios nuevos
    """
    
    def handle_registration_flow(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja el flujo de registro de usuarios
        """
        logger.info(f"🔄 Iniciando flujo de registro para: {numero_whatsapp}")
        
        from app.models.conversation_state import ConversationState
        from app.models.cliente import Cliente
        
        # Obtener estado actual
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        estado_actual = getattr(conv_state, 'estado_actual', self.ESTADOS['INICIO']) if conv_state else self.ESTADOS['INICIO']
        
        # Manejar diferentes estados del registro
        if estado_actual == self.ESTADOS['INICIO']:
            return self._handle_initial_registration(numero_whatsapp, mensaje)
        elif estado_actual == self.ESTADOS['REGISTRO_NOMBRE']:
            return self._handle_name_registration(numero_whatsapp, mensaje)
        elif estado_actual == self.ESTADOS['REGISTRO_DIRECCION']:
            return self._handle_address_registration(numero_whatsapp, mensaje)
        else:
            return {
                'success': False,
                'response': 'Estado de registro no válido'
            }
    
    def _handle_initial_registration(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja el inicio del registro
        """
        # Cambiar estado a registro de nombre
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['REGISTRO_NOMBRE'])
        
        return {
            'success': True,
            'response': "¡Hola! 🍕 Bienvenido a Pizza Express.\n\nPara comenzar, necesito que me digas tu nombre completo:"
        }
    
    def _handle_name_registration(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja el registro del nombre
        """
        # Validar que el nombre tenga al menos 3 caracteres
        if len(mensaje.strip()) < 3:
            return {
                'success': False,
                'response': "⚠️ El nombre debe tener al menos 3 caracteres. Por favor, ingresa tu nombre completo:"
            }
        
        # Validar que no tenga números
        if re.search(r'\d', mensaje):
            return {
                'success': False,
                'response': "⚠️ El nombre no puede contener números. Por favor, ingresa tu nombre completo:"
            }
        
        # Guardar nombre en datos temporales
        self.set_temporary_value(numero_whatsapp, 'nombre_pendiente', mensaje.strip())
        
        # Cambiar estado a registro de dirección
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['REGISTRO_DIRECCION'])
        
        return {
            'success': True,
            'response': f"¡Perfecto, {mensaje.strip()}! 👋\n\nAhora necesito tu dirección de entrega completa:"
        }
    
    def _handle_address_registration(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja el registro de la dirección
        """
        # Validar que la dirección tenga al menos 10 caracteres
        if len(mensaje.strip()) < 10:
            return {
                'success': False,
                'response': "⚠️ La dirección debe ser más específica. Por favor, ingresa tu dirección completa:"
            }
        
        # Obtener nombre pendiente
        nombre_pendiente = self.get_temporary_value(numero_whatsapp, 'nombre_pendiente')
        
        if not nombre_pendiente:
            # Si no hay nombre pendiente, reiniciar registro
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['REGISTRO_NOMBRE'])
            return {
                'success': False,
                'response': "❌ Error en el proceso de registro. Por favor, ingresa tu nombre completo:"
            }
        
        # Crear nuevo usuario
        from app.models.cliente import Cliente
        
        try:
            nuevo_usuario = Cliente(
                nombre=nombre_pendiente,
                numero_whatsapp=numero_whatsapp,
                direccion=mensaje.strip()
            )
            self.db.add(nuevo_usuario)
            self.db.commit()
            
            # Limpiar datos temporales
            self.clear_conversation_data(numero_whatsapp)
            
            # Cambiar estado a menú
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['MENU'])
            
            logger.info(f"✅ Usuario registrado exitosamente: {numero_whatsapp} - {nombre_pendiente}")
            
            return {
                'success': True,
                'response': f"¡Excelente, {nombre_pendiente}! ✅\n\nTu registro ha sido completado exitosamente.\n\n🍕 *MENÚ PRINCIPAL*\n\n1️⃣ Ver menú de pizzas\n2️⃣ Hacer un pedido\n3️⃣ Ver mi información\n4️⃣ Ayuda\n\nEscribe el número de la opción que deseas:"
            }
            
        except Exception as e:
            logger.error(f"❌ Error al registrar usuario: {e}")
            self.db.rollback()
            return {
                'success': False,
                'response': "❌ Error al completar el registro. Por favor, intenta nuevamente más tarde."
            }
    
    def is_valid_name(self, nombre: str) -> bool:
        """
        Valida si un nombre es válido
        """
        # Mínimo 3 caracteres
        if len(nombre.strip()) < 3:
            return False
        
        # No debe contener números
        if re.search(r'\d', nombre):
            return False
        
        # Solo letras, espacios y algunos caracteres especiales
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-\.]+$', nombre):
            return False
        
        return True
    
    def is_valid_address(self, direccion: str) -> bool:
        """
        Valida si una dirección es válida
        """
        # Mínimo 10 caracteres
        if len(direccion.strip()) < 10:
            return False
        
        return True
