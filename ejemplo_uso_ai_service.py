#!/usr/bin/env python3
"""
Ejemplo de uso del AIService mejorado con contexto de base de datos
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database.connection import get_db
from app.services.ai_service import AIService
from app.models.cliente import Cliente
from app.models.pizza import Pizza
from app.models.pedido import Pedido

async def ejemplo_uso_ai_service():
    """Ejemplo de cómo usar el AIService mejorado"""
    
    # Obtener sesión de base de datos
    db = next(get_db())
    
    # Crear instancia del servicio de IA
    ai_service = AIService(db)
    
    print("🤖 Servicio de IA iniciado con contexto de base de datos")
    print("=" * 60)
    
    # Ejemplo 1: Cliente nuevo
    print("\n📱 EJEMPLO 1: Cliente nuevo")
    numero_whatsapp = "+573001234567"
    mensaje = "Hola, quiero pedir una pizza"
    
    response = await ai_service.process_with_ai(
        numero_whatsapp=numero_whatsapp,
        mensaje=mensaje
    )
    
    print(f"Usuario: {mensaje}")
    print(f"Bot: {response['mensaje']}")
    print(f"Acción sugerida: {response.get('accion_sugerida', 'Ninguna')}")
    
    # Ejemplo 2: Cliente existente con historial
    print("\n👤 EJEMPLO 2: Cliente con historial")
    cliente_existente = db.query(Cliente).first()
    if cliente_existente:
        mensaje = "Quiero mi pizza favorita"
        response = await ai_service.process_with_ai(
            numero_whatsapp=str(cliente_existente.numero_whatsapp),
            mensaje=mensaje,
            cliente=cliente_existente
        )
        
        print(f"Usuario: {mensaje}")
        print(f"Bot: {response['mensaje']}")
        print(f"Acción sugerida: {response.get('accion_sugerida', 'Ninguna')}")
    
    # Ejemplo 3: Obtener recomendaciones personalizadas
    print("\n🎯 EJEMPLO 3: Recomendaciones personalizadas")
    if cliente_existente:
        recomendaciones = ai_service.get_personalized_recommendations(cliente_existente)
        print(f"Recomendaciones para {cliente_existente.nombre or 'Cliente'}:")
        print(recomendaciones)
    
    # Ejemplo 4: Contexto dinámico
    print("\n📊 EJEMPLO 4: Contexto dinámico")
    contexto_dinamico = ai_service.get_dynamic_context(numero_whatsapp)
    print("Contexto dinámico:")
    for key, value in contexto_dinamico.items():
        if key != 'cliente':
            print(f"- {key}: {value}")
    
    # Ejemplo 5: Validación de pedido
    print("\n✅ EJEMPLO 5: Validación de pedido")
    pizza_data = {
        "numero": 1,
        "tamaño": "mediana", 
        "cantidad": 2
    }
    
    validacion = ai_service.validate_pizza_order(pizza_data)
    print(f"Datos del pedido: {pizza_data}")
    print(f"Válido: {validacion['valido']}")
    if validacion['errores']:
        print(f"Errores: {', '.join(validacion['errores'])}")
    
    # Ejemplo 6: Búsqueda de pizza
    print("\n🔍 EJEMPLO 6: Búsqueda de pizza")
    pizza = ai_service.get_pizza_by_name_or_number("1")
    if pizza:
        print(f"Pizza encontrada: {pizza.nombre} - {pizza.descripcion}")
        print(f"Precios: Pequeña ${pizza.precio_pequena}, Mediana ${pizza.precio_mediana}, Grande ${pizza.precio_grande}")
    
    # Ejemplo 7: Conversación con contexto
    print("\n💬 EJEMPLO 7: Conversación con contexto")
    contexto_conversacion = {
        "estado": "menu",
        "carrito": [
            {"pizza_nombre": "Margarita", "tamano": "mediana", "precio": 12.99},
            {"pizza_nombre": "Pepperoni", "tamano": "grande", "precio": 15.99}
        ],
        "direccion_entrega": "Calle 123 #45-67"
    }
    
    mensaje = "¿Cuánto va mi pedido?"
    response = await ai_service.process_with_ai(
        numero_whatsapp=numero_whatsapp,
        mensaje=mensaje,
        contexto_conversacion=contexto_conversacion
    )
    
    print(f"Usuario: {mensaje}")
    print(f"Bot: {response['mensaje']}")
    
    # Cerrar sesión
    db.close()
    print("\n✅ Ejemplos completados")

def mostrar_estadisticas_bd():
    """Mostrar estadísticas de la base de datos"""
    db = next(get_db())
    
    try:
        total_pizzas = db.query(Pizza).filter(Pizza.disponible == True).count()
        total_clientes = db.query(Cliente).count()
        total_pedidos = db.query(Pedido).count()
        
        print("\n📊 ESTADÍSTICAS DE LA BASE DE DATOS")
        print("=" * 40)
        print(f"🍕 Pizzas disponibles: {total_pizzas}")
        print(f"👥 Clientes registrados: {total_clientes}")
        print(f"📦 Pedidos realizados: {total_pedidos}")
        
        # Mostrar pizzas disponibles
        print("\n🍕 PIZZAS DISPONIBLES:")
        pizzas = db.query(Pizza).filter(Pizza.disponible == True).limit(5).all()
        for i, pizza in enumerate(pizzas, 1):
            print(f"{i}. {pizza.emoji or '🍕'} {pizza.nombre} - ${pizza.precio_mediana}")
        
        if total_pizzas > 5:
            print(f"... y {total_pizzas - 5} más")
    
    except Exception as e:
        print(f"Error obteniendo estadísticas: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    print("🍕 PIZZA BOT AI - Ejemplo de uso del AIService")
    print("=" * 60)
    
    # Mostrar estadísticas primero
    mostrar_estadisticas_bd()
    
    # Ejecutar ejemplos
    asyncio.run(ejemplo_uso_ai_service())
