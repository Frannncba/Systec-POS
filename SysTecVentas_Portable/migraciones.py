import sqlite3

def asegurar_columnas_configuracion(nombre_db):
    columnas_requeridas = {
        "paleta_activa": "TEXT DEFAULT 'default'",
        # Agregá más columnas si las necesitás
    }

    conn = sqlite3.connect(nombre_db)
    cursor = conn.cursor()

    # Obtener columnas actuales de la tabla
    cursor.execute("PRAGMA table_info(configuracion);")
    columnas_actuales = [col[1] for col in cursor.fetchall()]

    # Verificar y agregar las columnas que falten
    for nombre_columna, definicion in columnas_requeridas.items():
        if nombre_columna not in columnas_actuales:
            try:
                cursor.execute(f"ALTER TABLE configuracion ADD COLUMN {nombre_columna} {definicion};")
                print(f"✅ Columna '{nombre_columna}' agregada.")
            except Exception as e:
                print(f"❌ Error al agregar la columna '{nombre_columna}': {e}")
        else:
            print(f"✔️ Columna '{nombre_columna}' ya existe.")

    conn.commit()
    conn.close()
