#!/usr/bin/env python3
"""
Script de migración para agregar la columna 'categoria' a la tabla productos
y actualizar datos existentes con categorías por defecto.
"""

import sqlite3
import os
from datetime import datetime

def migrar_base_datos():
    """Ejecuta la migración para agregar categorías a productos"""
    
    db_path = 'systec_ventas.db'
    
    if not os.path.exists(db_path):
        print("❌ Error: No se encontró la base de datos systec_ventas.db")
        print("   Asegúrate de que el archivo existe en el directorio actual")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Iniciando migración de base de datos...")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(productos)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'categoria' in columnas:
            print("✅ La columna 'categoria' ya existe en la tabla productos")
            conn.close()
            return True
        
        print("📝 Agregando columna 'categoria' a la tabla productos...")
        
        # Agregar la columna categoria
        cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'General'")
        
        # Actualizar productos existentes con categorías basadas en el nombre
        print("🏷️  Asignando categorías automáticas basadas en nombres de productos...")
        
        # Definir mapeo de palabras clave a categorías
        categorias_mapeo = {
            'Bebidas': ['coca', 'pepsi', 'agua', 'jugo', 'refresco', 'gaseosa', 'cafe', 'te', 'cerveza', 'vino', 'leche'],
            'Snacks': ['papa', 'galleta', 'chocolate', 'caramelo', 'dulce', 'chupete', 'chicle', 'mani', 'almendra'],
            'Comida': ['sandwich', 'hamburguesa', 'pizza', 'empanada', 'taco', 'burrito', 'sopa', 'ensalada', 'pollo', 'carne'],
            'Panadería': ['pan', 'torta', 'pastel', 'croissant', 'medialuna', 'facturas', 'bizcocho'],
            'Lácteos': ['queso', 'yogur', 'manteca', 'crema', 'ricota'],
            'Higiene': ['jabon', 'shampoo', 'pasta', 'cepillo', 'desodorante', 'papel'],
            'Limpieza': ['detergente', 'lavandina', 'desinfectante', 'esponja', 'trapo'],
            'Cigarrillos': ['marlboro', 'parlament', 'lucky', 'camel', 'cigarrillo', 'tabaco']
        }
        
        # Obtener todos los productos
        cursor.execute("SELECT id, nombre FROM productos")
        productos = cursor.fetchall()
        
        productos_actualizados = 0
        
        for producto_id, nombre in productos:
            nombre_lower = nombre.lower()
            categoria_asignada = 'General'  # Categoría por defecto
            
            # Buscar coincidencias con palabras clave
            for categoria, palabras_clave in categorias_mapeo.items():
                if any(palabra in nombre_lower for palabra in palabras_clave):
                    categoria_asignada = categoria
                    break
            
            # Actualizar la categoría del producto
            cursor.execute("UPDATE productos SET categoria = ? WHERE id = ?", 
                         (categoria_asignada, producto_id))
            productos_actualizados += 1
            
            print(f"   📦 {nombre} -> {categoria_asignada}")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n✅ Migración completada exitosamente!")
        print(f"   📊 {productos_actualizados} productos actualizados")
        print(f"   🏷️  Categorías disponibles: {', '.join(categorias_mapeo.keys())}")
        
        # Mostrar resumen de categorías
        print("\n📈 Resumen de productos por categoría:")
        cursor.execute("""
            SELECT categoria, COUNT(*) as cantidad 
            FROM productos 
            GROUP BY categoria 
            ORDER BY cantidad DESC
        """)
        
        for categoria, cantidad in cursor.fetchall():
            print(f"   {categoria}: {cantidad} productos")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error de base de datos: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def verificar_migracion():
    """Verifica que la migración se haya aplicado correctamente"""
    
    try:
        conn = sqlite3.connect('systec_ventas.db')
        cursor = conn.cursor()
        
        # Verificar estructura de la tabla
        cursor.execute("PRAGMA table_info(productos)")
        columnas = cursor.fetchall()
        
        print("\n🔍 Verificando estructura de tabla productos:")
        for col in columnas:
            print(f"   {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - Default: {col[4] or 'None'}")
        
        # Verificar datos de ejemplo
        cursor.execute("SELECT nombre, categoria FROM productos LIMIT 5")
        productos = cursor.fetchall()
        
        if productos:
            print("\n📋 Productos de ejemplo:")
            for nombre, categoria in productos:
                print(f"   {nombre} -> {categoria}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar: {e}")
        return False

def crear_productos_ejemplo():
    """Crea algunos productos de ejemplo con categorías si no hay productos"""
    
    try:
        conn = sqlite3.connect('systec_ventas.db')
        cursor = conn.cursor()
        
        # Verificar si hay productos
        cursor.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"✅ Ya hay {count} productos en la base de datos")
            conn.close()
            return True
        
        print("📦 Creando productos de ejemplo...")
        
        productos_ejemplo = [
            ('Coca Cola 500ml', 2.50, 50, 'Bebidas'),
            ('Agua Mineral 1L', 1.20, 30, 'Bebidas'),
            ('Papas Fritas', 1.80, 25, 'Snacks'),
            ('Galletas Oreo', 2.20, 15, 'Snacks'),
            ('Sandwich Jamón', 4.50, 12, 'Comida'),
            ('Café Americano', 2.80, 40, 'Bebidas'),
            ('Pan Francés', 0.50, 20, 'Panadería'),
            ('Leche Entera 1L', 1.80, 15, 'Lácteos'),
            ('Marlboro Box', 5.00, 10, 'Cigarrillos'),
            ('Detergente 500ml', 3.20, 8, 'Limpieza')
        ]
        
        for nombre, precio, stock, categoria in productos_ejemplo:
            cursor.execute("""
                INSERT INTO productos (nombre, precio, stock, categoria, activo) 
                VALUES (?, ?, ?, ?, 1)
            """, (nombre, precio, stock, categoria))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Se crearon {len(productos_ejemplo)} productos de ejemplo")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear productos de ejemplo: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SysTec Ventas - Migración de Categorías")
    print("=" * 50)
    
    # Ejecutar migración
    if migrar_base_datos():
        print("\n" + "=" * 50)
        
        # Verificar migración
        if verificar_migracion():
            print("\n" + "=" * 50)
            
            # Crear productos de ejemplo si es necesario
            crear_productos_ejemplo()
            
            print("\n🎉 ¡Migración completada exitosamente!")
            print("   Ahora puedes usar el Punto de Venta sin problemas")
            print("   Las categorías disponibles son:")
            print("   • Bebidas • Snacks • Comida • Panadería")
            print("   • Lácteos • Higiene • Limpieza • Cigarrillos • General")
            
        else:
            print("\n❌ Error en la verificación de la migración")
    else:
        print("\n❌ Error en la migración")
    
    print("\n" + "=" * 50)
    input("Presiona Enter para continuar...")