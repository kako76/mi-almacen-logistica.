import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri ERP", layout="wide", page_icon="🏢")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CARGA DE DATOS ---
def load_all_data():
    users = conn.read(worksheet="usuarios")
    inv = conn.read(worksheet="inventario")
    return users, inv

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
            df_u, _ = load_all_data()
            user_row = df_u[(df_u['user'] == u) & (df_u['clave'] == str(p))]
            if not user_row.empty:
                st.session_state.user = u
                st.session_state.rol = user_row.iloc[0]['rol']
                st.rerun()
            else:
                st.error("Error de acceso")
    st.stop()

# --- INTERFAZ SEGÚN ROL ---
rol = st.session_state.rol
user_act = st.session_state.user

st.sidebar.title(f"Usuario: {user_act}")
st.sidebar.info(f"Rol: {rol.upper()}")

# --- LOGICA DE PESTAÑAS ---
if rol in ['admin', 'almacen']:
    tabs = st.tabs(["📊 Administración", "📦 Almacén", "👨‍🔧 Técnicos", "👥 Usuarios", "🟠 Orange", "🟡 MásMóvil"])
    
    # 1. ADMINISTRACIÓN
    with tabs[0]:
        st.header("Rastreo Global de Material")
        sn_search = st.text_input("🔍 Buscar Número de Serie (SN)")
        _, inv = load_all_data()
        if sn_search:
            res = inv[inv['sn'].str.contains(sn_search, na=False)]
            st.dataframe(res)
        else:
            st.dataframe(inv)

    # 2. ALMACÉN
    with tabs[1]:
        st.header("Gestión de Almacén")
        col_in, col_out = st.columns(2)
        with col_in:
            st.subheader("Entrada de Material")
            new_sn = st.text_input("Nuevo SN")
            new_mod = st.selectbox("Modelo", ["Livebox 6", "Livebox 7", "Infinity", "ONT ZTE"])
            new_brand = st.selectbox("Marca", ["Orange", "MasMovil"])
            if st.button("Registrar en Almacén"):
                st.success(f"Equipo {new_sn} registrado")
        
        with col_out:
            st.subheader("Traspaso a Técnico")
            df_u, _ = load_all_data()
            tecs = df_u[df_u['rol'] == 'tecnico']['user'].tolist()
            dest = st.selectbox("Seleccionar Técnico", tecs)
            sn_out = st.text_input("SN a entregar")
            if st.button("Generar Albarán y Traspasar"):
                pdf = generar_pdf(dest, [{"sn": sn_out, "modelo": "Equipo Altri"}])
                st.download_button("Descargar Albarán", pdf, "albaran.pdf")

    # 3. TÉCNICOS (VISTA ADMIN)
    with tabs[2]:
        st.header("Estado de la Red de Técnicos")
        _, inv = load_all_data()
        st.write("Material en posesión de técnicos:")
        st.dataframe(inv[inv['ubicacion'] != 'Almacén'])

    # 4. USUARIOS
    with tabs[3]:
        st.header("Gestión de Personal")
        df_u, _ = load_all_data()
        st.table(df_u[['user', 'rol']])

    # 5 y 6. MARCAS
    with tabs[4]: st.header("Stock Orange")
    with tabs[5]: st.header("Stock MásMóvil")

# --- VISTA TÉCNICO ---
elif rol == 'tecnico':
    t_tabs = st.tabs(["📦 Mi Material", "🔄 Traspaso entre Técnicos", "✅ Instalado"])
    
    with t_tabs[0]:
        st.header(f"Equipos asignados a {user_act}")
        _, inv = load_all_data()
        mis_equipos = inv[inv['ubicacion'] == user_act]
        st.dataframe(mis_equipos)

    with t_tabs[1]:
        st.header("Enviar material a otro compañero")
        df_u, _ = load_all_data()
        otros_tecs = df_u[(df_u['rol'] == 'tecnico') & (df_u['user'] != user_act)]['user'].tolist()
        compañero = st.selectbox("Compañero", otros_tecs)
        sn_trap = st.text_input("SN a traspasar")
        if st.button("Confirmar Traspaso"):
            st.warning(f"Traspasando {sn_trap} a {compañero}...")

    with t_tabs[2]:
        st.header("Registrar Instalación")
        sn_inst = st.selectbox("Seleccionar equipo de mi stock", mis_equipos['sn'].tolist() if not mis_equipos.empty else ["Sin stock"])
        n_orden = st.text_input("Número de Orden / Incidencia")
        if st.button("Finalizar Instalación"):
            st.success(f"Equipo {sn_inst} instalado en orden {n_orden}")

if st.sidebar.button("Cerrar Sesión"):
    del st.session_state.user
    st.rerun()
