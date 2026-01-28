import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Telecom - Sistema Pro", layout="wide")

# --- CONEXIÓN Y REPARACIÓN DE BASE DE DATOS ---
def init_db():
    # Usamos v4 para asegurar una base limpia y sin errores de acceso
    conn = sqlite3.connect('altri_final_v4.db', check_same_thread=False)
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

# --- SISTEMA DE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso Altri Telecom")
    col1, _ = st.columns([1, 1])
    with col1:
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
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.title(f"👤 {st.session_state.nombre}")
if st.session_state.perfil == 'admin':
    menu = st.sidebar.radio("Panel Admin", ["📊 Stock Global", "🔍 Rastreador S/N", "📥 Entrada Almacén", "🚚 Asignación", "👥 Gestión Técnicos", "📑 Historial Completo"])
else:
    menu = st.sidebar.radio("Panel Técnico", ["🎒 Mi Mochila", "✅ Instalar Equipo", "⚠️ Reportar Defectuoso"])

# --- LÓGICA ADMIN ---
if menu == "📊 Stock Global":
    st.header("Inventario Completo")
    df = pd.read_sql_query("SELECT * FROM stock", conn)
    st.dataframe(df, use_container_width=True)

elif menu == "🔍 Rastreador S/N":
    st.header("Buscador de Equipos")
    busqueda = st.text_input("Introduce S/N para ver su historial")
    if busqueda:
        c.execute("SELECT * FROM stock WHERE sn=?", (busqueda,))
        item = c.fetchone()
        if item:
            st.write(f"**Estado Actual:** {item[3]} | **Localización:** {item[4]}")
            st.subheader("Movimientos")
            hist = pd.read_sql_query(f"SELECT * FROM movimientos WHERE sn='{busqueda}' ORDER BY id DESC", conn)
            st.table(hist)
        else: st.error("No se encuentra ese S/N")

elif menu == "📥 Entrada Almacén":
    st.header("Entrada de Material")
    marca = st.selectbox("Marca", ["ORANGE", "MASMOVIL"])
    mod = st.text_input("Modelo del equipo")
    sns = st.text_area("Números de Serie (uno por línea)")
    if st.button("Guardar en Almacén"):
        for s in sns.split('\n'):
            sn_clean = s.strip()
            if sn_clean:
                c.execute("INSERT OR REPLACE INTO stock VALUES (?,?,?,?,?,?)", 
                         (sn_clean, mod, marca, "Almacén", "ALMACEN", datetime.now().strftime("%d/%m/%Y")))
                registrar_movimiento(sn_clean, "Entrada Almacén", "Proveedor", "ALMACEN", st.session_state.nombre)
        st.success("Material cargado")

elif menu == "🚚 Asignación":
    st.header("Entregar a Técnico")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecs = [t[0] for t in c.fetchall()]
    if not tecs:
        st.warning("Primero crea técnicos en 'Gestión Técnicos'")
    else:
        tec_dest = st.selectbox("Selecciona Técnico", tecs)
        df_disp = pd.read_sql_query("SELECT sn, modelo FROM stock WHERE estado='Almacén'", conn)
        seleccionados = st.multiselect("Equipos a entregar", df_disp['sn'].tolist())
        if st.button("Confirmar Entrega"):
            for s in seleccionados:
                c.execute("UPDATE stock SET estado='En Mochila', poseedor=? WHERE sn=?", (tec_dest, s))
                registrar_movimiento(s, "Asignación", "ALMACEN", tec_dest, st.session_state.nombre)
            st.success(f"Asignados a {tec_dest}")

elif menu == "👥 Gestión Técnicos":
    st.header("Control de Personal")
    with st.expander("➕ Añadir Nuevo Técnico"):
        n_user = st.text_input("Usuario (Login)")
        n_nombre = st.text_input("Nombre Completo")
        n_pass = st.text_input("Contraseña")
        if st.button("Registrar Técnico"):
            if n_user and n_nombre and n_pass:
                c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,'tecnico')", (n_user, n_nombre, n_pass))
                conn.commit()
                st.success(f"Técnico {n_nombre} creado")
                st.rerun()
    
    st.subheader("Lista de Personal")
    usuarios_df = pd.read_sql_query("SELECT user as Login, nombre as Nombre FROM usuarios WHERE perfil='tecnico'", conn)
    st.dataframe(usuarios_df)
    
    borrar = st.text_input("Escribe el Login para eliminar")
    if st.button("❌ Eliminar Usuario"):
        if borrar != 'admin':
            c.execute("DELETE FROM usuarios WHERE user=?", (borrar,))
            conn.commit()
            st.rerun()

elif menu == "📑 Historial Completo":
    st.header("
