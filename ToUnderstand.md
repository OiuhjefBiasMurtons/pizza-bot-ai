# 🍕 Pizza Bot - Guía Completa de Funcionamiento

## 📋 Índice
1. [Arquitectura General](#arquitectura-general)
2. [Flujo Principal del Bot](#flujo-principal-del-bot)
3. [Servicios y Componentes](#servicios-y-componentes)
4. [Decisión IA vs Tradicional](#decisión-ia-vs-tradicional)
5. [Procesamiento con IA](#procesamiento-con-ia)
6. [Flujo Tradicional](#flujo-tradicional)
7. [Gestión de Estados](#gestión-de-estados)
8. [Casos de Uso Específicos](#casos-de-uso-específicos)
9. [Diagramas de Flujo](#diagramas-de-flujo)

---

## 🏗️ Arquitectura General

El bot de pizza tiene una arquitectura híbrida que combina:
- **Flujo Tradicional**: Para comandos simples y bien definidos
- **Inteligencia Artificial**: Para procesamiento de lenguaje natural complejo

### Componentes Principales:
```
📱 WhatsApp → 🌐 Webhook → 🧠 EnhancedBotService → 🤖 AIService / 🔧 BotService → 📊 Database
```

---

## 🔄 Flujo Principal del Bot

### 1. **Recepción del Mensaje** (`app/routers/webhook.py`)

```python
@router.post("/webhook/whatsapp/form")
async def receive_whatsapp_message()
```

**¿Qué hace?**
- Recibe mensaje de WhatsApp vía webhook de Twilio
- Extrae número de teléfono y contenido del mensaje
- Inicializa servicios necesarios
- Decide qué tipo de bot usar

**Funciones clave:**
- `WhatsAppService()` - Para enviar respuestas
- `EnhancedBotService(db)` - Bot inteligente (IA + tradicional)
- `BotService(db)` - Bot tradicional únicamente

### 2. **Procesamiento Principal** (`app/services/enhanced_bot_service.py`)

```python
async def process_message(self, numero_whatsapp: str, mensaje: str) -> str
```

**Pasos del procesamiento:**

#### a) **Limpieza y Obtención de Contexto**
```python
mensaje = mensaje.strip()
cliente = self.get_cliente(numero_whatsapp)
estado_actual = self.get_conversation_state(numero_whatsapp)
contexto = self.get_conversation_context(numero_whatsapp)
```

#### b) **Verificación de Registro**
```python
if not cliente or cliente.nombre is None or cliente.direccion is None:
    return await self.handle_registration_flow(numero_whatsapp, mensaje, cliente)
```

#### c) **Decisión de Procesamiento**
```python
should_use_ai = await self.should_use_ai_processing(mensaje, estado_actual, contexto)

if should_use_ai:
    return await self.process_with_ai(numero_whatsapp, mensaje, cliente, contexto)
else:
    return await self.process_with_traditional_flow(numero_whatsapp, mensaje, cliente)
```

---

## 🧩 Servicios y Componentes

### **WhatsAppService** (`app/services/whatsapp_service.py`)
- **Propósito**: Interfaz con Twilio para enviar mensajes
- **Función principal**: `send_message(to_number, message)`

### **EnhancedBotService** (`app/services/enhanced_bot_service.py`)
- **Propósito**: Orquestador principal que decide entre IA y flujo tradicional
- **Funciones clave**:
  - `process_message()` - Punto de entrada principal
  - `should_use_ai_processing()` - Decide qué tipo de procesamiento usar
  - `process_with_ai()` - Delega a AIService
  - `process_with_traditional_flow()` - Maneja flujo tradicional

### **AIService** (`app/services/ai_service.py`)
- **Propósito**: Procesamiento inteligente con OpenAI GPT
- **Funciones clave**:
  - `process_with_ai()` - Procesa mensaje con IA
  - `_create_system_prompt()` - Crea contexto para GPT
  - `_build_conversation_context()` - Construye contexto de conversación

### **BotService** (`app/services/bot_service.py`)
- **Propósito**: Lógica tradicional de flujo de pedidos
- **Funciones clave**:
  - Manejo de registro de usuarios
  - Flujo de selección de pizzas
  - Confirmación de pedidos

---

## 🤔 Decisión IA vs Tradicional

### **Función: `should_use_ai_processing()`**

```python
async def should_use_ai_processing(self, mensaje: str, estado_actual: str, contexto: Dict) -> bool
```

**Lógica de decisión:**

#### ✅ **Usa Flujo TRADICIONAL cuando:**
1. **Comandos simples**: 
   ```python
   if mensaje_lower in self.COMANDOS_TRADICIONALES:
       return False  # ['hola', 'hello', 'buenas', 'menu', 'ayuda', etc.]
   ```

2. **Números en menú**:
   ```python
   if mensaje_lower.isdigit() and estado_actual == self.ESTADOS['MENU']:
       return False  # Usuario selecciona "1", "2", "3", etc.
   ```

3. **Confirmaciones simples**:
   ```python
   if mensaje_lower in ['si', 'sí', 'no', 'confirmar', 'cancelar']:
       return False
   ```

#### 🤖 **Usa IA cuando:**
- Lenguaje natural complejo
- Modificaciones de pedido ("Solo quiero...", "Cambia mi pedido...")
- Preguntas sobre ingredientes
- Solicitudes ambiguas

---

## 🤖 Procesamiento con IA

### **Función: `process_with_ai()`** (AIService)

#### **Paso 1: Construcción de Contexto**
```python
context = self._build_conversation_context(numero_whatsapp, cliente, contexto_conversacion)
```

**Incluye:**
- Información del cliente
- Historial de pedidos
- Estado del carrito actual
- Menú de pizzas disponibles
- Estadísticas de la base de datos

#### **Paso 2: Creación del System Prompt**
```python
self.system_prompt = self._create_system_prompt()
```

**Contiene:**
- Información del negocio
- Menú actualizado con precios
- Personalidad del bot
- Instrucciones de formato JSON
- Palabras clave para modificaciones

#### **Paso 3: Llamada a OpenAI**
```python
response = self.openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": self.system_prompt},
        {"role": "user", "content": f"Contexto: {context}\n\nMensaje del usuario: {mensaje}"}
    ],
    temperature=0.7,
    max_tokens=500
)
```

#### **Paso 4: Procesamiento de Respuesta**
```python
# Limpiar markdown code blocks
if content.startswith("```json"):
    content = content.replace("```json", "").replace("```", "").strip()

# Parsear JSON
ai_response = json.loads(content)
```

#### **Paso 5: Ejecución de Acciones** (EnhancedBotService)
```python
return await self.execute_ai_action(numero_whatsapp, ai_response, cliente)
```

**Acciones disponibles:**
- `agregar_pizza` - Añadir pizza al carrito
- `confirmar_pedido` - Confirmar y finalizar pedido
- `reemplazar_pedido` - Reemplazar carrito completo
- `limpiar_carrito` - Vaciar carrito
- `modificar_carrito` - Modificar items específicos

---

## 🔧 Flujo Tradicional

### **Función: `process_with_traditional_flow()`**

#### **Comandos Especiales que Reinician el Flujo:**
```python
if mensaje_lower in ['hola', 'hello', 'buenas', 'inicio', 'empezar']:
    return self.handle_registered_greeting(numero_whatsapp, cliente)
```

#### **Otros Comandos:**
- `menu/menú/carta` → `handle_menu()`
- `ayuda/help` → `handle_ayuda()`
- `pedido/mis pedidos` → `handle_estado_pedido()`

#### **Flujo por Estados:**
```python
# Basado en estado actual
if estado_actual == self.ESTADOS['MENU']:
    return await self.handle_seleccion_pizza()
elif estado_actual == self.ESTADOS['CONFIRMACION']:
    return await self.handle_confirmacion()
# etc.
```

---

## 📊 Gestión de Estados

### **Estados Disponibles:**
```python
self.ESTADOS = {
    'INICIO': 'inicio',
    'REGISTRO_NOMBRE': 'registro_nombre',
    'REGISTRO_DIRECCION': 'registro_direccion',
    'MENU': 'menu',
    'SELECCION_PIZZA': 'seleccion_pizza',
    'CONFIRMACION': 'confirmacion',
    'PEDIDO': 'pedido',
    'FINALIZADO': 'finalizado'
}
```

### **Funciones de Estado:**
- `get_conversation_state(numero_whatsapp)` - Obtener estado actual
- `set_conversation_state(numero_whatsapp, estado)` - Cambiar estado
- `get_conversation_context(numero_whatsapp)` - Obtener contexto (carrito, etc.)
- `clear_conversation_data(numero_whatsapp)` - Limpiar datos de conversación

---

## 🎯 Casos de Uso Específicos

### **Caso 1: Usuario Nuevo (Registro)**
```
👤 Usuario: "Hola"
🤖 Bot: "¡Hola! Para empezar, ¿cuál es tu nombre?"
👤 Usuario: "Juan"
🤖 Bot: "Mucho gusto Juan. ¿Cuál es tu dirección de entrega?"
👤 Usuario: "Calle 123 #45-67"
🤖 Bot: "Perfecto Juan! Tu dirección ha sido registrada. ¿Qué pizza te gustaría ordenar hoy?"
```

**Flujo:**
1. `handle_registration_flow()` detecta usuario sin nombre
2. Estado: `registro_nombre` → `registro_direccion` → `inicio`

### **Caso 2: Pedido Simple (Tradicional)**
```
👤 Usuario: "Hola" [Cliente registrado]
🤖 Bot: "¡Hola Juan! ¿Qué te gustaría ordenar hoy?"
👤 Usuario: "menu"
🤖 Bot: [Muestra menú]
👤 Usuario: "1"
🤖 Bot: "Pizza Margherita seleccionada. ¿Qué tamaño? (1)Pequeña $12.99 (2)Mediana $16.99 (3)Grande $20.99"
```

**Flujo:**
1. `should_use_ai_processing()` → `False` (comandos simples)
2. `process_with_traditional_flow()` → `handle_registered_greeting()`
3. Estado resetea a `inicio`

### **Caso 3: Modificación Compleja (IA)**
```
👤 Usuario: "Solo quiero la pepperoni grande" [Con carrito existente]
🤖 Bot: "Entendido, reemplazaré tu pedido actual por una pizza Pepperoni grande por $22.99. ¿Está bien así?"
```

**Flujo:**
1. `should_use_ai_processing()` → `True` (lenguaje natural complejo)
2. `process_with_ai()` → GPT detecta intención de reemplazo
3. `execute_ai_action()` → `handle_reemplazar_pedido()`

### **Caso 4: Pregunta sobre Ingredientes (IA)**
```
👤 Usuario: "¿La pizza hawaiana lleva piña?"
🤖 Bot: "Sí, la pizza Hawaiana lleva jamón y piña sobre salsa de tomate y mozzarella. ¿Te gustaría ordenar una?"
```

**Flujo:**
1. `should_use_ai_processing()` → `True` (pregunta compleja)
2. GPT usa contexto del menú para responder
3. No requiere acción específica, solo respuesta informativa

---

## 📈 Diagramas de Flujo

### **Flujo Principal Simplificado:**

```
📱 Mensaje WhatsApp
    ↓
🌐 Webhook recibe mensaje
    ↓
🔍 ¿Cliente registrado?
    ↓ No          ↓ Sí
📝 Registro   🤔 ¿Usar IA?
    ↓            ↓ No     ↓ Sí
📋 Flujo    🔧 Tradicional  🤖 IA + GPT
   Completo      ↓           ↓
    ↓        📊 Ejecutar  🎯 Ejecutar
📤 Respuesta   Acción      Acción
                ↓           ↓
            📤 Respuesta  📤 Respuesta
```

### **Decisión IA vs Tradicional:**

```
📝 Mensaje recibido
    ↓
🔍 Analizar mensaje
    ↓
❓ ¿Es comando simple?
    ↓ Sí              ↓ No
✅ Flujo          ❓ ¿Es número en menú?
   Tradicional        ↓ Sí         ↓ No
                  ✅ Flujo      ❓ ¿Es confirmación simple?
                     Tradicional   ↓ Sí            ↓ No
                                ✅ Flujo          🤖 Usar IA
                                   Tradicional
```

---

## 🔧 Funciones Principales por Archivo

### **webhook.py**
- `receive_whatsapp_message()` - Punto de entrada desde WhatsApp

### **enhanced_bot_service.py**
- `process_message()` - Orquestador principal
- `should_use_ai_processing()` - Lógica de decisión
- `process_with_ai()` - Delegación a IA
- `process_with_traditional_flow()` - Flujo tradicional
- `execute_ai_action()` - Ejecutor de acciones de IA
- `handle_reemplazar_pedido()` - Reemplazar carrito
- `handle_limpiar_carrito()` - Limpiar carrito
- `handle_modificar_carrito()` - Modificar items

### **ai_service.py**
- `process_with_ai()` - Procesamiento con GPT
- `_create_system_prompt()` - Construcción del prompt
- `_build_conversation_context()` - Contexto de conversación
- `get_dynamic_context()` - Contexto dinámico de BD

### **bot_service.py**
- `handle_registration_flow()` - Registro de usuarios
- `handle_menu()` - Mostrar menú
- `handle_pizza_selection()` - Selección de pizzas
- `handle_order_confirmation()` - Confirmación de pedidos

---

## 🎯 Puntos Clave para Entender

1. **Hibridez Inteligente**: El bot no usa IA para todo, solo cuando es necesario
2. **Contexto Dinámico**: La IA tiene acceso a datos en tiempo real de la BD
3. **Gestión de Estado**: Cada conversación mantiene su estado independiente
4. **Fallbacks**: Si la IA falla, hay respuestas de respaldo predefinidas
5. **Optimización**: Comandos simples no consumen tokens de OpenAI
6. **Flexibilidad**: Puede manejar tanto flujos estructurados como lenguaje natural

---

## 📝 Notas Técnicas

- **Modelo IA**: GPT-4o para procesamiento principal
- **Base de Datos**: PostgreSQL con SQLAlchemy ORM
- **Estados**: Almacenados en caché/memoria (Redis en producción)
- **Logs**: Estructurados para debugging y monitoreo
- **Validaciones**: Múltiples capas de validación para robustez

Este sistema permite que el bot sea **eficiente** (usando flujo tradicional para lo simple) y **inteligente** (usando IA para casos complejos), proporcionando la mejor experiencia de usuario posible. 🍕
