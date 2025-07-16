# 🔄 Flujo de Trabajo - Pizza Bot WhatsApp con IA

## 📋 Resumen del Sistema

El **Pizza Bot** es una aplicación FastAPI que automatiza la toma de pedidos de pizza a través de WhatsApp. El sistema está diseñado con una arquitectura modular híbrida que combina **flujo tradicional** con **inteligencia artificial**, permitiendo tanto comandos simples como conversaciones naturales.

## 🏗️ Arquitectura General

```
📱 WhatsApp (Cliente) 
    ↓ Webhook
🌐 FastAPI (API Gateway)
    ↓ Routers
🧠 EnhancedBotService (Coordinador)
    ↓ ¿Usar IA?
   ↙         ↘
🤖 AIService   📋 BotService
(OpenAI)       (Tradicional)
    ↓ Models
🗄️ PostgreSQL (Base de datos)
```

---

## 📁 Estructura de Archivos `/app`

### 1. **Models** - Modelos de Datos (`/app/models/`)

#### **`cliente.py`**
- **Propósito**: Define la estructura de datos para los clientes de WhatsApp
- **Tabla**: `clientes`
- **Campos principales**:
  - `numero_whatsapp`: Identificador único del cliente
  - `nombre`: Nombre del cliente (opcional)
  - `direccion`: Dirección por defecto
  - `fecha_registro`: Timestamp de registro
  - `ultimo_pedido`: Fecha del último pedido

#### **`pizza.py`**
- **Propósito**: Define el catálogo de pizzas disponibles
- **Tabla**: `pizzas`
- **Campos principales**:
  - `nombre`: Nombre de la pizza
  - `descripcion`: Descripción detallada
  - `precio_pequena/mediana/grande`: Precios por tamaño
  - `disponible`: Estado de disponibilidad
  - `emoji`: Emoji para mostrar en el chat

#### **`pedido.py`**
- **Propósito**: Gestiona los pedidos y sus detalles
- **Tablas**: `pedidos` y `detalle_pedidos`
- **Funcionalidad**:
  - `Pedido`: Información general del pedido
  - `DetallePedido`: Items específicos de cada pedido
  - **Estados**: pendiente → confirmado → preparando → enviado → entregado

---

### 2. **Services** - Lógica de Negocio (`/app/services/`)

#### **`enhanced_bot_service.py`** ⭐ *NUEVO*
```python
class EnhancedBotService:
    # Funciones principales:
    - process_message()           # Procesador principal híbrido
    - should_use_ai_processing()  # Decide entre IA y tradicional
    - process_with_ai()           # Procesa con inteligencia artificial
    - process_with_traditional_flow() # Procesa con flujo tradicional
    - handle_ai_response()        # Maneja respuestas de IA
    - execute_ai_action()         # Ejecuta acciones sugeridas por IA
```

**Responsabilidades**:
- 🧠 **Coordinación inteligente**: Decide cuándo usar IA vs flujo tradicional
- 🤖 **Integración de IA**: Gestiona comunicación con OpenAI
- 📝 **Procesamiento híbrido**: Combina lo mejor de ambos mundos
- 🔄 **Gestión de estados**: Mantiene coherencia entre sistemas

**Criterios de Decisión**:
- **USA FLUJO TRADICIONAL**: Comandos simples ("hola", "menu", "1", "si")
- **USA IA**: Lenguaje natural ("Quiero una pizza margarita grande")

#### **`ai_service.py`** ⭐ *NUEVO*
```python
class AIService:
    # Funciones principales:
    - process_with_ai()           # Procesa mensaje con OpenAI
    - _create_system_prompt()     # Genera instrucciones para IA
    - _build_conversation_context() # Construye contexto de conversación
    - extract_intent()            # Extrae intención del mensaje
    - should_use_ai()             # Determina si usar IA
```

**Responsabilidades**:
- 🤖 **Comunicación con OpenAI**: Maneja llamadas a la API de OpenAI
- 📝 **Procesamiento de lenguaje natural**: Entiende mensajes complejos
- 🎯 **Extracción de intenciones**: Identifica qué quiere el usuario
- 📊 **Respuestas estructuradas**: Genera respuestas en formato JSON
- 🔄 **Manejo de contexto**: Mantiene memoria de la conversación

**Formato de Respuesta de IA**:
```json
{
    "tipo_respuesta": "pedido|informacion|menu|ayuda",
    "requiere_accion": true/false,
    "accion_sugerida": "agregar_pizza|confirmar_pedido|solicitar_direccion",
    "mensaje": "Respuesta para el usuario",
    "datos_extraidos": {
        "pizzas_solicitadas": [{"numero": 1, "tamaño": "grande", "cantidad": 1}],
        "direccion": "dirección si se menciona",
        "modificaciones": "cambios solicitados"
    }
}
```

#### **`whatsapp_service.py`**
```python
class WhatsAppService:
    # Funciones principales:
    - send_message()           # Enviar mensajes por WhatsApp
    - validate_webhook()       # Validar autenticidad de Twilio
    - _format_phone_number()   # Formatear números de teléfono
```

**Responsabilidades**:
- 📤 Envío de mensajes a través de Twilio
- 🔒 Validación de webhooks de seguridad
- 📞 Formateo correcto de números de teléfono
- 🚫 Manejo de errores de Twilio

#### **`bot_service.py`** *TRADICIONAL*
```python
class BotService:
    # Funciones principales:
    - process_message()           # Procesador tradicional de mensajes
    - handle_saludo()            # Maneja saludos iniciales
    - handle_menu()              # Muestra menú de pizzas
    - handle_seleccion_pizza()   # Procesa selección de pizzas
    - handle_direccion()         # Captura dirección de entrega
    - handle_confirmacion()      # Confirma pedido final
```

**Estados de Conversación**:
- `INICIO`: Usuario nuevo o saludo
- `REGISTRO_NOMBRE`: Captura nombre del cliente
- `REGISTRO_DIRECCION`: Captura dirección del cliente
- `MENU`: Mostrando opciones de pizzas
- `PEDIDO`: Construyendo carrito de compras
- `DIRECCION`: Solicitando dirección de entrega
- `CONFIRMACION`: Confirmando pedido final
- `FINALIZADO`: Pedido completado

**Responsabilidades**:
- 🧠 **Lógica tradicional**: Maneja comandos específicos y flujos predefinidos
- 💬 **Estados de conversación**: Gestiona transiciones de estado
- 🛒 **Carrito de compras**: Administra items del pedido
- 📝 **Comandos simples**: Procesa "menu", "1", "si", "no"

#### **`conversation_state.py`** ⭐ *NUEVO MODELO*
```python
class ConversationState:
    # Campos principales:
    - numero_whatsapp: str        # Identificador del cliente
    - estado_actual: str          # Estado actual de la conversación
    - datos_temporales: str       # Datos JSON temporales (carrito, etc.)
    - fecha_actualizacion: datetime # Última actualización
```

**Responsabilidades**:
- � **Persistencia de estado**: Guarda estado de conversación en BD
- 🔄 **Continuidad**: Mantiene contexto entre mensajes
- 📊 **Datos temporales**: Almacena carrito y datos de sesión
- 🧠 **Memoria de conversación**: Contexto para IA y flujo tradicional

#### **`pedido_service.py`**
```python
class PedidoService:
    # Funciones principales:
    - crear_pedido()              # Crear pedido en BD
    - obtener_pedido()            # Obtener pedido por ID
    - obtener_pedidos_cliente()   # Historial del cliente
    - actualizar_estado_pedido()  # Cambiar estado
    - calcular_total_carrito()    # Calcular totales
```

**Responsabilidades**:
- 💾 Operaciones CRUD de pedidos
- 🧮 Cálculos financieros (totales, subtotales)
- 📊 Consultas de historial
- 🔄 Gestión de estados de pedidos

---

### 3. **Routers** - Endpoints de API (`/app/routers/`)

#### **`webhook.py`**
```python
# Endpoints principales:
- POST /webhook/whatsapp      # Recibe mensajes de WhatsApp
- GET /webhook/test           # Endpoint de prueba
- POST /webhook/send-message  # Envío manual de mensajes
```

**Flujo de Webhook**:
1. ✅ **Validación**: Verificar firma de Twilio
2. 🔍 **Extracción**: Obtener número y mensaje
3. 🧠 **Procesamiento**: Llamar a `BotService`
4. 📤 **Respuesta**: Enviar respuesta via `WhatsAppService`
5. 📝 **Logging**: Registrar actividad

#### **`pizzas.py`**
```python
# Endpoints principales:
- GET /pizzas/               # Todas las pizzas
- GET /pizzas/{id}          # Pizza específica
- GET /pizzas/menu/text     # Menú formato WhatsApp
```

**Responsabilidades**:
- 📋 API para consultar catálogo
- 📱 Formato especial para WhatsApp
- ✅ Filtros de disponibilidad

#### **`pedidos.py`**
```python
# Endpoints principales:
- GET /pedidos/                    # Todos los pedidos
- GET /pedidos/{id}               # Pedido específico
- PUT /pedidos/{id}/estado        # Actualizar estado
- GET /pedidos/cliente/{whatsapp} # Pedidos por cliente
```

**Responsabilidades**:
- 📊 API administrativa de pedidos
- 🔄 Gestión de estados
- 👤 Consultas por cliente

---

### 4. **Utils** - Utilidades (`/app/utils/`)

#### **`logging_config.py`**
- **Propósito**: Configuración centralizada de logging
- **Funcionalidad**: 
  - Formato estructurado de logs
  - Integración con Sentry (producción)
  - LoggerMixin para clases

---

## 🔄 Flujo Completo de un Pedido (Híbrido: IA + Tradicional)

### **1. Recepción del Mensaje (Webhook)**
```
WhatsApp → Twilio → webhook.py
```
- Usuario envía mensaje por WhatsApp
- Twilio recibe y envía webhook a `/webhook/whatsapp`
- `process_whatsapp_message()` valida y extrae datos

### **2. Coordinación Inteligente (Enhanced Bot Service)**
```
webhook.py → enhanced_bot_service.py
```
- `EnhancedBotService.process_message()` recibe el mensaje
- Verifica si el cliente está registrado
- Obtiene estado actual de la conversación
- **DECISIÓN CRUCIAL**: `should_use_ai_processing()`

#### **2A. Flujo con IA (Lenguaje Natural)**
```
enhanced_bot_service.py → ai_service.py → OpenAI
```
- **Trigger**: Mensajes como "Quiero una pizza margarita grande"
- `AIService.process_with_ai()` construye contexto
- Envía a OpenAI con system prompt personalizado
- Recibe respuesta JSON estructurada
- `handle_ai_response()` procesa la respuesta
- `execute_ai_action()` ejecuta acciones (agregar pizza, cambiar estado)

#### **2B. Flujo Tradicional (Comandos)**
```
enhanced_bot_service.py → bot_service.py (tradicional)
```
- **Trigger**: Comandos como "menu", "1", "si", "no"
- `process_with_traditional_flow()` maneja comandos específicos
- Ejecuta función correspondiente al estado actual
- Procesamiento rápido y directo

### **3. Operaciones de Base de Datos (Services)**
```
Cualquier flujo → pedido_service.py → models
```
- Ambos flujos pueden interactuar con la BD
- `PedidoService` maneja operaciones de pedidos
- `ConversationState` persiste estado de conversación
- Modelos de SQLAlchemy interactúan con PostgreSQL

### **4. Generación de Respuesta (Inteligente)**
```
enhanced_bot_service.py → respuesta híbrida
```
- **IA**: Respuestas naturales y contextuales
- **Tradicional**: Respuestas rápidas y directas
- Sistema unificado de respuestas al usuario

### **5. Envío de Respuesta (WhatsApp Service)**
```
webhook.py → whatsapp_service.py → Twilio → WhatsApp
```
- `WhatsAppService.send_message()` envía respuesta
- Twilio entrega mensaje al usuario
- Sistema registra logs de la transacción

---

## 📊 Estados y Transiciones (Híbrido)

```mermaid
graph TD
    A[INICIO] -->|"hola" - Tradicional| B[Saludo]
    A -->|"menu" - Tradicional| C[MENU]
    A -->|"Quiero una pizza margarita" - IA| D[PEDIDO]
    C -->|"1 mediana" - Tradicional| D[PEDIDO]
    C -->|"¿Cuál pizza tiene más carne?" - IA| E[Consulta IA]
    D -->|"más items" - Ambos| D
    D -->|"confirmar" - Tradicional| F[DIRECCION]
    D -->|"Ya está, procede" - IA| F[DIRECCION]
    F -->|"dirección" - Ambos| G[CONFIRMACION]
    G -->|"sí" - Tradicional| H[FINALIZADO]
    G -->|"Confirmo el pedido" - IA| H[FINALIZADO]
    G -->|"no" - Tradicional| D
    
    B --> C
    E --> C
    H --> A
```

### **Nuevos Estados con IA**:
- `REGISTRO_NOMBRE`: Captura inteligente de nombre
- `REGISTRO_DIRECCION`: Captura inteligente de dirección
- **Estados híbridos**: Todos los estados pueden procesarse con IA o tradicional

---

## 🔧 Comandos y Respuestas del Bot (Actualizado)

### **Comandos Tradicionales** (Flujo rápido)
- `hola`, `hello`, `buenas` → Saludo inicial
- `menu`, `menú`, `carta` → Mostrar catálogo
- `1`, `2`, `3` → Selección por número
- `si`, `sí`, `no` → Confirmaciones
- `ayuda`, `help` → Información de ayuda

### **Lenguaje Natural con IA** (Flujo inteligente)
- `"Quiero una pizza margarita grande"` → Agregar al carrito automáticamente
- `"¿Qué pizzas tienen carne?"` → Consulta inteligente del menú
- `"Cambia el tamaño a mediano"` → Modificación de pedido
- `"Agrega dos hawaianas pequeñas"` → Múltiples items
- `"¿Cuánto cuesta mi pedido?"` → Consulta de total

### **Ejemplos de Respuestas de IA**:
```
Usuario: "Quiero una pizza margarita grande"
Bot: "¡Perfecto! Te agrego una pizza Margarita grande por $15.99. ¿Quieres agregar algo más a tu pedido? 🍕"

Usuario: "¿Cuál pizza tiene más carne?"
Bot: "Te recomiendo la pizza Carnívora 🥩 que tiene pepperoni, salchicha y jamón. ¿Te gustaría agregarla a tu pedido?"

Usuario: "Cambia la pizza a mediana"
Bot: "Perfecto, cambié tu pizza Margarita a tamaño mediano por $12.99. Tu pedido actualizado cuesta $12.99 👍"
```

---

## ⚡ Características Técnicas (Actualizadas)

### **Integración con OpenAI**
- **API Key**: Configurada en variables de entorno
- **Modelo**: gpt-4-turbo-preview (principal), gpt-3.5-turbo (intenciones)
- **Temperatura**: 0.7 (balance entre creatividad y precisión)
- **Tokens máximos**: 500 (respuestas concisas)
- **Fallback**: Sistema tradicional si IA falla

### **Sistema Híbrido Inteligente**
- **Decisión automática**: Entre IA y flujo tradicional
- **Criterios de selección**: Basados en tipo de mensaje
- **Manejo de errores**: Fallback automático
- **Logging avanzado**: Seguimiento de uso de IA vs tradicional

### **Persistencia de Estado Mejorada**
- **Modelo ConversationState**: Almacena estado en BD
- **Datos temporales**: Carrito y contexto en JSON
- **Continuidad**: Mantiene contexto entre mensajes
- **Limpieza automática**: Estados antiguos se limpian

### **Rate Limiting**
- Webhook WhatsApp: 30 requests/minuto
- Protección contra spam
- **Nuevo**: Límites específicos para llamadas a OpenAI

### **Validación de Seguridad**
- Verificación de firma de Twilio
- Validación en producción (DEBUG=False)
- **Nuevo**: Validación de respuestas de IA

### **Manejo de Errores Robusto**
- Excepciones de Twilio capturadas
- **Nuevo**: Manejo de errores de OpenAI
- **Nuevo**: Respuestas de fallback inteligentes
- Logging detallado para debugging
- **Nuevo**: Monitoreo de uso de IA vs tradicional

---

## 🔍 Puntos de Entrada del Sistema (Actualizados)

### **Endpoints Principales**
1. **`/webhook/whatsapp`** - Principal (mensajes de usuarios)
2. **`/pizzas/`** - Consulta de catálogo
3. **`/pedidos/`** - Gestión administrativa
4. **`/docs`** - Documentación automática de FastAPI

### **Nuevos Puntos de Monitoreo**
- **Uso de IA vs Tradicional**: Métricas de cuándo se usa cada flujo
- **Errores de OpenAI**: Seguimiento de fallos de IA
- **Respuestas de Fallback**: Cuándo el sistema cambia a tradicional
- **Extracción de Datos**: Precisión de la IA extrayendo información
- **Contexto de Conversación**: Efectividad de la memoria del bot

---

## 🚀 Inicialización del Sistema (Actualizada)

El sistema se inicializa en `main.py`:
1. **Configuración de FastAPI**: Servidor principal
2. **Conexión a base de datos**: PostgreSQL con SQLAlchemy
3. **Inicialización de servicios**: 
   - `EnhancedBotService` (coordinador principal)
   - `AIService` (integración con OpenAI)
   - `WhatsAppService` (comunicación con Twilio)
   - `PedidoService` (gestión de pedidos)
4. **Registro de routers**: Endpoints de API
5. **Configuración de CORS y middleware**: Seguridad y logging
6. **Validación de API Keys**: OpenAI y Twilio
7. **Inicio del servidor uvicorn**: Servidor ASGI

### **Variables de Entorno Requeridas**
```bash
# Base de datos
DATABASE_URL=postgresql://user:password@localhost/dbname

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# OpenAI (NUEVO)
OPENAI_API_KEY=your_openai_api_key

# Configuración
DEBUG=False
```

---

## 🎯 Beneficios del Sistema Híbrido

### **Para el Usuario**
- **Conversación natural**: Puede hablar como con una persona
- **Comandos rápidos**: Sigue funcionando con comandos simples
- **Flexibilidad**: No necesita recordar sintaxis específica
- **Comprensión contextual**: El bot entiende el contexto

### **Para el Negocio**
- **Mejor experiencia**: Clientes más satisfechos
- **Más conversiones**: Sugerencias inteligentes
- **Eficiencia**: Menos malentendidos
- **Escalabilidad**: Maneja conversaciones complejas

### **Para el Desarrollador**
- **Mantenibilidad**: Código bien estructurado
- **Robustez**: Fallback automático si IA falla
- **Monitoring**: Logging detallado
- **Flexibilidad**: Fácil agregar nuevas funcionalidades

---

## 🔮 Próximas Mejoras Sugeridas

1. **Memoria a largo plazo**: Recordar preferencias del cliente
2. **Análisis de sentimientos**: Detectar clientes insatisfechos
3. **Sugerencias personalizadas**: Basadas en historial
4. **Integración con inventario**: Disponibilidad en tiempo real
5. **Métricas de rendimiento**: Dashboard de uso de IA
6. **Soporte multiidioma**: Detección automática de idioma
7. **Integración con pagos**: Procesamiento de pagos automático

Este flujo híbrido permite un manejo completo del ciclo de vida de un pedido de pizza, combinando la eficiencia de comandos tradicionales con la flexibilidad de conversaciones naturales, todo a través de WhatsApp con inteligencia artificial integrada.
