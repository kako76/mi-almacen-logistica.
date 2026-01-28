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
            df_users = load_data()
            # Verifica si el usuario y clave coinciden en el Excel
            user_match = df_users[(df_users['user'] == user_input) & (df_users['clave'] == pass_input)]
            
            if not user_match.empty:
                st.session_state['logged_in'] = True
                st.success("¡Bienvenido!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

# 3. INTERFAZ PRINCIPAL
if not st.session_state['logged_in']:
    login()
else:
    st.sidebar.title("Menú Altri")
    opcion = st.sidebar.radio("Ir a:", ["Panel de Control", "Inventario", "Asistente IA"])

    if opcion == "Panel de Control":
        st.header("Resumen de Stock")
        # Aquí puedes mostrar gráficos o tablas
        st.write("Bienvenido al sistema de gestión de routers Livebox.")
        
    elif opcion == "Asistente IA":
        st.header("Pregunta a la IA de Altri")
        pregunta = st.text_input("Ej: ¿Cuántos Livebox Infinity tenemos?")
        if pregunta:
            # Aquí se conectaría con tu geminiService.ts
            st.info("La IA está analizando tu inventario...")
            st.write("Respuesta: Tenemos 10 unidades en Almacén Central.")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
