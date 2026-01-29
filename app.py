import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Altri Logística", layout="wide")

# 2. CONEXIÓN
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(worksheet="usuarios")

# 3. ESTADO DE SESIÓN
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 4. PANTALLA DE LOGIN
if not st.session_state['logged_in']:
    st.title("🚀 Altri Telecom - Inventario")
    with st.form("login_form"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            try:
                df = load_data()
                # Limpieza de datos para comparar
                df['user'] = df['user'].astype(str).str.strip()
                df['clave'] = df['clave'].astype(str).str.strip()
                
                if not df[(df['user'] == u) & (df['clave'] == p)].empty:
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Datos incorrectos")
            except Exception as e:
                st.error(f"Error: {e}")

# 5. PANTALLA PRINCIPAL
else:
    st.sidebar.title("Menú Altri")
    menu = st.sidebar.radio("Ir a:", ["Stock", "Inventario", "IA"])
    
    if menu == "Stock":
        st.header("📦 Panel de Stock")
        st.write("Bienvenido al control de almacén.")
        
    elif menu == "Inventario":
        st.header("📋 Gestión de Equipos")
        if st.button("Actualizar datos"):
            st.dataframe(load_data())

    elif menu == "IA":
        st.header("🤖 Asistente Gemini")
        q = st.text_input("Consulta a la IA:")
        if q:
            st.info("Procesando consulta...")

    if st.sidebar.button("Salir"):
        st.session_state['logged_in'] = False
        st.rerun()
