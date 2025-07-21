from fastapi import APIRouter, Request, Depends, HTTPException, Form, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database.connection import get_db
from app.services.whatsapp_service import WhatsAppService
from app.services.enhanced_bot_service import EnhancedBotService
from app.services.cache_service import cache_service
from twilio.request_validator import RequestValidator
from twilio.base.exceptions import TwilioRestException
from config.settings import settings
import logging
import time
from typing import Optional, Dict, Any

# Configuración de logging
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

# Router de webhook
router = APIRouter()

async def process_whatsapp_message(from_number: str, message_body: str, db: Session) -> dict:
    """Procesar mensaje de WhatsApp con bot híbrido (IA + tradicional)"""
    if not from_number or not message_body:
        raise HTTPException(
            status_code=400,
            detail="Datos incompletos: se requiere número de teléfono y mensaje"
        )

    # Métricas de rendimiento
    start_time = time.time()
    
    # Inicializar servicios
    whatsapp_service = WhatsAppService()
    
    # Usar siempre EnhancedBotService (decide internamente si usar IA o tradicional)
    bot_service = EnhancedBotService(db)
    
    # Log basado en configuración de OpenAI
    if settings.OPENAI_API_KEY:
        logger.info(f"🤖 Bot híbrido (IA+tradicional) disponible para {from_number}")
    else:
        logger.info(f"🔧 Bot híbrido en modo tradicional para {from_number} (sin OpenAI)")
    
    try:
        # Procesar mensaje con el bot
        response = await bot_service.process_message(from_number, message_body)
        
        # Enviar respuesta por WhatsApp
        await whatsapp_service.send_message(from_number, response)
        
        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Mensaje procesado exitosamente para {from_number} en {processing_time:.2f}s")
        
        # Limpiar caché periódicamente (cada 100 mensajes aprox)
        if hash(from_number) % 100 == 0:
            try:
                # Intentar limpieza de caché si está disponible
                logger.debug("🧹 Ejecutando limpieza periódica de caché...")
                # La limpieza se maneja automáticamente por el servicio de lifecycle
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error en limpieza de caché: {cleanup_error}")
        
        return {
            "status": "success", 
            "message": "Mensaje procesado",
            "processing_time": processing_time
        }
        
    except TwilioRestException as e:
        logger.error(f"❌ Error de Twilio para {from_number}: {e}")
        # Mapear errores comunes de Twilio a códigos HTTP apropiados
        if e.status == 429:  # Too Many Requests
            raise HTTPException(status_code=429, detail=str(e))
        elif e.status == 401:  # Unauthorized
            raise HTTPException(status_code=401, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje de {from_number}: {e}")
        
        # Enviar mensaje de error al usuario
        try:
            await whatsapp_service.send_message(
                from_number, 
                "Lo siento, hubo un error procesando tu mensaje. Por favor, intenta de nuevo."
            )
        except Exception as send_error:
            logger.error(f"Error enviando mensaje de error: {send_error}")
        
        raise HTTPException(status_code=500, detail=str(e))

# Webhook para recibir mensajes de WhatsApp (Form data)
@router.post("/whatsapp/form")
@limiter.limit("30/minute")
async def whatsapp_webhook_form(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db)
):
    """Webhook para recibir mensajes de WhatsApp via form data"""
    
    # Validar webhook de Twilio en producción
    if not settings.DEBUG:
        try:
            url = str(request.url)
            signature = request.headers.get("X-Twilio-Signature", "")
            form_dict = await request.form()
            
            whatsapp_service = WhatsAppService()
            if not whatsapp_service.validate_webhook(url, dict(form_dict), signature):
                logger.warning(f"Webhook validation failed from {request.client.host if request.client else 'unknown host'}")
                raise HTTPException(status_code=403, detail="Webhook validation failed")
        except Exception as e:
            logger.error(f"Error validating webhook: {e}")
            raise HTTPException(status_code=403, detail="Invalid webhook")
    
    try:
        from_number = From.replace("whatsapp:", "")
        result = await process_whatsapp_message(from_number, Body, db)
        return JSONResponse(status_code=200, content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error en webhook form: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook para recibir mensajes de WhatsApp (JSON)
@router.post("/whatsapp")
@limiter.limit("30/minute")
async def whatsapp_webhook_json(
    request: Request,
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Webhook para recibir mensajes de WhatsApp via JSON"""
    try:
        from_number = str(data.get("From", "")).replace("whatsapp:", "")
        message_body = str(data.get("Body", ""))
        
        if not from_number or not message_body:
            raise HTTPException(status_code=400, detail="Datos incompletos")
            
        result = await process_whatsapp_message(from_number, message_body, db)
        return JSONResponse(status_code=200, content=result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error en webhook json: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para enviar mensajes
@router.post("/send-message")
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    data: Dict = Body(...),
    db: Session = Depends(get_db)
):
    """Endpoint para enviar mensajes por WhatsApp"""
    try:
        to_number = data.get("to_number")
        message = data.get("message")
        
        if not to_number or not message:
            raise HTTPException(
                status_code=400,
                detail="Se requiere número de teléfono y mensaje"
            )
            
        whatsapp_service = WhatsAppService()
        message_sid = await whatsapp_service.send_message(to_number, message)
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message_sid": message_sid}
        )
        
    except TwilioRestException as e:
        logger.error(f"Error enviando mensaje: {e}")
        if e.status == 429:  # Too Many Requests
            raise HTTPException(status_code=429, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
            
    except Exception as e:
        logger.error(f"Error en send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para probar el webhook
@router.get("/test")
async def test_webhook():
    """Endpoint para probar el webhook"""
    return {"status": "success", "message": "Webhook funcionando correctamente"}

# Endpoint para monitoreo de rendimiento y caché
@router.get("/performance")
async def performance_stats(db: Session = Depends(get_db)):
    """Endpoint para obtener estadísticas de rendimiento"""
    try:
        # Estadísticas básicas del caché
        cache_stats: Dict[str, Any] = {
            'redis_enabled': cache_service.enabled,
            'redis_connected': cache_service.redis is not None if cache_service else False
        }
        
        # Estadísticas de Redis si está disponible
        if cache_service.redis:
            try:
                info = await cache_service.redis.info()
                cache_stats.update({
                    'redis_memory_used': info.get('used_memory_human', 'Unknown'),
                    'redis_connected_clients': info.get('connected_clients', 0),
                    'redis_total_commands': info.get('total_commands_processed', 0)
                })
            except Exception as redis_error:
                cache_stats['redis_error'] = str(redis_error)
        
        # Estadísticas de la base de datos (versión más robusta)
        db_stats = {}
        try:
            engine = db.get_bind()
            if hasattr(engine, 'pool'):
                pool = engine.pool  # type: ignore
                db_stats = {
                    'pool_size': getattr(pool, 'size', lambda: 'Unknown')(),
                    'checked_out': getattr(pool, 'checkedout', lambda: 'Unknown')(),
                    'checked_in': getattr(pool, 'checkedin', lambda: 'Unknown')(),
                    'overflow': getattr(pool, 'overflow', lambda: 'Unknown')(),
                    'invalid': getattr(pool, 'invalid', lambda: 'Unknown')()
                }
            else:
                db_stats = {
                    'pool_info': 'Pool information not available',
                    'connection_active': str(db.is_active)
                }
        except Exception as db_error:
            db_stats = {
                'error': f'Database stats unavailable: {str(db_error)}',
                'connection_active': 'Unknown'
            }
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "cache_stats": cache_stats,
                "database_stats": db_stats,
                "timestamp": time.time()
            }
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de rendimiento: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 