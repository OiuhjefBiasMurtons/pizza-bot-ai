from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import webhook, pizzas, pedidos, admin
from app.utils.logging_config import setup_logging, setup_sentry, get_logger, LoggingMiddleware
from config.settings import settings

# Configurar logging estructurado
setup_logging()
setup_sentry()
logger = get_logger(__name__)

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Pizza Bot API",
    description="API para chatbot de pedidos de pizza por WhatsApp",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configurar rate limiting
app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # Comentado temporalmente por problemas de tipo

# Agregar middleware de logging
app.add_middleware(LoggingMiddleware)

# Configurar CORS más específico para producción
if settings.DEBUG:
    # En desarrollo, permitir todos los orígenes
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # En producción, ser más específico
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://yourdomain.com",
            "https://www.yourdomain.com",
            settings.NGROK_URL
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["*"],
    )

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Incluir routers
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
app.include_router(pizzas.router, prefix="/pizzas", tags=["pizzas"])
app.include_router(pedidos.router, prefix="/pedidos", tags=["pedidos"])
app.include_router(admin.router, tags=["admin"])

@app.get("/")
async def root():
    return {
        "message": "¡Pizza Bot API funcionando! 🍕",
        "docs": "/docs",
        "status": "activo"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pizza-bot"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug" if settings.DEBUG else "info") 