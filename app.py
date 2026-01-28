
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Logística Altri Telecom", layout="wide")

# Conexión con Google Sheets (Asegúrate de tener el ID en Secrets)
ID_HOJA = "1CQXP7bX81ysb9fkr8pEqlLSms5wNAMI-_ojqLIzoSUw"
URL_HOJA = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(pestaña):
    try:
        return conn.read(spreadsheet=URL_HOJA, worksheet=pestaña)
    except:
        return pd.DataFrame()

def guardar_datos(df, pestaña):
    conn.update(spreadsheet=URL_HOJA, worksheet=pestaña, data=df)

# --- CATÁLOGO DE TUS FOTOS ---
CATALOGO = {
    "ROUTERS & ONT": [
        "702424 - ARCADYAN LIVEBOX 6", "702478 - ARCADYAN LIVEBOX 7", "702479 - ZTE LIVEBOX 7",
        "702452 - ARCADYAN LIVEBOX INFINITY", "702441 - ZTE F601 V7 (ONT)",
        "R075364W6 - ZTE H3640 Wifi 6", "RM14670W4 - SAGEMCOM FAST 5670", "702427 - REPETIDOR WIFI 6"
    ],
    "DECO / TV": [
        "G050JACM7 - TECHNICOLOR JADE", "730057 - P-KAON STB ANDROID",
        "702459 - SAGEMCOM STB VSB3918", "G050TVNN2 - DECO NEUTRO"
    ],
    "ACOMETIDAS": [
        "4910113 - PRODIGY EXT 80M", "4910114 - PRODIGY EXT 150M",
        "4910034 - HUAWEI EXT 100M", "4910041 - HUAWEI EXT 80M",
        "4910062 - CORNING EXT 150M", "611880 - OPTITAP EXT 30M"
    ],
    "VARIOS": ["4910049 - ROSETA TERMINAL", "611886 - ROSETA FINAL", "SIM ORANGE/MASMOVIL"]
}

# --- LOGIN ---
df_usuarios = leer_datos("usuarios")
if df_usuarios.empty:
    df_usuarios = pd.DataFrame([{"user": "admin", "nombre": "Administrador", "clave": "altri2026", "perfil": "admin"}])
    guardar_datos(df_usuarios, "usuarios")

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🚀 Altri Telecom Login")
    u = st.text_input("Usuario")
    p = st.text_input("Clave", type="password")
    if st.button("Entrar"):
        login = df_usuarios[(df_usuarios['user']==u) & (df_usuarios['clave'].astype(str)==p)]
        if not login.empty:
            st.session_state.update({"auth":True, "user":u, "nombre":login.iloc[0]['nombre'], "perfil":login.iloc[0]['perfil']})
            st.rerun()
    st.stop()

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("Menú", ["📊 Stock", "📥 Cargar Material", "🚚 Entregar", "👥 Personal"])
df_stock = leer_datos("stock")

if menu == "📊 Stock":
    st.header("Inventario Real")
    st.dataframe(df_stock, use_container_width=True)

elif menu == "📥 Cargar Material":
    st.header("Entrada de Stock")
    c1, c2 = st.columns(2)
    fam = c1.selectbox("Familia", list(CATALOGO.keys()))
    mod = c1.selectbox("Modelo", CATALOGO[fam])
    sns = st.text_area("Números de Serie (uno por línea)")
    if st.button("Guardar en Google Sheets"):
        series = [s.strip().upper() for s in sns.split('\n') if s.strip()]
        nuevos = pd.DataFrame([{
            "sn": s, "modelo": mod, "estado": "Almacén", "poseedor": "ALMACEN", "fecha": datetime.now().strftime("%d/%m/%Y")
        } for s in series])
        df_final = pd.concat([df_stock, nuevos], ignore_index=True)
        guardar_datos(df_final, "stock")
        st.success(f"Cargados {len(series)} equipos.")

elif menu == "🚚 Entregar":
    st.header("Asignar a Técnico")
    tecs = df_usuarios[df_usuarios['perfil']=='tecnico']['nombre'].tolist()
    if tecs:
        t_dest = st.selectbox("Técnico", tecs)
        disp = df_stock[df_stock['estado'] == 'Almacén']['sn'].tolist()
        sel = st.multiselect("Series", disp)
        if st.button("Generar Albarán"):
            df_stock.loc[df_stock['sn'].isin(sel), ['estado', 'poseedor']] = ["En Mochila", t_dest]
            guardar_datos(df_stock, "stock")
            st.success("Asignado.")
            st.table(df_stock[df_stock['sn'].isin(sel)])
    else: st.warning("Crea técnicos en el menú Personal.")

elif menu == "👥 Personal":
    st.header("Técnicos")
    with st.expander("Añadir Nuevo"):
        nu, nn, nc = st.text_input("Usuario"), st.text_input("Nombre"), st.text_input("Clave")
        if st.button("Crear"):
            df_usuarios = pd.concat([df_usuarios, pd.DataFrame([{"user":nu, "nombre":nn, "clave":nc, "perfil":"tecnico"}])], ignore_index=True)
            guardar_datos(df_usuarios, "usuarios")
            st.success("Técnico creado.")
    st.dataframe(df_usuarios)
