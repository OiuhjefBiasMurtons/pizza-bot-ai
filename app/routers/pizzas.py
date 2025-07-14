from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from app.models.pizza import Pizza

router = APIRouter()

# Obtener todas las pizzas disponibles
@router.get("/", response_model=List[dict])
async def get_pizzas(db: Session = Depends(get_db)):
    """Obtener todas las pizzas disponibles"""
    pizzas = db.query(Pizza).filter(Pizza.disponible == True).all()
    return [
        {
            "id": pizza.id,
            "nombre": pizza.nombre,
            "descripcion": pizza.descripcion,
            "precio_pequena": pizza.precio_pequena,
            "precio_mediana": pizza.precio_mediana,
            "precio_grande": pizza.precio_grande,
            "emoji": pizza.emoji
        }
        for pizza in pizzas
    ]

# Obtener una pizza específica por ID
@router.get("/{pizza_id}")
async def get_pizza(pizza_id: int, db: Session = Depends(get_db)):
    """Obtener una pizza específica por ID"""
    pizza = db.query(Pizza).filter(Pizza.id == pizza_id).first()
    if not pizza:
        raise HTTPException(status_code=404, detail="Pizza no encontrada")
    
    return {
        "id": pizza.id,
        "nombre": pizza.nombre,
        "descripcion": pizza.descripcion,
        "precio_pequena": pizza.precio_pequena,
        "precio_mediana": pizza.precio_mediana,
        "precio_grande": pizza.precio_grande,
        "emoji": pizza.emoji
    }

# Obtener el menú en formato texto para WhatsApp
@router.get("/menu/text")
async def get_menu_text(db: Session = Depends(get_db)):
    """Obtener el menú en formato texto para WhatsApp"""
    pizzas = db.query(Pizza).filter(Pizza.disponible == True).all()
    
    menu_text = "🍕 *MENÚ DE PIZZAS* 🍕\n\n"
    
    for i, pizza in enumerate(pizzas, 1):
        menu_text += f"{i}. {pizza.emoji} *{pizza.nombre}*\n"
        menu_text += f"   {pizza.descripcion}\n"
        menu_text += f"   • Pequeña: ${pizza.precio_pequena:.2f}\n"
        menu_text += f"   • Mediana: ${pizza.precio_mediana:.2f}\n"
        menu_text += f"   • Grande: ${pizza.precio_grande:.2f}\n\n"
    
    menu_text += "Para hacer un pedido, responde con el número de la pizza y el tamaño.\n"
    menu_text += "Ejemplo: '1 mediana' o '2 grande'"
    
    return {"menu": menu_text} 