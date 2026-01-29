import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Logística", layout="wide", page_icon="📦")

# ID de TU Google Sheet compartido
SHEET_ID = "173O3NU7o3twRXe3t3NHPLoGVL70mFNyPE-IOORo68Zk"

# --- 2. FUNCIÓN DE LECTURA ---
def cargar_datos(hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={hoja}"
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        # Limpiamos nombres de columnas (quita espacios y pone minúsculas)
        df.columns = [str(c).lower().strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 3. LOGIN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.rol = None

if not st.session_state.usuario:
    st.title("🚀 Acceso Altri Telecom")
    with st.form("login_form"):
        user_input = st.text_input("Usuario (Nombre en el Excel)")
        pass_input = st.text_input("Contraseña (Email en el Excel)", type="password")
        
        if st.form_submit_button("Entrar"):
            df_users = cargar_datos("usuarios")
            if not df_users.empty:
                # Buscamos en 'nombre' (user) y 'email' (clave)
                # Ajustamos según los nombres exactos de tu Excel
                user_col = 'nombre' if 'nombre' in df_users.columns else 'user'
                pass_col = 'email' if 'email' in df_users.columns else 'clave'
                
                match = df_users[(df_users[user_col].astype(str) == user_input) & 
                                 (df_users[pass_col].astype(str) == pass_input)]
                
                if not match.empty:
                    st.session_state.usuario = user_input
                    st.session_state.rol = str(match.iloc[0]['rol']).lower()
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Revisa el Nombre y el Email en tu Excel.")
            else:
                st.error("No se pudo leer la pestaña 'usuarios'. Verifica el nombre en el Excel.")
    st.stop()

# --- 4. INTERFAZ PRINCIPAL ---
rol = st.session_state.rol
usuario = st.session_state.usuario

st.sidebar.title(f"👤 {usuario}")
st.sidebar.info(f"Rol: {rol.upper()}")

# Cargamos los datos de movimientos (que es donde tienes el inventario)
df_mov = cargar_datos("movimientos")

# --- LÓGICA DE PESTAÑAS ---
if rol in ['admin', 'almacen']:
    tabs = st.tabs(["📊 ADMINISTRACIÓN", "📦 ALMACÉN", "🟠 ORANGE", "🟡 MÁSMÓVIL", "👨‍🔧 TÉCNICOS"])

    with tabs[0]:
        st.header("Buscador de Equipos")
        busqueda = st.text_input("Buscar por SN (Número de Serie):")
        if not df_mov.empty:
            if busqueda:
                res = df_mov[df_mov['sn'].astype(str).str.contains(busqueda, case=False, na=False)]
                st.dataframe(res)
            else:
                st.dataframe(df_mov)
        else:
            st.info("No hay datos en la pestaña 'movimientos'.")

    with tabs[1]:
        st.subheader("Gestión de Almacén")
        st.write("Aquí podrás registrar entradas y salidas.")
        if st.button("Descargar Reporte Actual (CSV)"):
            st.download_button("Descargar", df_mov.to_csv(), "inventario.csv")

    with tabs[2]:
        st.header("Stock Orange")
        # Filtramos por marca si existe la columna, o por tipo
        if 'tipo' in df_mov.columns:
            st.dataframe(df_mov[df_mov['tipo'].astype(str).str.contains("Orange", case=False, na=False)])

    with tabs[4]:
        st.header("Equipos Asignados a Técnicos")
        if 'destino' in df_mov.columns:
            # Mostramos todo lo que no sea 'Almacen'
            st.dataframe(df_mov[df_mov['destino'] != 'Almacen'])

elif rol == 'tecnico':
    st.title(f"Panel de Técnico: {usuario}")
    if not df_mov.empty and 'destino' in df_mov.columns:
        mi_material = df_mov[df_mov['destino'].astype(str) == usuario]
        st.subheader("Mi Material Asignado")
        st.dataframe(mi_material)
    else:
        st.warning("No tienes material asignado en la columna 'destino'.")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.usuario = None
    st.rerun()
