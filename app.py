import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Altri Logística", layout="wide")

# 2. CONFIGURACIÓN DEL ENLACE (Vía Directa)
# Sustituye el ID si es diferente, pero este es el de tu captura:
SHEET_ID = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"
SHEET_NAME = "usuarios"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

def load_data():
    # Leemos el Excel directamente como un CSV de internet
    return pd.read_csv(URL)

# 3. ESTADO DE SESIÓN
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 4. LOGIN
if not st.session_state['logged_in']:
    st.title("🚀 Altri Telecom - Logística")
    
    with st.form("login_form"):
        u = st.text_input("Usuario").strip()
        p = st.text_input("Contraseña", type="password").strip()
        
        if st.form_submit_button("Entrar"):
            try:
                df = load_data()
                # Limpiar nombres de columnas
                df.columns = [c.lower().replace(" ", "") for c in df.columns]
                
                # Buscar coincidencia
                valido = df[(df['user'].astype(str) == str(u)) & 
                            (df['clave'].astype(str) == str(p))]
                
                if not valido.empty:
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")
            except Exception as e:
                st.error(f"Error al conectar: {e}")
                st.info("Asegúrate de que el Excel esté compartido como 'Cualquier persona con el enlace'")

# 5. PANTALLA PRINCIPAL
else:
    st.sidebar.success("Conectado")
    if st.sidebar.button("Salir"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.header("📦 Gestión de Almacén Altri")
    st.write("Datos cargados correctamente desde el Excel compartido.")
    
    if st.button("Ver Inventario"):
        st.dataframe(load_data())
