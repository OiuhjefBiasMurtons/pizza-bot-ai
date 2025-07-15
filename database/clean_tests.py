#!/usr/bin/env python3
"""
Script rápido para limpiar datos de prueba
Uso: python clean_tests.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.models.cliente import Cliente
from app.models.pedido import Pedido, DetallePedido
from app.models.conversation_state import ConversationState

def quick_cleanup():
    """Limpieza rápida de datos de prueba"""
    
    db = SessionLocal()
    
    try:
        print("🧹 Limpieza rápida de datos de prueba...")
        
        # Eliminar datos de prueba (números que empiezan con +555)
        test_conversations = db.query(ConversationState).filter(
            ConversationState.numero_whatsapp.like("+555%")
        ).delete()
        
        test_clients = db.query(Cliente).filter(
            Cliente.numero_whatsapp.like("+555%")
        ).all()
        
        # Eliminar pedidos y detalles asociados
        pedidos_count = 0
        detalles_count = 0
        
        for cliente in test_clients:
            pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
            for pedido in pedidos:
                detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).delete()
                detalles_count += detalles
                db.delete(pedido)
                pedidos_count += 1
            db.delete(cliente)
        
        db.commit()
        
        print(f"✅ Limpieza completada:")
        print(f"   📞 {test_conversations} conversaciones eliminadas")
        print(f"   👥 {len(test_clients)} clientes eliminados")
        print(f"   📦 {pedidos_count} pedidos eliminados")
        print(f"   🍕 {detalles_count} detalles eliminados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    quick_cleanup()
