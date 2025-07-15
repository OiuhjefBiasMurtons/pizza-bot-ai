#!/usr/bin/env python3
"""
Script simple para limpiar las tablas de la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.models.cliente import Cliente
from app.models.pedido import Pedido, DetallePedido
from app.models.conversation_state import ConversationState

def clean_database():
    """Limpiar todas las tablas de la base de datos"""
    
    db = SessionLocal()
    
    try:
        print("🧹 Limpiando base de datos...")
        
        # Eliminar en orden (por las relaciones de claves foráneas)
        print("   🗑️  Eliminando detalles de pedidos...")
        deleted_detalles = db.query(DetallePedido).delete()
        
        print("   🗑️  Eliminando pedidos...")
        deleted_pedidos = db.query(Pedido).delete()
        
        print("   🗑️  Eliminando estados de conversación...")
        deleted_conversations = db.query(ConversationState).delete()
        
        print("   🗑️  Eliminando clientes...")
        deleted_clientes = db.query(Cliente).delete()
        
        # Confirmar cambios
        db.commit()
        
        print(f"\n✅ Limpieza completada:")
        print(f"   📦 {deleted_pedidos} pedidos eliminados")
        print(f"   🍕 {deleted_detalles} detalles eliminados")
        print(f"   👥 {deleted_clientes} clientes eliminados")
        print(f"   💬 {deleted_conversations} conversaciones eliminadas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    clean_database()
