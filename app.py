import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Altri Logística", layout="wide")

# 2. CONEXIÓN (La forma más estable)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_users():
    # Usamos SQL simple para traer la tabla. Esto evita el error <Response [200]>
    # Importante: La pestaña en tu Excel debe llamarse 'usuarios'
    query = 'SELECT * FROM "usuarios"'
    return conn.query(query, ttl=0)

# 3. MANEJO DE SESIÓN
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 4. PANTALLA DE ACCESO
if not st.session_state['logged_in']:
    st.title("🚀 Altri Telecom - Logística")
    
    with st.form("login_form"):
        u_input = st.text_input("Usuario")
        p_input = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            try:
                df = load_users()
                
                # Normalizamos nombres de columnas a minúsculas
                df.columns = [c.lower().strip() for c in df.columns]
                
                # Buscamos el usuario
                user_found = df[(df['user'].astype(str) == str(u_input)) & 
                                (df['clave'].astype(str) == str(p_input))]
                
                if not user_found.empty:
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o clave incorrectos")
            except Exception as e:
                st.error(f"Error de conexión: {e}")
                st.info("Asegúrate de que tu Excel tiene una pestaña llamada 'usuarios' con columnas 'user' y 'clave'")

# 5. PANTALLA PRINCIPAL (Una vez dentro)
else:
    st.sidebar.title("Menú Altri")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.header("📦 Panel de Control de Inventario")
    st.success("Conectado con éxito a Google Sheets")
    
    # Aquí mostramos los datos para confirmar que funciona
    if st.button("Cargar Inventario"):
        try:
            datos = load_users()
            st.dataframe(datos)
        except:
            st.warning("No se pudieron cargar los datos adicionales.")
