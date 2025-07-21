import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://usuario:password@localhost:5432/pizzabot_db")
    
    # Redis (para caché de conversaciones)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "True").lower() == "true"
    
    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # App
    SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_aqui")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Ngrok (para desarrollo)
    NGROK_URL = os.getenv("NGROK_URL", "https://tu-ngrok-url.ngrok.io")
    
    # Pizza Menu
    MENU_IMAGE_PATH = "app/static/images/menu.jpg"
    
    # Sentry (opcional para monitoreo en producción)
    SENTRY_DSN = os.getenv("SENTRY_DSN")

settings = Settings()