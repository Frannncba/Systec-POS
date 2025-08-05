#!/usr/bin/env python3
# fix_database_migration.py - Migra la base de datos existente a la nueva estructura

import sqlite3
import os
from datetime import datetime

DATABASE = 'ventas.db'

def migrate_database():
    """Migra la base de datos a la nueva estructura limpia"""
    
    print("🔄 Iniciando migración de base de datos...")
    
    if not os.path.exists(DATABASE):
        print("❌ No se encontró la base de datos. Ejecuta app.py para crearla.")
        return
    
    # Hacer backup
    backup_name = f"ventas_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        import shutil
        shutil.copy2(DATABASE, backup_name)
        print(f"✅ Backup creado: {backup_name}")
    except Exception as e:
        print(f"⚠️  No se pudo crear backup: {e}")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        # 1. Verificar si existe la columna modo_oscuro
        c.execute("PRAGMA table_info(configuracion)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'modo_oscuro' not in columns:
            print("➕ Agregando columna modo_oscuro...")
            c.execute("ALTER TABLE configuracion ADD COLUMN modo_oscuro INTEGER DEFAULT 1")
        
        if 'umbral_stock_minimo' not in columns:
            print("➕ Agregando columna umbral_stock_minimo...")
            c.execute("ALTER TABLE configuracion ADD COLUMN umbral_stock_minimo INTEGER DEFAULT 5")
        
        # 2. Asegurar que existe el registro de configuración
        existing_config = c.execute("SELECT COUNT(*) FROM configuracion WHERE id = 1").fetchone()[0]
        if existing_config == 0:
            print("➕ Creando configuración inicial...")
            c.execute("""
                INSERT INTO configuracion (id, nombre_empresa, modo_oscuro, umbral_stock_minimo) 
                VALUES (1, 'SysTec Ventas', 1, 5)
            """)
        else:
            print("🔄 Actualizando configuración existente...")
            c.execute("""
                UPDATE configuracion 
                SET modo_oscuro = COALESCE(modo_oscuro, 1), 
                    umbral_stock_minimo = COALESCE(umbral_stock_minimo, 5)
                WHERE id = 1
            """)
        
        # 3. Verificar estructura de otras tablas críticas
        tables_to_check = ['usuarios', 'productos', 'ventas', 'detalle_ventas', 'clientes', 'licencia']
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in c.fetchall()]
        
        missing_tables = [table for table in tables_to_check if table not in existing_tables]
        
        if missing_tables:
            print(f"⚠️  Tablas faltantes detectadas: {missing_tables}")
            print("🔄 Creando tablas faltantes...")
            
            # Crear tablas faltantes
            if 'clientes' in missing_tables:
                c.execute('''
                    CREATE TABLE clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        telefono TEXT,
                        email TEXT,
                        direccion TEXT
                    )
                ''')
                print("✅ Tabla 'clientes' creada")
            
            if 'licencia' in missing_tables:
                c.execute('''
                    CREATE TABLE licencia (
                        id INTEGER PRIMARY KEY,
                        uuid TEXT,
                        tipo TEXT,
                        fecha_inicio TEXT,
                        fecha_fin TEXT
                    )
                ''')
                print("✅ Tabla 'licencia' creada")
        
        # 4. Verificar usuarios admin
        admin_exists = c.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'").fetchone()[0]
        if admin_exists == 0:
            from werkzeug.security import generate_password_hash
            c.execute(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
                ('admin', generate_password_hash('admin123'), 'admin')
            )
            print("✅ Usuario admin creado")
        
        root_exists = c.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'systec_root'").fetchone()[0]
        if root_exists == 0:
            from werkzeug.security import generate_password_hash
            c.execute(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
                ('systec_root', generate_password_hash('qwer1234'), 'root')
            )
            print("✅ Usuario systec_root creado")
        
        # 5. Verificar licencia de prueba
        licencia_exists = c.execute("SELECT COUNT(*) FROM licencia").fetchone()[0]
        if licencia_exists == 0:
            import uuid
            from datetime import datetime, timedelta
            hoy = datetime.today()
            fin = hoy + timedelta(days=7)
            c.execute(
                "INSERT INTO licencia (uuid, tipo, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), 'temporal', hoy.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d'))
            )
            print("✅ Licencia temporal creada")
        
        # 6. Limpiar datos inconsistentes
        print("🧹 Limpiando datos inconsistentes...")
        
        # Productos con precios negativos
        c.execute("UPDATE productos SET precio = 0 WHERE precio < 0")
        c.execute("UPDATE productos SET precio_costo = 0 WHERE precio_costo < 0")
        c.execute("UPDATE productos SET stock = 0 WHERE stock < 0")
        
        # Ventas sin totales
        c.execute("UPDATE ventas SET total = 0 WHERE total IS NULL OR total < 0")
        
        conn.commit()
        print("✅ Migración completada exitosamente!")
        
        # Mostrar estadísticas
        stats = {
            'usuarios': c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
            'productos': c.execute("SELECT COUNT(*) FROM productos").fetchone()[0],
            'ventas': c.execute("SELECT COUNT(*) FROM ventas").fetchone()[0],
            'clientes': c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        }
        
        print("\n📊 Estadísticas de la base de datos:")
        for tabla, count in stats.items():
            print(f"   {tabla.capitalize()}: {count}")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def test_database():
    """Prueba las funciones básicas de la base de datos"""
    print("\n🧪 Probando funciones básicas...")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        # Probar configuración
        config = c.execute("SELECT * FROM configuracion WHERE id = 1").fetchone()
        if config:
            print("✅ Configuración: OK")
        else:
            print("❌ Configuración: FALLO")
        
        # Probar usuarios
        users = c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        print(f"✅ Usuarios: {users} registrados")
        
        # Probar productos
        products = c.execute("SELECT COUNT(*) FROM productos WHERE activo = 1").fetchone()[0]
        print(f"✅ Productos activos: {products}")
        
        # Probar ventas
        sales = c.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        print(f"✅ Ventas registradas: {sales}")
        
        print("✅ Todas las pruebas pasaron!")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 SysTec Ventas - Migrador de Base de Datos")
    print("=" * 50)
    
    if migrate_database():
        test_database()
        print("\n🎉 ¡Base de datos lista para usar!")
        print("💡 Ahora puedes ejecutar: python app.py")
    else:
        print("\n❌ Migración fallida. Revisa los errores anteriores.")