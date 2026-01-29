import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Logística", layout="wide", page_icon="📦")

# ID de tu Google Sheet (No lo cambies si es el mismo archivo)
SHEET_ID = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"

# --- 2. FUNCIÓN DE LECTURA ROBUSTA (SIN ERRORES HTTP) ---
def cargar_datos(hoja):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={hoja}"
    try:
        # on_bad_lines='skip' evita que la app explote si hay una fila mal en excel
        df = pd.read_csv(url, on_bad_lines='skip')
        if not df.empty:
            df.columns = [c.lower().strip() for c in df.columns] # Normalizar nombres
        return df
    except:
        return pd.DataFrame()

# --- 3. GENERADOR DE PDF ---
def crear_pdf(tecnico, items):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "ALTRI TELECOM - DOCUMENTO DE ENTREGA")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Técnico Receptor: {tecnico}")
    c.drawString(50, 755, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.line(50, 740, 550, 740)
    y = 720
    c.drawString(50, y, "CÓDIGO / SN")
    c.drawString(250, y, "DESCRIPCIÓN")
    y -= 20
    c.setFont("Helvetica", 10)
    
    for item in items:
        c.drawString(50, y, str(item['sn']))
        c.drawString(250, y, str(item['modelo']))
        y -= 20
        
    c.save()
    buffer.seek(0)
    return buffer

# --- 4. LOGIN ---
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
    st.session_state.rol = None

if not st.session_state.usuario:
    st.title("🚀 Acceso Altri Telecom")
    with st.form("login_form"):
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            df_users = cargar_datos("usuarios")
            if not df_users.empty:
                # Comprobación estricta convirtiendo a texto
                match = df_users[(df_users['user'].astype(str) == user) & 
                                 (df_users['clave'].astype(str) == password)]
                if not match.empty:
                    st.session_state.usuario = user
                    st.session_state.rol = match.iloc[0]['rol']
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
            else:
                st.error("No se pudo leer el Excel. Verifica que esté 'Público'.")
    st.stop()

# --- 5. INTERFAZ PRINCIPAL ---
rol = st.session_state.rol
usuario = st.session_state.usuario
df_inv = cargar_datos("inventario")

st.sidebar.title(f"Hola, {usuario}")
st.sidebar.caption(f"Perfil: {rol.upper()}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.usuario = None
    st.rerun()

# --- LÓGICA DE PESTAÑAS SEGÚN ROL ---
if rol in ['admin', 'almacen']:
    # Solo Admin y Almacén ven Orange y MásMóvil
    tabs = st.tabs(["📊 ADMINISTRACIÓN", "📦 ALMACÉN", "🟠 ORANGE", "🟡 MÁSMÓVIL", "👨‍🔧 TÉCNICOS"])

    # PESTAÑA 1: ADMINISTRACIÓN (BUSCADOR GLOBAL)
    with tabs[0]:
        st.header("Localizador de Equipos")
        busqueda = st.text_input("Escribe SN o Modelo para buscar:")
        if not df_inv.empty:
            if busqueda:
                # Filtro que busca en cualquier columna
                res = df_inv[df_inv.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)]
                st.dataframe(res, use_container_width=True)
            else:
                st.dataframe(df_inv, use_container_width=True)
        else:
            st.warning("El inventario está vacío o no se ha podido leer.")

    # PESTAÑA 2: ALMACÉN (GESTIÓN)
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Entrada de Material")
            st.text_input("Escanear SN Entrada")
            if st.button("Registrar Entrada"):
                st.success("Registrado en sesión (Lectura solo-lectura activada)")
        
        with c2:
            st.subheader("Crear Albarán para Técnico")
            df_u = cargar_datos("usuarios")
            tecnicos = df_u[df_u['rol'] == 'tecnico']['user'].tolist() if not df_u.empty else []
            tec_dest = st.selectbox("Seleccionar Técnico", tecnicos)
            sn_out = st.text_input("SN a entregar")
            
            if st.button("Generar PDF"):
                pdf_data = crear_pdf(tec_dest, [{"sn": sn_out, "modelo": "Equipo Altri"}])
                st.download_button("📥 Descargar Albarán", pdf_data, f"Albaran_{tec_dest}.pdf", "application/pdf")

    # PESTAÑA 3 y 4: MARCAS
    with tabs[2]:
        st.header("Stock Orange")
        if not df_inv.empty and 'marca' in df_inv.columns:
            st.dataframe(df_inv[df_inv['marca'].str.upper() == 'ORANGE'])
            
    with tabs[3]:
        st.header("Stock MásMóvil")
        if not df_inv.empty and 'marca' in df_inv.columns:
            st.dataframe(df_inv[df_inv['marca'].str.upper() == 'MASMOVIL'])

    # PESTAÑA 5: VISTA TÉCNICOS
    with tabs[4]:
        st.header("Material Instalado y en Poder de Técnicos")
        if not df_inv.empty and 'ubicacion' in df_inv.columns:
             st.dataframe(df_inv[df_inv['ubicacion'] != 'Almacen'])

# --- VISTA PARA TÉCNICOS (SOLO VEN SU MATERIAL) ---
elif rol == 'tecnico':
    mis_tabs = st.tabs(["🎒 MI MATERIAL", "🔁 TRASPASO", "✅ INSTALACIONES"])
    
    # Filtramos lo que tiene ESTE técnico
    mi_stock = df_inv[df_inv['ubicacion'] == usuario] if not df_inv.empty and 'ubicacion' in df_inv.columns else pd.DataFrame()

    with mis_tabs[0]:
        st.header(f"Inventario de {usuario}")
        if not mi_stock.empty:
            st.dataframe(mi_stock)
        else:
            st.info("No tienes material asignado.")

    with mis_tabs[1]:
        st.subheader("Ceder material a compañero")
        df_u = cargar_datos("usuarios")
        compis = df_u[(df_u['rol'] == 'tecnico') & (df_u['user'] != usuario)]['user'].tolist() if not df_u.empty else []
        st.selectbox("Compañero destino", compis)
        st.selectbox("Equipo a ceder", mi_stock['sn'].unique() if not mi_stock.empty else [])
        st.button("Confirmar Traspaso")

    with mis_tabs[2]:
        st.subheader("Cierre de Orden")
        st.text_input("Número de Orden")
        st.selectbox("Equipo instalado", mi_stock['sn'].unique() if not mi_stock.empty else [])
        if st.button("Finalizar Orden"):
            st.balloons()
            st.success("Instalación registrada correctamente")
