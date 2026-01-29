import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA (ESTILO ALTRI)
st.set_page_config(page_title="Altri Telecom - Logística", layout="wide", page_icon="🧡")

# 2. CONEXIÓN DIRECTA (REEMPLAZO DEL ERROR 200)
# Este ID es el que sacamos de tu captura de pantalla
SHEET_ID = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=usuarios"

def get_data():
    try:
        # Forzamos la descarga del CSV directo del Excel
        df = pd.read_csv(URL)
        df.columns = [c.lower().strip() for c in df.columns]
        return df
    except Exception as e:
        return None

# 3. CONTROL DE ACCESO
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🚀 Altri Telecom | Gestión de Almacén")
    with st.form("login_form"):
        user_val = st.text_input("Usuario")
        pass_val = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Acceder"):
            data = get_data()
            if data is not None:
                # Verificación exacta
                check = data[(data['user'].astype(str) == str(user_val)) & 
                             (data['clave'].astype(str) == str(pass_val))]
                if not check.empty:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Revisa el Excel.")
            else:
                st.error("No se pudo leer el Excel. ¿Está compartido como 'Cualquier persona con el enlace'?")

# 4. APLICACIÓN PRINCIPAL (Basada en tus archivos .ts)
else:
    st.sidebar.title("Altri Logística")
    option = st.sidebar.radio("Navegación", ["Panel de Stock", "Escáner SN", "Asistente IA"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

    if option == "Panel de Stock":
        st.header("📦 Inventario de Equipos")
        # Datos basados en tu initialData.ts
        stock_data = {
            "Código": ["702424", "702478", "702452", "702441"],
            "Material": ["ARCADYAN LIVEBOX 6", "ARCADYAN LIVEBOX 7", "ARCADYAN LIVEBOX INFINITY", "ZTE F601 V7"],
            "Marca": ["ORANGE", "MASMOVIL", "ORANGE", "ORANGE"],
            "Stock": [15, 12, 10, 20]
        }
        st.table(pd.DataFrame(stock_data))

    elif option == "Escáner SN":
        st.header("🔍 Registro de Salida")
        sn = st.text_input("Escanea o escribe el Número de Serie")
        if sn:
            st.info(f"Procesando unidad: {sn}...")
            st.button("Asignar a Técnico")

    elif option == "Asistente IA":
        st.header("🤖 Consulta con Gemini")
        st.write("La IA está lista para analizar tu stock.")
        pregunta = st.text_input("¿Qué quieres saber sobre el material?")
        if pregunta:
            st.warning("Configura tu GEMINI_API_KEY en los secretos de Streamlit para recibir respuesta.")
