# LicenciasSysTec.py actualizado con superusuario y expiración de prueba
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'systec-licencias-2025'
DATABASE = 'licencias.db'

# ====== DB INIT ======
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT DEFAULT 'user',
        fecha_inicio DATE,
        dias_licencia INTEGER,
        ilimitado INTEGER DEFAULT 0
    )
    ''')

    # Superusuario fijo (systec_root)
    c.execute("""
    INSERT OR IGNORE INTO usuarios (username, password_hash, rol, fecha_inicio, dias_licencia, ilimitado)
    VALUES (?, ?, 'superuser', ?, NULL, 1)
    """, ('systec_root', generate_password_hash('qwer1234'), datetime.now().date()))

    # Usuario demo por 7 días
    c.execute("""
    INSERT OR IGNORE INTO usuarios (username, password_hash, rol, fecha_inicio, dias_licencia, ilimitado)
    VALUES (?, ?, 'admin', ?, 7, 0)
    """, ('admin', generate_password_hash('admin123'), datetime.now().date()))

    conn.commit()
    conn.close()

# ====== CONEXIÓN DB ======
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ====== LOGIN ======
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM usuarios WHERE username = ?", (u,)).fetchone()

        if user and check_password_hash(user['password_hash'], p):
            if not user['ilimitado']:
                dias = int(user['dias_licencia'] or 0)
                inicio = datetime.strptime(user['fecha_inicio'], '%Y-%m-%d')
                expiracion = inicio + timedelta(days=dias)
                if datetime.now().date() > expiracion.date():
                    flash("Licencia expirada. Contacte con soporte.", "error")
                    return redirect(url_for('login'))
                else:
                    dias_restantes = (expiracion.date() - datetime.now().date()).days
                    flash(f"Licencia válida por {dias_restantes} días", "success")
            else:
                flash("Licencia ilimitada activa.", "success")
            session['usuario'] = user['username']
            session['rol'] = user['rol']
            return redirect(url_for('panel'))
        else:
            flash("Credenciales incorrectas", "error")
    return render_template('login_licencias.html')

# ====== PANEL PRINCIPAL ======
@app.route('/panel')
def panel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    usuarios = conn.execute("SELECT * FROM usuarios").fetchall()
    return render_template('panel_licencias.html', usuarios=usuarios)

@app.route('/crear', methods=['GET', 'POST'])
def crear():
    if session.get('rol') != 'superuser':
        return redirect(url_for('panel'))
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        dias = int(request.form['dias'] or 0)
        ilimitado = 1 if 'ilimitado' in request.form else 0

        conn = get_db()
        try:
            conn.execute("""
            INSERT INTO usuarios (username, password_hash, rol, fecha_inicio, dias_licencia, ilimitado)
            VALUES (?, ?, 'user', ?, ?, ?)""",
            (u, generate_password_hash(p), datetime.now().date(), dias, ilimitado))
            conn.commit()
            flash("Licencia creada con éxito", "success")
        except sqlite3.IntegrityError:
            flash("Ese usuario ya existe", "error")
    return redirect(url_for('panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
