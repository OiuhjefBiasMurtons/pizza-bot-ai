import pytest
from app.models.pizza import Pizza
from app.models.cliente import Cliente
from app.models.pedido import Pedido, DetallePedido

@pytest.mark.unit
def test_pizza_model(db):
    """Test Pizza model creation and attributes"""
    pizza = Pizza(
        nombre="Margherita",
        descripcion="Pizza clásica italiana",
        precio_pequena=12.99,
        precio_mediana=16.99,
        precio_grande=20.99,
        emoji="🍅"
    )
    
    db.add(pizza)
    db.commit()
    db.refresh(pizza)
    
    assert pizza.id is not None
    assert pizza.nombre == "Margherita"
    assert pizza.precio_pequena == 12.99
    assert pizza.disponible == True  # Default value
    assert pizza.emoji == "🍅"

@pytest.mark.unit
def test_cliente_model(db):
    """Test Cliente model creation and attributes"""
    cliente = Cliente(
        numero_whatsapp="+1234567890",
        nombre="Juan Pérez",
        direccion="Calle 123, Ciudad"
    )
    
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    
    assert cliente.id is not None
    assert cliente.numero_whatsapp == "+1234567890"
    assert cliente.nombre == "Juan Pérez"
    assert cliente.activo == True  # Default value
    assert cliente.fecha_registro is not None

@pytest.mark.unit
def test_pedido_model(db, sample_cliente, sample_pizza):
    """Test Pedido model creation and relationships"""
    pedido = Pedido(
        cliente_id=sample_cliente.id,
        total=25.98,
        direccion_entrega="Calle 456, Ciudad",
        estado="pendiente"
    )
    
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    
    assert pedido.id is not None
    assert pedido.cliente_id == sample_cliente.id
    assert pedido.total == 25.98
    assert pedido.estado == "pendiente"
    assert pedido.fecha_pedido is not None

@pytest.mark.unit
def test_detalle_pedido_model(db, sample_pedido, sample_pizza):
    """Test DetallePedido model creation and relationships"""
    detalle = DetallePedido(
        pedido_id=sample_pedido.id,
        pizza_id=sample_pizza.id,
        tamano="grande",
        cantidad=2,
        precio_unitario=20.99,
        subtotal=41.98
    )
    
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    
    assert detalle.id is not None
    assert detalle.pedido_id == sample_pedido.id
    assert detalle.pizza_id == sample_pizza.id
    assert detalle.tamano == "grande"
    assert detalle.cantidad == 2
    assert detalle.subtotal == 41.98

@pytest.mark.unit
def test_pizza_model_repr(db):
    """Test Pizza model string representation"""
    pizza = Pizza(
        nombre="Pepperoni",
        descripcion="Pizza con pepperoni",
        precio_pequena=14.99,
        precio_mediana=18.99,
        precio_grande=22.99
    )
    
    db.add(pizza)
    db.commit()
    db.refresh(pizza)
    
    repr_str = repr(pizza)
    assert "Pepperoni" in repr_str
    assert "14.99" in repr_str

@pytest.mark.unit
def test_cliente_unique_whatsapp(db):
    """Test that WhatsApp number is unique"""
    cliente1 = Cliente(numero_whatsapp="+1234567890", nombre="Cliente 1")
    cliente2 = Cliente(numero_whatsapp="+1234567890", nombre="Cliente 2")
    
    db.add(cliente1)
    db.commit()
    
    db.add(cliente2)
    
    # Debería fallar por constraint de unicidad
    with pytest.raises(Exception):
        db.commit() 