import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Altri Logística", layout="wide")

# 2. CONEXIÓN CORREGIDA
# Usamos el método directo para evitar el error de Response [200]
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Forzamos la lectura de la hoja 'usuarios' como un DataFrame de Pandas
    try:
        # Intentamos la lectura directa
        df = conn.read(worksheet="usuarios", ttl=0)
        return df
    except Exception:
        # Si falla, intentamos la lectura mediante query (método alternativo)
        return conn.query('SELECT * FROM "usuarios"', ttl=0)

# 3. ESTADO DE SESIÓN
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 4. LOGIN
if not st.session_state['logged_in']:
    st.title("🚀 Altri Telecom - Control de Inventario")
    
    with st.form("login_box"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Iniciar Sesión"):
            try:
                df = load_data()
                # Limpieza de seguridad: convertir todo a texto y quitar espacios
                df.columns = df.columns.str.strip().str.lower()
                df['user'] = df['user'].astype(str).str.strip()
                df['clave'] = df['clave'].astype(str).str.strip()
                
                # Verificación
                user_match = df[(df['user'] == str(u)) & (df['clave'] == str(p))]
                
                if not user_match.empty:
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Credenciales no encontradas en el Excel")
            except Exception as e:
                st.error(f"Error al leer la tabla: {e}")
                st.info("Asegúrate de que la primera fila del Excel tenga los títulos: user y clave")

# 5. PANEL PRINCIPAL (SI EL LOGIN ES CORRECTO)
else:
    st.sidebar.title("Menú Principal")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.header("📦 Gestión de Almacén Altri")
    st.success("Conexión con base de datos establecida.")
    
    if st.button("Ver Inventario"):
        st.dataframe(load_data())
