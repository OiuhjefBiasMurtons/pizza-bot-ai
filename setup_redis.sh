#!/bin/bash

# Script de instalación de Redis para optimización de rendimiento
# Ejecutar: bash setup_redis.sh

echo "🚀 Configurando Redis para optimización del Pizza Bot..."

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "📦 Instalando Redis en Linux..."
    
    # Ubuntu/Debian
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y redis-server
        sudo systemctl enable redis-server
        sudo systemctl start redis-server
    
    # CentOS/RHEL/Fedora
    elif command -v yum &> /dev/null; then
        sudo yum install -y epel-release
        sudo yum install -y redis
        sudo systemctl enable redis
        sudo systemctl start redis
    
    # Arch Linux
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm redis
        sudo systemctl enable redis
        sudo systemctl start redis
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Instalando Redis en macOS..."
    
    if command -v brew &> /dev/null; then
        brew install redis
        brew services start redis
    else
        echo "❌ Homebrew no encontrado. Por favor instala Homebrew primero:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "🪟 Para Windows, recomendamos usar Docker:"
    echo "   docker run -d -p 6379:6379 --name pizza-bot-redis redis:alpine"
    echo "   O usar WSL2 con Ubuntu"
    exit 1
fi

# Verificar instalación
sleep 2
if command -v redis-cli &> /dev/null; then
    if redis-cli ping | grep -q "PONG"; then
        echo "✅ Redis instalado y funcionando correctamente"
        
        echo "🔧 Configuración básica aplicada:"
        echo "   - Puerto: 6379"
        echo "   - Configuración: Por defecto"
        echo "   - Servicio: Habilitado"
        
        echo "📝 Para usar Redis en tu bot:"
        echo "   1. Asegúrate que REDIS_ENABLED=True en tu .env"
        echo "   2. Configura REDIS_URL=redis://localhost:6379/0"
        echo "   3. Reinicia tu aplicación"
        
        echo "🧪 Para probar Redis:"
        echo "   redis-cli ping  # Debe responder PONG"
        echo "   redis-cli monitor  # Ver comandos en tiempo real"
        
    else
        echo "❌ Redis instalado pero no está funcionando"
        echo "   Intenta: sudo systemctl start redis-server"
        exit 1
    fi
else
    echo "❌ Error en la instalación de Redis"
    exit 1
fi

echo ""
echo "🎉 ¡Redis configurado exitosamente para optimización de rendimiento!"
echo "   Tu bot ahora puede usar caché distribuido para mejor rendimiento."
