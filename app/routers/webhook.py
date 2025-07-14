from fastapi import APIRouter, Request, Depends, HTTPException, Form, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database.connection import get_db
from app.services.whatsapp_service import WhatsAppService
from app.services.bot_service import BotService
from twilio.request_validator import RequestValidator
from twilio.base.exceptions import TwilioRestException
from config.settings import settings
import logging
from typing import Optional, Dict

# Configuración de logging
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

# Router de webhook
router = APIRouter()

async def process_whatsapp_message(from_number: str, message_body: str, db: Session) -> dict:
    """Procesar mensaje de WhatsApp"""
    if not from_number or not message_body:
        raise HTTPException(
            status_code=400,
            detail="Datos incompletos: se requiere número de teléfono y mensaje"
        )

    # Inicializar servicios
    whatsapp_service = WhatsAppService()
    bot_service = BotService(db)
    
    try:
        # Procesar mensaje con el bot
        response = await bot_service.process_message(from_number, message_body)
        
        # Enviar respuesta por WhatsApp
        await whatsapp_service.send_message(from_number, response)
        
        logger.info(f"✅ Mensaje procesado exitosamente para {from_number}")
        return {"status": "success", "message": "Mensaje procesado"}
        
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