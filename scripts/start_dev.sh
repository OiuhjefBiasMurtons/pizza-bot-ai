#!/bin/bash

# Script para iniciar el servidor en desarrollo

echo "🍕 Iniciando Pizza Bot en modo desarrollo..."

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado. Copiando desde .env.example"
    cp .env.example .env
    echo "✅ Archivo .env creado. Por favor, configura tus variables de entorno."
    exit 1
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Inicializar base de datos
echo "🗄️  Inicializando base de datos..."
python database/init_db.py

# Iniciar servidor
echo "🚀 Iniciando servidor en http://localhost:8000"
echo "📱 Webhook URL: http://localhost:8000/webhook/whatsapp"
echo "📖 Documentación API: http://localhost:8000/docs"
echo ""
echo "Para exponer el servidor con ngrok, ejecuta en otra terminal:"
echo "ngrok http 8000"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000 