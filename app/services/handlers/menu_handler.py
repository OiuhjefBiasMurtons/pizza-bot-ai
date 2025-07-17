"""
Handler para manejar el menú principal del bot
"""

from .base_handler import BaseHandler
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MenuHandler(BaseHandler):
    """
    Handler para manejar el menú principal y navegación
    """
    
    def handle_menu(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja las opciones del menú principal
        """
        logger.info(f"🍕 Mostrando menú para: {numero_whatsapp}")
        
        # Verificar si el usuario está registrado
        from app.models.cliente import Cliente
        
        usuario = self.db.query(Cliente).filter(
            Cliente.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not usuario:
            return {
                'success': False,
                'response': "❌ Usuario no encontrado. Por favor, regístrate primero."
            }
        
        # Procesar opción del menú
        opcion = mensaje.strip().lower()
        
        # Si es comando "menu" desde comando especial, mostrar pizzas directamente (compatibilidad)
        if opcion in ['menu', 'menú']:
            return self._show_pizza_menu_original_style()
        elif opcion in ['1', 'ver menu', 'ver menú']:
            return self._show_pizza_menu()
        elif opcion in ['2', 'pedido', 'hacer pedido', 'pedir']:
            return self._start_order_process(numero_whatsapp)
        elif opcion in ['3', 'info', 'información', 'mi información']:
            return self._show_user_info(usuario)
        elif opcion in ['4', 'ayuda', 'help']:
            return self._show_help()
        else:
            return self._show_main_menu()
    
    def _show_pizza_menu(self) -> Dict[str, Any]:
        """
        Muestra el menú de pizzas disponibles
        """
        from app.models.pizza import Pizza
        
        pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
        if not pizzas:
            return {
                'success': False,
                'response': "❌ No hay pizzas disponibles en este momento."
            }
        
        menu_text = "🍕 *MENÚ DE PIZZAS* 🍕\n\n"
        
        for i, pizza in enumerate(pizzas, 1):
            menu_text += f"{i}️⃣ *{pizza.nombre}* {pizza.emoji}\n"
            menu_text += f"   📝 {pizza.descripcion}\n"
            menu_text += f"   💰 Pequeña: ${pizza.precio_pequena:.2f}\n"
            menu_text += f"   💰 Mediana: ${pizza.precio_mediana:.2f}\n"
            menu_text += f"   💰 Grande: ${pizza.precio_grande:.2f}\n\n"
        
        menu_text += "Para hacer un pedido, escribe *2* o *pedido*"
        
        return {
            'success': True,
            'response': menu_text
        }
    
    def _show_pizza_menu_original_style(self) -> Dict[str, Any]:
        """
        Muestra el menú de pizzas en estilo original (compatible con bot_service original)
        """
        from app.models.pizza import Pizza
        
        pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
        if not pizzas:
            return {
                'success': False,
                'response': "❌ No hay pizzas disponibles en este momento."
            }
        
        mensaje = "🍕 *MENÚ DE PIZZAS* 🍕\n\n"
        
        for i, pizza in enumerate(pizzas, 1):
            mensaje += f"{i}. {pizza.emoji} *{pizza.nombre}*\n"
            mensaje += f"   {pizza.descripcion}\n"
            mensaje += f"   • Pequeña: ${pizza.precio_pequena:.2f}\n"
            mensaje += f"   • Mediana: ${pizza.precio_mediana:.2f}\n"
            mensaje += f"   • Grande: ${pizza.precio_grande:.2f}\n\n"
        
        mensaje += "📝 *CÓMO ORDENAR:*\n"
        mensaje += "• Una pizza: '1 mediana' o '2 grande'\n"
        mensaje += "• Múltiples pizzas: '1 grande, 2 mediana'\n"
        mensaje += "• También: '1 grande, 3 pequeña, 2 mediana'\n\n"
        mensaje += "¿Qué pizzas te gustaría ordenar? 🍕"
        
        return {
            'success': True,
            'response': mensaje,
            'set_state': 'MENU'  # Indicar que debe establecer estado MENU
        }
    
    def _start_order_process(self, numero_whatsapp: str) -> Dict[str, Any]:
        """
        Inicia el proceso de pedido
        """
        # Cambiar estado a pedido
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['PEDIDO'])
        
        # Inicializar estado del pedido (no limpiar todo)
        self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'seleccion_pizza')
        
        return {
            'success': True,
            'response': "🛒 *NUEVO PEDIDO*\n\n¿Qué pizza te gustaría ordenar?\n\nPuedes escribir:\n• El nombre de la pizza\n• El número de la pizza del menú\n• *menu* para ver todas las opciones"
        }
    
    def _show_user_info(self, usuario) -> Dict[str, Any]:
        """
        Muestra información del usuario
        """
        info_text = f"👤 *TU INFORMACIÓN*\n\n"
        info_text += f"📱 Nombre: {usuario.nombre}\n"
        info_text += f"🏠 Dirección: {usuario.direccion}\n"
        info_text += f"📞 WhatsApp: {usuario.numero_whatsapp}\n\n"
        
        # Mostrar pedidos recientes si los hay
        from app.models.pedido import Pedido
        
        pedidos_recientes = self.db.query(Pedido).filter(
            Pedido.cliente_id == usuario.id
        ).order_by(Pedido.fecha_pedido.desc()).limit(3).all()
        
        if pedidos_recientes:
            info_text += "🍕 *PEDIDOS RECIENTES*\n\n"
            for pedido in pedidos_recientes:
                info_text += f"• {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')} - "
                info_text += f"Estado: {pedido.estado}\n"
        
        return {
            'success': True,
            'response': info_text
        }
    
    def _show_help(self) -> Dict[str, Any]:
        """
        Muestra información de ayuda
        """
        help_text = "🆘 *AYUDA*\n\n"
        help_text += "📋 *Comandos disponibles:*\n\n"
        help_text += "• *1* o *menu* - Ver menú de pizzas\n"
        help_text += "• *2* o *pedido* - Hacer un pedido\n"
        help_text += "• *3* o *info* - Ver tu información\n"
        help_text += "• *4* o *ayuda* - Mostrar esta ayuda\n"
        help_text += "• *cancelar* - Cancelar operación actual\n"
        help_text += "• *menu principal* - Volver al menú principal\n\n"
        help_text += "💡 *Consejos:*\n"
        help_text += "• Puedes escribir de forma natural\n"
        help_text += "• Si tienes problemas, escribe *ayuda*\n"
        help_text += "• Para cancelar cualquier proceso, escribe *cancelar*\n\n"
        help_text += "🕐 *Horario de atención:*\n"
        help_text += "Lunes a Domingo: 11:00 AM - 11:00 PM"
        
        return {
            'success': True,
            'response': help_text
        }
    
    def _show_main_menu(self) -> Dict[str, Any]:
        """
        Muestra el menú principal
        """
        menu_text = "🍕 *MENÚ PRINCIPAL*\n\n"
        menu_text += "1️⃣ Ver menú de pizzas\n"
        menu_text += "2️⃣ Hacer un pedido\n"
        menu_text += "3️⃣ Ver mi información\n"
        menu_text += "4️⃣ Ayuda\n\n"
        menu_text += "Escribe el número de la opción que deseas:"
        
        return {
            'success': True,
            'response': menu_text
        }
    
    def is_menu_option(self, mensaje: str) -> bool:
        """
        Verifica si el mensaje es una opción válida del menú
        """
        opciones_validas = [
            '1', '2', '3', '4',
            'menu', 'menú', 'ver menu', 'ver menú',
            'pedido', 'hacer pedido', 'pedir',
            'info', 'información', 'mi información',
            'ayuda', 'help'
        ]
        
        return mensaje.strip().lower() in opciones_validas
