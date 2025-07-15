#!/usr/bin/env python3
"""
Script para limpiar datos de prueba de la base de datos
Elimina todos los registros creados durante los tests
"""

import sys
import os

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from app.models.cliente import Cliente
from app.models.pedido import Pedido, DetallePedido
from app.models.conversation_state import ConversationState
from sqlalchemy import text
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_test_data():
    """Limpiar todos los datos de prueba de la base de datos"""
    
    db = SessionLocal()
    
    try:
        print("🧹 Iniciando limpieza de datos de prueba...")
        print("=" * 60)
        
        # 1. Limpiar datos de conversaciones de prueba
        print("\n1️⃣ Limpiando estados de conversación de prueba...")
        
        # Eliminar conversaciones de números de prueba
        test_conversations = db.query(ConversationState).filter(
            ConversationState.numero_whatsapp.like("+555%")
        ).all()
        
        print(f"   📞 Conversaciones de prueba encontradas: {len(test_conversations)}")
        
        for conv in test_conversations:
            print(f"   🗑️  Eliminando conversación: {conv.numero_whatsapp}")
            db.delete(conv)
        
        # 2. Limpiar pedidos de prueba
        print("\n2️⃣ Limpiando pedidos de prueba...")
        
        # Obtener clientes de prueba
        test_clients = db.query(Cliente).filter(
            Cliente.numero_whatsapp.like("+555%")
        ).all()
        
        total_pedidos = 0
        total_detalles = 0
        
        for cliente in test_clients:
            # Obtener pedidos del cliente
            pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
            
            for pedido in pedidos:
                # Eliminar detalles del pedido
                detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).all()
                for detalle in detalles:
                    db.delete(detalle)
                    total_detalles += 1
                
                # Eliminar pedido
                db.delete(pedido)
                total_pedidos += 1
                
                print(f"   🗑️  Eliminando pedido #{pedido.id} de {cliente.nombre}")
        
        print(f"   📦 Pedidos eliminados: {total_pedidos}")
        print(f"   🍕 Detalles eliminados: {total_detalles}")
        
        # 3. Limpiar clientes de prueba
        print("\n3️⃣ Limpiando clientes de prueba...")
        
        print(f"   👥 Clientes de prueba encontrados: {len(test_clients)}")
        
        for cliente in test_clients:
            print(f"   🗑️  Eliminando cliente: {cliente.nombre} ({cliente.numero_whatsapp})")
            db.delete(cliente)
        
        # 4. Commit todos los cambios
        print("\n4️⃣ Guardando cambios...")
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ ¡Limpieza completada exitosamente!")
        print(f"   📞 {len(test_conversations)} conversaciones eliminadas")
        print(f"   👥 {len(test_clients)} clientes eliminados")
        print(f"   📦 {total_pedidos} pedidos eliminados")
        print(f"   🍕 {total_detalles} detalles eliminados")
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()

def cleanup_specific_test_pattern(pattern: str):
    """Limpiar datos de prueba con un patrón específico"""
    
    db = SessionLocal()
    
    try:
        print(f"🧹 Limpiando datos de prueba con patrón: {pattern}")
        print("=" * 60)
        
        # Limpiar conversaciones con patrón específico
        conversations = db.query(ConversationState).filter(
            ConversationState.numero_whatsapp.like(f"%{pattern}%")
        ).all()
        
        print(f"   📞 Conversaciones encontradas: {len(conversations)}")
        
        for conv in conversations:
            print(f"   🗑️  Eliminando: {conv.numero_whatsapp}")
            db.delete(conv)
        
        # Limpiar clientes con patrón específico
        clients = db.query(Cliente).filter(
            Cliente.numero_whatsapp.like(f"%{pattern}%")
        ).all()
        
        print(f"   👥 Clientes encontrados: {len(clients)}")
        
        total_pedidos = 0
        total_detalles = 0
        
        for cliente in clients:
            # Limpiar pedidos del cliente
            pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).all()
            
            for pedido in pedidos:
                # Eliminar detalles
                detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).all()
                for detalle in detalles:
                    db.delete(detalle)
                    total_detalles += 1
                
                # Eliminar pedido
                db.delete(pedido)
                total_pedidos += 1
            
            # Eliminar cliente
            print(f"   🗑️  Eliminando cliente: {cliente.nombre} ({cliente.numero_whatsapp})")
            db.delete(cliente)
        
        db.commit()
        
        print(f"\n✅ Limpieza completada!")
        print(f"   📞 {len(conversations)} conversaciones eliminadas")
        print(f"   👥 {len(clients)} clientes eliminados")
        print(f"   📦 {total_pedidos} pedidos eliminados")
        print(f"   🍕 {total_detalles} detalles eliminados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()

def reset_auto_increment():
    """Resetear los auto-incrementos de las tablas"""
    
    db = SessionLocal()
    
    try:
        print("🔄 Reseteando auto-incrementos...")
        
        # Obtener el máximo ID actual de cada tabla
        max_cliente_id = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM clientes")).scalar()
        max_pedido_id = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM pedidos")).scalar()
        max_detalle_id = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM detalle_pedidos")).scalar()
        max_conv_id = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM conversation_states")).scalar()
        
        # Resetear secuencias (PostgreSQL)
        db.execute(text(f"ALTER SEQUENCE clientes_id_seq RESTART WITH {max_cliente_id}"))
        db.execute(text(f"ALTER SEQUENCE pedidos_id_seq RESTART WITH {max_pedido_id}"))
        db.execute(text(f"ALTER SEQUENCE detalle_pedidos_id_seq RESTART WITH {max_detalle_id}"))
        db.execute(text(f"ALTER SEQUENCE conversation_states_id_seq RESTART WITH {max_conv_id}"))
        
        db.commit()
        
        print("✅ Auto-incrementos reseteados correctamente")
        
    except Exception as e:
        print(f"❌ Error al resetear auto-incrementos: {e}")
        db.rollback()
    
    finally:
        db.close()

def show_test_data_summary():
    """Mostrar resumen de datos de prueba en la base de datos"""
    
    db = SessionLocal()
    
    try:
        print("📊 Resumen de datos de prueba en la base de datos:")
        print("=" * 60)
        
        # Contar conversaciones de prueba
        test_conversations = db.query(ConversationState).filter(
            ConversationState.numero_whatsapp.like("+555%")
        ).count()
        
        print(f"📞 Conversaciones de prueba: {test_conversations}")
        
        # Contar clientes de prueba
        test_clients = db.query(Cliente).filter(
            Cliente.numero_whatsapp.like("+555%")
        ).count()
        
        print(f"👥 Clientes de prueba: {test_clients}")
        
        # Contar pedidos de prueba
        test_orders = db.query(Pedido).join(Cliente).filter(
            Cliente.numero_whatsapp.like("+555%")
        ).count()
        
        print(f"📦 Pedidos de prueba: {test_orders}")
        
        # Contar detalles de pedidos de prueba
        test_details = db.query(DetallePedido).join(Pedido).join(Cliente).filter(
            Cliente.numero_whatsapp.like("+555%")
        ).count()
        
        print(f"🍕 Detalles de pedidos de prueba: {test_details}")
        
        # Mostrar algunos ejemplos
        if test_clients > 0:
            print("\n📋 Ejemplos de datos de prueba:")
            sample_clients = db.query(Cliente).filter(
                Cliente.numero_whatsapp.like("+555%")
            ).limit(5).all()
            
            for cliente in sample_clients:
                print(f"   👤 {cliente.nombre} ({cliente.numero_whatsapp})")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error al mostrar resumen: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpiar datos de prueba de la base de datos")
    parser.add_argument("--action", choices=["cleanup", "summary", "reset", "pattern"], 
                       default="cleanup", help="Acción a realizar")
    parser.add_argument("--pattern", type=str, help="Patrón específico para limpiar (ej: 'test123')")
    
    args = parser.parse_args()
    
    if args.action == "cleanup":
        cleanup_test_data()
    elif args.action == "summary":
        show_test_data_summary()
    elif args.action == "reset":
        reset_auto_increment()
    elif args.action == "pattern":
        if args.pattern:
            cleanup_specific_test_pattern(args.pattern)
        else:
            print("❌ Debes especificar un patrón con --pattern")
