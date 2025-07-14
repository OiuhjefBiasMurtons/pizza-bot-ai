# 🗄️ Modelo de Datos - Pizza Bot

## Descripción General

El modelo de datos del Pizza Bot está diseñado para gestionar de manera eficiente los pedidos de pizza a través de WhatsApp. La base de datos utiliza PostgreSQL y está estructurada en 4 tablas principales que manejan clientes, pizzas, pedidos y detalles de pedidos.

## Tablas

### 1. `clientes`

Almacena información de los clientes que interactúan con el bot.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Identificador único del cliente |
| `numero_whatsapp` | VARCHAR(20) | NOT NULL, UNIQUE, INDEX | Número de WhatsApp del cliente (formato: +1234567890) |
| `nombre` | VARCHAR(100) | NULL | Nombre del cliente (opcional) |
| `direccion` | VARCHAR(200) | NULL | Dirección por defecto del cliente |
| `activo` | BOOLEAN | DEFAULT TRUE | Estado del cliente (activo/inactivo) |
| `fecha_registro` | TIMESTAMP | DEFAULT NOW() | Fecha de registro del cliente |
| `ultimo_pedido` | TIMESTAMP | NULL | Fecha del último pedido realizado |

**Índices:**
- `idx_clientes_whatsapp` en `numero_whatsapp`

**Relaciones:**
- Uno a muchos con `pedidos`

### 2. `pizzas`

Catálogo de pizzas disponibles en el menú.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Identificador único de la pizza |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre de la pizza |
| `descripcion` | TEXT | NULL | Descripción de ingredientes |
| `precio_pequena` | DECIMAL(10,2) | NOT NULL | Precio para tamaño pequeño |
| `precio_mediana` | DECIMAL(10,2) | NOT NULL | Precio para tamaño mediano |
| `precio_grande` | DECIMAL(10,2) | NOT NULL | Precio para tamaño grande |
| `disponible` | BOOLEAN | DEFAULT TRUE | Disponibilidad de la pizza |
| `emoji` | VARCHAR(10) | DEFAULT '🍕' | Emoji para mostrar en el menú |

**Relaciones:**
- Uno a muchos con `detalle_pedidos`

### 3. `pedidos`

Información principal de cada pedido realizado.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Identificador único del pedido |
| `cliente_id` | INTEGER | NOT NULL, FOREIGN KEY | Referencia al cliente que hizo el pedido |
| `estado` | VARCHAR(50) | DEFAULT 'pendiente' | Estado del pedido |
| `total` | DECIMAL(10,2) | NOT NULL | Total del pedido |
| `direccion_entrega` | VARCHAR(200) | NULL | Dirección de entrega |
| `notas` | TEXT | NULL | Notas adicionales del pedido |
| `fecha_pedido` | TIMESTAMP | DEFAULT NOW() | Fecha y hora del pedido |
| `fecha_entrega` | TIMESTAMP | NULL | Fecha y hora de entrega |

**Estados posibles:**
- `pendiente` - Pedido recibido, pendiente de confirmación
- `confirmado` - Pedido confirmado, listo para preparar
- `preparando` - Pedido en preparación
- `enviado` - Pedido enviado para entrega
- `entregado` - Pedido entregado exitosamente
- `cancelado` - Pedido cancelado

**Relaciones:**
- Muchos a uno con `clientes`
- Uno a muchos con `detalle_pedidos`

### 4. `detalle_pedidos`

Detalle de cada pizza incluida en un pedido.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Identificador único del detalle |
| `pedido_id` | INTEGER | NOT NULL, FOREIGN KEY | Referencia al pedido |
| `pizza_id` | INTEGER | NOT NULL, FOREIGN KEY | Referencia a la pizza |
| `tamano` | VARCHAR(20) | NOT NULL | Tamaño de la pizza |
| `cantidad` | INTEGER | NOT NULL | Cantidad ordenada |
| `precio_unitario` | DECIMAL(10,2) | NOT NULL | Precio unitario al momento del pedido |
| `subtotal` | DECIMAL(10,2) | NOT NULL | Subtotal (cantidad × precio_unitario) |

**Tamaños válidos:**
- `pequeña`
- `mediana`
- `grande`

**Relaciones:**
- Muchos a uno con `pedidos`
- Muchos a uno con `pizzas`

## Relaciones

```
CLIENTES (1) ----< PEDIDOS (1) ----< DETALLE_PEDIDOS (N) >---- PIZZAS (1)
```

- Un **cliente** puede tener múltiples **pedidos**
- Un **pedido** puede tener múltiples **detalles de pedido**
- Una **pizza** puede estar en múltiples **detalles de pedido**

## Consultas Comunes

### 1. Obtener pedidos de un cliente

```sql
SELECT p.*, c.nombre, c.numero_whatsapp
FROM pedidos p
JOIN clientes c ON p.cliente_id = c.id
WHERE c.numero_whatsapp = '+1234567890'
ORDER BY p.fecha_pedido DESC;
```

### 2. Obtener detalles de un pedido

```sql
SELECT dp.*, pz.nombre, pz.emoji
FROM detalle_pedidos dp
JOIN pizzas pz ON dp.pizza_id = pz.id
WHERE dp.pedido_id = 1;
```

### 3. Obtener pizzas más populares

```sql
SELECT pz.nombre, COUNT(dp.id) as total_pedidos
FROM pizzas pz
JOIN detalle_pedidos dp ON pz.id = dp.pizza_id
GROUP BY pz.id, pz.nombre
ORDER BY total_pedidos DESC
LIMIT 5;
```

### 4. Obtener estadísticas de pedidos por estado

```sql
SELECT estado, COUNT(*) as total
FROM pedidos
GROUP BY estado;
```

## Migraciones con Alembic

El proyecto incluye Alembic para el manejo de migraciones de base de datos:

```bash
# Generar nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Ver historial
alembic history

# Volver a versión anterior
alembic downgrade -1
```

## Consideraciones de Diseño

### 1. Normalización
- Las tablas están normalizadas para evitar redundancia
- Los precios se almacenan en `detalle_pedidos` para mantener un histórico

### 2. Escalabilidad
- Índices en campos de búsqueda frecuente
- Soft deletes usando campos `activo` y `disponible`

### 3. Integridad
- Claves foráneas para mantener integridad referencial
- Validaciones en nivel de aplicación

### 4. Auditoria
- Campos de timestamp para rastrear cambios
- Estado de pedidos para seguimiento

## Datos de Ejemplo

El sistema incluye datos de ejemplo que se pueden cargar ejecutando:

```bash
python database/init_db.py
```

Esto crea:
- 6 pizzas con diferentes precios
- Tablas vacías para clientes y pedidos

## Backup y Restauración

### Backup
```bash
pg_dump -h localhost -U usuario -d pizzabot_db > backup.sql
```

### Restauración
```bash
psql -h localhost -U usuario -d pizzabot_db < backup.sql
```

## Monitoreo

Se recomienda monitorear:
- Tamaño de las tablas
- Consultas lentas
- Conexiones activas
- Espacio en disco

## Optimizaciones Futuras

1. **Particionamiento**: Particionar tabla `pedidos` por fecha
2. **Índices**: Agregar índices compuestos según patrones de consulta
3. **Caching**: Implementar Redis para consultas frecuentes
4. **Archiving**: Archivar pedidos antiguos 