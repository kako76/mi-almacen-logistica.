import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Logística Orange/MásMóvil", layout="wide")

# --- BASE DE DATOS LOCAL ---
def init_db():
    conn = sqlite3.connect('almacen.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS tecnicos (nombre TEXT PRIMARY KEY)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock 
                      (sn TEXT PRIMARY KEY, operadora TEXT, categoria TEXT, modelo TEXT, poseedor TEXT, fecha TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- LISTA DE MATERIALES (TUS FOTOS) ---
materiales_movistar_orange = {
    "ROUTERS/ONT": ["ARCADYAN LIVEBOX 6", "ZTE LIVEBOX 7", "ZTE H3640 Wifi 6", "Nokia G-010G-P", "Sagemcom 5670"],
    "DECOS TV": ["STB Android TV 4K", "Technicolor Jade", "Kaon KSTB7259"],
    "ACOMETIDAS": ["Interior 20m", "Interior 40m", "Exterior 50m", "Exterior 80m", "Exterior 100m"]
}

# --- LOGIN SIMPLE ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso Almacén")
    user = st.text_input("Usuario")
    passw = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if user == "admin" and passw == "1234":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- MENÚ ---
st.title("📦 Gestión de Inventario")
menu = st.sidebar.radio("Navegación", ["Entrada Material", "Entrega a Técnico", "Ver Inventario", "Gestionar Técnicos"])

if menu == "Entrada Material":
    st.header("📥 Alta de nuevo material")
    op = st.selectbox("Operadora", ["ORANGE", "MASMOVIL"])
    cat = st.selectbox("Categoría", list(materiales_movistar_orange.keys()))
    mod = st.selectbox("Modelo", materiales_movistar_orange[cat])
    sn = st.text_input("Número de Serie (S/N)")
    
    if st.button("Guardar en Almacén"):
        try:
            cursor = conn.cursor()
            fecha = datetime.now().strftime("%d/%m/%Y")
            cursor.execute("INSERT INTO stock VALUES (?,?,?,?,?,?)", (sn, op, cat, mod, "ALMACEN", fecha))
            conn.commit()
            st.success(f"Registrado: {mod} ({sn})")
        except:
            st.error("Ese S/N ya existe en el sistema.")

elif menu == "Entrega a Técnico":
    st.header("📤 Entrega de material")
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM tecnicos")
    lista_t = [r[0] for r in cursor.fetchall()]
    
    tec = st.selectbox("Selecciona al Técnico", lista_t)
    sns = st.text_area("Pega aquí los S/N (separados por espacio o coma)")
    
    if st.button("Asignar Material"):
        lista_sns = [s.strip() for s in sns.replace(",", " ").split() if s.strip()]
        for s in lista_sns:
            conn.cursor().execute("UPDATE stock SET poseedor=? WHERE sn=?", (tec, s))
        conn.commit()
        st.success(f"Material asignado a {tec}")

elif menu == "Ver Inventario":
    st.header("📊 Stock Actual")
    df = pd.read_sql_query("SELECT * FROM stock", conn)
    st.dataframe(df)

elif menu == "Gestionar Técnicos":
    st.header("👥 Alta de Técnicos")
    nuevo_t = st.text_input("Nombre del técnico")
    if st.button("Añadir"):
        try:
            conn.cursor().execute("INSERT INTO tecnicos VALUES (?)", (nuevo_t,))
            conn.commit()
            st.success("Técnico añadido")
        except: st.error("Ya existe")
