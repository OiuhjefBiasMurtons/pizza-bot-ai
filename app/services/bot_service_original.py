from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido, DetallePedido
from app.models.conversation_state import ConversationState
from app.services.pedido_service import PedidoService
import re
import logging
import json
from datetime import datetime
from typing import Optional

# Configurar logger
logger = logging.getLogger(__name__)

# Servicio de bot
class BotService:
    def __init__(self, db: Session):
        self.db = db
        self.pedido_service = PedidoService(db)
        
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
        
        # Almacenar estados de conversación (ahora con persistencia)
        self.conversaciones = {}  # Cache en memoria para rendimiento
    
    # Procesar mensaje del usuario y generar respuesta
    async def process_message(self, numero_whatsapp: str, mensaje: str) -> str:
        """Procesar mensaje del usuario y generar respuesta"""
        
        # Limpiar mensaje
        mensaje = mensaje.strip()
        mensaje_lower = mensaje.lower()
        
        # Verificar si el cliente está registrado
        cliente = self.get_cliente(numero_whatsapp)
        
        # Obtener estado actual de la conversación (persistente)
        estado_actual = self.get_conversation_state(numero_whatsapp)
        
        # Debug: Log del estado actual
        logger.info(f"🔍 Debug - Usuario: {numero_whatsapp}, Estado: {estado_actual}, Mensaje: '{mensaje}'")
        
        # Si el cliente no está registrado completamente, iniciar proceso de registro
        if not cliente or cliente.nombre is None or cliente.direccion is None:
            return await self.handle_registration_flow(numero_whatsapp, mensaje, cliente)
        
        # Cliente ya registrado - comandos especiales que reinician el flujo
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
        
        elif estado_actual == self.ESTADOS['REGISTRO_NOMBRE']:
            return await self.handle_registration_flow(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['REGISTRO_DIRECCION']:
            return await self.handle_registration_flow(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['MENU']:
            return await self.handle_seleccion_pizza(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['PEDIDO']:
            return await self.handle_continuar_pedido(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['DIRECCION']:
            return await self.handle_direccion(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['CONFIRMACION']:
            return await self.handle_confirmacion(numero_whatsapp, mensaje, cliente)
        
        else:
            # Si llegamos aquí, hay un problema con el estado
            logger.warning(f"⚠️  Estado desconocido: {estado_actual}, reiniciando...")
            return self.handle_registered_greeting(numero_whatsapp, cliente)
    
    def get_cliente(self, numero_whatsapp: str) -> Cliente:
        """Obtener cliente por número de WhatsApp"""
        return self.db.query(Cliente).filter(
            Cliente.numero_whatsapp == numero_whatsapp
        ).first()

    def get_or_create_cliente(self, numero_whatsapp: str) -> Cliente:
        """Obtener cliente existente o crear uno nuevo"""
        cliente = self.get_cliente(numero_whatsapp)
        
        if not cliente:
            cliente = Cliente(numero_whatsapp=numero_whatsapp)
            self.db.add(cliente)
            self.db.commit()
            self.db.refresh(cliente)
        
        return cliente
    
    async def handle_menu(self, numero_whatsapp: str, cliente: Optional[Cliente] = None) -> str:
        """Mostrar menú de pizzas"""
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['MENU'])
        
        pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
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
        
        return mensaje
    
    async def handle_seleccion_pizza(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Manejar selección de pizza"""
        
        # Parsear mensaje para múltiples pizzas (ej: "1 mediana", "2 grande", "1 grande, 2 mediana")
        # Buscar todos los patrones de número + tamaño
        patrones = re.findall(r'(\d+)\s*(pequeña|mediana|grande|pequeña|small|medium|large)', mensaje)
        
        if not patrones:
            return "Por favor, especifica el número de pizza y tamaño.\nEjemplo: '1 mediana' o '2 grande'\nTambién puedes pedir múltiples pizzas: '1 grande, 2 mediana'"
        
        # Obtener pizzas disponibles
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
                return f"Por favor, selecciona un número entre 1 y {len(pizzas)}"
            
            pizza = pizzas[numero_pizza - 1]
            
            # Obtener precio según tamaño
            if tamano == 'pequeña':
                precio = pizza.precio_pequena
            elif tamano == 'mediana':
                precio = pizza.precio_mediana
            else:
                precio = pizza.precio_grande
            
            # Agregar al carrito (solo datos serializables)
            carrito.append({
                'pizza_id': pizza.id,
                'pizza_nombre': pizza.nombre,
                'pizza_emoji': pizza.emoji,
                'tamano': tamano,
                'precio': precio,
                'cantidad': 1
            })
            
            pizzas_agregadas.append({
                'nombre': pizza.nombre,
                'emoji': pizza.emoji,
                'tamano': tamano,
                'precio': precio
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
        
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['PEDIDO'])
        
        return mensaje_respuesta
    
    async def handle_continuar_pedido(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Continuar con el pedido"""
        
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
            # Intentar agregar otra pizza
            return await self.handle_seleccion_pizza(numero_whatsapp, mensaje, cliente)
    
    async def handle_direccion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Procesar dirección de entrega"""
        
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
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        
        # Generar resumen
        mensaje_respuesta = "📋 *RESUMEN DEL PEDIDO*\n\n"
        mensaje_respuesta += "*Pizzas:*\n"
        for item in carrito:
            mensaje_respuesta += f"• {item['pizza_emoji']} {item['pizza_nombre']} - {item['tamano'].title()}\n"
            mensaje_respuesta += f"  ${item['precio']:.2f}\n"
        
        mensaje_respuesta += f"\n*Dirección de entrega:*\n{direccion_entrega}\n"
        mensaje_respuesta += f"\n*Total a pagar: ${total:.2f}*\n\n"
        mensaje_respuesta += "¿Confirmas tu pedido?\n"
        mensaje_respuesta += "• Escribe 'sí' para confirmar\n"
        mensaje_respuesta += "• Escribe 'no' para cancelar"
        
        return mensaje_respuesta
    
    async def handle_confirmacion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Confirmar pedido final"""
        
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
            
            pedido_id = await self.pedido_service.crear_pedido(cliente, carrito, direccion)
            
            # Limpiar conversación
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['FINALIZADO'])
            
            mensaje = f"🎉 ¡Pedido confirmado!\n\n"
            mensaje += f"Número de pedido: #{pedido_id}\n"
            mensaje += f"Tiempo estimado: 30-45 minutos\n\n"
            mensaje += "📱 Te notificaremos cuando tu pedido esté listo.\n"
            mensaje += "¡Gracias por elegir Pizza Bot! 🍕"
            
            return mensaje
        
        else:
            # Cancelar pedido
            self.clear_conversation_data(numero_whatsapp)
            self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
            
            return "Pedido cancelado. ¡Esperamos verte pronto! 👋"
    
    async def handle_estado_pedido(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Mostrar estado de pedidos"""
        
        pedidos = self.db.query(Pedido).filter(
            Pedido.cliente_id == cliente.id
        ).order_by(Pedido.fecha_pedido.desc()).limit(5).all()
        
        if not pedidos:
            return "No tienes pedidos registrados. ¡Haz tu primer pedido escribiendo 'menu'! 🍕"
        
        mensaje = "📋 *TUS PEDIDOS*\n\n"
        
        for pedido in pedidos:
            mensaje += f"*Pedido #{pedido.id}*\n"
            mensaje += f"Estado: {pedido.estado.title()}\n"
            mensaje += f"Total: ${pedido.total:.2f}\n"
            mensaje += f"Fecha: {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}\n\n"
        
        mensaje += "Para hacer un nuevo pedido, escribe 'menu' 🍕"
        
        return mensaje
    
    def handle_ayuda(self, cliente: Optional[Cliente] = None) -> str:
        """Mostrar ayuda"""
        nombre = cliente.nombre if cliente and cliente.nombre is not None else "usuario"
        
        mensaje = f"🤖 *AYUDA - PIZZA BOT* {nombre}!\n\n"
        mensaje += "*Comandos disponibles:*\n"
        mensaje += "• 'menu' - Ver pizzas disponibles\n"
        mensaje += "• 'pedido' - Ver tus pedidos\n"
        mensaje += "• 'ayuda' - Mostrar esta ayuda\n"
        mensaje += "• 'hola' - Reiniciar conversación\n\n"
        mensaje += "*Para hacer un pedido:*\n"
        mensaje += "1. Escribe 'menu'\n"
        mensaje += "2. Selecciona pizza (ej: '1 mediana')\n"
        mensaje += "3. Proporciona tu dirección\n"
        mensaje += "4. Confirma el pedido\n\n"
        mensaje += "¿Necesitas más ayuda? ¡Escribe 'menu' para empezar! 🍕"
        
        return mensaje
    
    async def handle_registration_flow(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Manejar el flujo de registro de nuevo usuario"""
        
        # Si el cliente no existe, crearlo
        if not cliente:
            cliente = self.get_or_create_cliente(numero_whatsapp)
        
        # Obtener estado actual del registro
        estado_actual = self.get_conversation_state(numero_whatsapp)
        
        logger.info(f"📝 Registration flow - Usuario: {numero_whatsapp}, Estado: {estado_actual}, Cliente nombre: {cliente.nombre}")
        
        # Si es la primera vez o no tiene nombre
        if cliente.nombre is None:
            if estado_actual == self.ESTADOS['INICIO']:
                # Pedir nombre
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['REGISTRO_NOMBRE'])
                return ("¡Hola! 👋 Bienvenido a Pizza Bot 🍕\n\n"
                       "Veo que es tu primera vez aquí. Para brindarte un mejor servicio, "
                       "necesito conocerte un poco mejor.\n\n"
                       "¿Cuál es tu nombre completo? (Ejemplo: Juan Pérez)")
            
            elif estado_actual == self.ESTADOS['REGISTRO_NOMBRE']:
                # Validar y guardar nombre
                nombre_limpio = mensaje.strip()
                
                if len(nombre_limpio) < 2:
                    return "Por favor, ingresa un nombre válido (mínimo 2 caracteres)."
                
                # Validar que el nombre tenga al menos 2 palabras (nombre y apellido)
                palabras = nombre_limpio.split()
                if len(palabras) < 2:
                    return ("Por favor, ingresa tu nombre completo (nombre y apellido).\n"
                           "Ejemplo: Juan Pérez")
                
                # Validar que solo contenga letras y espacios
                if not all(palabra.replace('-', '').isalpha() for palabra in palabras):
                    return ("Por favor, ingresa solo letras en tu nombre.\n"
                           "Ejemplo: Juan Pérez")
                
                logger.info(f"✅ Guardando nombre: '{nombre_limpio}' para usuario {numero_whatsapp}")
                
                setattr(cliente, 'nombre', nombre_limpio)
                self.db.commit()
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['REGISTRO_DIRECCION'])
                
                return (f"¡Mucho gusto, {cliente.nombre}! 😊\n\n"
                       "Ahora necesito tu dirección para poder enviarte las pizzas.\n\n"
                       "Por favor, ingresa tu dirección completa (calle, número, ciudad, código postal):")
        
        # Si tiene nombre pero no dirección
        elif cliente.direccion is None:
            if estado_actual in [self.ESTADOS['INICIO'], self.ESTADOS['REGISTRO_DIRECCION']]:
                direccion_limpia = mensaje.strip()
                
                if len(direccion_limpia) < 10:
                    return "Por favor, ingresa una dirección completa con calle, número, ciudad y código postal."
                
                # Validar que la dirección tenga elementos básicos
                if not any(word.isdigit() for word in direccion_limpia.split()):
                    return ("Por favor, incluye el número de la calle en tu dirección.\n"
                           "Ejemplo: Calle 123, Colonia Centro, Ciudad, CP 12345")
                
                logger.info(f"✅ Guardando dirección: '{direccion_limpia}' para usuario {numero_whatsapp}")
                
                setattr(cliente, 'direccion', direccion_limpia)
                self.db.commit()
                
                # Registro completado
                self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
                return (f"¡Perfecto, {cliente.nombre}! 🎉\n\n"
                       "Tu registro ha sido completado exitosamente.\n\n"
                       f"📍 Dirección registrada: {cliente.direccion}\n\n"
                       "Ahora puedes hacer pedidos. ¿Te gustaría ver nuestro menú? 🍕\n\n"
                       "Escribe 'menu' para ver nuestras pizzas disponibles.")
        
        # Si llegamos aquí, hay un error
        return "Ocurrió un error durante el registro. Por favor, intenta de nuevo."

    def handle_registered_greeting(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Manejar saludo para usuario registrado"""
        self.set_conversation_state(numero_whatsapp, self.ESTADOS['INICIO'])
        
        mensaje = f"¡Hola de nuevo, {cliente.nombre}! 👋 Bienvenido a Pizza Bot 🍕\n\n"
        mensaje += "¿Qué puedo hacer por ti hoy?\n"
        mensaje += "• Escribe 'menu' para ver nuestras pizzas\n"
        mensaje += "• Escribe 'pedido' para revisar tu pedido actual\n"
        mensaje += "• Escribe 'ayuda' para más opciones\n\n"
        mensaje += "¿Te gustaría ver nuestro menú? 🍕"
        
        return mensaje

    def get_conversation_state(self, numero_whatsapp: str) -> str:
        """Obtener estado de conversación desde la base de datos"""
        # Primero revisar cache
        if numero_whatsapp in self.conversaciones:
            return self.conversaciones[numero_whatsapp]
        
        # Buscar en base de datos
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if conv_state:
            estado = str(conv_state.estado_actual)
            # Guardar en cache
            self.conversaciones[numero_whatsapp] = estado
            return estado
        
        # Estado por defecto
        return self.ESTADOS['INICIO']

    def set_conversation_state(self, numero_whatsapp: str, estado: str, datos_temporales: Optional[dict] = None):
        """Guardar estado de conversación en la base de datos"""
        # Actualizar cache
        self.conversaciones[numero_whatsapp] = estado
        
        # Buscar o crear registro
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not conv_state:
            conv_state = ConversationState(numero_whatsapp=numero_whatsapp)
            self.db.add(conv_state)
        
        # Actualizar datos
        setattr(conv_state, 'estado_actual', estado)
        if datos_temporales:
            setattr(conv_state, 'datos_temporales', json.dumps(datos_temporales))
        
        self.db.commit()
        logger.info(f"💾 Estado guardado - Usuario: {numero_whatsapp}, Estado: {estado}")

    def get_temporary_data(self, numero_whatsapp: str) -> dict:
        """Obtener datos temporales de la conversación"""
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if conv_state and conv_state.datos_temporales is not None:
            try:
                return json.loads(str(conv_state.datos_temporales))
            except:
                return {}
        
        return {}

    def get_temporary_value(self, numero_whatsapp: str, key: str):
        """Obtener un valor específico de los datos temporales"""
        datos = self.get_temporary_data(numero_whatsapp)
        return datos.get(key)

    def set_temporary_value(self, numero_whatsapp: str, key: str, value):
        """Guardar un valor específico en los datos temporales"""
        datos = self.get_temporary_data(numero_whatsapp)
        datos[key] = value
        self.set_temporary_data(numero_whatsapp, datos)

    def set_temporary_data(self, numero_whatsapp: str, datos: dict):
        """Guardar datos temporales de la conversación"""
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not conv_state:
            conv_state = ConversationState(numero_whatsapp=numero_whatsapp)
            self.db.add(conv_state)
        
        setattr(conv_state, 'datos_temporales', json.dumps(datos))
        self.db.commit()

    def clear_conversation_data(self, numero_whatsapp: str):
        """Limpiar datos de conversación"""
        # Limpiar cache
        self.conversaciones.pop(numero_whatsapp, None)
        
        # Limpiar base de datos
        conv_state = self.db.query(ConversationState).filter(
            ConversationState.numero_whatsapp == numero_whatsapp
        ).first()
        
        if conv_state:
            setattr(conv_state, 'estado_actual', self.ESTADOS['INICIO'])
            setattr(conv_state, 'datos_temporales', None)
            self.db.commit()