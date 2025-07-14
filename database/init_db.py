from sqlalchemy import create_engine
from database.connection import Base, engine
from app.models import Pizza, Cliente, Pedido, DetallePedido

def init_database():
    """Crear todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente")

def populate_pizzas():
    """Poblar la base de datos con pizzas de ejemplo"""
    from database.connection import SessionLocal
    
    db = SessionLocal()
    
    # Verificar si ya hay pizzas
    if db.query(Pizza).count() > 0:
        print("⚠️  Ya hay pizzas en la base de datos")
        db.close()
        return
    
    pizzas_data = [
        {
            "nombre": "Margherita",
            "descripcion": "Salsa de tomate, mozzarella, albahaca fresca",
            "precio_pequena": 12.99,
            "precio_mediana": 16.99,
            "precio_grande": 20.99,
            "emoji": "🍅"
        },
        {
            "nombre": "Pepperoni",
            "descripcion": "Salsa de tomate, mozzarella, pepperoni",
            "precio_pequena": 14.99,
            "precio_mediana": 18.99,
            "precio_grande": 22.99,
            "emoji": "🍕"
        },
        {
            "nombre": "Hawaiana",
            "descripcion": "Salsa de tomate, mozzarella, jamón, piña",
            "precio_pequena": 15.99,
            "precio_mediana": 19.99,
            "precio_grande": 23.99,
            "emoji": "🍍"
        },
        {
            "nombre": "Cuatro Quesos",
            "descripcion": "Mozzarella, parmesano, gorgonzola, ricotta",
            "precio_pequena": 16.99,
            "precio_mediana": 20.99,
            "precio_grande": 24.99,
            "emoji": "🧀"
        },
        {
            "nombre": "Vegetariana",
            "descripcion": "Salsa de tomate, mozzarella, pimientos, cebolla, champiñones",
            "precio_pequena": 13.99,
            "precio_mediana": 17.99,
            "precio_grande": 21.99,
            "emoji": "🥬"
        },
        {
            "nombre": "Carnívora",
            "descripcion": "Salsa de tomate, mozzarella, pepperoni, salchicha, jamón, tocino",
            "precio_pequena": 17.99,
            "precio_mediana": 21.99,
            "precio_grande": 25.99,
            "emoji": "🥩"
        }
    ]
    
    for pizza_data in pizzas_data:
        pizza = Pizza(**pizza_data)
        db.add(pizza)
    
    db.commit()
    db.close()
    print("✅ Pizzas agregadas a la base de datos")

if __name__ == "__main__":
    init_database()
    populate_pizzas() 