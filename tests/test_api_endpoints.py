import pytest
from fastapi.testclient import TestClient

@pytest.mark.unit
def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "Pizza Bot API funcionando" in data["message"]
    assert data["status"] == "activo"

@pytest.mark.unit
def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "pizza-bot"

@pytest.mark.unit
def test_get_pizzas_empty(client, db):
    """Test get pizzas when database is empty"""
    response = client.get("/pizzas/")
    
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.unit
def test_get_pizzas_with_data(client, db, sample_pizza):
    """Test get pizzas with data"""
    response = client.get("/pizzas/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nombre"] == sample_pizza.nombre
    assert data[0]["precio_pequena"] == sample_pizza.precio_pequena

@pytest.mark.unit
def test_get_pizza_by_id_existing(client, db, sample_pizza):
    """Test get pizza by existing ID"""
    response = client.get(f"/pizzas/{sample_pizza.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == sample_pizza.nombre
    assert data["id"] == sample_pizza.id

@pytest.mark.unit
def test_get_pizza_by_id_not_found(client, db):
    """Test get pizza by non-existing ID"""
    response = client.get("/pizzas/999")
    
    assert response.status_code == 404
    assert "Pizza no encontrada" in response.json()["detail"]

@pytest.mark.unit
def test_get_menu_text(client, db, sample_pizza):
    """Test get menu in text format"""
    response = client.get("/pizzas/menu/text")
    
    assert response.status_code == 200
    data = response.json()
    menu_text = data["menu"]
    assert "MENÚ DE PIZZAS" in menu_text
    assert sample_pizza.nombre in menu_text
    assert str(sample_pizza.precio_pequena) in menu_text

@pytest.mark.unit
def test_get_pedidos_empty(client, db):
    """Test get pedidos when database is empty"""
    response = client.get("/pedidos/")
    
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.unit
def test_get_pedidos_with_data(client, db, sample_pedido):
    """Test get pedidos with data"""
    response = client.get("/pedidos/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_pedido.id
    assert data[0]["total"] == sample_pedido.total

@pytest.mark.unit
def test_get_pedido_by_id_existing(client, db, sample_pedido):
    """Test get pedido by existing ID"""
    response = client.get(f"/pedidos/{sample_pedido.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_pedido.id
    assert data["total"] == sample_pedido.total
    assert "detalles" in data

@pytest.mark.unit
def test_get_pedido_by_id_not_found(client, db):
    """Test get pedido by non-existing ID"""
    response = client.get("/pedidos/999")
    
    assert response.status_code == 404
    assert "Pedido no encontrado" in response.json()["detail"]

@pytest.mark.unit
def test_update_pedido_estado_valid(client, db, sample_pedido):
    """Test update pedido estado with valid state"""
    response = client.put(f"/pedidos/{sample_pedido.id}/estado", params={
        "nuevo_estado": "confirmado"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "confirmado" in data["message"]

@pytest.mark.unit
def test_update_pedido_estado_invalid(client, db, sample_pedido):
    """Test update pedido estado with invalid state"""
    response = client.put(f"/pedidos/{sample_pedido.id}/estado", params={
        "nuevo_estado": "estado_invalido"
    })
    
    assert response.status_code == 400
    assert "Estado no válido" in response.json()["detail"]

@pytest.mark.unit
def test_update_pedido_estado_not_found(client, db):
    """Test update pedido estado with non-existing ID"""
    response = client.put("/pedidos/999/estado", params={
        "nuevo_estado": "confirmado"
    })
    
    assert response.status_code == 404
    assert "Pedido no encontrado" in response.json()["detail"]

@pytest.mark.unit
def test_get_pedidos_cliente_existing(client, db, sample_cliente, sample_pedido):
    """Test get pedidos for existing cliente"""
    response = client.get(f"/pedidos/cliente/{sample_cliente.numero_whatsapp}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_pedido.id

@pytest.mark.unit
def test_get_pedidos_cliente_not_found(client, db):
    """Test get pedidos for non-existing cliente"""
    response = client.get("/pedidos/cliente/+9999999999")
    
    assert response.status_code == 404
    assert "Cliente no encontrado" in response.json()["detail"]

@pytest.mark.unit
def test_get_pedidos_cliente_no_orders(client, db, sample_cliente):
    """Test get pedidos for cliente with no orders"""
    response = client.get(f"/pedidos/cliente/{sample_cliente.numero_whatsapp}")
    
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.integration
def test_api_docs_endpoint(client):
    """Test API documentation endpoint"""
    response = client.get("/docs")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.integration
def test_api_openapi_endpoint(client):
    """Test OpenAPI schema endpoint"""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Pizza Bot API" 