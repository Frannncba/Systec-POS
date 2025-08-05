import sqlite3
import os

def diagnosticar_base_datos():
    """Diagnostica la estructura actual de la base de datos"""
    
    db_path = 'ventas.db'
    
    if not os.path.exists(db_path):
        print("❌ La base de datos ventas.db no existe")
        return False
    
    print(f"✅ Base de datos encontrada: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        print(f"\n📋 Tablas existentes: {[tabla[0] for tabla in tablas]}")
        
        # Verificar estructura de la tabla productos
        if ('productos',) in tablas:
            cursor.execute("PRAGMA table_info(productos);")
            columnas = cursor.fetchall()
            print(f"\n🔍 Estructura de la tabla 'productos':")
            for columna in columnas:
                print(f"  - {columna[1]} ({columna[2]})")
            
            # Verificar si existe la columna categoria
            columnas_nombres = [col[1] for col in columnas]
            if 'categoria' not in columnas_nombres:
                print(f"\n❌ PROBLEMA: La columna 'categoria' NO existe en la tabla productos")
                print(f"   Columnas actuales: {columnas_nombres}")
                return False
            else:
                print(f"\n✅ La columna 'categoria' existe correctamente")
        else:
            print(f"\n❌ PROBLEMA: La tabla 'productos' no existe")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al acceder a la base de datos: {e}")
        return False

def corregir_base_datos():
    """Corrige la base de datos agregando las columnas faltantes"""
    
    db_path = 'ventas.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Iniciando corrección de la base de datos...")
        
        # Verificar estructura actual
        cursor.execute("PRAGMA table_info(productos);")
        columnas_actuales = [col[1] for col in cursor.fetchall()]
        print(f"Columnas actuales: {columnas_actuales}")
        
        # Agregar columna categoria si no existe
        if 'categoria' not in columnas_actuales:
            print("➕ Agregando columna 'categoria'...")
            cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT")
            print("✅ Columna 'categoria' agregada")
        
        # Agregar otras columnas que puedan faltar
        columnas_necesarias = {
            'marca': 'TEXT',
            'modelo': 'TEXT', 
            'descripcion_corta': 'TEXT',
            'especificaciones': 'TEXT',
            'garantia': 'TEXT',
            'activo': 'INTEGER DEFAULT 1'
        }
        
        for columna, tipo in columnas_necesarias.items():
            if columna not in columnas_actuales:
                print(f"➕ Agregando columna '{columna}'...")
                cursor.execute(f"ALTER TABLE productos ADD COLUMN {columna} {tipo}")
                print(f"✅ Columna '{columna}' agregada")
        
        # Actualizar productos existentes con valores por defecto
        print("🔄 Actualizando productos existentes...")
        cursor.execute("""
            UPDATE productos 
            SET categoria = 'General',
                marca = 'Sin especificar',
                modelo = 'N/A',
                descripcion_corta = nombre,
                especificaciones = 'Sin especificar',
                garantia = '12 meses',
                activo = 1
            WHERE categoria IS NULL OR categoria = ''
        """)
        
        # Verificar que todo esté correcto
        cursor.execute("PRAGMA table_info(productos);")
        columnas_finales = cursor.fetchall()
        
        print(f"\n✅ Estructura final de la tabla 'productos':")
        for columna in columnas_finales:
            print(f"  - {columna[1]} ({columna[2]})")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 ¡Base de datos corregida exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error al corregir la base de datos: {e}")
        return False

def main():
    print("🔍 DIAGNÓSTICO Y CORRECCIÓN DE BASE DE DATOS")
    print("=" * 50)
    
    # Primero diagnosticar
    if diagnosticar_base_datos():
        print("\n✅ La base de datos está correcta, no necesita corrección")
    else:
        print("\n🔧 Se detectaron problemas, procediendo a corregir...")
        if corregir_base_datos():
            print("\n🔍 Verificando corrección...")
            diagnosticar_base_datos()
        else:
            print("\n❌ No se pudo corregir la base de datos")
            
            # Opción de recrear completamente
            respuesta = input("\n¿Desea recrear la base de datos completamente? (s/n): ")
            if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                recrear_base_datos()

def recrear_base_datos():
    """Recrea la base de datos completamente"""
    
    db_path = 'ventas.db'
    
    # Hacer backup si existe
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup"
        os.rename(db_path, backup_path)
        print(f"📋 Backup creado: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Recreando base de datos...")
        
        # Crear tabla productos con estructura completa
        cursor.execute('''
            CREATE TABLE productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                categoria TEXT DEFAULT 'General',
                marca TEXT DEFAULT 'Sin especificar',
                modelo TEXT DEFAULT 'N/A',
                precio REAL NOT NULL,
                costo REAL DEFAULT 0,
                stock INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 5,
                descripcion TEXT,
                descripcion_corta TEXT,
                especificaciones TEXT DEFAULT 'Sin especificar',
                garantia TEXT DEFAULT '12 meses',
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear otras tablas necesarias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT,
                telefono TEXT,
                direccion TEXT,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                total REAL NOT NULL,
                fecha TEXT DEFAULT CURRENT_TIMESTAMP,
                metodo_pago TEXT DEFAULT 'Efectivo',
                estado TEXT DEFAULT 'Completada',
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT DEFAULT 'vendedor',
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insertar usuario admin por defecto
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol) 
            VALUES ('admin', 'admin123', 'administrador')
        ''')
        
        # Insertar algunos productos de ejemplo
        productos_ejemplo = [
            ('Laptop HP Pavilion', 'Computadoras', 'HP', 'Pavilion 15', 850.00, 650.00, 5, 2, 'Laptop para uso general', 'Laptop HP Pavilion 15"', 'Intel i5, 8GB RAM, 256GB SSD', '12 meses'),
            ('Mouse Logitech', 'Accesorios', 'Logitech', 'M100', 15.00, 8.00, 20, 5, 'Mouse óptico básico', 'Mouse óptico USB', 'USB, óptico, ergonómico', '6 meses'),
            ('Teclado Mecánico', 'Accesorios', 'Generic', 'KB-500', 45.00, 25.00, 8, 3, 'Teclado mecánico RGB', 'Teclado gaming RGB', 'Switches azules, retroiluminado', '12 meses')
        ]
        
        for producto in productos_ejemplo:
            cursor.execute('''
                INSERT INTO productos (nombre, categoria, marca, modelo, precio, costo, stock, stock_minimo, descripcion, descripcion_corta, especificaciones, garantia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', producto)
        
        conn.commit()
        conn.close()
        
        print("✅ Base de datos recreada exitosamente")
        print("👤 Usuario por defecto: admin / admin123")
        
    except Exception as e:
        print(f"❌ Error al recrear la base de datos: {e}")

if __name__ == "__main__":
    main()