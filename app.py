import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai

# --- CONFIGURACIÓN DE DATOS (Basado en tus archivos initialData.ts) ---
SHEET_ID = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"
URL_USUARIOS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=usuarios"

# Datos de materiales extraídos de tu initialData.ts
MATERIALES_ALTRITEL = [
    {"id": "item-o-1", "code": "702452", "material": "ARCADYAN LIVEBOX INFINITY (XGSPON)", "brand": "ORANGE", "stock": 10},
    {"id": "item-o-2", "code": "702424", "material": "ARCADYAN LIVEBOX 6", "brand": "ORANGE", "stock": 15},
    {"id": "item-o-3", "code": "702441", "material": "ZTE F601 V7", "brand": "ORANGE", "stock": 20},
    {"id": "item-m-1", "code": "702478", "material": "ARCADYAN LIVEBOX 7", "brand": "MASMOVIL", "stock": 12},
]

# --- CONFIGURACIÓN PÁGINA ---
st.set_page_config(page_title="Altri Logística v2", layout="wide", page_icon="🚀")

# --- FUNCIONES ---
def load_users():
    return pd.read_csv(URL_USUARIOS)

def inicializar_ia():
    # Intenta obtener la clave de secretos
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-pro')
    except:
        return None

# --- LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- INTERFAZ DE LOGIN ---
if not st.session_state.logged_in:
    st.title("🚀 Altri Telecom - Logística")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            try:
                df = load_users()
                df.columns = [c.lower().strip() for c in df.columns]
                if not df[(df['user'].astype(str) == str(u)) & (df['clave'].astype(str) == str(p))].empty:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except:
                st.error("Error conectando con la base de datos de usuarios.")

# --- INTERFAZ PRINCIPAL (DASHBOARD) ---
else:
    st.sidebar.title("Altri Logística")
    menu = st.sidebar.selectbox("Menú", ["Dashboard", "Inventario", "Asistente IA", "Albaranes"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Resumen de Almacén")
        col1, col2, col3 = st.columns(3)
        
        df_inv = pd.DataFrame(MATERIALES_ALTRITEL)
        col1.metric("Total Equipos", len(df_inv))
        col2.metric("Stock Total", df_inv['stock'].sum())
        col3.metric("Marca Principal", "ORANGE")
        
        st.subheader("Estado Crítico de Material")
        st.table(df_inv)

    elif menu == "Inventario":
        st.header("📋 Gestión de Números de Serie")
        st.write("Registra entradas y salidas de material.")
        # Simulación de escaneo
        sn = st.text_input("Escanea Número de Serie (SN)")
        if sn:
            st.success(f"Equipo {sn} detectado. Listo para asignar.")

    elif menu == "Asistente IA":
        st.header("🤖 Altri AI Assistant")
        st.write("Pregunta sobre el stock o técnicos.")
        
        model = inicializar_ia()
        if model:
            query = st.text_input("Ej: ¿Cuántos Livebox 6 tenemos?")
            if query:
                contexto = f"Inventario actual: {MATERIALES_ALTRITEL}"
                response = model.generate_content(f"{contexto}\n\nPregunta: {query}")
                st.info(response.text)
        else:
            st.warning("IA deshabilitada: Falta GEMINI_API_KEY en Secretos.")

    elif menu == "Albaranes":
        st.header("📄 Generación de Albaranes PDF")
        st.write("Crea el documento de entrega para el técnico.")
        nombre_tecnico = st.selectbox("Selecciona Técnico", ["Admin", "Técnico 1", "Técnico 2"])
        if st.button("Generar Albarán"):
            st.info(f"Generando Albarán para {nombre_tecnico}...")
            # Aquí se integraría la lógica de pdfService.ts
