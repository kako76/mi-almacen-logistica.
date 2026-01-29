import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Altri Logística", layout="wide")

# 2. CONEXIÓN REFORZADA
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Usamos ttl=0 para que siempre traiga datos frescos del Excel
    # Agregamos .query() para forzar la conversión de la respuesta a DataFrame
    df = conn.read(worksheet="usuarios", ttl=0)
    return df

# 3. ESTADO DE SESIÓN
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 4. LÓGICA DE ACCESO
if not st.session_state['logged_in']:
    st.title("🚀 Altri Telecom - Inventario")
    st.subheader("Acceso al Sistema")
    
    with st.form("login_form"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        boton = st.form_submit_button("Entrar")
        
        if boton:
            try:
                df = load_data()
                # Aseguramos que los datos sean tratados como texto
                df['user'] = df['user'].astype(str).str.strip()
                df['clave'] = df['clave'].astype(str).str.strip()
                
                # Buscamos coincidencia
                match = df[(df['user'] == u) & (df['clave'] == str(p))]
                
                if not match.empty:
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o clave incorrectos")
            except Exception as e:
                st.error(f"Error crítico de conexión: {e}")
                st.info("Revisa que la pestaña del Excel se llame exactamente 'usuarios'")

# 5. APLICACIÓN FUNCIONANDO
else:
    st.sidebar.success(f"Conectado como: Admin")
    menu = st.sidebar.radio("Navegación", ["Inicio", "Inventario Real-Time", "Asistente IA"])
    
    if menu == "Inicio":
        st.header("📦 Panel de Control Altri")
        st.write("El sistema está conectado correctamente con Google Sheets.")
        
    elif menu == "Inventario Real-Time":
        st.header("📋 Equipos en Stock")
        if st.button("Refrescar Inventario"):
            st.dataframe(load_data())

    elif menu == "Asistente IA":
        st.header("🤖 Consultas Inteligentes")
        st.write("Usa la IA para analizar los movimientos de stock.")
        q = st.text_input("¿Qué quieres saber?")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
