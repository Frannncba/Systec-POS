import sqlite3
from utils.licencia import Licencia

def crear_tablas():
    """Crea todas las tablas necesarias para el sistema POS"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    print("🔧 Creando tablas del sistema...")
    
    # Tabla usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            clave TEXT NOT NULL,
            rol TEXT NOT NULL,
            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # Tabla proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            email TEXT,
            direccion TEXT,
            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    # Tabla productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            descripcion TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            proveedor_id INTEGER,
            activo INTEGER DEFAULT 1,
            fecha_creacion TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
        )
    ''')
    
    # Tabla ventas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            total REAL NOT NULL,
            fecha TEXT DEFAULT (datetime('now')),
            estado TEXT DEFAULT 'completada',
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Tabla detalle_ventas
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
    
    # Tabla configuración
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comercio TEXT NOT NULL,
            requiere_login INTEGER DEFAULT 1,
            logo TEXT,
            fecha_actualizacion TEXT DEFAULT (datetime('now'))
        )
    ''')
    
    conn.commit()
    print("✅ Tablas creadas correctamente")
    
    # Insertar datos por defecto
    print("🔧 Insertando datos por defecto...")
    
    # Usuario administrador por defecto
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (usuario, clave, rol) 
        VALUES ('admin', 'admin', 'dueño')
    ''')
    
    # Configuración por defecto
    cursor.execute('''
        INSERT OR IGNORE INTO configuracion (comercio, requiere_login) 
        VALUES ('SysTec Ventas', 1)
    ''')
    
    # Proveedor de ejemplo
    cursor.execute('''
        INSERT OR IGNORE INTO proveedores (nombre, telefono, email) 
        VALUES ('Proveedor Ejemplo', '123456789', 'ejemplo@email.com')
    ''')
    
    # Producto de ejemplo
    cursor.execute('''
        INSERT OR IGNORE INTO productos (codigo, descripcion, precio, stock, proveedor_id) 
        VALUES ('P001', 'Producto de Ejemplo', 100.00, 50, 1)
    ''')
    
    conn.commit()
    print("✅ Datos por defecto insertados")
    
    # Crear y registrar licencia
    print("🔧 Configurando licencia...")
    licencia = Licencia()
    nueva_licencia = licencia.generar_licencia("SysTec Demo", 365)
    
    if licencia.registrar_licencia(nueva_licencia):
        print("✅ Licencia registrada correctamente")
        print(f"   Comercio: {nueva_licencia['comercio']}")
        print(f"   Válida hasta: {nueva_licencia['valido_hasta']}")
    else:
        print("❌ Error al registrar licencia")
    
    conn.close()
    print("🎉 ¡Base de datos inicializada completamente!")

def mostrar_resumen():
    """Muestra un resumen de los datos en la base"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    print("\n📊 RESUMEN DE LA BASE DE DATOS:")
    print("-" * 40)
    
    # Contar registros en cada tabla
    tablas = ['usuarios', 'proveedores', 'productos', 'ventas', 'configuracion', 'licencia']
    
    for tabla in tablas:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"{tabla.capitalize():15}: {count} registros")
        except:
            print(f"{tabla.capitalize():15}: Tabla no encontrada")
    
    print("\n🔑 CREDENCIALES DE ACCESO:")
    print("Usuario: admin")
    print("Contraseña: admin")
    
    conn.close()

if __name__ == '__main__':
    print("🚀 Inicializando base de datos SysTec POS...")
    crear_tablas()
    mostrar_resumen()
    print("\n✨ ¡Listo! Ya puedes ejecutar tu aplicación con: python app.py")