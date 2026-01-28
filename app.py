import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Altri Logística - Inventario", layout="wide")

# 1. CONEXIÓN CON EL EXCEL
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Lee la pestaña 'usuarios' del Excel
    return conn.read(worksheet="usuarios")

# 2. SISTEMA DE LOGIN
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
                # Verifica si el usuario y clave coinciden en el Excel
                user_match = df_users[(df_users['user'] == user_input) & (df_users['clave'].astype(str) == str(pass_input))]
                
                if not user_match.empty:
                    st.session_state['logged_in'] = True
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

# 3. INTERFAZ PRINCIPAL
if not st.session_state['logged_in']:
    login()
else:
    st.sidebar.title("Menú Altri")
    opcion = st.sidebar.radio("Ir a:", ["Panel de Control", "Inventario", "Asistente IA"])

    if opcion == "Panel de Control":
        st.header("Resumen de Stock")
        st.write("Bienvenido al sistema de gestión de materiales de Altri Telecom.")
        
    elif opcion == "Inventario":
        st.header("Gestión de Equipos")
        st.info("Aquí podrás registrar entradas y salidas de routers.")

    elif opcion == "Asistente IA":
        st.header("Asistente Inteligente Gemini")
        pregunta = st.text_input("Haz una consulta sobre el stock:")
        if pregunta:
            st.info("La IA está consultando el Excel...")
            st.write("Respuesta: Conexión establecida correctamente con la base de datos.")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
