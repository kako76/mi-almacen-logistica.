import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Altri Telecom - Logística", layout="wide")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('altri_v5.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (user TEXT PRIMARY KEY, nombre TEXT, clave TEXT, perfil TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stock 
                 (sn TEXT PRIMARY KEY, modelo TEXT, marca TEXT, estado TEXT, poseedor TEXT, fecha_actualizacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sn TEXT, tipo TEXT, origen TEXT, destino TEXT, fecha TEXT, usuario_accion TEXT)''')
    c.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios VALUES ('admin', 'Administrador', '1234', 'admin')")
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

def registrar_movimiento(sn, tipo, origen, destino, usuario):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO movimientos (sn, tipo, origen, destino, fecha, usuario_accion) VALUES (?,?,?,?,?,?)",
              (sn, tipo, origen, destino, fecha, usuario))
    conn.commit()

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso Altri Telecom")
    u_input = st.text_input("Usuario")
    p_input = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        c.execute("SELECT nombre, perfil FROM usuarios WHERE user=? AND clave=?", (u_input, p_input))
        res = c.fetchone()
        if res:
            st.session_state.auth = True
            st.session_state.usuario_id = u_input
            st.session_state.nombre = res[0]
            st.session_state.perfil = res[1]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- INTERFAZ ---
st.sidebar.title(f"👤 {st.session_state.nombre}")
if st.session_state.perfil == 'admin':
    menu = st.sidebar.radio("Menú Admin", ["📊 Stock Global", "🔍 Rastreador S/N", "📥 Entrada Almacén", "🚚 Asignación", "👥 Gestión Técnicos", "📑 Historial"])
else:
    menu = st.sidebar.radio("Menú Técnico", ["🎒 Mi Mochila", "✅ Instalar", "⚠️ Defectuoso"])

# --- FUNCIONES ADMIN ---
if menu == "📊 Stock Global":
    st.header("Inventario Completo")
    df = pd.read_sql_query("SELECT * FROM stock", conn)
    st.dataframe(df, use_container_width=True)

elif menu == "🔍 Rastreador S/N":
    st.header("Buscador de Equipos")
    busqueda = st.text_input("Introduce S/N")
    if busqueda:
        c.execute("SELECT * FROM stock WHERE sn=?", (busqueda,))
        item = c.fetchone()
        if item:
            st.write(f"Estado: {item[3]} | Poseedor: {item[4]}")
            hist = pd.read_sql_query(f"SELECT * FROM movimientos WHERE sn='{busqueda}' ORDER BY id DESC", conn)
            st.table(hist)
        else: st.error("No encontrado")

elif menu == "📥 Entrada Almacén":
    st.header("Entrada de Material")
    marca = st.selectbox("Operadora", ["ORANGE", "MASMOVIL"])
    mod = st.text_input("Modelo")
    sns = st.text_area("S/N (uno por línea)")
    if st.button("Cargar"):
        for s in sns.split('\n'):
            if s.strip():
                c.execute("INSERT OR REPLACE INTO stock VALUES (?,?,?,?,?,?)", 
                         (s.strip(), mod, marca, "Almacén", "ALMACEN", datetime.now().strftime("%d/%m/%Y")))
                registrar_movimiento(s.strip(), "Entrada", "Proveedor", "ALMACEN", st.session_state.nombre)
        st.success("
