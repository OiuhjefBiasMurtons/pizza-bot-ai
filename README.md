# 🍕 Pizza Bot - Chatbot Automatizado para Pedidos de Pizza

Un chatbot inteligente para WhatsApp que automatiza la toma de pedidos de pizza utilizando Python, FastAPI, PostgreSQL y Twilio.

## 🚀 Características

- ✅ **Respuestas automatizadas por WhatsApp**
- ✅ **Menú interactivo con precios**
- ✅ **Sistema de pedidos completo**
- ✅ **Cálculo automático de totales**
- ✅ **Gestión de direcciones de entrega**
- ✅ **Base de datos PostgreSQL con migraciones**
- ✅ **API REST con FastAPI**
- ✅ **Integración completa con Twilio**
- ✅ **Testing completo con mocks**
- ✅ **Logging estructurado**
- ✅ **Rate limiting y seguridad**
- ✅ **Validación de webhooks**
- ✅ **Fácil despliegue con Docker**

## 🛠️ Tecnologías Utilizadas

- **Backend**: FastAPI
- **Base de datos**: PostgreSQL con Alembic (migraciones)
- **WhatsApp**: Twilio API
- **Testing**: pytest con mocks completos
- **Logging**: structlog + Sentry (producción)
- **Security**: Rate limiting, webhook validation
- **Hosting desarrollo**: ngrok
- **Hosting producción**: Render, Railway u otros
- **Deploy**: uvicorn
- **Lenguaje**: Python 3.9+

## 📋 Prerrequisitos

- Python 3.9+
- PostgreSQL
- Cuenta en Twilio
- ngrok (para desarrollo)

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd Pizza-bot
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
cp env_example.txt .env
```

Edita el archivo `.env` con tus credenciales:

```env
# Database
DATABASE_URL=postgresql://usuario:password@localhost:5432/pizzabot_db

# Twilio
TWILIO_ACCOUNT_SID=tu_account_sid_aqui
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_PHONE_NUMBER=+1234567890

# App
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True

# Ngrok (para desarrollo)
NGROK_URL=https://tu-ngrok-url.ngrok.io
```

### 5. Configurar base de datos

```bash
# Crear base de datos PostgreSQL
createdb pizzabot_db

# Opción 1: Usar migraciones de Alembic (recomendado)
alembic upgrade head
python database/init_db.py  # Solo para datos de ejemplo

# Opción 2: Inicialización directa
python database/init_db.py
```

### 6. Iniciar servidor

```bash
# Opción 1: Usar script de desarrollo
chmod +x scripts/start_dev.sh
./scripts/start_dev.sh

# Opción 2: Comando directo
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Exponer servidor con ngrok

En otra terminal:

```bash
ngrok http 8000
```

Copia la URL de ngrok y actualiza tu archivo `.env`:

```env
NGROK_URL=https://tu-url-generada.ngrok.io
```

## 🔧 Configuración de Twilio

### 1. Crear cuenta en Twilio

1. Ve a [Twilio Console](https://console.twilio.com/)
2. Crea una cuenta o inicia sesión
3. Obtén tu Account SID y Auth Token

### 2. Configurar WhatsApp Sandbox

1. Ve a **Develop > Messaging > Try it out > Send a WhatsApp message**
2. Sigue las instrucciones para configurar el sandbox
3. Configura el webhook URL: `https://tu-ngrok-url.ngrok.io/webhook/whatsapp`

### 3. Configurar webhook

En la consola de Twilio:
- **Webhook URL**: `https://tu-ngrok-url.ngrok.io/webhook/whatsapp`
- **HTTP Method**: POST

## 🍕 Cómo funciona el Bot

### Comandos disponibles:

- `hola` - Inicia la conversación
- `menu` - Muestra el menú de pizzas
- `pedido` - Revisa tus pedidos
- `ayuda` - Muestra ayuda

### Flujo de pedido:

1. **Saludo**: El bot saluda y ofrece opciones
2. **Menú**: Muestra pizzas disponibles con precios
3. **Selección**: Usuario selecciona pizza y tamaño (ej: "1 mediana")
4. **Carrito**: Muestra resumen y permite agregar más pizzas
5. **Dirección**: Solicita dirección de entrega
6. **Confirmación**: Muestra resumen final para confirmar
7. **Pedido**: Guarda pedido en base de datos y envía confirmación

### Ejemplo de conversación:

```
Usuario: hola
Bot: ¡Hola! 👋 Bienvenido a Pizza Bot 🍕
     ¿Te gustaría ver nuestro menú?

Usuario: menu
Bot: 🍕 MENÚ DE PIZZAS 🍕

     1. 🍅 Margherita
        Salsa de tomate, mozzarella, albahaca fresca
        • Pequeña: $12.99
        • Mediana: $16.99
        • Grande: $20.99

     2. 🍕 Pepperoni
        Salsa de tomate, mozzarella, pepperoni
        • Pequeña: $14.99
        • Mediana: $18.99
        • Grande: $22.99

Usuario: 1 mediana
Bot: ✅ Agregado al carrito:
     🍅 Margherita - Mediana
     Precio: $16.99
     
     Total: $16.99
     
     ¿Quieres agregar algo más?

Usuario: confirmar
Bot: Perfecto! 🎉
     Por favor, envía tu dirección de entrega:

Usuario: Calle 123, Ciudad, CP 12345
Bot: 📋 RESUMEN DEL PEDIDO
     
     Total a pagar: $16.99
     
     ¿Confirmas tu pedido?

Usuario: sí
Bot: 🎉 ¡Pedido confirmado!
     Número de pedido: #1
     Tiempo estimado: 30-45 minutos
```

## 📖 API Endpoints

### Pizzas
- `GET /pizzas/` - Obtener todas las pizzas
- `GET /pizzas/{id}` - Obtener pizza específica
- `GET /pizzas/menu/text` - Obtener menú en formato texto

### Pedidos
- `GET /pedidos/` - Obtener todos los pedidos
- `GET /pedidos/{id}` - Obtener pedido específico
- `PUT /pedidos/{id}/estado` - Actualizar estado del pedido
- `GET /pedidos/cliente/{whatsapp}` - Pedidos de un cliente

### Webhook
- `POST /webhook/whatsapp` - Webhook para mensajes de WhatsApp
- `GET /webhook/test` - Probar webhook
- `POST /webhook/send-message` - Enviar mensaje de prueba

### Documentación
- `GET /docs` - Documentación interactiva de la API

## 🐳 Despliegue con Docker

### Desarrollo

```bash
# Construir imagen
docker build -t pizza-bot .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env pizza-bot
```

### Producción

```bash
# Con docker-compose (crear docker-compose.yml)
docker-compose up -d
```

## 🌐 Despliegue en Producción

### Opciones recomendadas:

1. **Render.com**
   - Conecta tu repositorio de GitHub
   - Configura variables de entorno
   - Deploy automático

2. **Railway.app**
   - Deploy directo desde GitHub
   - PostgreSQL incluido
   - Fácil configuración

3. **Heroku**
   - Requiere Procfile
   - Add-on para PostgreSQL
   - Dyno para el servidor

### Variables de entorno para producción:

```env
DATABASE_URL=postgresql://usuario:password@host:5432/pizzabot_db
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_PHONE_NUMBER=whatsapp:+1234567890
SECRET_KEY=clave_secreta_segura
DEBUG=False
SENTRY_DSN=https://tu-sentry-dsn@sentry.io/proyecto
```

## 🧪 Testing

El proyecto incluye una suite completa de tests con mocks para Twilio:

```bash
# Ejecutar todas las pruebas
pytest

# Con coverage detallado
pytest --cov=app --cov-report=html tests/

# Ejecutar solo tests unitarios
pytest -m unit

# Ejecutar solo tests de integración
pytest -m integration

# Ejecutar solo tests de Twilio
pytest -m twilio

# Ejecutar tests específicos
pytest tests/test_bot_service.py

# Con verbose output
pytest -v
```

### Estrategia de Testing

- **Tests unitarios**: Componentes aislados
- **Tests de integración**: Flujos completos
- **Mocks de Twilio**: Tests sin dependencias externas
- **Base de datos en memoria**: Tests aislados
- **Fixtures reutilizables**: Datos de prueba consistentes

Ver [docs/testing_guide.md](docs/testing_guide.md) para más detalles.

## 🗄️ Migraciones de Base de Datos

El proyecto utiliza Alembic para el manejo de migraciones:

```bash
# Generar nueva migración automáticamente
alembic revision --autogenerate -m "Agregar tabla nueva"

# Aplicar migraciones
alembic upgrade head

# Ver historial de migraciones
alembic history

# Volver a versión anterior
alembic downgrade -1

# Ver migración específica
alembic show <revision_id>
```

### Modelo de Datos

El sistema utiliza 4 tablas principales:

- **`clientes`**: Información de usuarios de WhatsApp
- **`pizzas`**: Catálogo de pizzas disponibles
- **`pedidos`**: Pedidos realizados
- **`detalle_pedidos`**: Detalles de cada pedido

Ver [docs/database_model.md](docs/database_model.md) para documentación completa.

## 🔒 Seguridad

### Características de Seguridad

- **Rate Limiting**: Límites por IP en endpoints críticos
- **Validación de Webhooks**: Verificación de firmas Twilio
- **CORS Configurado**: Restricciones según ambiente
- **Logging Estructurado**: Rastreo de actividad
- **Variables de Entorno**: Configuración segura

### Rate Limits

- Webhook WhatsApp: 30 requests/minuto
- Envío de mensajes: 10 requests/minuto
- API general: Configurado según endpoint

## 📊 Logging y Monitoreo

### Logging Estructurado

```python
# Ejemplo de log
{
  "timestamp": "2023-12-01T10:30:00Z",
  "level": "INFO",
  "message": "Mensaje enviado exitosamente",
  "to_number": "+1234567890",
  "message_sid": "SM123456789",
  "duration": 0.5
}
```

### Monitoreo en Producción

- **Sentry**: Monitoreo de errores
- **Logs estructurados**: JSON para análisis
- **Métricas**: Requests, errores, latencia

## 📁 Estructura del Proyecto

```
Pizza-bot/
├── app/
│   ├── models/          # Modelos de base de datos
│   ├── routers/         # Endpoints de la API
│   ├── services/        # Lógica de negocio
│   ├── static/          # Archivos estáticos
│   └── __init__.py
├── config/
│   └── settings.py      # Configuración
├── database/
│   ├── connection.py    # Conexión a BD
│   └── init_db.py       # Inicialización
├── scripts/
│   └── start_dev.sh     # Script de desarrollo
├── tests/               # Pruebas
├── .env                 # Variables de entorno
├── .gitignore
├── Dockerfile
├── main.py              # Punto de entrada
├── requirements.txt     # Dependencias
└── README.md
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Solución de Problemas

### Errores comunes:

1. **Error de conexión a base de datos**
   - Verificar que PostgreSQL esté corriendo
   - Revisar credenciales en `.env`
   - Ejecutar `alembic upgrade head` para migraciones

2. **Webhook no recibe mensajes**
   - Verificar URL de ngrok
   - Confirmar configuración en Twilio
   - Revisar logs estructurados para detalles

3. **Error de autenticación Twilio**
   - Verificar Account SID y Auth Token
   - Revisar número de teléfono en formato correcto
   - Verificar validación de webhook en producción

4. **Tests fallan**
   - Verificar que pytest esté instalado
   - Revisar imports en conftest.py
   - Ejecutar `pytest -v` para más detalles

5. **Rate limiting muy restrictivo**
   - Ajustar límites en `main.py`
   - Revisar logs para identificar patrones

### Logs útiles:

```bash
# Ver logs del servidor con debug
uvicorn main:app --reload --log-level debug

# Ver logs estructurados en desarrollo
# Los logs aparecerán en formato legible en consola

# Ver logs de base de datos
tail -f /var/log/postgresql/postgresql-*.log

# Ver logs de Alembic
alembic -c alembic.ini upgrade head --sql

# Debugging de tests
pytest --log-cli-level=DEBUG

# Ver logs de rate limiting
# Buscar "rate limit exceeded" en los logs
```

## 👨‍💻 Autor

Tu nombre - [tu-email@ejemplo.com](mailto:tu-email@ejemplo.com)

Enlace del proyecto: [https://github.com/tu-usuario/Pizza-bot](https://github.com/tu-usuario/Pizza-bot)

---

¡Gracias por usar Pizza Bot! 🍕 Si tienes alguna pregunta o sugerencia, no dudes en abrir un issue.

## 🔒 Configuración de Seguridad

⚠️ **IMPORTANTE**: Este proyecto utiliza variables de entorno para manejar credenciales sensibles.

### Archivo .env requerido
Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/pizza_bot

# Twilio
TWILIO_ACCOUNT_SID=tu_account_sid_real
TWILIO_AUTH_TOKEN=tu_auth_token_real
TWILIO_PHONE_NUMBER=tu_numero_de_twilio

# Webhooks
WEBHOOK_URL=tu_url_ngrok_o_produccion
SECRET_KEY=tu_clave_secreta_para_sessions

# Opcional: Logging
SENTRY_DSN=tu_sentry_dsn_opcional
```

**Nota**: El archivo `.env` está incluido en `.gitignore` y NO se sube al repositorio por seguridad.