# diagnose_and_fix.py
import sqlite3
import os

def diagnosticar_y_reparar_db():
    print("🔍 Diagnosticando base de datos...")
    
    try:
        # Verificar si el archivo de base de datos existe
        if not os.path.exists('dashboard.db'):
            print("❌ El archivo dashboard.db no existe")
            print("🛠️  Creando nueva base de datos...")
            crear_base_datos_completa()
            return
        
        conn = sqlite3.connect('dashboard.db')
        cursor = conn.cursor()
        
        # Verificar si la tabla configuracion existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='configuracion'")
        if not cursor.fetchone():
            print("❌ La tabla 'configuracion' no existe")
            print("🛠️  Creando tabla configuracion...")
            crear_tabla_configuracion(cursor)
        else:
            print("✅ La tabla 'configuracion' existe")
            
            # Mostrar estructura actual
            cursor.execute("PRAGMA table_info(configuracion)")
            columnas = cursor.fetchall()
            print("\n📋 Estructura actual de la tabla:")
            for col in columnas:
                print(f"  - {col[1]} ({col[2]})")
            
            # Verificar columnas requeridas
            columnas_existentes = [col[1] for col in columnas]
            columnas_requeridas = ['id', 'tema', 'idioma', 'paleta_activa', 'notificaciones', 'actualizacion_auto']
            
            print("\n🔧 Verificando columnas requeridas...")
            for col_requerida in columnas_requeridas:
                if col_requerida not in columnas_existentes:
                    print(f"❌ Falta columna: {col_requerida}")
                    agregar_columna(cursor, col_requerida)
                else:
                    print(f"✅ Columna OK: {col_requerida}")
        
        # Verificar si hay datos
        cursor.execute("SELECT COUNT(*) FROM configuracion")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\n📊 Insertando configuración inicial...")
            cursor.execute("""
                INSERT INTO configuracion (tema, idioma, paleta_activa, notificaciones, actualizacion_auto)
                VALUES ('claro', 'es', 'moderna', 1, 1)
            """)
            print("✅ Configuración inicial creada")
        else:
            print(f"\n✅ Encontrados {count} registros de configuración")
        
        conn.commit()
        conn.close()
        print("\n🎉 Base de datos reparada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        print("\n🔄 Intentando crear base de datos desde cero...")
        crear_base_datos_completa()

def agregar_columna(cursor, columna):
    """Agrega una columna específica con el tipo correcto"""
    tipos_columnas = {
        'paleta_activa': 'TEXT DEFAULT "moderna"',
        'notificaciones': 'INTEGER DEFAULT 1',
        'actualizacion_auto': 'INTEGER DEFAULT 1',
        'tema': 'TEXT DEFAULT "claro"',
        'idioma': 'TEXT DEFAULT "es"'
    }
    
    if columna in tipos_columnas:
        try:
            sql = f"ALTER TABLE configuracion ADD COLUMN {columna} {tipos_columnas[columna]}"
            cursor.execute(sql)
            print(f"✅ Columna '{columna}' agregada exitosamente")
        except sqlite3.Error as e:
            print(f"❌ Error agregando columna {columna}: {e}")

def crear_tabla_configuracion(cursor):
    """Crea la tabla configuracion con todas las columnas necesarias"""
    try:
        cursor.execute("""
            CREATE TABLE configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tema TEXT DEFAULT 'claro',
                idioma TEXT DEFAULT 'es',
                paleta_activa TEXT DEFAULT 'moderna',
                notificaciones INTEGER DEFAULT 1,
                actualizacion_auto INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'configuracion' creada exitosamente")
    except sqlite3.Error as e:
        print(f"❌ Error creando tabla: {e}")

def crear_base_datos_completa():
    """Crea una nueva base de datos completa desde cero"""
    try:
        conn = sqlite3.connect('dashboard.db')
        cursor = conn.cursor()
        
        print("🏗️  Creando base de datos completa...")
        
        # Tabla configuracion
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tema TEXT DEFAULT 'claro',
                idioma TEXT DEFAULT 'es',
                paleta_activa TEXT DEFAULT 'moderna',
                notificaciones INTEGER DEFAULT 1,
                actualizacion_auto INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar configuración por defecto
        cursor.execute("""
            INSERT INTO configuracion (tema, idioma, paleta_activa, notificaciones, actualizacion_auto)
            VALUES ('claro', 'es', 'moderna', 1, 1)
        """)
        
        # Otras tablas que puedas necesitar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio REAL NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Base de datos completa creada exitosamente")
        print("📊 Tablas creadas: configuracion, usuarios, ventas")
        
    except Exception as e:
        print(f"❌ Error creando base de datos completa: {e}")

def mostrar_estado_final():
    """Muestra el estado final de la base de datos"""
    try:
        conn = sqlite3.connect('dashboard.db')
        cursor = conn.cursor()
        
        print("\n" + "="*50)
        print("📊 ESTADO FINAL DE LA BASE DE DATOS")
        print("="*50)
        
        # Mostrar todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        print(f"\n📋 Tablas encontradas: {len(tablas)}")
        for tabla in tablas:
            print(f"  - {tabla[0]}")
        
        # Mostrar estructura de configuracion
        print(f"\n🔧 Estructura de tabla 'configuracion':")
        cursor.execute("PRAGMA table_info(configuracion)")
        columnas = cursor.fetchall()
        for col in columnas:
            print(f"  - {col[1]}: {col[2]} {'(PK)' if col[5] else ''}")
        
        # Mostrar datos de configuración
        cursor.execute("SELECT * FROM configuracion")
        config = cursor.fetchone()
        if config:
            print(f"\n⚙️  Configuración actual:")
            labels = ['ID', 'Tema', 'Idioma', 'Paleta', 'Notif.', 'Auto-Act.']
            for i, (label, valor) in enumerate(zip(labels, config[:6])):
                print(f"  - {label}: {valor}")
        
        conn.close()
        print("\n🎉 ¡Base de datos lista para usar!")
        
    except Exception as e:
        print(f"❌ Error mostrando estado: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando reparación de base de datos...")
    diagnosticar_y_reparar_db()
    mostrar_estado_final()
    print("\n💡 Ahora puedes ejecutar tu servidor sin problemas!")