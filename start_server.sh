#!/bin/bash

# Script para iniciar el servidor PizzaBot con Frontend

echo "🍕 Iniciando PizzaBot con Frontend Admin..."
echo "📁 Directorio actual: $(pwd)"

# Configurar Python Path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Verificar que los archivos existen
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py no encontrado"
    exit 1
fi

if [ ! -d "app" ]; then
    echo "❌ Error: directorio app no encontrado"
    exit 1
fi

echo "✅ Archivos verificados"
echo "🚀 Iniciando servidor en http://localhost:8000"
echo "📊 Frontend Admin disponible en: http://localhost:8000/admin/"
echo ""

# Ejecutar el servidor
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
