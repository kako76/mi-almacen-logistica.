import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri ERP", layout="wide", page_icon="🏢")

# --- CONEXIÓN DIRECTA (TÉCNICA DE EXPORTACIÓN CSV) ---
# Usamos el ID de tu hoja para construir URLs de descarga directa
SHEET_ID = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"

def load_data(sheet_name):
    """Carga una pestaña específica usando la exportación a CSV de Google"""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        # Forzamos la lectura ignorando errores de líneas malas
        return pd.read_csv(url, on_bad_lines='skip')
    except Exception as e:
        # Si falla, devolvemos un DataFrame vacío para que la app no se rompa
        return pd.DataFrame()

# --- FUNCIONES DE ALBARÁN ---
def generar_pdf(tecnico, items):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "ALTRI TELECOM - ALBARÁN DE TRASPASO")
    c.setFont("Helvetica", 10)
    c.drawString(50, 780, f"Destinatario: {tecnico} | Fecha: {datetime.now().strftime('%d/%m/%Y')}")
    y = 750
    for item in items:
        c.drawString(50, y, f"- SN: {item['sn']} | Modelo: {item['modelo']}")
        y -= 20
    c.save()
    buf.seek(0)
    return buf

# --- LOGIN ---
if 'user' not in st.session_state:
    st.title("🚀 Altri Telecom - Acceso")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.form_submit_button("Entrar"):
            # Cargamos usuarios directamente
            df_u = load_data("usuarios")
            
            if not df_u.empty:
                # Normalizamos columnas (minusculas y sin espacios)
                df_u.columns = [c.lower().strip() for c in df_u.columns]
                
                # Buscamos coincidencia (convertimos todo a string para evitar errores de números)
                user_row = df_u[(df_u['user'].astype(str) == str(u)) & 
                                (df_u['clave'].astype(str) == str(p))]
                
                if not user_row.empty:
                    st.session_state.user = u
                    # Guardamos el rol (si existe la columna, si no, por defecto admin)
                    st.session_state.rol = user_row.iloc[0]['rol'] if 'rol' in user_row.columns else 'admin'
                    st.rerun()
                else:
                    st.error("❌ Usuario o clave incorrectos")
            else:
                st.error("⚠️ No se pudo conectar con el Excel. Revisa los permisos.")
    st.stop()

# --- INTERFAZ SEGÚN ROL ---
rol = st.session_state.rol
user_act = st.session_state.user

st.sidebar.title(f"Usuario: {user_act}")
st.sidebar.info(f"Rol: {rol.upper()}")

# --- LOGICA DE PESTAÑAS ---
if rol in ['admin', 'almacen']:
    tabs = st.tabs(["📊 Administración", "📦 Almacén", "👨‍🔧 Técnicos", "👥 Usuarios", "🟠 Orange", "🟡 MásMóvil"])
    
    # Cargar inventario una sola vez
    df_inv = load_data("inventario")
    df_inv.columns = [c.lower().strip() for c in df_inv.columns]

    # 1. ADMINISTRACIÓN
    with tabs[0]:
        st.header("Rastreo Global de Material")
        sn_search = st.text_input("🔍 Buscar Número de Serie (SN)")
        
        if not df_inv.empty:
            if sn_search:
                # Filtro insensible a mayúsculas/minúsculas
                res = df_inv[df_inv['sn'].astype(str).str.contains(sn_search, case=False, na=False)]
                st.dataframe(res, use_container_width=True)
            else:
                st.dataframe(df_inv, use_container_width=True)
        else:
            st.warning("La pestaña 'inventario' está vacía o no existe en el Excel.")

    # 2. ALMACÉN
    with tabs[1]:
        st.header("Gestión de Almacén")
        col_in, col_out = st.columns(2)
        with col_in:
            st.subheader("Entrada de Material")
            new_sn = st.text_input("Nuevo SN")
            new_mod = st.selectbox("Modelo", ["Livebox 6", "Livebox 7", "Infinity", "ONT ZTE"])
            if st.button("Registrar"):
                st.info("Para guardar datos reales, necesitamos configurar la API de escritura (Google Cloud Console).")
        
        with col_out:
            st.subheader("Traspaso a Técnico")
            df_u = load_data("usuarios")
            if not df_u.empty:
                df_u.columns = [c.lower().strip() for c in df_u.columns]
                tecs = df_u[df_u['rol'] == 'tecnico']['user'].tolist() if 'rol' in df_u.columns else []
                dest = st.selectbox("Seleccionar Técnico", tecs)
                sn_out = st.text_input("SN a entregar")
                if st.button("Generar Albarán"):
                    pdf = generar_pdf(dest, [{"sn": sn_out, "modelo": "Generico"}])
                    st.download_button("Descargar PDF", pdf, f"albaran_{sn_out}.pdf")

    # 3. TÉCNICOS (VISTA ADMIN)
    with tabs[2]:
        st.header("Material en poder de técnicos")
        if not df_inv.empty and 'ubicacion' in df_inv.columns:
            st.dataframe(df_inv[df_inv['ubicacion'] != 'Almacén'])

    # 4. USUARIOS
    with tabs[3]:
        df_u = load_data("usuarios")
        st.dataframe(df_u)

    with tabs[4]: st.header("Stock Orange")
    with tabs[5]: st.header("Stock MásMóvil")

# --- VISTA TÉCNICO ---
elif rol == 'tecnico':
    t_tabs = st.tabs(["📦 Mi Material", "🔄 Traspaso", "✅ Instalaciones"])
    
    df_inv = load_data("inventario")
    if not df_inv.empty:
        df_inv.columns = [c.lower().strip() for c in df_inv.columns]
        
    with t_tabs[0]:
        st.header(f"Equipos de {user_act}")
        if not df_inv.empty and 'ubicacion' in df_inv.columns:
            # Filtramos por el nombre del usuario actual
            mis_equipos = df_inv[df_inv['ubicacion'].astype(str) == str(user_act)]
            st.dataframe(mis_equipos)
        else:
            st.info("No tienes material asignado o la columna 'ubicacion' falta en el Excel.")

if st.sidebar.button("Cerrar Sesión"):
    del st.session_state.user
    st.rerun()
