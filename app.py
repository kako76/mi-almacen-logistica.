import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Altri Telecom - Logística Pro", layout="wide")

# Configuración de conexión con Google Sheets
ID_HOJA = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"
URL_HOJA = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(pestaña):
    try: return conn.read(spreadsheet=URL_HOJA, worksheet=pestaña)
    except: return pd.DataFrame()

def guardar_datos(df, pestaña):
    conn.update(spreadsheet=URL_HOJA, worksheet=pestaña, data=df)

# --- CATÁLOGO EXTRAÍDO DE TUS ARCHIVOS ---
# Organizado por familias según tus listas de inventario
CATALOGO_MATERIAL = {
    "ROUTERS & ONT (ORANGE/MASMOVIL)": [
        "702424 - ARCADYAN LIVEBOX 6",
        "702452 - ARCADYAN LIVEBOX INFINITY (XGSPON)",
        "702478 - ARCADYAN LIVEBOX 7",
        "702479 - ZTE LIVEBOX 7",
        "702441 - ZTE F601 V7 (ONT)",
        "R075364W6 - ROUTER ZTE H3640 WIFI 6",
        "RM14670W4 - ROUTER FTTH SAGEMCOM FAST 5670 WIFI 6",
        "RM14670W5 - ROUTER FTTH SAGEMCOM FAST 5670 WIFI",
        "RU14670W3 - ROUTER RECUPERADO FAST 5670 WIFI 6",
        "R069R45W2 - REPETIDOR TP-LINK RE450",
        "702427 - SERCOMM REPETIDOR WIFI 6"
    ],
    "DECODIFICADORES TV": [
        "G050TVNN2 - DECODIFICADOR TV NEUTRO",
        "G050JADM7 - STB TECHNICOLOR JADE UZW4060MM",
        "702459 - SAGEMCOM STB VSB3918 ATV (2022)",
        "702471 - KAON STB KSTB7259 ATV (2024)",
        "730057 - P-KAON STB ANDROID TV"
    ],
    "ACOMETIDAS Y FIBRA": [
        "4910113 - PRODIGY ACOMETIDA EXTERIOR 80M",
        "4910114 - PRODIGY ACOMETIDA EXTERIOR 150M",
        "4910116 - PRODIGY ACOMETIDA EXTERIOR 400M",
        "4910034 - FTTH EXTERIOR HUAWEI 100M",
        "4910041 - FTTH EXTERIOR HUAWEI 80M",
        "4910062 - FTTH EXTERIOR CORNING 150M",
        "611876 - ACOMETIDA EXTERIOR 30M",
        "611880 - ACOMETIDA EXTERIOR OPTITAP 30M"
    ],
    "COMPONENTES Y VARIOS": [
        "4910049 - ROSETA TERMINAL ÓPTICA",
        "4910070 - ROSETA ÓPTICA TRANSICIÓN",
        "611886 - ROSETA OPTICA FINAL",
        "P02370C - TARJETA MASMOVIL ECOSIM 4G",
        "TSOMXCOU3 - TARJETA SIM UNIVERSAL OM CONTRATAS",
        "4920080 - CABLE UTP CAT 6 (BOBINA 305M)"
    ]
}

# --- SESIÓN ---
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LÓGICA DE LOGIN ---
if not st.session_state.auth:
    st.title("Sistema de Gestión Altri Telecom")
    user = st.text_input("Usuario")
    passw = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if user == "admin" and passw == "altri2026": # Cambia esto por tus credenciales
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.sidebar.title("Navegación")
menu = st.sidebar.radio("Ir a:", ["Inventario", "Carga de Material", "Asignación a Técnico", "Historial"])

df_stock = leer_datos("stock")

if menu == "Carga de Material":
    st.header("📥 Carga Masiva de Material")
    col1, col2 = st.columns(2)
    
    with
