import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Altri Logística", layout="wide")

# 2. ENLACE DIRECTO (CUIDADO: Revisa que este ID sea el de tu Excel actual)
SHEET_ID = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=usuarios"

def load_data():
    # Esta función ahora es más "valiente" al leer
    try:
        df = pd.read_csv(URL)
        # Limpieza de columnas
        df.columns = [c.lower().strip() for c in df.columns]
        return df
    except Exception as e:
        # Esto nos dirá si el problema es el enlace o el nombre de la pestaña
        st.error(f"Error técnico: {e}")
        return None

# 3. LÓGICA DE LOGIN
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚀 Altri Telecom - Acceso")
    with st.form("login"):
        u = st.text_input("Usuario").strip()
        p = st.text_input("Contraseña", type="password").strip()
        if st.form_submit_button("Entrar"):
            df = load_data()
            if df is not None:
                # Buscamos al usuario
                match = df[(df['user'].astype(str) == str(u)) & (df['clave'].astype(str) == str(p))]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o clave no coinciden en el Excel")
            else:
                st.warning("⚠️ No se pudo acceder al archivo. ¿Está compartido como 'Cualquier persona con el enlace'?")

else:
    st.success("¡Bienvenido al sistema Altri!")
    if st.sidebar.button("Salir"):
        st.session_state.logged_in = False
        st.rerun()
        st.write("Crea el documento de entrega para el técnico.")
        nombre_tecnico = st.selectbox("Selecciona Técnico", ["Admin", "Técnico 1", "Técnico 2"])
        if st.button("Generar Albarán"):
            st.info(f"Generando Albarán para {nombre_tecnico}...")
            # Aquí se integraría la lógica de pdfService.ts
