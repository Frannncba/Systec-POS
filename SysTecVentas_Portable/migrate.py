# migrate.py - Script independiente para ejecutar migraciones
import sqlite3
import os

def migrate_database():
    """Ejecuta todas las migraciones necesarias"""
    db_path = 'ventas.db'
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada. Ejecutar app.py primero.")
        return
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    
    print("🔄 Iniciando migraciones...")
    
    # Migración 1: Agregar columna metodo_pago
    try:
        c.execute("SELECT metodo_pago FROM ventas LIMIT 1")
        print("✓ Columna metodo_pago ya existe")
    except sqlite3.OperationalError:
        print("➕ Agregando columna metodo_pago...")
        c.execute("ALTER TABLE ventas ADD COLUMN metodo_pago TEXT DEFAULT 'efectivo'")
        print("✓ Columna metodo_pago agregada")
    
    # Migración 2: Agregar columna cliente_id
    try:
        c.execute("SELECT cliente_id FROM ventas LIMIT 1")
        print("✓ Columna cliente_id ya existe")
    except sqlite3.OperationalError:
        print("➕ Agregando columna cliente_id...")
        c.execute("ALTER TABLE ventas ADD COLUMN cliente_id INTEGER")
        print("✓ Columna cliente_id agregada")
    
    # Migración 3: Agregar columna modo_oscuro a configuracion
    try:
        c.execute("SELECT modo_oscuro FROM configuracion LIMIT 1")
        print("✓ Columna modo_oscuro ya existe")
    except sqlite3.OperationalError:
        print("➕ Agregando columna modo_oscuro...")
        c.execute("ALTER TABLE configuracion ADD COLUMN modo_oscuro INTEGER DEFAULT 1")
        print("✓ Columna modo_oscuro agregada")
    
    # Actualizar ventas existentes sin metodo_pago
    updated = c.execute("UPDATE ventas SET metodo_pago = 'efectivo' WHERE metodo_pago IS NULL").rowcount
    if updated > 0:
        print(f"✓ Actualizadas {updated} ventas con método de pago por defecto")
    
    conn.commit()
    conn.close()
    
    print("🎉 Migraciones completadas exitosamente!")
    print("\nAhora puedes ejecutar la aplicación normalmente:")
    print("python app.py")

if __name__ == '__main__':
    migrate_database()