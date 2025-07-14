from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido, DetallePedido
from app.services.pedido_service import PedidoService
import re
from datetime import datetime

# Servicio de bot
class BotService:
    def __init__(self, db: Session):
        self.db = db
        self.pedido_service = PedidoService(db)
        
        # Estados de conversación
        self.ESTADOS = {
            'INICIO': 'inicio',
            'MENU': 'menu',
            'PEDIDO': 'pedido',
            'DIRECCION': 'direccion',
            'CONFIRMACION': 'confirmacion',
            'FINALIZADO': 'finalizado'
        }
        
        # Almacenar estados de conversación (en producción usar Redis)
        self.conversaciones = {}
    
    # Procesar mensaje del usuario y generar respuesta
    async def process_message(self, numero_whatsapp: str, mensaje: str) -> str:
        """Procesar mensaje del usuario y generar respuesta"""
        
        # Limpiar mensaje
        mensaje = mensaje.strip().lower()
        
        # Obtener o crear cliente
        cliente = self.get_or_create_cliente(numero_whatsapp)
        
        # Obtener estado actual de la conversación
        estado_actual = self.conversaciones.get(numero_whatsapp, self.ESTADOS['INICIO'])
        
        # Comandos especiales
        if mensaje in ['hola', 'hello', 'buenas', 'inicio', 'empezar']:
            return self.handle_saludo(numero_whatsapp, cliente)
        
        elif mensaje in ['menu', 'menú', 'carta']:
            return await self.handle_menu(numero_whatsapp)
        
        elif mensaje in ['ayuda', 'help']:
            return self.handle_ayuda()
        
        elif mensaje in ['pedido', 'mis pedidos', 'estado']:
            return await self.handle_estado_pedido(numero_whatsapp, cliente)
        
        # Procesar según estado actual
        if estado_actual == self.ESTADOS['INICIO']:
            return self.handle_saludo(numero_whatsapp, cliente)
        
        elif estado_actual == self.ESTADOS['MENU']:
            return await self.handle_seleccion_pizza(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['PEDIDO']:
            return await self.handle_continuar_pedido(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['DIRECCION']:
            return await self.handle_direccion(numero_whatsapp, mensaje, cliente)
        
        elif estado_actual == self.ESTADOS['CONFIRMACION']:
            return await self.handle_confirmacion(numero_whatsapp, mensaje, cliente)
        
        else:
            return "Lo siento, no entiendo. Escribe 'menu' para ver nuestras pizzas o 'ayuda' para más opciones."
    
    def get_or_create_cliente(self, numero_whatsapp: str) -> Cliente:
        """Obtener cliente existente o crear uno nuevo"""
        cliente = self.db.query(Cliente).filter(
            Cliente.numero_whatsapp == numero_whatsapp
        ).first()
        
        if not cliente:
            cliente = Cliente(numero_whatsapp=numero_whatsapp)
            self.db.add(cliente)
            self.db.commit()
            self.db.refresh(cliente)
        
        return cliente
    
    def handle_saludo(self, numero_whatsapp: str, cliente: Cliente) -> str:
        """Manejar saludo inicial"""
        self.conversaciones[numero_whatsapp] = self.ESTADOS['INICIO']
        
        mensaje = f"¡Hola! 👋 Bienvenido a Pizza Bot 🍕\n\n"
        mensaje += "Soy tu asistente virtual para pedidos de pizza.\n\n"
        mensaje += "¿Qué puedo hacer por ti?\n"
        mensaje += "• Escribe 'menu' para ver nuestras pizzas\n"
        mensaje += "• Escribe 'pedido' para revisar tu pedido actual\n"
        mensaje += "• Escribe 'ayuda' para más opciones\n\n"
        mensaje += "¿Te gustaría ver nuestro menú? 🍕"
        
        return mensaje
    
    async def handle_menu(self, numero_whatsapp: str) -> str:
        """Mostrar menú de pizzas"""
        self.conversaciones[numero_whatsapp] = self.ESTADOS['MENU']
        
        pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
        mensaje = "🍕 *MENÚ DE PIZZAS* 🍕\n\n"
        
        for i, pizza in enumerate(pizzas, 1):
            mensaje += f"{i}. {pizza.emoji} *{pizza.nombre}*\n"
            mensaje += f"   {pizza.descripcion}\n"
            mensaje += f"   • Pequeña: ${pizza.precio_pequena:.2f}\n"
            mensaje += f"   • Mediana: ${pizza.precio_mediana:.2f}\n"
            mensaje += f"   • Grande: ${pizza.precio_grande:.2f}\n\n"
        
        mensaje += "Para ordenar, responde con el número y tamaño:\n"
        mensaje += "Ejemplo: '1 mediana' o '2 grande'\n\n"
        mensaje += "¿Qué pizza te gustaría? 🍕"
        
        return mensaje
    
    async def handle_seleccion_pizza(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Manejar selección de pizza"""
        
        # Parsear mensaje (ej: "1 mediana", "2 grande")
        match = re.match(r'(\d+)\s*(pequeña|mediana|grande|pequeña|small|medium|large)', mensaje)
        
        if not match:
            return "Por favor, especifica el número de pizza y tamaño.\nEjemplo: '1 mediana' o '2 grande'"
        
        numero_pizza = int(match.group(1))
        tamano = match.group(2).lower()
        
        # Normalizar tamaño
        if tamano in ['pequeña', 'small']:
            tamano = 'pequeña'
        elif tamano in ['mediana', 'medium']:
            tamano = 'mediana'
        elif tamano in ['grande', 'large']:
            tamano = 'grande'
        
        # Obtener pizza
        pizzas = self.db.query(Pizza).filter(Pizza.disponible == True).all()
        
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
        
        # Agregar al carrito temporal
        carrito = self.conversaciones.get(f"{numero_whatsapp}_carrito", [])
        carrito.append({
            'pizza': pizza,
            'tamano': tamano,
            'precio': precio,
            'cantidad': 1
        })
        self.conversaciones[f"{numero_whatsapp}_carrito"] = carrito
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        
        mensaje = f"✅ Agregado al carrito:\n"
        mensaje += f"{pizza.emoji} {pizza.nombre} - {tamano.title()}\n"
        mensaje += f"Precio: ${precio:.2f}\n\n"
        mensaje += f"*Carrito actual:*\n"
        
        for item in carrito:
            mensaje += f"• {item['pizza'].emoji} {item['pizza'].nombre} - {item['tamano'].title()} - ${item['precio']:.2f}\n"
        
        mensaje += f"\n*Total: ${total:.2f}*\n\n"
        mensaje += "¿Quieres agregar algo más?\n"
        mensaje += "• Escribe el número y tamaño de otra pizza\n"
        mensaje += "• Escribe 'confirmar' para finalizar el pedido\n"
        mensaje += "• Escribe 'cancelar' para cancelar"
        
        self.conversaciones[numero_whatsapp] = self.ESTADOS['PEDIDO']
        
        return mensaje
    
    async def handle_continuar_pedido(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Continuar con el pedido"""
        
        if mensaje == 'confirmar':
            self.conversaciones[numero_whatsapp] = self.ESTADOS['DIRECCION']
            return "Perfecto! 🎉\n\nPor favor, envía tu dirección de entrega:"
        
        elif mensaje == 'cancelar':
            self.conversaciones.pop(f"{numero_whatsapp}_carrito", None)
            self.conversaciones[numero_whatsapp] = self.ESTADOS['INICIO']
            return "Pedido cancelado. ¡Esperamos verte pronto! 👋"
        
        else:
            # Intentar agregar otra pizza
            return await self.handle_seleccion_pizza(numero_whatsapp, mensaje, cliente)
    
    async def handle_direccion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Procesar dirección de entrega"""
        # Validar dirección
        if len(mensaje.strip()) < 10:
            return "Por favor ingresa una dirección completa con calle, número, ciudad y código postal."
            
        # Guardar dirección
        direccion = mensaje.strip()
        self.conversaciones[f"{numero_whatsapp}_direccion"] = direccion
        self.conversaciones[numero_whatsapp] = self.ESTADOS['CONFIRMACION']
        
        # Obtener carrito
        carrito = self.conversaciones.get(f"{numero_whatsapp}_carrito", [])
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in carrito)
        
        # Generar resumen
        mensaje = "📋 *RESUMEN DEL PEDIDO*\n\n"
        mensaje += "*Pizzas:*\n"
        for item in carrito:
            mensaje += f"• {item['pizza'].emoji} {item['pizza'].nombre} - {item['tamano'].title()}\n"
            mensaje += f"  ${item['precio']:.2f}\n"
        
        mensaje += f"\n*Dirección de entrega:*\n{direccion}\n"
        mensaje += f"\n*Total a pagar: ${total:.2f}*\n\n"
        mensaje += "¿Confirmas tu pedido?\n"
        mensaje += "• Escribe 'sí' para confirmar\n"
        mensaje += "• Escribe 'no' para cancelar"
        
        return mensaje
    
    async def handle_confirmacion(self, numero_whatsapp: str, mensaje: str, cliente: Cliente) -> str:
        """Confirmar pedido final"""
        
        if mensaje.lower() in ['sí', 'si', 'yes', 'confirmar', 'ok']:
            # Crear pedido en base de datos
            carrito = self.conversaciones.get(f"{numero_whatsapp}_carrito", [])
            direccion = self.conversaciones.get(f"{numero_whatsapp}_direccion", "")
            
            pedido_id = await self.pedido_service.crear_pedido(cliente, carrito, direccion)
            
            # Limpiar conversación
            self.conversaciones.pop(f"{numero_whatsapp}_carrito", None)
            self.conversaciones.pop(f"{numero_whatsapp}_direccion", None)
            self.conversaciones[numero_whatsapp] = self.ESTADOS['FINALIZADO']
            
            mensaje = f"🎉 ¡Pedido confirmado!\n\n"
            mensaje += f"Número de pedido: #{pedido_id}\n"
            mensaje += f"Tiempo estimado: 30-45 minutos\n\n"
            mensaje += "📱 Te notificaremos cuando tu pedido esté listo.\n"
            mensaje += "¡Gracias por elegir Pizza Bot! 🍕"
            
            return mensaje
        
        else:
            # Cancelar pedido
            self.conversaciones.pop(f"{numero_whatsapp}_carrito", None)
            self.conversaciones.pop(f"{numero_whatsapp}_direccion", None)
            self.conversaciones[numero_whatsapp] = self.ESTADOS['INICIO']
            
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
    
    def handle_ayuda(self) -> str:
        """Mostrar ayuda"""
        mensaje = "🤖 *AYUDA - PIZZA BOT*\n\n"
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