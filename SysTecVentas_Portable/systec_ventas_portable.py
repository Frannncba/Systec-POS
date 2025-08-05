# ============================
# ARCHIVO: app.py
# ============================
from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3
from datetime import datetime
from utils.licencia import validar_licencia

app = Flask(__name__)
app.secret_key = 'clave_super_secreta_systec'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ============================
# BASE DE DATOS
# ============================
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

# ============================
# RUTA INICIAL (LOGIN O DASHBOARD)
# ============================
@app.route('/')
def index():
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM configuracion LIMIT 1').fetchone()

    if config and config['requiere_login']:
        if 'usuario_id' not in session:
            return redirect('/login')

    return redirect('/dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE usuario = ? AND clave = ? AND activo = 1",
                            (usuario, clave)).fetchone()
        conn.close()

        if user:
            session['usuario_id'] = user['id']
            session['rol'] = user['rol']
            return redirect('/')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    ventas_dia = conn.execute("""
        SELECT COUNT(*) AS cantidad, SUM(total) AS total
        FROM ventas
        WHERE DATE(fecha) = DATE('now')
    """).fetchone()

    top_productos = conn.execute("""
        SELECT p.descripcion, SUM(dv.cantidad) as total_vendidos
        FROM detalle_ventas dv
        JOIN productos p ON p.id = dv.producto_id
        JOIN ventas v ON v.id = dv.venta_id
        WHERE DATE(v.fecha) = DATE('now')
        GROUP BY p.id
        ORDER BY total_vendidos DESC
        LIMIT 5
    """).fetchall()

    stock_bajo = conn.execute("""
        SELECT p.descripcion, p.stock, p.stock_minimo, pr.nombre as proveedor
        FROM productos p
        LEFT JOIN proveedores pr ON pr.id = p.proveedor_id
        WHERE p.stock <= p.stock_minimo
    """).fetchall()

    conn.close()
    return render_template('index.html', ventas=ventas_dia, top=top_productos, alertas=stock_bajo)

# ============================
# PRODUCTOS
# ============================
@app.route('/productos')
def productos():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    productos = conn.execute("SELECT p.*, pr.nombre as proveedor FROM productos p LEFT JOIN proveedores pr ON pr.id = p.proveedor_id").fetchall()
    proveedores = conn.execute("SELECT * FROM proveedores").fetchall()
    conn.close()
    return render_template('productos.html', productos=productos, proveedores=proveedores)

@app.route('/producto/nuevo', methods=['POST'])
def nuevo_producto():
    if 'usuario_id' not in session:
        return redirect('/login')

    codigo = request.form['codigo']
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    stock = request.form['stock']
    stock_minimo = request.form['stock_minimo']
    proveedor_id = request.form['proveedor_id']

    conn = get_db_connection()
    conn.execute("INSERT INTO productos (codigo, descripcion, precio, stock, stock_minimo, proveedor_id) VALUES (?, ?, ?, ?, ?, ?)",
                 (codigo, descripcion, precio, stock, stock_minimo, proveedor_id))
    conn.commit()
    conn.close()
    return redirect('/productos')

# ============================
# PROVEEDORES
# ============================
@app.route('/proveedores')
def proveedores():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    proveedores = conn.execute("SELECT * FROM proveedores").fetchall()
    conn.close()
    return render_template('proveedores.html', proveedores=proveedores)

@app.route('/proveedor/nuevo', methods=['POST'])
def nuevo_proveedor():
    if 'usuario_id' not in session:
        return redirect('/login')

    nombre = request.form['nombre']
    telefono = request.form['telefono']
    email = request.form['email']
    direccion = request.form['direccion']
    conn = get_db_connection()
    conn.execute("INSERT INTO proveedores (nombre, telefono, email, direccion) VALUES (?, ?, ?, ?)",
                 (nombre, telefono, email, direccion))
    conn.commit()
    conn.close()
    return redirect('/proveedores')

# ============================
# LICENCIA Y EJECUCIÓN
# ============================
if __name__ == '__main__':
    if not validar_licencia():
        print("Licencia inválida. Contacte a francorodriguez33@gmail.com")
    else:
        app.run(debug=True)
