import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuración profesional
st.set_page_config(page_title="Altri Telecom - Logística Avanzada", layout="wide")

# Conexión a Base de Datos
conn = sqlite3.connect('altri_v2.db', check_same_thread=False)
c = conn.cursor()

# Tablas necesarias
c.execute('CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, nombre TEXT, clave TEXT, perfil TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS stock (sn TEXT PRIMARY KEY, modelo TEXT, estado TEXT, poseedor TEXT, fecha TEXT)')
conn.commit()

# Insertar admin inicial
c.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'Administrador', '1234', 'admin')")
conn.commit()

# --- INTERFAZ DE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso Altri Telecom")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        c.execute("SELECT perfil FROM usuarios WHERE user=? AND clave=?", (u, p))
        res = c.fetchone()
        if res:
            st.session_state.auth = True
            st.session_state.perfil = res[0]
            st.rerun()
    st.stop()

# --- MENÚ SUPERIOR (Estilo el código React que pasaste) ---
st.title("🚀 Altri Telecom | Gestión de Inventario")
menu = st.tabs(["📊 Dashboard", "📥 Entradas", "🚚 Asignación", "🛠️ Servicio Técnico", "👥 Personal"])

with menu[0]: # Dashboard
    st.header("Inventario Global")
    df = pd.read_sql_query("SELECT * FROM stock", conn)
    st.dataframe(df, use_container_width=True)

with menu[1]: # Entradas
    st.header("Entrada de Material Nuevo")
    mod = st.selectbox("Modelo", ["ZTE Livebox 7", "Arcadyan L6", "ONT Nokia", "Acometida 80m"])
    sns = st.text_area("Pega los S/N (uno por línea)")
    if st.button("Registrar en Almacén"):
        lista = sns.split('\n')
        for s in lista:
            if s.strip():
                c.execute("INSERT OR REPLACE INTO stock VALUES (?, ?, ?, ?, ?)", 
                         (s.strip(), mod, "Disponible", "ALMACEN", datetime.now().strftime("%d/%m/%Y")))
        conn.commit()
        st.success("Equipos registrados")

with menu[2]: # Asignación
    st.header("Entrega a Técnicos / Traspasos")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecs = [t[0] for t in c.fetchall()]
    dest = st.selectbox("Destinatario", tecs)
    sn_ent = st.text_input("S/N del equipo a entregar")
    if st.button("Confirmar Entrega"):
        c.execute("UPDATE stock SET estado='En Técnico', poseedor=? WHERE sn=?", (dest, sn_ent))
        conn.commit()
        st.info(f"Equipo {sn_ent} entregado a {dest}")

with menu[3]: # Servicio Técnico (Función Defectuosos del código React)
    st.header("Gestión de Equipos Defectuosos")
    sn_def = st.text_input("S/N del equipo averiado")
    if st.button("Reportar como Malo"):
        c.execute("UPDATE stock SET estado='DEFECTUOSO', poseedor='TALLER' WHERE sn=?", (sn_def,))
        conn.commit()
        st.warning(f"Equipo {sn_def} enviado a revisión técnica")

with menu[4]: # Personal
    if st.session_state.perfil == "admin":
        st.header("Alta de Técnicos")
        n_u = st.text_input("ID Login")
        n_n = st.text_input("Nombre Real")
        n_c = st.text_input("Clave")
        if st.button("Crear Usuario"):
            c.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (n_u, n_n, n_c, 'tecnico'))
            conn.commit()
            st.success("Técnico creado")
