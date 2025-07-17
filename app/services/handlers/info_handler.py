"""
Handler para manejar información y ayuda del bot
"""

from .base_handler import BaseHandler
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class InfoHandler(BaseHandler):
    """
    Handler para manejar información del usuario y ayuda
    """
    
    def handle_info_request(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja solicitudes de información
        """
        mensaje_lower = mensaje.lower().strip()
        
        if mensaje_lower in ['info', 'información', 'mi información', 'perfil']:
            return self._show_user_info(numero_whatsapp)
        elif mensaje_lower in ['ayuda', 'help', 'comandos']:
            return self._show_help()
        elif mensaje_lower in ['horario', 'horarios', 'cuando abren']:
            return self._show_business_hours()
        elif mensaje_lower in ['contacto', 'teléfono', 'telefono']:
            return self._show_contact_info()
        else:
            return self._show_general_info()
    
    def _show_user_info(self, numero_whatsapp: str) -> Dict[str, Any]:
        """
        Muestra información del usuario
        """
        from app.models.cliente import Cliente
        
        usuario = self.db.query(Cliente).filter(
            Cliente.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not usuario:
            return {
                'success': False,
                'response': "❌ Usuario no encontrado. Por favor, regístrate primero."
            }
        
        info_text = f"👤 *TU INFORMACIÓN*\n\n"
        info_text += f"📱 Nombre: {usuario.nombre}\n"
        info_text += f"🏠 Dirección: {usuario.direccion}\n"
        info_text += f"📞 WhatsApp: {usuario.numero_whatsapp}\n"
        info_text += f"📅 Registrado: {usuario.fecha_registro.strftime('%d/%m/%Y')}\n\n"
        
        # Mostrar estadísticas de pedidos
        from app.models.pedido import Pedido
        
        total_pedidos = self.db.query(Pedido).filter(
            Pedido.cliente_id == usuario.id
        ).count()
        
        pedidos_completados = self.db.query(Pedido).filter(
            Pedido.cliente_id == usuario.id,
            Pedido.estado == 'entregado'
        ).count()
        
        info_text += f"📊 *ESTADÍSTICAS*\n"
        info_text += f"🛒 Total de pedidos: {total_pedidos}\n"
        info_text += f"✅ Pedidos completados: {pedidos_completados}\n\n"
        
        # Mostrar pedidos recientes
        pedidos_recientes = self.db.query(Pedido).filter(
            Pedido.cliente_id == usuario.id
        ).order_by(Pedido.fecha_pedido.desc()).limit(3).all()
        
        if pedidos_recientes:
            info_text += "🍕 *PEDIDOS RECIENTES*\n\n"
            for pedido in pedidos_recientes:
                info_text += f"• #{pedido.id} - {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}\n"
                info_text += f"  Estado: {pedido.estado.upper()}\n"
                info_text += f"  Total: ${pedido.total:.2f}\n\n"
        
        return {
            'success': True,
            'response': info_text
        }
    
    def _show_help(self) -> Dict[str, Any]:
        """
        Muestra información de ayuda
        """
        help_text = "🆘 *AYUDA - PIZZA EXPRESS*\n\n"
        help_text += "📋 *Comandos principales:*\n\n"
        help_text += "• *1* o *menu* - Ver menú de pizzas\n"
        help_text += "• *2* o *pedido* - Hacer un pedido\n"
        help_text += "• *3* o *info* - Ver tu información\n"
        help_text += "• *4* o *ayuda* - Mostrar esta ayuda\n\n"
        help_text += "📋 *Comandos adicionales:*\n\n"
        help_text += "• *horario* - Ver horario de atención\n"
        help_text += "• *contacto* - Información de contacto\n"
        help_text += "• *cancelar* - Cancelar operación actual\n"
        help_text += "• *menu principal* - Volver al menú principal\n\n"
        help_text += "💡 *Consejos útiles:*\n\n"
        help_text += "• Puedes escribir de forma natural\n"
        help_text += "• No necesitas usar mayúsculas\n"
        help_text += "• Si algo no funciona, escribe *ayuda*\n"
        help_text += "• Para cancelar cualquier proceso, escribe *cancelar*\n\n"
        help_text += "🤖 *Acerca de este bot:*\n\n"
        help_text += "Este bot te ayuda a:\n"
        help_text += "• Ver nuestro menú de pizzas\n"
        help_text += "• Hacer pedidos fácilmente\n"
        help_text += "• Seguir el estado de tus pedidos\n"
        help_text += "• Gestionar tu información\n\n"
        help_text += "¿Necesitas más ayuda? Escribe *contacto*"
        
        return {
            'success': True,
            'response': help_text
        }
    
    def _show_business_hours(self) -> Dict[str, Any]:
        """
        Muestra horarios de atención
        """
        hours_text = "🕐 *HORARIOS DE ATENCIÓN*\n\n"
        hours_text += "📅 **Lunes a Jueves:**\n"
        hours_text += "   🕐 11:00 AM - 10:00 PM\n\n"
        hours_text += "📅 **Viernes a Sábado:**\n"
        hours_text += "   🕐 11:00 AM - 11:00 PM\n\n"
        hours_text += "📅 **Domingo:**\n"
        hours_text += "   🕐 12:00 PM - 10:00 PM\n\n"
        hours_text += "⏰ *Tiempo de entrega:*\n"
        hours_text += "   📍 25-35 minutos promedio\n\n"
        hours_text += "🚚 *Zona de entrega:*\n"
        hours_text += "   📍 Radio de 5 km desde nuestra pizzería\n\n"
        hours_text += "💡 *Nota:* Los pedidos se procesan hasta 30 minutos antes del cierre"
        
        return {
            'success': True,
            'response': hours_text
        }
    
    def _show_contact_info(self) -> Dict[str, Any]:
        """
        Muestra información de contacto
        """
        contact_text = "📞 *INFORMACIÓN DE CONTACTO*\n\n"
        contact_text += "🏪 **Pizza Express**\n\n"
        contact_text += "📍 *Dirección:*\n"
        contact_text += "   Av. Principal 123\n"
        contact_text += "   Colonia Centro\n"
        contact_text += "   Ciudad, CP 12345\n\n"
        contact_text += "📞 *Teléfono:*\n"
        contact_text += "   +52 55 1234-5678\n\n"
        contact_text += "📱 *WhatsApp:*\n"
        contact_text += "   Este mismo número\n\n"
        contact_text += "🌐 *Redes sociales:*\n"
        contact_text += "   📘 Facebook: @PizzaExpress\n"
        contact_text += "   📷 Instagram: @pizza_express\n\n"
        contact_text += "✉️ *Email:*\n"
        contact_text += "   info@pizzaexpress.com\n\n"
        contact_text += "🆘 *Soporte técnico:*\n"
        contact_text += "   soporte@pizzaexpress.com"
        
        return {
            'success': True,
            'response': contact_text
        }
    
    def _show_general_info(self) -> Dict[str, Any]:
        """
        Muestra información general del bot
        """
        info_text = "ℹ️ *INFORMACIÓN GENERAL*\n\n"
        info_text += "🍕 **Pizza Express - Bot de WhatsApp**\n\n"
        info_text += "¿Qué puedo hacer por ti?\n\n"
        info_text += "• 📋 Ver nuestro menú completo\n"
        info_text += "• 🛒 Hacer pedidos rápidamente\n"
        info_text += "• 👤 Gestionar tu información\n"
        info_text += "• 📞 Obtener información de contacto\n"
        info_text += "• 🕐 Consultar horarios\n"
        info_text += "• 🆘 Recibir ayuda\n\n"
        info_text += "💡 *Comandos útiles:*\n"
        info_text += "• Escribe *menu* para ver pizzas\n"
        info_text += "• Escribe *pedido* para ordenar\n"
        info_text += "• Escribe *ayuda* para más información\n\n"
        info_text += "¿Listo para comenzar? Escribe *menu* para ver nuestras deliciosas pizzas 🍕"
        
        return {
            'success': True,
            'response': info_text
        }
    
    def handle_order_status(self, numero_whatsapp: str, pedido_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Maneja consultas de estado de pedido
        """
        from app.models.cliente import Cliente
        from app.models.pedido import Pedido
        
        usuario = self.db.query(Cliente).filter(
            Cliente.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not usuario:
            return {
                'success': False,
                'response': "❌ Usuario no encontrado. Por favor, regístrate primero."
            }
        
        if pedido_id:
            # Buscar pedido específico
            try:
                pedido_num = int(pedido_id.replace('#', ''))
                pedido = self.db.query(Pedido).filter(
                    Pedido.id == pedido_num,
                    Pedido.cliente_id == usuario.id
                ).first()
                
                if not pedido:
                    return {
                        'success': False,
                        'response': f"❌ No se encontró el pedido #{pedido_num} o no te pertenece."
                    }
                
                return self._show_order_details(pedido)
                
            except ValueError:
                return {
                    'success': False,
                    'response': "❌ Formato de número de pedido inválido. Usa el formato: #123"
                }
        else:
            # Mostrar pedidos recientes
            pedidos_recientes = self.db.query(Pedido).filter(
                Pedido.cliente_id == usuario.id
            ).order_by(Pedido.fecha_pedido.desc()).limit(5).all()
            
            if not pedidos_recientes:
                return {
                    'success': False,
                    'response': "📋 No tienes pedidos registrados.\n\n¿Quieres hacer tu primer pedido? Escribe *pedido*"
                }
            
            status_text = "📋 *TUS PEDIDOS RECIENTES*\n\n"
            
            for pedido in pedidos_recientes:
                status_icon = self._get_status_icon(getattr(pedido, 'estado', 'pendiente'))
                status_text += f"{status_icon} **#{pedido.id}** - {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}\n"
                status_text += f"   Estado: {getattr(pedido, 'estado', 'pendiente').upper()}\n"
                status_text += f"   Total: ${pedido.total:.2f}\n\n"
            
            status_text += "💡 Para ver detalles de un pedido específico, escribe: *pedido #123*"
            
            return {
                'success': True,
                'response': status_text
            }
    
    def _show_order_details(self, pedido) -> Dict[str, Any]:
        """
        Muestra detalles de un pedido específico
        """
        from app.models.pedido import DetallePedido
        
        detalles = self.db.query(DetallePedido).filter(
            DetallePedido.pedido_id == pedido.id
        ).all()
        
        status_icon = self._get_status_icon(getattr(pedido, 'estado', 'pendiente'))
        
        details_text = f"📋 *DETALLES DEL PEDIDO #{pedido.id}*\n\n"
        details_text += f"📅 Fecha: {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}\n"
        details_text += f"{status_icon} Estado: {getattr(pedido, 'estado', 'pendiente').upper()}\n"
        details_text += f"🏠 Dirección: {pedido.direccion_entrega}\n\n"
        details_text += "🍕 *Productos:*\n\n"
        
        for detalle in detalles:
            details_text += f"• {detalle.pizza.nombre} ({detalle.tamano})\n"
            details_text += f"  Cantidad: {detalle.cantidad}\n"
            details_text += f"  Precio: ${detalle.precio_unitario:.2f} c/u\n"
            details_text += f"  Subtotal: ${detalle.subtotal:.2f}\n\n"
        
        details_text += f"💰 **Total: ${pedido.total:.2f}**\n\n"
        details_text += self._get_status_message(getattr(pedido, 'estado', 'pendiente'))
        
        return {
            'success': True,
            'response': details_text
        }
    
    def _get_status_icon(self, estado: str) -> str:
        """
        Obtiene el icono correspondiente al estado
        """
        iconos = {
            'pendiente': '⏳',
            'confirmado': '✅',
            'preparando': '👨‍🍳',
            'horneando': '🔥',
            'listo': '🍕',
            'en_camino': '🚚',
            'entregado': '✅',
            'cancelado': '❌'
        }
        return iconos.get(estado, '❓')
    
    def _get_status_message(self, estado: str) -> str:
        """
        Obtiene el mensaje correspondiente al estado
        """
        mensajes = {
            'pendiente': '⏳ Tu pedido está siendo procesado...',
            'confirmado': '✅ Tu pedido ha sido confirmado y está en la cola de preparación.',
            'preparando': '👨‍🍳 Nuestros chefs están preparando tu pedido.',
            'horneando': '🔥 Tu pizza está en el horno. ¡Casi lista!',
            'listo': '🍕 Tu pedido está listo para ser entregado.',
            'en_camino': '🚚 Tu pedido está en camino. ¡Llegará pronto!',
            'entregado': '✅ Tu pedido ha sido entregado. ¡Gracias por elegirnos!',
            'cancelado': '❌ Este pedido ha sido cancelado.'
        }
        return mensajes.get(estado, '❓ Estado desconocido')
