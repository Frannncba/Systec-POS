import sqlite3
from werkzeug.security import generate_password_hash

def crear_base_datos():
    # Eliminar archivo existente si existe
    import os
    if os.path.exists('ventas.db'):
        os.remove('ventas.db')
        print("Base de datos anterior eliminada")
    
    conn = sqlite3.connect('ventas.db')
    cursor = conn.cursor()
    
    print("Creando tablas...")
    
    # Crear tablas
    cursor.executescript('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'vendedor'
        );
        
        CREATE TABLE configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_empresa TEXT NOT NULL
        );
        
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER DEFAULT 0
        );
        
        CREATE TABLE ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            usuario_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        );
    ''')
    
    print("Insertando usuario admin...")
    
    # Insertar usuario admin
    password_hash = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO usuarios (username, password_hash, rol) 
        VALUES ('admin', ?, 'admin')
    ''', (password_hash,))
    
    # Insertar configuración
    cursor.execute('''
        INSERT INTO configuracion (nombre_empresa) 
        VALUES ('SysTec Ventas')
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Base de datos creada exitosamente")
    print("Usuario: admin")
    print("Contraseña: admin123")

if __name__ == '__main__':
    crear_base_datos()