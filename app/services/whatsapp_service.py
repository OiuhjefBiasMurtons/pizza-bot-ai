from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from config.settings import settings
from app.utils.logging_config import LoggerMixin
import re
from typing import Optional, Dict

class WhatsAppService(LoggerMixin):
    def __init__(self, twilio_client: Optional[Client] = None):
        """Inicializar servicio de WhatsApp"""
        if twilio_client is None:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        else:
            self.client = twilio_client
        self.from_number = f"whatsapp:{settings.TWILIO_PHONE_NUMBER}"
        self.validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    
    def validate_webhook(self, request_url: str, post_data: Dict, signature: str) -> bool:
        """Validar webhook de Twilio"""
        try:
            # Asegurar que los datos requeridos estén presentes
            if not all([request_url, post_data, signature]):
                self.logger.warning(
                    "Datos incompletos para validación de webhook",
                    request_url=bool(request_url),
                    post_data=bool(post_data),
                    signature=bool(signature)
                )
                return False
                
            # En modo debug, aceptar todas las solicitudes con datos válidos
            if settings.DEBUG:
                return True
                
            # Validar firma
            return self.validator.validate(
                request_url,
                post_data,
                signature
            )
        except Exception as e:
            self.logger.error(
                "Error validando webhook",
                error=str(e),
                request_url=request_url
            )
            return False
    
    def _format_phone_number(self, number: str) -> str:
        """Formatear número de teléfono para WhatsApp"""
        # Remover prefijo whatsapp: si existe
        clean_number = number.replace("whatsapp:", "")
        
        # Asegurar que el número comience con +
        if not clean_number.startswith("+"):
            clean_number = f"+{clean_number}"
        
        # Validar formato básico del número
        if not re.match(r"^\+\d{10,15}$", clean_number):
            raise ValueError(f"Número de teléfono inválido: {number}")
        
        return f"whatsapp:{clean_number}"
    
    async def send_message(self, to_number: str, message: str) -> str:
        """Enviar mensaje por WhatsApp"""
        try:
            formatted_number = self._format_phone_number(to_number)
            
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=formatted_number
            )
            
            if twilio_message is None or twilio_message.sid is None:
                raise TwilioRestException(
                    status=500,
                    uri="",
                    msg="Error: No se recibió un SID válido de Twilio"
                )
            
            self.logger.info(
                "Mensaje enviado exitosamente",
                to_number=formatted_number,
                message_sid=twilio_message.sid,
                message_length=len(message)
            )
            return twilio_message.sid
            
        except ValueError as e:
            self.logger.error(
                "Error de formato en número de teléfono",
                to_number=to_number,
                error=str(e)
            )
            raise
            
        except TwilioRestException as e:
            self.logger.error(
                "Error de Twilio enviando mensaje",
                to_number=to_number,
                error=str(e),
                error_code=e.code,
                message_length=len(message)
            )
            raise
            
        except Exception as e:
            self.logger.error(
                "Error inesperado enviando mensaje",
                to_number=to_number,
                error=str(e),
                message_length=len(message)
            )
            raise
    
    async def send_image(self, to_number: str, image_url: str, caption: str = "") -> str:
        """Enviar imagen por WhatsApp"""
        try:
            formatted_number = self._format_phone_number(to_number)
            
            twilio_message = self.client.messages.create(
                body=caption,
                media_url=[image_url],
                from_=self.from_number,
                to=formatted_number
            )
            
            if twilio_message is None or twilio_message.sid is None:
                raise TwilioRestException(
                    status=500,
                    uri="",
                    msg="Error: No se recibió un SID válido de Twilio"
                )
            
            return twilio_message.sid
            
        except ValueError as e:
            self.logger.error(
                "Error de formato en número de teléfono",
                to_number=to_number,
                error=str(e)
            )
            raise
            
        except TwilioRestException as e:
            self.logger.error(
                "Error de Twilio enviando imagen",
                to_number=to_number,
                error=str(e),
                error_code=e.code
            )
            raise
            
        except Exception as e:
            self.logger.error(
                "Error inesperado enviando imagen",
                to_number=to_number,
                error=str(e)
            )
            raise 