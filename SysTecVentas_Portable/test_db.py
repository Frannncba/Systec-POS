import sqlite3
from werkzeug.security import check_password_hash

conn = sqlite3.connect('ventas.db')
cursor = conn.cursor()

# Verificar si el usuario admin existe
cursor.execute("SELECT username, password_hash, rol FROM usuarios WHERE username = 'admin'")
result = cursor.fetchone()

if result:
    print(f"Usuario encontrado: {result[0]}")
    print(f"Rol: {result[2]}")
    print(f"Hash de contraseña: {result[1][:50]}...")  # Solo primeros 50 caracteres
    
    # Verificar si la contraseña es correcta
    if check_password_hash(result[1], 'admin123'):
        print("✅ La contraseña 'admin123' es CORRECTA")
    else:
        print("❌ La contraseña 'admin123' es INCORRECTA")
else:
    print("❌ No se encontró el usuario 'admin'")

conn.close()