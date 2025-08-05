# fix_database.py
import sqlite3

def agregar_columna_paleta():
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('dashboard.db')
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(configuracion)")
        columnas = [columna[1] for columna in cursor.fetchall()]
        
        if 'paleta_activa' not in columnas:
            # Agregar la columna paleta_activa
            cursor.execute("""
                ALTER TABLE configuracion 
                ADD COLUMN paleta_activa TEXT DEFAULT 'moderna'
            """)
            
            print("✅ Columna 'paleta_activa' agregada exitosamente")
            
            # Verificar que se agregó correctamente
            cursor.execute("SELECT * FROM configuracion")
            resultado = cursor.fetchone()
            print(f"📊 Configuración actual: {resultado}")
            
        else:
            print("ℹ️  La columna 'paleta_activa' ya existe")
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Error en la base de datos: {e}")
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    agregar_columna_paleta()