import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Altri ERP", layout="wide", page_icon="📡")

# --- CONEXIÓN DIRECTA (SIN LIBRERÍAS EXTERNAS QUE FALLEN) ---
# Este es el ID de tu hoja. Si creas una nueva, cámbialo.
SHEET_ID = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"

def cargar_datos(hoja):
    """Lee el Excel directamente como CSV público para evitar errores de API"""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={hoja}"
    try:
        df = pd.read_csv(url, on_bad_lines='skip')
        # Limpiamos los nombres de las columnas (minúsculas y sin espacios)
        df.columns = [c.lower().strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame() # Devuelve vacío si falla para no romper la app

# --- GENERADOR DE PDF ---
def generar_albaran(origen, destino, items):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "ALTRI TELECOM - ALBARÁN DE ENTREGA")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(50, 750, f"Origen: {origen}")
    c.drawString(50, 730, f"Destino: {destino}")
    
    c.line(50, 710, 550, 710)
    y = 690
    c.drawString(50, y, "CÓDIGO / SN")
    c.drawString(250, y, "DESCRIPCIÓN")
    y -= 20
    
    c.setFont("Helvetica", 10)
    for item in items:
        c.drawString(50, y, str(item['sn']))
        c.drawString(250, y, str(item['modelo']))
        y -= 20
        
    c.line(50, 150, 550, 150)
    c.drawString(50, 130, "Firma Entrega")
    c.drawString(350, 130, "Firma Recibe")
    
    c.save()
    buffer.seek(0)
    return buffer

# --- SISTEMA DE LOGIN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.rol = None

if not st.session_state.usuario:
    st.title("🔐 Acceso Altri Telecom")
    with st.form("login"):
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            df_users = cargar_datos("usuarios")
            if not df_users.empty:
                # Verificación segura convirtiendo a string
                u_check = df_users[(df_users['user'].astype(str) == user) & 
                                   (df_users['clave'].astype(str) == password)]
                if not u_check.empty:
                    st.session_state.usuario = user
                    st.session_state.rol = u_check.iloc[0]['rol']
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
            else:
                st.error("Error de conexión. ¿El Excel está como 'Cualquier persona con el enlace'?")
    st.stop()

# --- INTERFAZ PRINCIPAL ---
rol = st.session_state.rol
usuario = st.session_state.usuario

st.sidebar.title(f"👤 {usuario}")
st.sidebar.caption(f"Perfil: {rol.upper()}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.usuario = None
    st.rerun()

# Cargamos inventario global
df_inv = cargar_datos("inventario")

# === PESTAÑAS DE ADMINISTRACIÓN Y ALMACÉN ===
if rol in ['admin', 'almacen']:
    tabs = st.tabs(["🏢 ADMINISTRACIÓN", "📦 ALMACÉN", "🟠 ORANGE", "🟡 MÁSMÓVIL", "👥 TÉCNICOS"])
    
    # 1. ADMINISTRACIÓN (Buscador Global)
    with tabs[0]:
        st.header("Control Total de Activos")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Equipos", len(df_inv))
        col2.metric("En Almacén", len(df_inv[df_inv['ubicacion'] == 'Almacén']) if not df_inv.empty else 0)
        col3.metric("Instalados", len(df_inv[df_inv['ubicacion'] == 'Instalado']) if not df_inv.empty else 0)
        
        st.divider()
        st.subheader("🔍 Localizador de Equipos")
        busqueda = st.text_input("Escribe el Número de Serie (SN) para rastrearlo:")
        if busqueda and not df_inv.empty:
            resultado = df_inv[df_inv['sn'].astype(str).str.contains(busqueda, case=False)]
            if not resultado.empty:
                st.dataframe(resultado)
                ubicacion = resultado.iloc[0]['ubicacion']
                st.info(f"El equipo está actualmente en: **{ubicacion}**")
            else:
                st.warning("No se encuentra ese número de serie.")
        else:
            st.dataframe(df_inv)

    # 2. ALMACÉN (Entradas y Salidas)
    with tabs[1]:
        col_ent, col_sal = st.columns(2)
        
        with col_ent:
            st.subheader("📥 Recepción de Material")
            with st.form("entrada"):
                nuevo_sn = st.text_input("Escanear SN")
                nuevo_mod = st.selectbox("Modelo", ["Livebox 6", "Livebox 7", "Infinity", "ZTE F680", "Deco Android"])
                nueva_marca = st.selectbox("Marca", ["Orange", "MasMovil"])
                if st.form_submit_button("Registrar Entrada"):
                    st.success(f"Equipo {nuevo_sn} registrado en Almacén (Simulado)")
                    st.caption("Nota: Para guardar en Excel real se necesita API de escritura.")

        with col_sal:
            st.subheader("📤 Traspaso a Técnico")
            df_u = cargar_datos("usuarios")
            lista_tecnicos = df_u[df_u['rol'] == 'tecnico']['user'].tolist() if not df_u.empty else []
            
            tecnico_dest = st.selectbox("Seleccionar Técnico", lista_tecnicos)
            sn_salida = st.text_input("SN a Entregar")
            
            if st.button("Generar Albarán PDF"):
                items_demo = [{"sn": sn_salida, "modelo": "Equipo Genérico"}]
                pdf = generar_albaran("Almacén Central", tecnico_dest, items_demo)
                st.download_button("Descargar Albarán", pdf, f"albaran_{tecnico_dest}.pdf", "application/pdf")
    
    # 3. MARCAS (Solo lectura visual)
    with tabs[2]:
        st.header("Stock Orange")
        if not df_inv.empty:
            st.dataframe(df_inv[df_inv['marca'].str.lower() == 'orange'])
    
    with tabs[3]:
        st.header("Stock MásMóvil")
        if not df_inv.empty:
            st.dataframe(df_inv[df_inv['marca'].str.lower() == 'masmovil'])
            
    # 4. TÉCNICOS (Vista Admin)
    with tabs[4]:
        st.header("Material en manos de técnicos")
        if not df_inv.empty:
            st.dataframe(df_inv[df_inv['ubicacion'].isin(lista_tecnicos)])

# === PESTAÑAS DE TÉCNICOS ===
elif rol == 'tecnico':
    st.info(f"Bienvenido al panel técnico, {usuario}")
    tabs_tec = st.tabs(["🎒 MI MATERIAL", "🔁 TRASPASO ENTRE TÉCNICOS", "✅ INSTALACIONES"])
    
    # Filtramos el inventario para mostrar solo lo que tiene ESTE técnico
    mis_equipos = pd.DataFrame()
    if not df_inv.empty:
        mis_equipos = df_inv[df_inv['ubicacion'] == usuario]

    with tabs_tec[0]:
        st.header("Material Asignado")
        if not mis_equipos.empty:
            st.dataframe(mis_equipos)
        else:
            st.warning("No tienes material asignado actualmente.")

    with tabs_tec[1]:
        st.header("Ceder material a compañero")
        df_u = cargar_datos("usuarios")
        comis = df_u[(df_u['rol'] == 'tecnico') & (df_u['user'] != usuario)]['user'].tolist() if not df_u.empty else []
        
        destinatario = st.selectbox("Compañero", comis)
        sn_ceder = st.selectbox("Seleccionar equipo", mis_equipos['sn'].tolist()) if not mis_equipos.empty else None
        
        if st.button("Confirmar Cesión"):
            st.success(f"Has cedido el equipo {sn_ceder} a {destinatario}")

    with tabs_tec[2]:
        st.header("Cierre de Orden")
        if not mis_equipos.empty:
            sn_instalar = st.selectbox("Equipo a instalar", mis_equipos['sn'].unique())
            n_orden = st.text_input("Número de Orden / Incidencia")
            
            if st.button("Finalizar Instalación"):
                st.balloons()
                st.success(f"Equipo {sn_instalar} asociado a la orden {n_orden}. Stock actualizado.")
        else:
            st.warning("Necesitas tener material para poder instalar.")
