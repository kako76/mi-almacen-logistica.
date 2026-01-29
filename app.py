import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Altri Logística - Inventario", layout="wide")

# 2. CONEXIÓN CON EL EXCEL
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Lee la pestaña 'usuarios' del Excel
    return conn.read(worksheet="usuarios")

# 3. SISTEMA DE LOGIN
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    st.title("🚀 Altri Telecom - Control de Inventario")
    with st.form("login_form"):
        user_input = st.text_input("Usuario")
        pass_input = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            try:
                df_users = load_data()
                # Limpiamos espacios y convertimos a texto para comparar bien
                df_users['user'] = df_users['user'].astype(str).str.strip()
                df_users['clave'] = df_users['clave'].astype(str).str.strip()
                
                user_match = df_users[(df_users['user'] == user_input) & (df_users['clave'] == str(pass_input))]
                
                if not user_match.empty:
                    st.session_state['logged_in'] = True
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
            except Exception as e:
                st.error(f"Error de conexión con Excel: {e}")

# 4. INTERFAZ PRINCIPAL
if not st.session_state['logged_in']:
    login()
else:
    st.sidebar.title("Menú Altri")
    opcion = st.sidebar.radio("Ir a:", ["Panel de Control", "Inventario", "Asistente IA"])

    if opcion == "Panel de Control":
        st.header("Resumen de Stock")
        st.write("Bienvenido al sistema de gestión de materiales de Altri Telecom.")
        st.info("Conexión con Excel: ACTIVA ✅")
        
    elif opcion == "Inventario":
        st.header("Gestión de Equipos")
        st.write("Cargando base de datos de materiales...")
        # Aquí puedes añadir un botón para ver los datos del Excel
        if st.button("Ver lista de usuarios"):
            st.dataframe(load_data())

    elif opcion == "Asistente IA":
        st.header("Asistente Inteligente Gemini")
        pregunta = st.text_input("Haz una consulta sobre el stock:")
        if pregunta:
            st.info("La IA está analizando tu inventario...")
            st.write("Pronto integraremos las respuestas detalladas aquí.")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
