# config_handler.py - Versión mejorada con manejo de errores
import sqlite3
import os

class ConfigHandler:
    def __init__(self, db_path='dashboard.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con todas las tablas y columnas necesarias"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear tabla configuracion si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    id INTEGER PRIMARY KEY,
                    tema TEXT DEFAULT 'claro',
                    idioma TEXT DEFAULT 'es',
                    paleta_activa TEXT DEFAULT 'moderna',
                    notificaciones INTEGER DEFAULT 1,
                    actualizacion_auto INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Verificar si hay configuración inicial
            cursor.execute("SELECT COUNT(*) FROM configuracion")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO configuracion (tema, idioma, paleta_activa, notificaciones, actualizacion_auto)
                    VALUES ('claro', 'es', 'moderna', 1, 1)
                """)
                print("✅ Configuración inicial creada")
            
            # Verificar y agregar columnas faltantes
            self._verificar_columnas(cursor)
            
            conn.commit()
            conn.close()
            print("✅ Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
    
    def _verificar_columnas(self, cursor):
        """Verifica y agrega columnas faltantes"""
        # Obtener columnas actuales
        cursor.execute("PRAGMA table_info(configuracion)")
        columnas_actuales = [col[1] for col in cursor.fetchall()]
        
        # Columnas requeridas
        columnas_requeridas = {
            'paleta_activa': 'TEXT DEFAULT "moderna"',
            'notificaciones': 'INTEGER DEFAULT 1',
            'actualizacion_auto': 'INTEGER DEFAULT 1',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        # Agregar columnas faltantes
        for columna, tipo in columnas_requeridas.items():
            if columna not in columnas_actuales:
                try:
                    cursor.execute(f"ALTER TABLE configuracion ADD COLUMN {columna} {tipo}")
                    print(f"✅ Columna '{columna}' agregada")
                except sqlite3.Error as e:
                    print(f"⚠️  Error agregando columna {columna}: {e}")
    
    def get_config(self):
        """Obtiene la configuración actual con manejo de errores"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM configuracion LIMIT 1")
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                # Mapear resultado a diccionario con valores por defecto
                return {
                    'id': resultado[0] if len(resultado) > 0 else 1,
                    'tema': resultado[1] if len(resultado) > 1 else 'claro',
                    'idioma': resultado[2] if len(resultado) > 2 else 'es',
                    'paleta_activa': resultado[3] if len(resultado) > 3 else 'moderna',
                    'notificaciones': resultado[4] if len(resultado) > 4 else 1,
                    'actualizacion_auto': resultado[5] if len(resultado) > 5 else 1
                }
            else:
                return self._config_por_defecto()
                
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo configuración: {e}")
            return self._config_por_defecto()
    
    def _config_por_defecto(self):
        """Retorna configuración por defecto"""
        return {
            'id': 1,
            'tema': 'claro',
            'idioma': 'es',
            'paleta_activa': 'moderna',
            'notificaciones': 1,
            'actualizacion_auto': 1
        }
    
    def update_config(self, **kwargs):
        """Actualiza la configuración"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construir query de actualización dinámicamente
            campos = []
            valores = []
            
            for campo, valor in kwargs.items():
                if campo in ['tema', 'idioma', 'paleta_activa', 'notificaciones', 'actualizacion_auto']:
                    campos.append(f"{campo} = ?")
                    valores.append(valor)
            
            if campos:
                campos.append("updated_at = CURRENT_TIMESTAMP")
                query = f"UPDATE configuracion SET {', '.join(campos)} WHERE id = 1"
                cursor.execute(query, valores)
                conn.commit()
                print(f"✅ Configuración actualizada: {kwargs}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando configuración: {e}")
            return False

# Script para usar directamente
if __name__ == "__main__":
    # Inicializar manejador
    config = ConfigHandler()
    
    # Mostrar configuración actual
    print("\n📋 Configuración actual:")
    config_actual = config.get_config()
    for key, value in config_actual.items():
        print(f"  {key}: {value}")
    
    print("\n🚀 Base de datos lista para usar!")