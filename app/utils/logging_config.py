import logging
import structlog
import sys
from typing import Any, Dict
from config.settings import settings

def setup_logging() -> None:
    """Configurar logging estructurado"""
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging estándar
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    )
    
    # Configurar logger para uvicorn
    logging.getLogger("uvicorn.access").disabled = True

def get_logger(name: str) -> Any:
    """Obtener logger estructurado"""
    return structlog.get_logger(name)

class LoggerMixin:
    """Mixin para agregar logging a las clases"""
    
    @property
    def logger(self) -> Any:
        """Obtener logger para la clase"""
        return get_logger(self.__class__.__name__)

# Middleware para logging de requests
class LoggingMiddleware:
    """Middleware para logging de requests HTTP"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("http")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = scope
        start_time = time.time()
        
        # Log request
        self.logger.info(
            "Request started",
            method=request.get("method"),
            path=request.get("path"),
            query_string=request.get("query_string", b"").decode(),
            client_ip=request.get("client", ["unknown"])[0] if request.get("client") else "unknown"
        )
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                self.logger.info(
                    "Request completed",
                    method=request.get("method"),
                    path=request.get("path"),
                    status_code=message["status"],
                    duration=duration,
                    client_ip=request.get("client", ["unknown"])[0] if request.get("client") else "unknown"
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# Configurar Sentry para monitoreo en producción
def setup_sentry() -> None:
    """Configurar Sentry para monitoreo de errores"""
    if not settings.DEBUG and hasattr(settings, 'SENTRY_DSN'):
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(auto_enabling=True),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            environment="production" if not settings.DEBUG else "development",
        )

import time 