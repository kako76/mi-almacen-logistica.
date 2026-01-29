import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Telecom - Logística", layout="wide", page_icon="🧡")

# Conexión para el historial
conn = st.connection("gsheets", type=GSheetsConnection)

# --- BASE DE DATOS DE MATERIALES ---
DATA_ALTRI = {
    "ORANGE": [
        {"code": "702452", "material": "ARCADYAN LIVEBOX INFINITY (XGSPON)", "family": "ROUTER"},
        {"code": "702424", "material": "ARCADYAN LIVEBOX 6", "family": "ROUTER"},
        {"code": "732426", "material": "P-ARCADYAN LIVEBOX 6 PLUS", "family": "ROUTER"},
        {"code": "702478", "material": "ARCADYAN LIVEBOX 7", "family": "ROUTER"},
        {"code": "702441", "material": "ZTE F601 V7", "family": "ONT"},
        {"code": "732415", "material": "P-ZTE F601 V6", "family": "ONT"},
        {"code": "702459", "material": "SAGEMCOM STB VSB3918 ATV", "family": "DECO"},
        {"code": "702471", "material": "KAON STB KSTB7259 ATV", "family": "DECO"},
        {"code": "730057", "material": "P-KAON STB ANDROID TV", "family": "DECO"},
        {"code": "702461", "material": "REPETIDOR WIFI6 PREMIUM", "family": "REP"},
    ],
    "MASMOVIL": [
        {"code": "702478", "material": "ARCADYAN LIVEBOX 7", "family": "ROUTER"},
        {"code": "702411", "material": "ZTE F680", "family": "ROUTER"},
        {"code": "702432", "material": "ZTE F6640 Wifi 6", "family": "ROUTER"},
        {"code": "702441", "material": "ZTE F601 V7", "family": "ONT"},
        {"code": "702429", "material": "NOKIA G-010G-P", "family": "ONT"},
        {"code": "702459", "material": "SAGEMCOM STB VSB3918 ATV", "family": "DECO"},
        {"code": "702415", "material": "REPETIDOR WIFI TP-LINK RE450", "family": "REP"},
    ]
}

# --- FUNCIONES ---
def guardar_en_historial(tecnico, items, marca):
    try:
        # Crear filas para el historial
        nuevas_filas = []
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
        for item in items:
            nuevas_filas.append({
                "Fecha": fecha,
                "Tecnico": tecnico,
                "Marca": marca,
                "Codigo": item['code'],
                "Material": item['name'],
                "SN_Cantidad": item['sn']
            })
        
        # Leer historial actual
        df_existente = conn.read(worksheet="historial")
        df_nuevo = pd.concat([df_existente, pd.DataFrame(nuevas_filas)], ignore_index=True)
        
        # Actualizar Google Sheets
        conn.update(worksheet="historial", data=df_nuevo)
        return True
    except:
        return False

def create_pdf(tecnico, items):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "ALTRI TELECOM - ALBARÁN DE ENTREGA")
    c.setFont("Helvetica", 11)
    c.drawString(50, 780, f"Técnico: {tecnico} | Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.line(50, 770, 550, 770)
    
    y = 740
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "CÓDIGO")
    c.drawString(120, y, "DESCRIPCIÓN")
    c.drawString(450, y, "S/N o CANT.")
    
    c.setFont("Helvetica", 10)
    for item in items:
        y -= 20
        c.drawString(50, y, item['code'])
        c.drawString(120, y, item['name'][:50])
        c.drawString(450, y, item['sn'])
    
    c.line(50, 150, 550, 150)
    c.drawString(50, 130, "Firma Almacén")
    c.drawString(400, 130, "Firma Técnico")
    c.save()
    buf.seek(0)
    return buf

# --- INTERFAZ ---
st.title("📦 Gestión Altri Telecom")

tab_o, tab_m, tab_h = st.tabs(["🟠 ORANGE", "🟡 MASMOVIL", "📋 HISTORIAL"])

def render_seccion(brand):
    col_inv, col_trans = st.columns([1.2, 1])
    
    with col_inv:
        st.subheader(f"Almacén {brand}")
        busqueda = st.text_input(f"Buscar en {brand}", key=f"search_{brand}")
        for item in DATA_ALTRI[brand]:
            if busqueda.lower() in item['material'].lower() or busqueda in item['code']:
                with st.expander(f"{item['code']} - {item['material']}"):
                    st.write(f"Familia: {item['family']}")
                    st.write("Estado: 🟢 En Stock")

    with col_trans:
        st.subheader("Traspaso a Técnico")
        tecnico = st.text_input("Nombre del Técnico", key=f"tec_name_{brand}")
        
        if f"cart_{brand}" not in st.session_state:
            st.session_state[f"cart_{brand}"] = []
            
        mat_sel = st.selectbox("Material", [f"{i['code']} | {i['material']}" for i in DATA_ALTRI[brand]], key=f"sel_{brand}")
        sn_val = st.text_input("S/N o Unidades", key=f"sn_val_{brand}")
        
        if st.button("Añadir al Albarán", key=f"btn_{brand}"):
            c, n = mat_sel.split(" | ")
            st.session_state[f"cart_{brand}"].append({"code": c, "name": n, "sn": sn_val})
            st.rerun()

        if st.session_state[f"cart_{brand}"]:
            st.table(pd.DataFrame(st.session_state[f"cart_{brand}"]))
            
            if st.button("Finalizar y Registrar", key=f"save_{brand}"):
                if tecnico:
                    exito = guardar_en_historial(tecnico, st.session_state[f"cart_{brand}"], brand)
                    pdf = create_pdf(tecnico, st.session_state[f"cart_{brand}"])
                    
                    st.download_button("📥 Descargar PDF", data=pdf, file_name=f"Albaran_{tecnico}.pdf")
                    if exito: st.success("Registrado en historial")
                    st.session_state[f"cart_{brand}"] = []
                else:
                    st.error("Escribe el nombre del técnico")

with tab_o: render_seccion("ORANGE")
with tab_m: render_seccion("MASMOVIL")
with tab_h:
    st.subheader("Últimos Movimientos")
    try:
        df_h = conn.read(worksheet="historial")
        st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)
    except:
        st.info("Crea una pestaña llamada 'historial' en tu Excel con las columnas: Fecha, Tecnico, Marca, Codigo, Material, SN_Cantidad")
