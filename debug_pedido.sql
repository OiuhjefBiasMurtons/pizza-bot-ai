-- Consulta para verificar el último pedido creado
SELECT 
    p.id,
    p.fecha_pedido,
    p.estado,
    p.total,
    p.direccion_entrega,
    p.telefono_contacto,
    c.nombre as cliente_nombre,
    c.direccion as cliente_direccion_registrada,
    dp.cantidad,
    dp.tamano,
    dp.subtotal,
    pizza.nombre as pizza_nombre
FROM pedidos p
LEFT JOIN clientes c ON p.cliente_id = c.id
LEFT JOIN detalle_pedidos dp ON p.id = dp.pedido_id
LEFT JOIN pizzas pizza ON dp.pizza_id = pizza.id
ORDER BY p.fecha_pedido DESC
LIMIT 3;
