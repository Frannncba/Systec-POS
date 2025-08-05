# app.py mejorado y CORREGIDO para SysTec Ventas
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, json, uuid
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__)
app.secret_key = 'clave-secreta-systec-2025'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DATABASE'] = 'systec_ventas.db'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ========== CONFIGURACIÓN GLOBAL ==========
CONFIGURACION_DEFAULT = {
    "empresa_nombre": "SysTec Ventas",
    "modo_oscuro": True,
    "umbral_stock_minimo": 5
}

# ========== CONEXIÓN DB ==========
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ========== INICIALIZACIÓN DB ==========
def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Crear tablas básicas
    c.executescript('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT DEFAULT 'vendedor'
    );
    CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY,
        nombre_empresa TEXT,
        logo_path TEXT,
        paleta_activa TEXT,
        colores_personalizados TEXT,
        modo_oscuro INTEGER DEFAULT 1,
        umbral_stock_minimo INTEGER DEFAULT 5
    );
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        precio REAL,
        precio_costo REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1,
        categoria TEXT DEFAULT 'General',
        codigo_barras TEXT,
        descripcion TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total REAL,
        usuario_id INTEGER,
        metodo_pago TEXT,
        pagado INTEGER DEFAULT 1,
        cliente_id INTEGER,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    );
    CREATE TABLE IF NOT EXISTS detalle_ventas (
        id INTEGER PRIMARY KEY,
        venta_id INTEGER,
        producto_id INTEGER,
        cantidad INTEGER,
        precio_unitario REAL,
        subtotal REAL,
        FOREIGN KEY (venta_id) REFERENCES ventas(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    );
    CREATE TABLE IF NOT EXISTS caja (
        id INTEGER PRIMARY KEY,
        apertura TIMESTAMP,
        cierre TIMESTAMP,
        monto_inicial REAL,
        monto_final REAL,
        usuario_id INTEGER,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    CREATE TABLE IF NOT EXISTS licencia (
        id INTEGER PRIMARY KEY,
        uuid TEXT,
        tipo TEXT,
        fecha_inicio TEXT,
        fecha_fin TEXT
    );
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        accion TEXT,
        tabla_afectada TEXT,
        registro_id INTEGER,
        detalles TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        descripcion TEXT,
        activa INTEGER DEFAULT 1
    );
    ''')

    # Insertar configuración inicial
    c.execute("INSERT OR IGNORE INTO configuracion (id, nombre_empresa, modo_oscuro, umbral_stock_minimo) VALUES (1, 'SysTec Ventas', 1, 5)")
    c.execute("INSERT OR IGNORE INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)", ('admin', generate_password_hash('admin123'), 'admin'))
    c.execute("INSERT OR IGNORE INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)", ('systec_root', generate_password_hash('qwer1234'), 'root'))

    # Categorías por defecto
    categorias_default = [
        ('Bebidas', 'Bebidas y refrescos'),
        ('Alimentos', 'Productos alimentarios'),
        ('Limpieza', 'Productos de limpieza'),
        ('Cuidado Personal', 'Productos de higiene y cuidado'),
        ('Electronica', 'Productos electrónicos'),
        ('General', 'Productos varios')
    ]
    
    for nombre, descripcion in categorias_default:
        c.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))

    # Licencia de prueba
    existe_licencia = c.execute("SELECT COUNT(*) FROM licencia").fetchone()[0]
    if not existe_licencia:
        hoy = datetime.today()
        fin = hoy + timedelta(days=7)
        c.execute("INSERT INTO licencia (uuid, tipo, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?)",
                  (str(uuid.uuid4()), 'temporal', hoy.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')))

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente.")

# ========== FUNCIONES DE CONFIGURACIÓN ==========
def cargar_configuracion():
    conn = get_db_connection()
    config = conn.execute("SELECT * FROM configuracion WHERE id = 1").fetchone()
    conn.close()
    
    if config:
        return {
            "empresa_nombre": config['nombre_empresa'] or "SysTec Ventas",
            "modo_oscuro": bool(config['modo_oscuro']),
            "umbral_stock_minimo": config['umbral_stock_minimo'] or 5
        }
    return CONFIGURACION_DEFAULT

def guardar_configuracion(nombre_empresa=None, modo_oscuro=None, umbral_stock=None):
    conn = get_db_connection()
    updates = []
    params = []
    
    if nombre_empresa is not None:
        updates.append("nombre_empresa = ?")
        params.append(nombre_empresa)
    if modo_oscuro is not None:
        updates.append("modo_oscuro = ?")
        params.append(1 if modo_oscuro else 0)
    if umbral_stock is not None:
        updates.append("umbral_stock_minimo = ?")
        params.append(umbral_stock)
    
    if updates:
        params.append(1)  # WHERE id = 1
        conn.execute(f"UPDATE configuracion SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()

# ========== FUNCIÓN DE LOG ==========
def registrar_log(accion, tabla_afectada=None, registro_id=None, detalles=None):
    """Registrar actividad en el sistema"""
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO logs (usuario_id, accion, tabla_afectada, registro_id, detalles)
            VALUES (?, ?, ?, ?, ?)
        """, (session.get('user_id'), accion, tabla_afectada, registro_id, detalles))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error registrando log: {e}")

# ========== MIDDLEWARE DE AUTENTICACIÓN ==========
def requiere_login(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ========== RUTAS DE AUTENTICACIÓN ==========
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, redirigir al dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash('Por favor, completa todos los campos.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']

            registrar_log("Inicio de sesión", "usuarios", user['id'])
            flash(f'¡Bienvenido, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales inválidas. Verifica tu usuario y contraseña.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@requiere_login
def logout():
    username = session.get('username', 'Usuario')
    registrar_log("Cierre de sesión", "usuarios", session.get('user_id'))
    session.clear()
    flash(f'Hasta luego, {username}. Sesión cerrada correctamente.', 'success')
    return redirect(url_for('login'))

# ========== DASHBOARD ==========
@app.route('/dashboard')
@requiere_login
def dashboard():
    conn = get_db_connection()
    
    # Estadísticas de hoy
    hoy = datetime.now().strftime('%Y-%m-%d')
    stats_hoy = conn.execute("""
        SELECT COUNT(*) as ventas_hoy, COALESCE(SUM(total),0) as total_hoy
        FROM ventas WHERE DATE(fecha) = ?
    """, (hoy,)).fetchone()
    
    # Productos con stock bajo
    config = cargar_configuracion()
    umbral = config['umbral_stock_minimo']
    productos_bajos = conn.execute(
        "SELECT COUNT(*) as count FROM productos WHERE stock <= ? AND activo = 1", 
        (umbral,)
    ).fetchone()['count']
    
    # Productos activos
    productos_activos = conn.execute(
        "SELECT COUNT(*) as count FROM productos WHERE activo = 1"
    ).fetchone()['count']
    
    # Últimas 5 ventas
    ultimas_ventas = conn.execute("""
        SELECT v.id, v.fecha, v.total, v.metodo_pago, u.username,
               COALESCE(c.nombre, 'Cliente general') as cliente_nombre
        FROM ventas v
        LEFT JOIN usuarios u ON u.id = v.usuario_id
        LEFT JOIN clientes c ON c.id = v.cliente_id
        ORDER BY v.fecha DESC LIMIT 5
    """).fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         stats_hoy=stats_hoy,
                         productos_bajos=productos_bajos,
                         productos_activos=productos_activos,
                         ultimas_ventas=ultimas_ventas,
                         umbral=umbral)

# ========== VENTAS ==========
@app.route('/punto_venta')
@requiere_login
def punto_venta():
    """Redirección a POS para compatibilidad con dashboard"""
    return redirect(url_for('pos'))

@app.route('/nueva_venta')
@requiere_login  
def nueva_venta():
    """Redirección a POS para compatibilidad con dashboard"""
    return redirect(url_for('pos'))

@app.route('/agregar_producto')
@requiere_login
def agregar_producto():
    """Redirección a crear producto para compatibilidad"""
    return redirect(url_for('crear_producto'))

@app.route('/ventas/detalle/<int:venta_id>')
@requiere_login
def detalle_venta(venta_id):
    conn = get_db_connection()
    venta = conn.execute("""
        SELECT v.*, u.username, COALESCE(c.nombre, 'Cliente general') as cliente_nombre
        FROM ventas v 
        LEFT JOIN usuarios u ON u.id = v.usuario_id 
        LEFT JOIN clientes c ON c.id = v.cliente_id
        WHERE v.id = ?
    """, (venta_id,)).fetchone()
    
    detalles = conn.execute("""
        SELECT d.*, p.nombre 
        FROM detalle_ventas d 
        LEFT JOIN productos p ON p.id = d.producto_id 
        WHERE d.venta_id = ?
    """, (venta_id,)).fetchall()
    conn.close()
    
    if not venta:
        flash("Venta no encontrada", "danger")
        return redirect(url_for('ventas'))
    
    return render_template('detalle_venta.html', venta=venta, detalles=detalles)

# ========== PRODUCTOS MEJORADO ==========
@app.route('/productos')
@requiere_login
def productos():
    conn = get_db_connection()
    
    # Filtros
    categoria_filtro = request.args.get('categoria', '')
    busqueda = request.args.get('busqueda', '')
    estado = request.args.get('estado', 'activos')
    
    # Query base
    query = """
        SELECT p.*, c.nombre as categoria_nombre
        FROM productos p
        LEFT JOIN categorias c ON c.nombre = p.categoria
    """
    
    conditions = []
    params = []
    
    # Aplicar filtros
    if estado == 'activos':
        conditions.append("p.activo = 1")
    elif estado == 'inactivos':
        conditions.append("p.activo = 0")
    
    if categoria_filtro:
        conditions.append("p.categoria = ?")
        params.append(categoria_filtro)
    
    if busqueda:
        conditions.append("(p.nombre LIKE ? OR p.codigo_barras LIKE ?)")
        params.extend([f'%{busqueda}%', f'%{busqueda}%'])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY p.nombre"
    
    productos = conn.execute(query, params).fetchall()
    
    # Obtener categorías para el filtro
    categorias = conn.execute("SELECT nombre FROM categorias WHERE activa = 1 ORDER BY nombre").fetchall()
    
    config = cargar_configuracion()
    conn.close()
    
    return render_template('productos.html', 
                         productos=productos, 
                         categorias=categorias,
                         umbral=config['umbral_stock_minimo'],
                         categoria_actual=categoria_filtro,
                         busqueda_actual=busqueda,
                         estado_actual=estado)

@app.route('/productos/crear', methods=['GET', 'POST'])
@requiere_login
def crear_producto():
    """Crear nuevo producto con interfaz completa"""
    conn = get_db_connection()
    categorias = conn.execute("SELECT nombre FROM categorias WHERE activa = 1 ORDER BY nombre").fetchall()
    
    if request.method == 'POST':
        try:
            # Datos del formulario
            nombre = request.form['nombre'].strip()
            precio = float(request.form['precio']) if request.form['precio'] else 0
            precio_costo = float(request.form.get('precio_costo', 0)) if request.form.get('precio_costo') else 0
            stock = int(request.form.get('stock', 0)) if request.form.get('stock') else 0
            categoria = request.form.get('categoria', 'General')
            codigo_barras = request.form.get('codigo_barras', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            activo = 1 if request.form.get('activo') == 'on' else 0
            
            # Validaciones
            if not nombre:
                flash('El nombre del producto es obligatorio.', 'danger')
                conn.close()
                return render_template('crear_producto.html', categorias=categorias)
            
            if precio < 0:
                flash('El precio no puede ser negativo.', 'danger')
                conn.close()
                return render_template('crear_producto.html', categorias=categorias)
            
            # Verificar código de barras único
            if codigo_barras:
                existe_codigo = conn.execute("SELECT id FROM productos WHERE codigo_barras = ? AND codigo_barras != ''", (codigo_barras,)).fetchone()
                if existe_codigo:
                    flash('El código de barras ya existe en otro producto.', 'warning')
                    conn.close()
                    return render_template('crear_producto.html', categorias=categorias)
            
            # Crear nueva categoría si no existe
            if categoria and categoria not in [c['nombre'] for c in categorias]:
                conn.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", 
                           (categoria, f'Categoría: {categoria}'))
            
            # Insertar producto
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO productos (nombre, precio, precio_costo, stock, categoria, codigo_barras, descripcion, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre, precio, precio_costo, stock, categoria, codigo_barras, descripcion, activo))
            
            producto_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            registrar_log("Producto creado", "productos", producto_id, f"Nombre: {nombre}, Categoría: {categoria}")
            flash(f'Producto "{nombre}" creado exitosamente.', 'success')
            return redirect(url_for('productos'))
            
        except ValueError as e:
            flash('Error en los datos numéricos. Verifica precio y stock.', 'danger')
            conn.close()
            return render_template('crear_producto.html', categorias=categorias)
        except Exception as e:
            flash(f'Error al crear producto: {str(e)}', 'danger')
            conn.close()
            return render_template('crear_producto.html', categorias=categorias)
    
    conn.close()
    return render_template('crear_producto.html', categorias=categorias)

@app.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@requiere_login
def editar_producto(id):
    """Editar producto existente"""
    conn = get_db_connection()
    producto = conn.execute("SELECT * FROM productos WHERE id = ?", (id,)).fetchone()
    categorias = conn.execute("SELECT nombre FROM categorias WHERE activa = 1 ORDER BY nombre").fetchall()
    
    if not producto:
        conn.close()
        flash('Producto no encontrado.', 'danger')
        return redirect(url_for('productos'))
    
    if request.method == 'POST':
        try:
            # Datos del formulario
            nombre = request.form['nombre'].strip()
            precio = float(request.form['precio']) if request.form['precio'] else 0
            precio_costo = float(request.form.get('precio_costo', 0)) if request.form.get('precio_costo') else 0
            stock = int(request.form.get('stock', 0)) if request.form.get('stock') else 0
            categoria = request.form.get('categoria', 'General')
            codigo_barras = request.form.get('codigo_barras', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            activo = 1 if request.form.get('activo') == 'on' else 0
            
            # Validaciones
            if not nombre:
                flash('El nombre del producto es obligatorio.', 'danger')
                conn.close()
                return render_template('editar_producto.html', producto=producto, categorias=categorias)
            
            if precio < 0:
                flash('El precio no puede ser negativo.', 'danger')
                conn.close()
                return render_template('editar_producto.html', producto=producto, categorias=categorias)
            
            # Verificar código de barras único (excluyendo el producto actual)
            if codigo_barras:
                existe_codigo = conn.execute("SELECT id FROM productos WHERE codigo_barras = ? AND id != ? AND codigo_barras != ''", (codigo_barras, id)).fetchone()
                if existe_codigo:
                    flash('El código de barras ya existe en otro producto.', 'warning')
                    conn.close()
                    return render_template('editar_producto.html', producto=producto, categorias=categorias)
            
            # Crear nueva categoría si no existe
            if categoria and categoria not in [c['nombre'] for c in categorias]:
                conn.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", 
                           (categoria, f'Categoría: {categoria}'))
            
            # Actualizar producto
            conn.execute("""
                UPDATE productos 
                SET nombre=?, precio=?, precio_costo=?, stock=?, categoria=?, codigo_barras=?, descripcion=?, activo=?
                WHERE id=?
            """, (nombre, precio, precio_costo, stock, categoria, codigo_barras, descripcion, activo, id))
            
            conn.commit()
            conn.close()
            
            registrar_log("Producto editado", "productos", id, f"Nombre: {nombre}")
            flash(f'Producto "{nombre}" actualizado exitosamente.', 'success')
            return redirect(url_for('productos'))
            
        except ValueError as e:
            flash('Error en los datos numéricos. Verifica precio y stock.', 'danger')
            conn.close()
            return render_template('editar_producto.html', producto=producto, categorias=categorias)
        except Exception as e:
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
            conn.close()
            return render_template('editar_producto.html', producto=producto, categorias=categorias)
    
    conn.close()
    return render_template('editar_producto.html', producto=producto, categorias=categorias)

@app.route('/productos/eliminar/<int:id>', methods=['POST'])
@requiere_login
def eliminar_producto(id):
    """Eliminar producto (marcar como inactivo)"""
    try:
        conn = get_db_connection()
        producto = conn.execute("SELECT nombre FROM productos WHERE id = ?", (id,)).fetchone()
        
        if not producto:
            flash('Producto no encontrado.', 'danger')
            conn.close()
            return redirect(url_for('productos'))
        
        # Marcar como inactivo en lugar de eliminar
        conn.execute("UPDATE productos SET activo = 0 WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        
        registrar_log("Producto eliminado", "productos", id, f"Nombre: {producto['nombre']}")
        flash(f'Producto "{producto["nombre"]}" eliminado exitosamente.', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar producto: {str(e)}', 'danger')
    
    return redirect(url_for('productos'))

@app.route('/productos/activar/<int:id>', methods=['POST'])
@requiere_login
def activar_producto(id):
    """Reactivar producto"""
    try:
        conn = get_db_connection()
        producto = conn.execute("SELECT nombre FROM productos WHERE id = ?", (id,)).fetchone()
        
        if not producto:
            flash('Producto no encontrado.', 'danger')
            conn.close()
            return redirect(url_for('productos'))
        
        conn.execute("UPDATE productos SET activo = 1 WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        
        registrar_log("Producto reactivado", "productos", id, f"Nombre: {producto['nombre']}")
        flash(f'Producto "{producto["nombre"]}" reactivado exitosamente.', 'success')
        
    except Exception as e:
        flash(f'Error al reactivar producto: {str(e)}', 'danger')
    
    return redirect(url_for('productos'))

# RESTO DEL CÓDIGO PERMANECE IGUAL...
# [Aquí continúa el resto del código original sin la ruta nueva_venta]

# ========== CLIENTES ==========
@app.route('/clientes')
@requiere_login
def clientes():
    conn = get_db_connection()
    clientes = conn.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
    conn.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/clientes/agregar', methods=['POST'])
@requiere_login
def agregar_cliente():
    nombre = request.form['nombre'].strip()
    telefono = request.form.get('telefono', '').strip()
    email = request.form.get('email', '').strip()
    direccion = request.form.get('direccion', '').strip()
    
    if not nombre:
        flash('El nombre del cliente es obligatorio.', 'danger')
        return redirect(url_for('clientes'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (nombre, telefono, email, direccion) VALUES (?, ?, ?, ?)",
                 (nombre, telefono, email, direccion))
    cliente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    registrar_log("Cliente agregado", "clientes", cliente_id, f"Nombre: {nombre}")
    flash(f'Cliente "{nombre}" agregado correctamente.', 'success')
    return redirect(url_for('clientes'))

# ========== CONFIGURACIÓN ==========
@app.route('/configuracion', methods=['GET', 'POST'])
@requiere_login
def configuracion():
    if request.method == 'POST':
        nombre_empresa = request.form.get('nombre_empresa', '').strip()
        modo_oscuro = request.form.get('modo_oscuro') == 'on'
        umbral_stock = int(request.form.get('umbral_stock', 5))
        
        # Manejar logo
        logo = request.files.get('logo')
        if logo and logo.filename:
            logo_path = os.path.join('static', 'empresa_logo.png')
            logo.save(logo_path)
        
        guardar_configuracion(nombre_empresa, modo_oscuro, umbral_stock)
        registrar_log("Configuración actualizada", "configuracion", 1)
        flash('Configuración guardada correctamente.', 'success')
        return redirect(url_for('configuracion'))
    
    config = cargar_configuracion()
    return render_template('configuracion.html', config=config)
@app.route('/configuracion/validar', methods=['POST'])
@requiere_login
def validar_configuracion():
    """Validar configuración antes de guardar"""
    try:
        nombre_empresa = request.form.get('nombre_empresa', '').strip()
        umbral_stock = request.form.get('umbral_stock', '5')
        
        # Validaciones
        if not nombre_empresa:
            return jsonify({'success': False, 'error': 'El nombre de la empresa es obligatorio'})
        
        if not umbral_stock.isdigit() or int(umbral_stock) < 0:
            return jsonify({'success': False, 'error': 'El umbral de stock debe ser un número positivo'})
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
# ========== CONTEXT PROCESSOR ==========
@app.context_processor
def inject_globals():
    config = cargar_configuracion()
    logo_exists = os.path.exists('static/empresa_logo.png')
    
    return dict(
        empresa_nombre=config['empresa_nombre'],
        modo_oscuro=config['modo_oscuro'],
        empresa_logo='empresa_logo.png' if logo_exists else None,
        usuario_actual=session.get('username', ''),
        rol_actual=session.get('rol', ''),
        umbral_stock=config['umbral_stock_minimo']
    )

# ========== PUNTO DE VENTA ==========
@app.route('/pos')
@requiere_login
def pos():  # <-- NOMBRE CORRECTO
    """Interfaz moderna de punto de venta"""
    conn = get_db_connection()
    productos = conn.execute("SELECT * FROM productos WHERE activo = 1 AND stock > 0 ORDER BY nombre").fetchall()
    clientes = conn.execute("SELECT id, nombre FROM clientes ORDER BY nombre").fetchall()
    categorias = conn.execute("SELECT DISTINCT categoria FROM productos WHERE activo = 1 AND categoria IS NOT NULL ORDER BY categoria").fetchall()
    conn.close()
    return render_template('pos.html', productos=productos, clientes=clientes, categorias=categorias)

# ========== VENTAS (HISTORIAL) ==========
@app.route('/ventas')
@requiere_login
def ventas():
    """Mostrar historial de ventas con filtros"""
    conn = get_db_connection()
    
    # Obtener filtros de fecha
    fecha_desde = request.args.get('desde', '')
    fecha_hasta = request.args.get('hasta', '')
    
    # Query base
    query = """
        SELECT v.id, v.fecha, v.total, v.metodo_pago, u.username,
               COALESCE(c.nombre, 'Cliente general') as cliente_nombre
        FROM ventas v 
        LEFT JOIN usuarios u ON u.id = v.usuario_id 
        LEFT JOIN clientes c ON c.id = v.cliente_id
    """
    
    params = []
    
    # Aplicar filtros de fecha si están presentes
    if fecha_desde and fecha_hasta:
        query += " WHERE DATE(v.fecha) BETWEEN ? AND ?"
        params = [fecha_desde, fecha_hasta]
    elif fecha_desde:
        query += " WHERE DATE(v.fecha) >= ?"
        params = [fecha_desde]
    elif fecha_hasta:
        query += " WHERE DATE(v.fecha) <= ?"
        params = [fecha_hasta]
    
    query += " ORDER BY v.fecha DESC"
    
    ventas = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('ventas.html', 
                         ventas=ventas,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)

# ========== API ENDPOINTS ==========
@app.route('/api/productos/buscar')
@requiere_login
def buscar_productos():
    """API para buscar productos (para autocompletado)"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    productos = conn.execute("""
        SELECT id, nombre, precio, stock
        FROM productos 
        WHERE activo = 1 AND (nombre LIKE ? OR codigo_barras LIKE ?)
        ORDER BY nombre 
        LIMIT 10
    """, (f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    
    return jsonify([{
        'id': p['id'],
        'nombre': p['nombre'],
        'precio': p['precio'],
        'stock': p['stock']
    } for p in productos])

@app.route('/api/pos/productos')
@requiere_login
def api_pos_productos():
    """API para obtener productos para el POS"""
    busqueda = request.args.get('q', '').strip()
    categoria = request.args.get('categoria', '')
    
    conn = get_db_connection()
    
    query = """
        SELECT id, nombre, precio, stock, categoria,
               CASE 
                   WHEN categoria = 'Bebidas' THEN '🥤'
                   WHEN categoria = 'Alimentos' THEN '🥖'
                   WHEN categoria = 'Limpieza' THEN '🧽'
                   WHEN categoria = 'Cuidado Personal' THEN '🧴'
                   WHEN categoria = 'Electronica' THEN '📱'
                   ELSE '📦'
               END as emoji
        FROM productos 
        WHERE activo = 1 AND stock > 0
    """
    
    params = []
    
    if busqueda:
        query += " AND (nombre LIKE ? OR CAST(id as TEXT) LIKE ? OR codigo_barras LIKE ?)"
        params.extend([f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'])
    
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    
    query += " ORDER BY nombre LIMIT 50"
    
    productos = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([{
        'id': p['id'],
        'nombre': p['nombre'],
        'precio': float(p['precio']),
        'stock': p['stock'],
        'categoria': p['categoria'],
        'emoji': p['emoji'],
        'codigo': str(p['id']).zfill(3)
    } for p in productos])

@app.route('/api/pos/procesar_venta', methods=['POST'])
@requiere_login
def api_pos_procesar_venta():
    """API para procesar venta desde POS"""
    try:
        data = request.get_json()
        
        carrito = data.get('carrito', [])
        metodo_pago = data.get('metodo_pago', 'efectivo')
        cliente_id = data.get('cliente_id')
        dinero_recibido = data.get('dinero_recibido', 0)
        
        if not carrito:
            return jsonify({'success': False, 'error': 'Carrito vacío'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calcular total
        total = 0
        detalles_venta = []
        
        for item in carrito:
            # Verificar stock
            producto = cursor.execute(
                "SELECT precio, stock FROM productos WHERE id = ? AND activo = 1",
                (item['id'],)
            ).fetchone()
            
            if not producto:
                conn.close()
                return jsonify({'success': False, 'error': f'Producto {item["nombre"]} no encontrado'})
            
            if producto['stock'] < item['cantidad']:
                conn.close()
                return jsonify({'success': False, 'error': f'Stock insuficiente para {item["nombre"]}'})
            
            subtotal = float(producto['precio']) * int(item['cantidad'])
            total += subtotal
            
            detalles_venta.append({
                'producto_id': item['id'],
                'cantidad': item['cantidad'],
                'precio_unitario': float(producto['precio']),
                'subtotal': subtotal
            })
        
        # Validar pago en efectivo
        if metodo_pago == 'efectivo':
            if float(dinero_recibido) < total:
                conn.close()
                return jsonify({'success': False, 'error': 'Dinero insuficiente'})
        
        # Registrar venta
        cursor.execute("""
            INSERT INTO ventas (fecha, total, usuario_id, metodo_pago, cliente_id, pagado)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (datetime.now(), total, session.get('user_id'), metodo_pago, cliente_id))
        
        venta_id = cursor.lastrowid
        
        # Registrar detalles y actualizar stock
        for detalle in detalles_venta:
            cursor.execute("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (venta_id, detalle['producto_id'], detalle['cantidad'], 
                  detalle['precio_unitario'], detalle['subtotal']))
            
            # Actualizar stock
            cursor.execute("""
                UPDATE productos SET stock = stock - ? WHERE id = ?
            """, (detalle['cantidad'], detalle['producto_id']))
        
        conn.commit()
        conn.close()
        
        # Registrar log
        registrar_log("Venta procesada", "ventas", venta_id, f"Total: ${total:.2f}")
        
        # Calcular cambio
        cambio = float(dinero_recibido) - total if metodo_pago == 'efectivo' else 0
        
        return jsonify({
            'success': True,
            'venta_id': venta_id,
            'total': total,
            'cambio': cambio,
            'mensaje': 'Venta procesada exitosamente'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/productos/verificar_stock/<int:producto_id>')
@requiere_login
def verificar_stock(producto_id):
    """Verificar stock de un producto específico"""
    try:
        conn = get_db_connection()
        producto = conn.execute("SELECT id, nombre, stock FROM productos WHERE id = ? AND activo = 1", (producto_id,)).fetchone()
        conn.close()
        
        if not producto:
            return jsonify({'success': False, 'error': 'Producto no encontrado'})
        
        config = cargar_configuracion()
        umbral = config['umbral_stock_minimo']
        
        return jsonify({
            'success': True,
            'producto': {
                'id': producto['id'],
                'nombre': producto['nombre'],
                'stock': producto['stock'],
                'stock_bajo': producto['stock'] <= umbral,
                'umbral': umbral
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/productos/actualizar_stock', methods=['POST'])
@requiere_login
def actualizar_stock():
    """Actualización rápida de stock"""
    try:
        producto_id = request.form.get('producto_id')
        nuevo_stock = request.form.get('stock')
        
        if not producto_id or not nuevo_stock:
            flash('Datos incompletos', 'danger')
            return redirect(url_for('productos'))
        
        nuevo_stock = int(nuevo_stock)
        if nuevo_stock < 0:
            flash('El stock no puede ser negativo', 'danger')
            return redirect(url_for('productos'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el producto existe
        producto = cursor.execute("SELECT nombre FROM productos WHERE id = ?", (producto_id,)).fetchone()
        if not producto:
            flash('Producto no encontrado', 'danger')
            conn.close()
            return redirect(url_for('productos'))
        
        # Actualizar stock
        cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto_id))
        conn.commit()
        conn.close()
        
        registrar_log("Stock actualizado", "productos", producto_id, f"Nuevo stock: {nuevo_stock}")
        flash(f'Stock de "{producto["nombre"]}" actualizado a {nuevo_stock}', 'success')
        
        return redirect(url_for('productos'))
        
    except ValueError:
        flash('El stock debe ser un número válido', 'danger')
    except Exception as e:
        flash(f'Error al actualizar stock: {str(e)}', 'danger')
    
    return redirect(url_for('productos'))

@app.route('/api/productos/buscar_avanzada')
@requiere_login
def buscar_productos_avanzada():
    """Búsqueda avanzada de productos"""
    try:
        query = request.args.get('q', '').strip()
        categoria = request.args.get('categoria', '')
        stock_minimo = request.args.get('stock_minimo', 0)
        activos_solo = request.args.get('activos', 'true') == 'true'
        
        if len(query) < 2 and not categoria:
            return jsonify([])
        
        conn = get_db_connection()
        
        sql_query = """
            SELECT id, nombre, precio, stock, categoria, codigo_barras,
                   CASE WHEN activo = 1 THEN 'Activo' ELSE 'Inactivo' END as estado
            FROM productos 
            WHERE 1=1
        """
        params = []
        
        if activos_solo:
            sql_query += " AND activo = 1"
        
        if query:
            sql_query += " AND (nombre LIKE ? OR codigo_barras LIKE ?)"
            params.extend([f'%{query}%', f'%{query}%'])
        
        if categoria:
            sql_query += " AND categoria = ?"
            params.append(categoria)
        
        if stock_minimo:
            sql_query += " AND stock >= ?"
            params.append(int(stock_minimo))
        
        sql_query += " ORDER BY nombre LIMIT 20"
        
        productos = conn.execute(sql_query, params).fetchall()
        conn.close()
        
        return jsonify([{
            'id': p['id'],
            'nombre': p['nombre'],
            'precio': float(p['precio']),
            'stock': p['stock'],
            'categoria': p['categoria'],
            'codigo_barras': p['codigo_barras'],
            'estado': p['estado']
        } for p in productos])
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/estadisticas/resumen')
@requiere_login
def estadisticas_resumen():
    """Estadísticas completas para el dashboard"""
    try:
        conn = get_db_connection()
        
        # Fechas importantes
        hoy = datetime.now().strftime('%Y-%m-%d')
        ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        semana_pasada = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        mes_actual = datetime.now().strftime('%Y-%m')
        
        # Ventas de hoy vs ayer
        ventas_hoy = conn.execute("SELECT COUNT(*) as count, COALESCE(SUM(total),0) as total FROM ventas WHERE DATE(fecha) = ?", (hoy,)).fetchone()
        ventas_ayer = conn.execute("SELECT COUNT(*) as count, COALESCE(SUM(total),0) as total FROM ventas WHERE DATE(fecha) = ?", (ayer,)).fetchone()
        
        # Productos más vendidos esta semana
        productos_top = conn.execute("""
            SELECT p.nombre, SUM(dv.cantidad) as vendido
            FROM detalle_ventas dv
            JOIN productos p ON p.id = dv.producto_id
            JOIN ventas v ON v.id = dv.venta_id
            WHERE DATE(v.fecha) >= ?
            GROUP BY p.id, p.nombre
            ORDER BY vendido DESC
            LIMIT 5
        """, (semana_pasada,)).fetchall()
        
        # Stock crítico
        config = cargar_configuracion()
        umbral = config['umbral_stock_minimo']
        stock_critico = conn.execute("""
            SELECT nombre, stock FROM productos 
            WHERE stock <= ? AND stock > 0 AND activo = 1 
            ORDER BY stock ASC 
            LIMIT 5
        """, (umbral,)).fetchall()
        
        conn.close()
        
        return jsonify({
            'ventas': {
                'hoy': {'cantidad': ventas_hoy['count'], 'total': float(ventas_hoy['total'])},
                'ayer': {'cantidad': ventas_ayer['count'], 'total': float(ventas_ayer['total'])},
                'cambio_cantidad': ventas_hoy['count'] - ventas_ayer['count'],
                'cambio_total': float(ventas_hoy['total']) - float(ventas_ayer['total'])
            },
            'productos_top': [{'nombre': p['nombre'], 'vendido': p['vendido']} for p in productos_top],
            'stock_critico': [{'nombre': p['nombre'], 'stock': p['stock']} for p in stock_critico],
            'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})
    
# ========== CATEGORÍAS ==========
@app.route('/api/categorias')
@requiere_login
def api_categorias():
    """API para obtener categorías"""
    conn = get_db_connection()
    categorias = conn.execute("SELECT nombre FROM categorias WHERE activa = 1 ORDER BY nombre").fetchall()
    conn.close()
    return jsonify([c['nombre'] for c in categorias])

@app.route('/categorias/crear', methods=['POST'])
@requiere_login
def crear_categoria():
    """Crear nueva categoría"""
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    
    if not nombre:
        flash('El nombre de la categoría es obligatorio.', 'danger')
        return redirect(url_for('configuracion'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        categoria_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        registrar_log("Categoría creada", "categorias", categoria_id, f"Nombre: {nombre}")
        flash(f'Categoría "{nombre}" creada exitosamente.', 'success')
    except sqlite3.IntegrityError:
        flash('Ya existe una categoría con ese nombre.', 'warning')
    except Exception as e:
        flash(f'Error al crear categoría: {str(e)}', 'danger')
    
    return redirect(url_for('configuracion'))

# ========== DASHBOARD STATS API ==========
@app.route('/api/dashboard/stats')
@requiere_login
def api_dashboard_stats():
    """API para obtener estadísticas del dashboard"""
    conn = get_db_connection()
    
    # Stats de hoy
    hoy = datetime.now().strftime('%Y-%m-%d')
    stats_hoy = conn.execute("""
        SELECT COUNT(*) as ventas_hoy, COALESCE(SUM(total),0) as total_hoy
        FROM ventas WHERE DATE(fecha) = ?
    """, (hoy,)).fetchone()
    
    # Stats del mes
    mes_actual = datetime.now().strftime('%Y-%m')
    stats_mes = conn.execute("""
        SELECT COUNT(*) as ventas_mes, COALESCE(SUM(total),0) as total_mes
        FROM ventas WHERE strftime('%Y-%m', fecha) = ?
    """, (mes_actual,)).fetchone()
    
    # Productos con stock bajo
    config = cargar_configuracion()
    umbral = config['umbral_stock_minimo']
    productos_bajos = conn.execute(
        "SELECT COUNT(*) as count FROM productos WHERE stock <= ? AND activo = 1", 
        (umbral,)
    ).fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'hoy': dict(stats_hoy) if stats_hoy else {'ventas_hoy': 0, 'total_hoy': 0},
        'mes': dict(stats_mes) if stats_mes else {'ventas_mes': 0, 'total_mes': 0},
        'productos_bajos': productos_bajos
    })

# ========== EXPORTACIONES ==========
@app.route('/productos/exportar', methods=['POST'])
@requiere_login
def exportar_productos():
    """Exportar inventario como CSV"""
    try:
        conn = get_db_connection()
        productos = conn.execute("""
            SELECT nombre, precio, precio_costo, stock, categoria, codigo_barras,
                   CASE WHEN activo = 1 THEN 'Activo' ELSE 'Inactivo' END as estado
            FROM productos 
            ORDER BY nombre
        """).fetchall()
        conn.close()
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow(['Nombre', 'Precio', 'Precio Costo', 'Stock', 'Categoría', 'Código Barras', 'Estado'])
        
        # Escribir datos
        for producto in productos:
            writer.writerow([
                producto['nombre'],
                f"{producto['precio']:.2f}",
                f"{producto['precio_costo']:.2f}",
                producto['stock'],
                producto['categoria'] or 'General',
                producto['codigo_barras'] or '',
                producto['estado']
            ])
        
        # Preparar respuesta
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        registrar_log("Exportación productos", "productos", None, "CSV generado")
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=inventario_{timestamp}.csv'
            }
        )
        
    except Exception as e:
        flash(f'Error al exportar inventario: {str(e)}', 'danger')
        return redirect(url_for('configuracion'))

@app.route('/ventas/exportar')
@requiere_login
def exportar_ventas():
    """Exportar ventas como CSV"""
    try:
        fecha_desde = request.args.get('desde', '')
        fecha_hasta = request.args.get('hasta', '')
        
        conn = get_db_connection()
        query = """
            SELECT v.id, v.fecha, v.total, v.metodo_pago, u.username,
                   COALESCE(c.nombre, 'Cliente general') as cliente_nombre
            FROM ventas v 
            LEFT JOIN usuarios u ON u.id = v.usuario_id 
            LEFT JOIN clientes c ON c.id = v.cliente_id
        """
        params = []
        
        if fecha_desde and fecha_hasta:
            query += " WHERE DATE(v.fecha) BETWEEN ? AND ?"
            params = [fecha_desde, fecha_hasta]
        
        query += " ORDER BY v.fecha DESC"
        
        ventas = conn.execute(query, params).fetchall()
        conn.close()
        
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['ID', 'Fecha', 'Cliente', 'Total', 'Método Pago', 'Usuario'])
        
        for venta in ventas:
            fecha_str = venta['fecha'][:19] if venta['fecha'] else 'N/A'
            writer.writerow([
                venta['id'],
                fecha_str,
                venta['cliente_nombre'],
                f"{venta['total']:.2f}",
                venta['metodo_pago'],
                venta['username']
            ])
        
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        registrar_log("Exportación ventas", "ventas", None, f"Período: {fecha_desde} - {fecha_hasta}")
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=ventas_{timestamp}.csv'
            }
        )
        
    except Exception as e:
        flash(f'Error al exportar ventas: {str(e)}', 'danger')
        return redirect(url_for('ventas'))

# ========== GESTIÓN DE USUARIOS ==========
@app.route('/usuarios')
@requiere_login
def usuarios():
    if session.get('rol') not in ['admin', 'root']:
        flash('No tienes permisos para acceder a esta sección.', 'danger')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    usuarios = conn.execute("SELECT id, username, rol FROM usuarios ORDER BY username").fetchall()
    conn.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/agregar', methods=['POST'])
@requiere_login
def agregar_usuario():
    if session.get('rol') not in ['admin', 'root']:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        username = request.form['username'].strip()
        password = request.form['password']
        rol = request.form['rol']
        
        if not username or not password:
            flash('Nombre de usuario y contraseña son obligatorios.', 'danger')
            return redirect(url_for('usuarios'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), rol)
        )
        usuario_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        registrar_log("Usuario creado", "usuarios", usuario_id, f"Username: {username}, Rol: {rol}")
        flash(f'Usuario {username} creado correctamente.', 'success')
    except sqlite3.IntegrityError:
        flash('El nombre de usuario ya existe.', 'danger')
    except Exception as e:
        flash(f'Error al crear usuario: {str(e)}', 'danger')
    
    return redirect(url_for('usuarios'))

@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@requiere_login
def eliminar_usuario(id):
    if session.get('rol') not in ['admin', 'root']:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('dashboard'))
    
    # No permitir eliminar el propio usuario
    if id == session.get('user_id'):
        flash('No puedes eliminar tu propio usuario.', 'warning')
        return redirect(url_for('usuarios'))
    
    try:
        conn = get_db_connection()
        # Verificar que el usuario existe
        usuario = conn.execute("SELECT username FROM usuarios WHERE id = ?", (id,)).fetchone()
        if not usuario:
            flash('Usuario no encontrado.', 'danger')
            conn.close()
            return redirect(url_for('usuarios'))
        
        # Eliminar usuario
        conn.execute("DELETE FROM usuarios WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        
        registrar_log("Usuario eliminado", "usuarios", id, f"Username: {usuario['username']}")
        flash(f'Usuario "{usuario["username"]}" eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'danger')
    
    return redirect(url_for('usuarios'))

# ========== REPORTES ==========
@app.route('/reportes')
@requiere_login
def reportes():
    conn = get_db_connection()
    
    # Ventas por día (últimos 30 días)
    ventas_diarias = conn.execute("""
        SELECT DATE(fecha) as fecha, COUNT(*) as cantidad, SUM(total) as total
        FROM ventas 
        WHERE fecha >= date('now', '-30 days')
        GROUP BY DATE(fecha)
        ORDER BY fecha DESC
    """).fetchall()
    
    # Productos más vendidos
    productos_vendidos = conn.execute("""
        SELECT p.nombre, SUM(dv.cantidad) as total_vendido, SUM(dv.subtotal) as ingresos
        FROM detalle_ventas dv
        JOIN productos p ON p.id = dv.producto_id
        GROUP BY p.id, p.nombre
        ORDER BY total_vendido DESC
        LIMIT 10
    """).fetchall()
    
    # Métodos de pago
    metodos_pago = conn.execute("""
        SELECT metodo_pago, COUNT(*) as cantidad, SUM(total) as total
        FROM ventas
        WHERE fecha >= date('now', '-30 days')
        GROUP BY metodo_pago
        ORDER BY cantidad DESC
    """).fetchall()
    
    conn.close()
    
    return render_template('reportes.html', 
                         ventas_diarias=ventas_diarias,
                         productos_vendidos=productos_vendidos,
                         metodos_pago=metodos_pago)

# ========== UTILIDADES ==========
@app.route('/productos/cargar_prueba')
@requiere_login
def cargar_productos_prueba():
    """Cargar productos de prueba"""
    if session.get('rol') not in ['admin', 'root']:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('productos'))
    
    productos = [
        ("Coca Cola 500ml", 800, 500, 20, "Bebidas", "7790001001", "Gaseosa sabor cola", 1),
        ("Pepsi 1L", 1200, 700, 15, "Bebidas", "7790001002", "Gaseosa sabor cola", 1),
        ("Agua Mineral", 600, 300, 30, "Bebidas", "7790001003", "Agua mineral sin gas", 1),
        ("Galletitas Oreo", 900, 400, 25, "Alimentos", "7790001004", "Galletitas chocolate", 1),
        ("Yerba Mate La Merced", 2500, 1800, 10, "Alimentos", "7790001005", "Yerba mate suave", 1),
        ("Leche Entera 1L", 1500, 1000, 12, "Alimentos", "7790001006", "Leche entera pasteurizada", 1),
        ("Pan Francés", 400, 200, 50, "Alimentos", "7790001007", "Pan francés fresco", 1),
        ("Arroz Largo Fino 1kg", 1800, 1200, 8, "Alimentos", "7790001008", "Arroz largo fino", 1),
        ("Aceite Girasol Natura", 2200, 1600, 6, "Alimentos", "7790001009", "Aceite de girasol", 1),
        ("Shampoo Sedal 400ml", 3500, 2000, 5, "Cuidado Personal", "7790001010", "Shampoo reparación", 1),
        ("Detergente Skip", 1800, 1100, 8, "Limpieza", "7790001011", "Detergente en polvo", 1),
        ("Papel Higiénico Elite", 2200, 1300, 15, "Cuidado Personal", "7790001012", "Papel higiénico doble hoja", 1)
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    productos_agregados = 0
    
    for nombre, precio, precio_costo, stock, categoria, codigo, descripcion, activo in productos:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO productos 
                (nombre, precio, precio_costo, stock, categoria, codigo_barras, descripcion, activo) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre, precio, precio_costo, stock, categoria, codigo, descripcion, activo))
            if cursor.rowcount > 0:
                productos_agregados += 1
        except Exception as e:
            print(f"Error agregando {nombre}: {e}")
    
    conn.commit()
    conn.close()
    
    registrar_log("Productos de prueba cargados", "productos", None, f"{productos_agregados} productos agregados")
    flash(f'{productos_agregados} productos de prueba cargados correctamente.', 'success')
    return redirect(url_for('productos'))

# ========== MANTENIMIENTO ==========
@app.route('/mantenimiento/limpiar_logs')
@requiere_login
def limpiar_logs():
    """Limpiar logs antiguos"""
    if session.get('rol') not in ['admin', 'root']:
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('configuracion'))
    
    try:
        # Limpiar logs antiguos (más de 90 días)
        conn = get_db_connection()
        resultado = conn.execute("DELETE FROM logs WHERE fecha < date('now', '-90 days')")
        logs_eliminados = resultado.rowcount
        conn.commit()
        conn.close()
        
        registrar_log("Limpieza de logs", "sistema", None, f"{logs_eliminados} logs eliminados")
        flash(f'Limpieza completada. {logs_eliminados} logs antiguos eliminados.', 'success')
    except Exception as e:
        flash(f'Error durante la limpieza: {str(e)}', 'danger')
    
    return redirect(url_for('configuracion'))

# ========== API CAMBIO DE TEMA ==========
@app.route('/api/tema/cambiar', methods=['POST'])
@requiere_login
def cambiar_tema():
    """API para cambiar tema sin recargar página"""
    try:
        modo_oscuro = request.json.get('modo_oscuro', True)
        guardar_configuracion(modo_oscuro=modo_oscuro)
        return jsonify({'success': True, 'modo_oscuro': modo_oscuro})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ========== INFORMACIÓN DEL SISTEMA ==========
@app.route('/api/sistema/info')
@requiere_login
def info_sistema():
    """Obtener información del sistema"""
    try:
        import platform
        import sqlite3 as sql
        
        conn = get_db_connection()
        
        # Estadísticas de la base de datos
        total_productos = conn.execute("SELECT COUNT(*) as count FROM productos WHERE activo = 1").fetchone()['count']
        total_ventas = conn.execute("SELECT COUNT(*) as count FROM ventas").fetchone()['count']
        total_clientes = conn.execute("SELECT COUNT(*) as count FROM clientes").fetchone()['count']
        total_logs = conn.execute("SELECT COUNT(*) as count FROM logs").fetchone()['count']
        
        # Tamaño de la base de datos
        db_size = os.path.getsize(app.config['DATABASE']) if os.path.exists(app.config['DATABASE']) else 0
        db_size_mb = round(db_size / (1024 * 1024), 2)
        
        conn.close()
        
        return jsonify({
            'version': '2.1.0',
            'python_version': platform.python_version(),
            'sistema_operativo': platform.system(),
            'sqlite_version': sql.sqlite_version,
            'base_datos': {
                'tamaño_mb': db_size_mb,
                'productos': total_productos,
                'ventas': total_ventas,
                'clientes': total_clientes,
                'logs': total_logs
            },
            'uptime': 'Sistema funcionando correctamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# =========== FILTROS DE TEMPLATE ===========
@app.template_filter('currency')
def currency_filter(value):
    """Formatear números como moneda"""
    if value is None:
        return "$0.00"
    return f"${value:.2f}"

@app.template_filter('date_format')
def date_format_filter(value):
    """Formatear fechas"""
    if not value:
        return 'N/A'
    
    # Convertir string a datetime si es necesario
    if isinstance(value, str):
        try:
            value = datetime.strptime(value[:19], '%Y-%m-%d %H:%M:%S')
        except:
            return value
    
    return value.strftime('%d/%m/%Y %H:%M')

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Error interno del servidor"), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', 
                         error_code=403, 
                         error_message="No tienes permisos para acceder a este recurso"), 403

# ========== MIDDLEWARE PARA LOGS ==========
@app.before_request
def log_request():
    """Log de requests importantes"""
    if request.method in ['POST', 'PUT', 'DELETE'] and 'user_id' in session:
        endpoint = request.endpoint
        if endpoint in ['crear_producto', 'editar_producto', 'api_pos_procesar_venta', 'agregar_cliente']:
            registrar_log(f"Acceso a {endpoint}", "sistema", None, f"IP: {request.remote_addr}")

if __name__ == '__main__':
    init_db()
    print("🚀 SysTec Ventas v2.1.0 iniciando...")
    print("📂 Base de datos: ventas.db")
    print("👤 Usuario admin: admin | Contraseña: admin123")
    print("🔧 Usuario root: systec_root | Contraseña: qwer1234")
    print("🌐 Servidor: http://localhost:5000")
    print("✅ Eliminada ruta 'nueva_venta' - usar POS")
    print("✅ Mejorada gestión de productos con categorías")
    app.run(debug=True, host='0.0.0.0', port=5000)