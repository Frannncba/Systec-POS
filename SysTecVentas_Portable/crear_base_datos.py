#!/usr/bin/env python3
"""
Script para crear la base de datos completa del sistema SysTec Ventas
con todas las tablas, datos de ejemplo y configuración inicial.
"""

import sqlite3
import os
import hashlib
from datetime import datetime, date

def crear_hash_password(password):
    """Crea un hash seguro de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def crear_base_datos():
    """Crea la base de datos completa con todas las tablas"""
    
    db_path = 'systec_ventas.db'
    
    # Eliminar base de datos existente si existe
    if os.path.exists(db_path):
        respuesta = input(f"⚠️  La base de datos {db_path} ya existe. ¿Recrearla? (s/N): ")
        if respuesta.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada")
            return False
        os.remove(db_path)
        print("🗑️  Base de datos anterior eliminada")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🚀 Creando base de datos SysTec Ventas...")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ============ TABLA USUARIOS ============
        print("👥 Creando tabla usuarios...")
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'vendedor',
                nombre_completo TEXT,
                email TEXT,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TIMESTAMP
            )
        """)
        
        # ============ TABLA CONFIGURACION ============
        print("⚙️  Creando tabla configuracion...")
        cursor.execute("""
            CREATE TABLE configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clave TEXT UNIQUE NOT NULL,
                valor TEXT,
                descripcion TEXT,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============ TABLA PRODUCTOS ============
        print("📦 Creando tabla productos...")
        cursor.execute("""
            CREATE TABLE productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                stock_minimo INTEGER DEFAULT 5,
                categoria TEXT DEFAULT 'General',
                codigo_barras TEXT,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============ TABLA CLIENTES ============
        print("👤 Creando tabla clientes...")
        cursor.execute("""
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                dni_cuit TEXT,
                limite_credito REAL DEFAULT 0,
                deuda_actual REAL DEFAULT 0,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============ TABLA VENTAS ============
        print("🛒 Creando tabla ventas...")
        cursor.execute("""
            CREATE TABLE ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cliente_id INTEGER,
                usuario_id INTEGER NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                descuento REAL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                metodo_pago TEXT NOT NULL DEFAULT 'efectivo',
                dinero_recibido REAL DEFAULT 0,
                cambio REAL DEFAULT 0,
                estado TEXT DEFAULT 'completada',
                notas TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        """)
        
        # ============ TABLA DETALLE_VENTAS ============
        print("📋 Creando tabla detalle_ventas...")
        cursor.execute("""
            CREATE TABLE detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        """)
        
        # ============ TABLA CREDITOS ============
        print("💳 Creando tabla creditos...")
        cursor.execute("""
            CREATE TABLE creditos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                venta_id INTEGER,
                monto REAL NOT NULL,
                saldo REAL NOT NULL,
                fecha_otorgado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_vencimiento DATE,
                estado TEXT DEFAULT 'pendiente',
                notas TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                FOREIGN KEY (venta_id) REFERENCES ventas (id)
            )
        """)
        
        # ============ TABLA PAGOS_CREDITO ============
        print("💰 Creando tabla pagos_credito...")
        cursor.execute("""
            CREATE TABLE pagos_credito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credito_id INTEGER NOT NULL,
                monto REAL NOT NULL,
                fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_id INTEGER NOT NULL,
                metodo_pago TEXT DEFAULT 'efectivo',
                notas TEXT,
                FOREIGN KEY (credito_id) REFERENCES creditos (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        """)
        
        # ============ ÍNDICES PARA OPTIMIZACIÓN ============
        print("🔍 Creando índices...")
        indices = [
            "CREATE INDEX idx_productos_categoria ON productos(categoria)",
            "CREATE INDEX idx_productos_activo ON productos(activo)",
            "CREATE INDEX idx_ventas_fecha ON ventas(fecha)",
            "CREATE INDEX idx_ventas_usuario ON ventas(usuario_id)",
            "CREATE INDEX idx_detalle_venta ON detalle_ventas(venta_id)",
            "CREATE INDEX idx_creditos_cliente ON creditos(cliente_id)",
            "CREATE INDEX idx_creditos_estado ON creditos(estado)"
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        conn.commit()
        print("✅ Estructura de base de datos creada correctamente")
        
        return conn, cursor
        
    except sqlite3.Error as e:
        print(f"❌ Error al crear base de datos: {e}")
        if 'conn' in locals():
            conn.close()
        return None, None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        if 'conn' in locals():
            conn.close()
        return None, None

def insertar_datos_iniciales(conn, cursor):
    """Inserta configuración inicial y datos de ejemplo"""
    
    try:
        print("\n📝 Insertando configuración inicial...")
        
        # ============ CONFIGURACIÓN INICIAL ============
        configuraciones = [
            ('empresa_nombre', 'SysTec Software', 'Nombre de la empresa'),
            ('empresa_direccion', 'Cruz del Eje, Córdoba', 'Dirección de la empresa'),
            ('empresa_telefono', '+54 3549 123456', 'Teléfono de contacto'),
            ('empresa_email', 'contacto@systec.com.ar', 'Email de contacto'),
            ('moneda', 'ARS', 'Moneda utilizada'),
            ('simbolo_moneda', '$', 'Símbolo de la moneda'),
            ('stock_minimo_default', '5', 'Stock mínimo por defecto'),
            ('limite_credito_default', '1000', 'Límite de crédito por defecto'),
            ('dias_mora_amarillo', '7', 'Días para mora amarilla'),
            ('dias_mora_rojo', '15', 'Días para mora roja'),
            ('modo_oscuro', 'true', 'Tema oscuro activado'),
            ('version_sistema', '1.0.0', 'Versión del sistema')
        ]
        
        cursor.executemany("""
            INSERT INTO configuracion (clave, valor, descripcion) 
            VALUES (?, ?, ?)
        """, configuraciones)
        
        print("✅ Configuración inicial insertada")
        
        # ============ USUARIO ADMINISTRADOR ============
        print("👤 Creando usuario administrador...")
        
        admin_password = crear_hash_password('admin123')
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, rol, nombre_completo, email, activo) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('admin', admin_password, 'admin', 'Administrador Sistema', 'admin@systec.com.ar', 1))
        
        print("✅ Usuario administrador creado:")
        print("   👤 Usuario: admin")
        print("   🔑 Contraseña: admin123")
        
        # ============ PRODUCTOS DE EJEMPLO ============
        print("📦 Creando productos de ejemplo...")
        
        productos = [
            ('Coca Cola 500ml', 'Gaseosa cola 500ml', 2.50, 50, 10, 'Bebidas', '7791234567890'),
            ('Pepsi 500ml', 'Gaseosa cola 500ml', 2.30, 30, 10, 'Bebidas', '7791234567891'),
            ('Agua Mineral 1L', 'Agua mineral sin gas', 1.20, 40, 15, 'Bebidas', '7791234567892'),
            ('Papas Fritas 150g', 'Papas fritas sabor original', 1.80, 25, 5, 'Snacks', '7791234567893'),
            ('Galletas Oreo', 'Galletas chocolate con crema', 2.20, 15, 5, 'Snacks', '7791234567894'),
            ('Chocolate Milka', 'Chocolate con leche 100g', 3.50, 20, 3, 'Snacks', '7791234567895'),
            ('Sandwich Jamón', 'Sandwich jamón y queso', 4.50, 12, 3, 'Comida', '7791234567896'),
            ('Empanada Carne', 'Empanada de carne casera', 2.80, 20, 5, 'Comida', '7791234567897'),
            ('Pizza Slice', 'Porción de pizza muzzarella', 3.20, 15, 3, 'Comida', '7791234567898'),
            ('Café Americano', 'Café americano grande', 2.80, 100, 20, 'Bebidas', '7791234567899'),
            ('Pan Francés', 'Pan francés tradicional', 0.50, 30, 10, 'Panadería', '7791234567900'),
            ('Medialuna', 'Medialuna de manteca', 0.80, 25, 8, 'Panadería', '7791234567901'),
            ('Leche Entera 1L', 'Leche entera pasteurizada', 1.80, 20, 8, 'Lácteos', '7791234567902'),
            ('Yogur Natural', 'Yogur natural cremoso 200g', 1.50, 15, 5, 'Lácteos', '7791234567903'),
            ('Marlboro Box', 'Cigarrillos Marlboro rojo', 5.00, 10, 2, 'Cigarrillos', '7791234567904'),
            ('Parliament', 'Cigarrillos Parliament', 5.20, 8, 2, 'Cigarrillos', '7791234567905'),
            ('Detergente 500ml', 'Detergente líquido multiuso', 3.20, 12, 3, 'Limpieza', '7791234567906'),
            ('Jabón Antibacterial', 'Jabón líquido antibacterial', 2.80, 10, 3, 'Higiene', '7791234567907'),
            ('Papel Higiénico', 'Papel higiénico doble hoja x4', 4.50, 15, 5, 'Higiene', '7791234567908'),
            ('Shampoo 400ml', 'Shampoo para todo tipo de cabello', 6.80, 8, 2, 'Higiene', '7791234567909')
        ]
        
        cursor.executemany("""
            INSERT INTO productos (nombre, descripcion, precio, stock, stock_minimo, categoria, codigo_barras) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, productos)
        
        print(f"✅ {len(productos)} productos de ejemplo creados")
        
        # ============ CLIENTES DE EJEMPLO ============
        print("👥 Creando clientes de ejemplo...")
        
        clientes = [
            ('Juan Pérez', '3549-123456', 'juan.perez@email.com', 'San Martín 123', '12345678', 1500.00, 0.00),
            ('María García', '3549-234567', 'maria.garcia@email.com', 'Belgrano 456', '23456789', 2000.00, 350.00),
            ('Carlos López', '3549-345678', 'carlos.lopez@email.com', 'Rivadavia 789', '34567890', 1000.00, 800.00),
            ('Ana Martínez', '3549-456789', 'ana.martinez@email.com', 'Mitre 321', '45678901', 1200.00, 0.00),
            ('Roberto Silva', '3549-567890', 'roberto.silva@email.com', 'Sarmiento 654', '56789012', 800.00, 150.00)
        ]
        
        cursor.executemany("""
            INSERT INTO clientes (nombre, telefono, email, direccion, dni_cuit, limite_credito, deuda_actual) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, clientes)
        
        print(f"✅ {len(clientes)} clientes de ejemplo creados")
        
        # ============ VENTAS DE EJEMPLO ============
        print("🛒 Creando ventas de ejemplo...")
        
        # Obtener IDs necesarios
        cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
        admin_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM productos LIMIT 5")
        productos_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM clientes LIMIT 3")
        clientes_ids = [row[0] for row in cursor.fetchall()]
        
        # Crear algunas ventas de ejemplo
        ventas_ejemplo = [
            (clientes_ids[0], admin_id, 12.50, 0, 12.50, 'efectivo', 15.00, 2.50, 'completada', 'Venta de prueba 1'),
            (None, admin_id, 8.30, 0, 8.30, 'tarjeta', 8.30, 0, 'completada', 'Venta de prueba 2'),
            (clientes_ids[1], admin_id, 25.80, 0, 25.80, 'credito', 0, 0, 'completada', 'Venta a crédito'),
        ]
        
        for venta in ventas_ejemplo:
            cursor.execute("""
                INSERT INTO ventas (cliente_id, usuario_id, subtotal, descuento, total, metodo_pago, dinero_recibido, cambio, estado, notas) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, venta)
            
            venta_id = cursor.lastrowid
            
            # Agregar algunos productos a cada venta
            for i, producto_id in enumerate(productos_ids[:2]):  # Solo primeros 2 productos por venta
                cantidad = i + 1
                cursor.execute("SELECT precio FROM productos WHERE id = ?", (producto_id,))
                precio = cursor.fetchone()[0]
                subtotal = precio * cantidad
                
                cursor.execute("""
                    INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal) 
                    VALUES (?, ?, ?, ?, ?)
                """, (venta_id, producto_id, cantidad, precio, subtotal))
        
        print(f"✅ {len(ventas_ejemplo)} ventas de ejemplo creadas")
        
        # ============ CRÉDITOS DE EJEMPLO ============
        print("💳 Creando créditos de ejemplo...")
        
        creditos_ejemplo = [
            (clientes_ids[1], None, 350.00, 350.00, '2024-12-31', 'pendiente', 'Crédito inicial'),
            (clientes_ids[2], None, 800.00, 800.00, '2024-11-30', 'vencido', 'Crédito vencido')
        ]
        
        cursor.executemany("""
            INSERT INTO creditos (cliente_id, venta_id, monto, saldo, fecha_vencimiento, estado, notas) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, creditos_ejemplo)
        
        print(f"✅ {len(creditos_ejemplo)} créditos de ejemplo creados")
        
        conn.commit()
        print("\n✅ Todos los datos iniciales insertados correctamente")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error al insertar datos: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        conn.rollback()
        return False

def mostrar_resumen(cursor):
    """Muestra un resumen de la base de datos creada"""
    
    try:
        print("\n" + "="*60)
        print("📊 RESUMEN DE BASE DE DATOS CREADA")
        print("="*60)
        
        # Contar registros en cada tabla
        tablas = ['usuarios', 'productos', 'clientes', 'ventas', 'creditos', 'configuracion']
        
        for tabla in tablas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"📋 {tabla.capitalize()}: {count} registros")
        
        print("\n" + "="*60)
        print("🏷️  CATEGORÍAS DE PRODUCTOS")
        print("="*60)
        
        cursor.execute("""
            SELECT categoria, COUNT(*) as cantidad 
            FROM productos 
            GROUP BY categoria 
            ORDER BY cantidad DESC
        """)
        
        for categoria, cantidad in cursor.fetchall():
            print(f"   {categoria}: {cantidad} productos")
        
        print("\n" + "="*60)
        print("👤 INFORMACIÓN DE ACCESO")
        print("="*60)
        print("🔐 Usuario Administrador:")
        print("   👤 Usuario: admin")
        print("   🔑 Contraseña: admin123")
        print("   🎯 Rol: Administrador")
        
        print("\n" + "="*60)
        print("🚀 SISTEMA LISTO PARA USAR")
        print("="*60)
        print("✅ Base de datos creada: systec_ventas.db")
        print("✅ Todas las tablas configuradas")
        print("✅ Datos de ejemplo insertados")
        print("✅ Índices de optimización creados")
        print("✅ Usuario administrador configurado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al mostrar resumen: {e}")
        return False

def main():
    """Función principal"""
    
    print("🚀 SysTec Ventas - Creador de Base de Datos")
    print("=" * 60)
    
    # Crear base de datos y estructura
    conn, cursor = crear_base_datos()
    
    if conn is None or cursor is None:
        print("❌ Error fatal: No se pudo crear la base de datos")
        return False
    
    try:
        # Insertar datos iniciales
        if insertar_datos_iniciales(conn, cursor):
            # Mostrar resumen
            mostrar_resumen(cursor)
            
            conn.close()
            
            print("\n🎉 ¡BASE DE DATOS CREADA EXITOSAMENTE!")
            print("   Ahora puedes ejecutar tu aplicación Flask")
            print("   El Punto de Venta funcionará perfectamente")
            
            return True
        else:
            print("❌ Error al insertar datos iniciales")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    
    if success:
        print("✅ Proceso completado exitosamente")
        print("💡 Siguiente paso: Ejecutar tu aplicación Flask")
    else:
        print("❌ Proceso completado con errores")
        print("💡 Revisa los mensajes de error arriba")
    
    input("\nPresiona Enter para continuar...")