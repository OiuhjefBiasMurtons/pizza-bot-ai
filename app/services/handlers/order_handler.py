"""
Handler para manejar el proceso de pedidos
"""

from .base_handler import BaseHandler
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)

class OrderHandler(BaseHandler):
    """
    Handler para manejar el proceso completo de pedidos
    """
    
    def handle_order_process(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja el proceso completo de pedidos
        """
        logger.info(f"🛒 Procesando pedido para: {numero_whatsapp}")
        
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
        
        # Obtener estado actual del pedido
        estado_pedido = self.get_temporary_value(numero_whatsapp, 'estado_pedido') or 'seleccion_pizza'
        
        if estado_pedido == 'seleccion_pizza':
            return self._handle_pizza_selection(numero_whatsapp, mensaje)
        elif estado_pedido == 'continuar_pedido':
            return self._handle_continuar_pedido_original(numero_whatsapp, mensaje)
        elif estado_pedido == 'confirmar_pizza':
            return self._handle_pizza_confirmation(numero_whatsapp, mensaje)
        elif estado_pedido == 'seleccionar_tamano':
            return self._handle_size_selection(numero_whatsapp, mensaje)
        elif estado_pedido == 'cantidad':
            return self._handle_quantity_selection(numero_whatsapp, mensaje)
        elif estado_pedido == 'direccion':
            return self._handle_delivery_address(numero_whatsapp, mensaje, usuario)
        elif estado_pedido == 'confirmacion_final':
            return self._handle_final_confirmation(numero_whatsapp, mensaje, usuario)
        else:
            return self._restart_order_process(numero_whatsapp)
    
    def _handle_pizza_selection(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja la selección de pizza (compatible con formato original)
        """
        # Primero intentar con el formato original "1 mediana, 2 grande"
        if self._is_original_format_selection(mensaje):
            return self._handle_original_format_selection(numero_whatsapp, mensaje)
        
        # Si el usuario pide ver el menú
        if mensaje.lower() in ['menu', 'menú', 'ver menu', 'ver menú']:
            return self._show_pizza_menu_for_order()
        
        # Buscar pizza por nombre o número (formato nuevo)
        pizza_encontrada = self._find_pizza_by_input(mensaje)
        
        if not pizza_encontrada:
            return {
                'success': False,
                'response': "❌ No encontré esa pizza. Por favor, escribe:\n• El nombre exacto de la pizza\n• El número de la pizza del menú\n• Formato: '1 mediana' o '2 grande'\n• Múltiples: '1 grande, 2 mediana'\n• *menu* para ver todas las opciones"
            }
        
        # Guardar pizza seleccionada
        self.set_temporary_value(numero_whatsapp, 'pizza_seleccionada', {
            'id': pizza_encontrada.id,
            'nombre': pizza_encontrada.nombre,
            'descripcion': pizza_encontrada.descripcion,
            'precio_pequena': float(getattr(pizza_encontrada, 'precio_pequena', 0)),
            'precio_mediana': float(getattr(pizza_encontrada, 'precio_mediana', 0)),
            'precio_grande': float(getattr(pizza_encontrada, 'precio_grande', 0))
        })
        
        # Cambiar estado a confirmación
        self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'confirmar_pizza')
        
        return {
            'success': True,
            'response': f"🍕 *{pizza_encontrada.nombre}* {getattr(pizza_encontrada, 'emoji', '🍕')}\n\n📝 {pizza_encontrada.descripcion}\n\n💰 Precios:\n• Pequeña: ${getattr(pizza_encontrada, 'precio_pequena', 0):.2f}\n• Mediana: ${getattr(pizza_encontrada, 'precio_mediana', 0):.2f}\n• Grande: ${getattr(pizza_encontrada, 'precio_grande', 0):.2f}\n\n¿Confirmas esta pizza?\n\n✅ *Sí* - Continuar\n❌ *No* - Elegir otra pizza"
        }
    
    def _handle_pizza_confirmation(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja la confirmación de la pizza seleccionada
        """
        respuesta = mensaje.lower().strip()
        
        if respuesta in ['si', 'sí', 'yes', 'confirmar', 'ok', 'vale']:
            # Cambiar estado a selección de tamaño
            self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'seleccionar_tamano')
            
            return {
                'success': True,
                'response': "� ¿Qué tamaño quieres?\n\n1️⃣ *Pequeña*\n2️⃣ *Mediana*\n3️⃣ *Grande*\n\nEscribe el número o el nombre del tamaño:"
            }
        
        elif respuesta in ['no', 'cambiar', 'otra', 'diferente']:
            # Volver a selección de pizza
            self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'seleccion_pizza')
            
            return {
                'success': True,
                'response': "🔄 Perfecto, elige otra pizza:\n\n¿Qué pizza te gustaría ordenar?\n\nPuedes escribir:\n• El nombre de la pizza\n• El número de la pizza del menú\n• *menu* para ver todas las opciones"
            }
        
        else:
            return {
                'success': False,
                'response': "❓ Por favor, responde:\n\n✅ *Sí* - Para confirmar la pizza\n❌ *No* - Para elegir otra pizza"
            }
    
    def _handle_size_selection(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja la selección de tamaño de pizza
        """
        respuesta = mensaje.lower().strip()
        
        # Mapear respuestas a tamaños
        tamanos = {
            '1': 'pequeña',
            '2': 'mediana', 
            '3': 'grande',
            'pequeña': 'pequeña',
            'pequena': 'pequeña',
            'mediana': 'mediana',
            'grande': 'grande',
            'chica': 'pequeña',
            'medium': 'mediana',
            'large': 'grande'
        }
        
        if respuesta not in tamanos:
            return {
                'success': False,
                'response': "❓ Por favor, selecciona un tamaño válido:\n\n1️⃣ *Pequeña*\n2️⃣ *Mediana*\n3️⃣ *Grande*"
            }
        
        # Guardar tamaño seleccionado
        tamano_seleccionado = tamanos[respuesta]
        self.set_temporary_value(numero_whatsapp, 'tamano_seleccionado', tamano_seleccionado)
        
        # Cambiar estado a cantidad
        self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'cantidad')
        
        return {
            'success': True,
            'response': f"📏 Perfecto, tamaño *{tamano_seleccionado}* seleccionado.\n\n🔢 ¿Cuántas pizzas quieres?\n\nEscribe el número de pizzas (1-10):"
        }
    
    def _handle_quantity_selection(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja la selección de cantidad
        """
        try:
            cantidad = int(mensaje.strip())
            
            if cantidad < 1 or cantidad > 10:
                return {
                    'success': False,
                    'response': "❌ La cantidad debe estar entre 1 y 10 pizzas.\n\nPor favor, escribe un número válido:"
                }
            
            # Guardar cantidad
            self.set_temporary_value(numero_whatsapp, 'cantidad', cantidad)
            
            # Cambiar estado a dirección
            self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'direccion')
            
            return {
                'success': True,
                'response': "🏠 *DIRECCIÓN DE ENTREGA*\n\n¿Quieres usar tu dirección registrada o una diferente?\n\n1️⃣ *Usar mi dirección registrada*\n2️⃣ *Usar una dirección diferente*"
            }
            
        except ValueError:
            return {
                'success': False,
                'response': "❌ Por favor, escribe un número válido (1-10):"
            }
    
    def _handle_delivery_address(self, numero_whatsapp: str, mensaje: str, usuario) -> Dict[str, Any]:
        """
        Maneja la selección de dirección de entrega
        """
        respuesta = mensaje.strip()
        
        if respuesta in ['1', 'usar mi dirección', 'mi dirección', 'registrada']:
            # Usar dirección registrada
            direccion_entrega = usuario.direccion
            
        elif respuesta in ['2', 'diferente', 'otra dirección', 'cambiar dirección']:
            # Pedir nueva dirección
            self.set_temporary_value(numero_whatsapp, 'esperando_nueva_direccion', True)
            
            return {
                'success': True,
                'response': "📍 Escribe la dirección completa donde quieres recibir tu pedido:"
            }
        
        elif self.get_temporary_value(numero_whatsapp, 'esperando_nueva_direccion'):
            # El usuario está escribiendo una nueva dirección
            if len(mensaje.strip()) < 10:
                return {
                    'success': False,
                    'response': "❌ La dirección debe ser más específica.\n\nPor favor, escribe la dirección completa:"
                }
            
            direccion_entrega = mensaje.strip()
            self.set_temporary_value(numero_whatsapp, 'esperando_nueva_direccion', False)
            
        else:
            return {
                'success': False,
                'response': "❓ Por favor, selecciona una opción:\n\n1️⃣ *Usar mi dirección registrada*\n2️⃣ *Usar una dirección diferente*"
            }
        
        # Guardar dirección y continuar
        self.set_temporary_value(numero_whatsapp, 'direccion_entrega', direccion_entrega)
        self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'confirmacion_final')
        
        # Mostrar resumen del pedido
        return self._show_order_summary(numero_whatsapp)
    
    def _handle_final_confirmation(self, numero_whatsapp: str, mensaje: str, usuario) -> Dict[str, Any]:
        """
        Maneja la confirmación final del pedido
        """
        respuesta = mensaje.lower().strip()
        
        if respuesta in ['si', 'sí', 'confirmar', 'ok', 'confirmo', 'proceder']:
            return self._create_order(numero_whatsapp, usuario)
        
        elif respuesta in ['no', 'cancelar', 'cambiar']:
            # Cancelar pedido
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['MENU'])
            
            return {
                'success': True,
                'response': "❌ Pedido cancelado.\n\nVuelve al menú principal cuando quieras hacer otro pedido."
            }
        
        else:
            return {
                'success': False,
                'response': "❓ Por favor, confirma tu pedido:\n\n✅ *Sí* - Proceder con el pedido\n❌ *No* - Cancelar pedido"
            }
    
    def _find_pizza_by_input(self, input_text: str):
        """
        Busca una pizza por nombre o número
        """
        from app.models.pizza import Pizza
        
        # Intentar buscar por número
        try:
            numero = int(input_text.strip())
            pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
            if 1 <= numero <= len(pizzas):
                return pizzas[numero - 1]
        except ValueError:
            pass
        
        # Buscar por nombre (búsqueda parcial)
        pizza = self.db.query(Pizza).filter(
            Pizza.disponible == True,
            Pizza.nombre.ilike(f'%{input_text}%')
        ).first()
        
        return pizza
    
    def _show_pizza_menu_for_order(self) -> Dict[str, Any]:
        """
        Muestra el menú de pizzas para pedido
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
            menu_text += f"{i}️⃣ *{pizza.nombre}* {getattr(pizza, 'emoji', '🍕')}\n"
            menu_text += f"   📝 {pizza.descripcion}\n"
            menu_text += f"   💰 Pequeña: ${getattr(pizza, 'precio_pequena', 0):.2f}\n"
            menu_text += f"   💰 Mediana: ${getattr(pizza, 'precio_mediana', 0):.2f}\n"
            menu_text += f"   💰 Grande: ${getattr(pizza, 'precio_grande', 0):.2f}\n\n"
        
        menu_text += "Escribe el número o nombre de la pizza que deseas:"
        
        return {
            'success': True,
            'response': menu_text
        }
    
    def _show_order_summary(self, numero_whatsapp: str) -> Dict[str, Any]:
        """
        Muestra el resumen del pedido
        """
        pizza_data = self.get_temporary_value(numero_whatsapp, 'pizza_seleccionada')
        cantidad = self.get_temporary_value(numero_whatsapp, 'cantidad')
        tamano = self.get_temporary_value(numero_whatsapp, 'tamano_seleccionado')
        direccion = self.get_temporary_value(numero_whatsapp, 'direccion_entrega')
        
        if not all([pizza_data, cantidad, tamano, direccion]):
            return self._restart_order_process(numero_whatsapp)
        
        # Validar que pizza_data no sea None
        if not pizza_data or not isinstance(pizza_data, dict):
            return self._restart_order_process(numero_whatsapp)
        
        # Obtener precio según tamaño
        precio_key = f'precio_{tamano}'
        precio_unitario = pizza_data.get(precio_key, 0)
        subtotal = precio_unitario * cantidad
        
        summary_text = "📋 *RESUMEN DEL PEDIDO*\n\n"
        summary_text += f"🍕 Pizza: {pizza_data.get('nombre', 'Sin nombre')}\n"
        summary_text += f"📏 Tamaño: {tamano.title() if tamano else 'Sin especificar'}\n"
        summary_text += f"🔢 Cantidad: {cantidad}\n"
        summary_text += f"💰 Precio unitario: ${precio_unitario:.2f}\n"
        summary_text += f"💳 Subtotal: ${subtotal:.2f}\n\n"
        summary_text += f"🏠 Dirección: {direccion}\n\n"
        summary_text += "⏰ Tiempo estimado de entrega: 25-35 minutos\n\n"
        summary_text += "¿Confirmas el pedido?\n\n"
        summary_text += "✅ *Sí* - Proceder con el pedido\n"
        summary_text += "❌ *No* - Cancelar pedido"
        
        return {
            'success': True,
            'response': summary_text
        }
    
    def _create_order(self, numero_whatsapp: str, usuario) -> Dict[str, Any]:
        """
        Crea el pedido en la base de datos
        """
        try:
            from app.models.pedido import Pedido, DetallePedido
            from datetime import datetime
            
            # Obtener datos del pedido
            pizza_data = self.get_temporary_value(numero_whatsapp, 'pizza_seleccionada')
            cantidad = self.get_temporary_value(numero_whatsapp, 'cantidad')
            tamano = self.get_temporary_value(numero_whatsapp, 'tamano_seleccionado')
            direccion = self.get_temporary_value(numero_whatsapp, 'direccion_entrega')
            
            if not all([pizza_data, cantidad, tamano, direccion]):
                return {
                    'success': False,
                    'response': "❌ Error: datos incompletos del pedido."
                }
            
            # Validar que pizza_data no sea None
            if not pizza_data or not isinstance(pizza_data, dict):
                return {
                    'success': False,
                    'response': "❌ Error: datos de pizza no encontrados."
                }
            
            # Obtener precio según tamaño
            precio_key = f'precio_{tamano}'
            precio_unitario = pizza_data.get(precio_key, 0)
            
            # Crear pedido
            nuevo_pedido = Pedido(
                cliente_id=usuario.id,
                direccion_entrega=direccion,
                estado='pendiente',
                total=precio_unitario * cantidad
            )
            
            self.db.add(nuevo_pedido)
            self.db.flush()  # Para obtener el ID del pedido
            
            # Crear detalle del pedido
            detalle = DetallePedido(
                pedido_id=nuevo_pedido.id,
                pizza_id=pizza_data.get('id'),
                tamano=tamano,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=precio_unitario * cantidad
            )
            
            self.db.add(detalle)
            self.db.commit()
            
            # Limpiar datos temporales
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['MENU'])
            
            logger.info(f"✅ Pedido creado exitosamente - ID: {nuevo_pedido.id}, Usuario: {usuario.nombre}")
            
            return {
                'success': True,
                'response': f"🎉 *¡PEDIDO CONFIRMADO!*\n\n📋 Número de pedido: #{nuevo_pedido.id}\n🍕 Pizza: {pizza_data.get('nombre', 'Sin nombre')} ({tamano})\n🔢 Cantidad: {cantidad}\n💰 Total: ${nuevo_pedido.total:.2f}\n\n⏰ Tiempo estimado: 25-35 minutos\n\n¡Gracias por tu pedido! Te notificaremos cuando esté listo."
            }
            
        except Exception as e:
            logger.error(f"❌ Error al crear pedido: {e}")
            self.db.rollback()
            return {
                'success': False,
                'response': "❌ Error al procesar el pedido. Por favor, intenta nuevamente."
            }
    
    def _restart_order_process(self, numero_whatsapp: str) -> Dict[str, Any]:
        """
        Reinicia el proceso de pedido
        """
        self.clear_conversation_data(numero_whatsapp)
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['PEDIDO'])
        
        return {
            'success': True,
            'response': "🔄 Reiniciando pedido...\n\n🛒 *NUEVO PEDIDO*\n\n¿Qué pizza te gustaría ordenar?\n\nPuedes escribir:\n• El nombre de la pizza\n• El número de la pizza del menú\n• *menu* para ver todas las opciones"
        }
    
    def _is_original_format_selection(self, mensaje: str) -> bool:
        """
        Verifica si el mensaje está en formato original: '1 mediana', '2 grande', '1 grande, 2 mediana'
        """
        import re
        # Buscar patrones como "1 mediana", "2 grande", etc.
        patrones = re.findall(r'(\d+)\s*(pequeña|mediana|grande|pequeña|small|medium|large)', mensaje.lower())
        return len(patrones) > 0
    
    def _handle_original_format_selection(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Maneja la selección en formato original: '1 mediana', '1 grande, 2 mediana'
        """
        import re
        
        # Parsear mensaje para múltiples pizzas
        patrones = re.findall(r'(\d+)\s*(pequeña|mediana|grande|pequeña|small|medium|large)', mensaje.lower())
        
        if not patrones:
            return {
                'success': False,
                'response': "Por favor, especifica el número de pizza y tamaño.\nEjemplo: '1 mediana' o '2 grande'\nTambién puedes pedir múltiples pizzas: '1 grande, 2 mediana'"
            }
        
        # Obtener pizzas disponibles
        from app.models.pizza import Pizza
        pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
        # Obtener carrito actual
        carrito = self.get_temporary_value(numero_whatsapp, 'carrito') or []
        
        pizzas_agregadas = []
        
        # Procesar cada pizza en el mensaje
        for numero_pizza_str, tamano in patrones:
            numero_pizza = int(numero_pizza_str)
            tamano = tamano.lower()
            
            # Normalizar tamaño
            if tamano in ['pequeña', 'small']:
                tamano = 'pequeña'
            elif tamano in ['mediana', 'medium']:
                tamano = 'mediana'
            elif tamano in ['grande', 'large']:
                tamano = 'grande'
            
            # Validar número de pizza
            if numero_pizza < 1 or numero_pizza > len(pizzas):
                return {
                    'success': False,
                    'response': f"Por favor, selecciona un número entre 1 y {len(pizzas)}"
                }
            
            pizza = pizzas[numero_pizza - 1]
            
            # Obtener precio según tamaño
            if tamano == 'pequeña':
                precio = getattr(pizza, 'precio_pequena', 0)
            elif tamano == 'mediana':
                precio = getattr(pizza, 'precio_mediana', 0)
            else:
                precio = getattr(pizza, 'precio_grande', 0)
            
            # Agregar al carrito
            carrito.append({
                'pizza_id': pizza.id,
                'pizza_nombre': pizza.nombre,
                'pizza_emoji': getattr(pizza, 'emoji', '🍕'),
                'tamano': tamano,
                'precio': float(precio),
                'cantidad': 1
            })
            
            pizzas_agregadas.append({
                'nombre': pizza.nombre,
                'emoji': getattr(pizza, 'emoji', '🍕'),
                'tamano': tamano,
                'precio': float(precio)
            })
        
        # Guardar carrito actualizado
        self.set_temporary_value(numero_whatsapp, 'carrito', carrito)
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        
        # Generar mensaje de respuesta
        mensaje_respuesta = f"✅ Agregado al carrito:\n"
        for pizza_agregada in pizzas_agregadas:
            mensaje_respuesta += f"{pizza_agregada['emoji']} {pizza_agregada['nombre']} - {pizza_agregada['tamano'].title()}\n"
            mensaje_respuesta += f"Precio: ${pizza_agregada['precio']:.2f}\n"
        
        mensaje_respuesta += f"\n*Carrito actual:*\n"
        
        for item in carrito:
            mensaje_respuesta += f"• {item['pizza_emoji']} {item['pizza_nombre']} - {item['tamano'].title()} - ${item['precio']:.2f}\n"
        
        mensaje_respuesta += f"\n*Total: ${total:.2f}*\n\n"
        mensaje_respuesta += "¿Quieres agregar algo más?\n"
        mensaje_respuesta += "• Escribe el número y tamaño de otra pizza\n"
        mensaje_respuesta += "• Puedes pedir múltiples: '1 grande, 3 mediana'\n"
        mensaje_respuesta += "• Escribe 'confirmar' para finalizar el pedido\n"
        mensaje_respuesta += "• Escribe 'cancelar' para cancelar"
        
        # Cambiar estado a pedido continuo (compatible con original)
        self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'continuar_pedido')
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['PEDIDO'])
        
        return {
            'success': True,
            'response': mensaje_respuesta
        }
    
    def _handle_continuar_pedido_original(self, numero_whatsapp: str, mensaje: str) -> Dict[str, Any]:
        """
        Continuar con el pedido en formato original (compatible con bot_service original)
        """
        import re
        
        # Limpiar mensaje de espacios y signos de puntuación
        mensaje_limpio = re.sub(r'[^\w\s]', '', mensaje).lower().strip()
        
        if mensaje_limpio in ['confirmar', 'confirm', 'ok', 'si', 'yes']:
            # Proceder a solicitar dirección
            from app.models.cliente import Cliente
            cliente = self.db.query(Cliente).filter(
                Cliente.numero_whatsapp == numero_whatsapp
            ).first()
            
            if cliente and getattr(cliente, 'direccion', None):
                direccion_cliente = getattr(cliente, 'direccion', '')
                self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'direccion')
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['DIRECCION'])
                return {
                    'success': True,
                    'response': f"Perfecto! 🎉\n\n¿Deseas usar tu dirección registrada?\n\n📍 {direccion_cliente}\n\n• Escribe 'sí' para usar esta dirección\n• Escribe 'no' para ingresar otra dirección"
                }
            else:
                self.set_temporary_value(numero_whatsapp, 'estado_pedido', 'direccion')
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['DIRECCION'])
                return {
                    'success': True,
                    'response': "Perfecto! 🎉\n\nPor favor, envía tu dirección de entrega:"
                }
        
        elif mensaje_limpio in ['cancelar', 'cancel', 'no']:
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
            return {
                'success': True,
                'response': "Pedido cancelado. ¡Esperamos verte pronto! 👋"
            }
        
        else:
            # Intentar agregar otra pizza en formato original
            if self._is_original_format_selection(mensaje):
                return self._handle_original_format_selection(numero_whatsapp, mensaje)
            else:
                return {
                    'success': False,
                    'response': "¿Qué te gustaría hacer?\n\n• Escribe 'confirmar' para finalizar el pedido\n• Escribe 'cancelar' para cancelar\n• Agrega más pizzas: '1 grande, 2 mediana'"
                }
