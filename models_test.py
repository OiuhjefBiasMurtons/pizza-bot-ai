"""
Modelos de prueba para el menú de pizzería basado en las imágenes del menú.
Este archivo modela los items del menú para una nueva base de datos.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class TamanoPizza(Enum):
    """Enum para los tamaños de pizza disponibles"""
    JUNIOR = "junior"
    PERSONAL = "personal"
    PEQUENA = "pequena"
    MEDIANA = "mediana"
    GRANDE = "grande"
    FAMILIAR = "familiar"


class TamanoLasagna(Enum):
    """Enum para los tamaños de lasagna disponibles"""
    PEQUENA = "pequena"
    GRANDE = "grande"
    EXTRA = "extra"


class CategoriaItem(Enum):
    """Categorías de items del menú"""
    PIZZA = "pizza"
    LASAGNA = "lasagna"
    ENTRADA = "entrada"

@dataclass
class TamanoInfo:
    """Información sobre un tamaño específico"""
    nombre: str
    porciones: str
    precio: int


@dataclass
class VariedadPizza:
    """Información sobre una variedad de pizza"""
    nombre: str
    ingredientes: List[str]
    descripcion: Optional[str] = None


@dataclass
class VariedadLasagna:
    """Información sobre una variedad de lasagna"""
    nombre: str
    ingredientes: List[str]
    descripcion: Optional[str] = None


@dataclass
class Entrada:
    """Información sobre una entrada"""
    nombre: str
    descripcion: str
    precio: int


class MenuModels:
    """Clase que contiene todos los modelos del menú"""
    
    # Tamaños de pizza con precios
    TAMANOS_PIZZA = {
        TamanoPizza.JUNIOR: TamanoInfo("Junior", "4 porciones (21 CM)", 12000),
        TamanoPizza.PERSONAL: TamanoInfo("Personal", "4 porciones", 22000),
        TamanoPizza.PEQUENA: TamanoInfo("Pequeña", "6 porciones (30 CM)", 29000),
        TamanoPizza.MEDIANA: TamanoInfo("Mediana", "8 porciones (35 CM)", 37000),
        TamanoPizza.GRANDE: TamanoInfo("Grande", "10 porciones (40 CM)", 44000),
        TamanoPizza.FAMILIAR: TamanoInfo("Familiar", "12 porciones (45 CM)", 55000),
    }
    
    # Tamaños de lasagna con precios
    TAMANOS_LASAGNA = {
        TamanoLasagna.PEQUENA: TamanoInfo("Pequeña", "", 14000),
        TamanoLasagna.GRANDE: TamanoInfo("Grande", "", 20000),
        TamanoLasagna.EXTRA: TamanoInfo("Extra", "", 27000),
    }
    
    # Variedades de pizza
    VARIEDADES_PIZZA = [
        VariedadPizza("De la Casa", ["jamón", "salami", "cabano", "cebolla", "champiñones", "pimentón"]),
        VariedadPizza("Carne", ["jamón", "salami", "cabano", "carne bolognesa"]),
        VariedadPizza("Mediterránea", ["jamón", "champiñón", "cebolla", "carne bolognesa"]),
        VariedadPizza("Ibérica", ["jamón", "salami", "cabano", "pollo"]),
        VariedadPizza("Peperoni", ["peperoni"]),
        VariedadPizza("Bolognesa", ["jamón", "maíz", "tomate", "pimentón", "cebolla", "carne bolognesa"]),
        VariedadPizza("Mexicana", ["jamón", "jalapeño", "carne bolognesa", "maíz", "pimentón", "cebolla", "tomate"]),
        VariedadPizza("Zamba", ["maduritos", "tocineta", "maíz"]),
        VariedadPizza("Maduritos", ["maduritos", "cabano", "maíz"]),
        VariedadPizza("Hawaiana", ["jamón", "piña"]),
        VariedadPizza("Piña", ["piña", "carne bolognesa"]),
        VariedadPizza("Tropical", ["pollo", "piña", "tocineta"]),
        VariedadPizza("Parmesana", ["maduro", "tocineta", "queso parmesano"]),
        VariedadPizza("Del Campo", ["jamón", "maíz", "tocineta", "tomate"]),
        VariedadPizza("Topo", ["pollo", "tomate", "tocineta"]),
        VariedadPizza("Toposa", ["tocineta", "pollo", "salami"]),
        VariedadPizza("Margarita", ["tomate", "albahaca", "aceite de oliva"]),
        VariedadPizza("Vegetariana", ["cebolla", "ajo", "champiñones", "tomate", "pimentón"]),
        VariedadPizza("Margarita Especial", ["tomate", "albahaca", "tocineta", "aceite de oliva"]),
        VariedadPizza("Italiana", ["jamón", "champiñones", "tomate", "maíz"]),
        VariedadPizza("Primavera", ["pollo", "tomate", "maíz"]),
        VariedadPizza("Americana", ["jamón", "salchicha ranchera", "maíz"]),
        VariedadPizza("Julieta", ["jamón", "salami", "maíz"]),
        VariedadPizza("Pollo con Champiñones", ["pollo", "champiñones"]),
        VariedadPizza("Pollo con Bolognesa y Piña", ["pollo", "carne bolognesa", "piña"]),
        VariedadPizza("Pollo con Tocineta y Maíz", ["pollo", "tocineta", "maíz"]),
        VariedadPizza("Pollo y Jamón", ["pollo", "jamón"]),
        VariedadPizza("Española", ["salami", "cabano", "aceitunas"]),
        VariedadPizza("Picante", ["jamón", "pollo", "carne bolognesa", "pimienta negra"]),
    ]
    
    # Variedades de lasagna
    VARIEDADES_LASAGNA = [
        VariedadLasagna("De Bolognesa", ["carne bolognesa"], "Acompañada con pan de ajo"),
        VariedadLasagna("De Bolognesa + Jamón", ["carne bolognesa", "jamón"], "Acompañada con pan de ajo"),
        VariedadLasagna("De Bolognesa + Maíz", ["carne bolognesa", "maíz"], "Acompañada con pan de ajo"),
        VariedadLasagna("De Pollo", ["pollo"], "Acompañada con pan de ajo"),
        VariedadLasagna("De Pollo + Maíz", ["pollo", "maíz"], "Acompañada con pan de ajo"),
        VariedadLasagna("Pocha", ["pollo", "champiñón"], "Acompañada con pan de ajo"),
        VariedadLasagna("Mixta", ["pollo", "carne bolognesa"], "Acompañada con pan de ajo"),
        VariedadLasagna("Tropical", ["pollo", "carne bolognesa", "piña"], "Acompañada con pan de ajo"),
        VariedadLasagna("Vegetariana", ["champiñones", "cebolla", "ajo", "tomate"], "Acompañada con pan de ajo"),
    ]
    
    # Entradas
    ENTRADAS = [
        Entrada("Pancito con Queso Crema o Parmesano", "Pancito con queso crema o parmesano", 10000),
        Entrada("Pancito con Tomate y Queso Crema", "Pancito con tomate y queso crema", 10000),
        Entrada("Pancitos con Tocineta y Queso Crema", "Pancitos con tocineta y queso crema", 10000),
    ]


@dataclass
class ItemMenu:
    """Modelo genérico para un item del menú"""
    id: Optional[int]
    categoria: CategoriaItem
    nombre: str
    variedad: str
    tamano: Optional[str]
    precio: int
    ingredientes: List[str]
    descripcion: Optional[str] = None
    disponible: bool = True


class MenuBuilder:
    """Constructor para crear items del menú"""
    
    @staticmethod
    def crear_pizza(variedad_nombre: str, tamano: TamanoPizza) -> ItemMenu:
        """Crea un item de pizza"""
        variedad = next((v for v in MenuModels.VARIEDADES_PIZZA if v.nombre == variedad_nombre), None)
        if not variedad:
            raise ValueError(f"Variedad de pizza '{variedad_nombre}' no encontrada")
        
        tamano_info = MenuModels.TAMANOS_PIZZA[tamano]
        
        return ItemMenu(
            id=None,
            categoria=CategoriaItem.PIZZA,
            nombre="Pizza",
            variedad=variedad.nombre,
            tamano=tamano_info.nombre,
            precio=tamano_info.precio,
            ingredientes=variedad.ingredientes,
            descripcion=f"Pizza {variedad.nombre} {tamano_info.nombre} ({tamano_info.porciones})"
        )
    
    @staticmethod
    def crear_lasagna(variedad_nombre: str, tamano: TamanoLasagna) -> ItemMenu:
        """Crea un item de lasagna"""
        variedad = next((v for v in MenuModels.VARIEDADES_LASAGNA if v.nombre == variedad_nombre), None)
        if not variedad:
            raise ValueError(f"Variedad de lasagna '{variedad_nombre}' no encontrada")
        
        tamano_info = MenuModels.TAMANOS_LASAGNA[tamano]
        
        return ItemMenu(
            id=None,
            categoria=CategoriaItem.LASAGNA,
            nombre="Lasagna",
            variedad=variedad.nombre,
            tamano=tamano_info.nombre,
            precio=tamano_info.precio,
            ingredientes=variedad.ingredientes,
            descripcion=f"Lasagna {variedad.nombre} {tamano_info.nombre}. {variedad.descripcion}"
        )
    
    @staticmethod
    def crear_entrada(entrada_nombre: str) -> ItemMenu:
        """Crea un item de entrada"""
        entrada = next((e for e in MenuModels.ENTRADAS if e.nombre == entrada_nombre), None)
        if not entrada:
            raise ValueError(f"Entrada '{entrada_nombre}' no encontrada")
        
        return ItemMenu(
            id=None,
            categoria=CategoriaItem.ENTRADA,
            nombre="Entrada",
            variedad=entrada.nombre,
            tamano=None,
            precio=entrada.precio,
            ingredientes=[],
            descripcion=entrada.descripcion
        )


def test_models():
    """Función de prueba para validar los modelos"""
    print("=== PRUEBA DE MODELOS DEL MENÚ ===\n")
    
    # Crear algunas pizzas de ejemplo
    print("🍕 PIZZAS:")
    pizza1 = MenuBuilder.crear_pizza("De la Casa", TamanoPizza.MEDIANA)
    pizza2 = MenuBuilder.crear_pizza("Hawaiana", TamanoPizza.GRANDE)
    
    print(f"- {pizza1.descripcion}")
    print(f"  Ingredientes: {', '.join(pizza1.ingredientes)}")
    print(f"  Precio: ${pizza1.precio:,}")
    print()
    
    print(f"- {pizza2.descripcion}")
    print(f"  Ingredientes: {', '.join(pizza2.ingredientes)}")
    print(f"  Precio: ${pizza2.precio:,}")
    print()
    
    # Crear algunas lasagnas de ejemplo
    print("🍝 LASAGNAS:")
    lasagna1 = MenuBuilder.crear_lasagna("De Bolognesa", TamanoLasagna.GRANDE)
    lasagna2 = MenuBuilder.crear_lasagna("Tropical", TamanoLasagna.PEQUENA)
    
    print(f"- {lasagna1.descripcion}")
    print(f"  Ingredientes: {', '.join(lasagna1.ingredientes)}")
    print(f"  Precio: ${lasagna1.precio:,}")
    print()
    
    print(f"- {lasagna2.descripcion}")
    print(f"  Ingredientes: {', '.join(lasagna2.ingredientes)}")
    print(f"  Precio: ${lasagna2.precio:,}")
    print()
    
    # Crear algunas entradas de ejemplo
    print("🥖 ENTRADAS:")
    entrada1 = MenuBuilder.crear_entrada("Pancito con Queso Crema o Parmesano")
    
    print(f"- {entrada1.descripcion}")
    print(f"  Precio: ${entrada1.precio:,}")
    print()
    
    print("=== RESUMEN DEL MENÚ ===")
    print(f"📊 Total variedades de pizza: {len(MenuModels.VARIEDADES_PIZZA)}")
    print(f"📊 Total tamaños de pizza: {len(MenuModels.TAMANOS_PIZZA)}")
    print(f"📊 Total variedades de lasagna: {len(MenuModels.VARIEDADES_LASAGNA)}")
    print(f"📊 Total tamaños de lasagna: {len(MenuModels.TAMANOS_LASAGNA)}")
    print(f"📊 Total entradas: {len(MenuModels.ENTRADAS)}")


if __name__ == "__main__":
    test_models()
