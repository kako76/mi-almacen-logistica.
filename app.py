import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Telecom - Gestión Logística", layout="wide")

# --- BASE DE DATOS ---
conn = sqlite3.connect('altri_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, nombre TEXT, clave TEXT, perfil TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS stock (sn TEXT PRIMARY KEY, modelo TEXT, marca TEXT, estado TEXT, poseedor TEXT, fecha TEXT)')
conn.commit()

# --- MATERIALES ACTUALIZADOS ---
MATERIALES = {
    "ORANGE": {
        "Routers/ONT": ["ZTE LIVEBOX 7", "ARCADYAN LIVEBOX 6", "LIVEBOX INFINITY", "Nokia G-010G-P"],
        "TV": ["STB Android TV 4K", "Jade"],
        "Acometidas": ["Interior 20m", "Interior 40m", "Exterior 80m", "Exterior 100m"]
    },
    "MASMOVIL": {
        "Routers/ONT": ["ZTE H3640 Wifi 6", "Sagemcom 5670", "ONT Huawei"],
        "TV": ["Agile TV Box"],
        "Acometidas": ["Acometida Prodigy 80m", "Interior MMV 20m"]
    }
}

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso Altri Telecom")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "1234":
            st.session_state.auth = True
            st.session_state.perfil = "admin"
            st.rerun()
    st.stop()

# --- INTERFAZ ---
st.title("🚀 Altri Telecom | Control de Almacén")
menu = st.sidebar.radio("Menú", ["📦 Stock Global", "📥 Entrada Almacén", "🚚 Asignación y Albarán", "🔄 Traspaso entre Técnicos", "👥 Gestión Personal"])

# 1. STOCK GLOBAL
if menu == "📦 Stock Global":
    st.header("Inventario de Equipos")
    marca_filtro = st.selectbox("Filtrar por Operadora", ["TODAS", "ORANGE", "MASMOVIL"])
    query = "SELECT * FROM stock" if marca_filtro == "TODAS" else f"SELECT * FROM stock WHERE marca='{marca_filtro}'"
    df = pd.read_sql_query(query, conn)
    st.dataframe(df, use_container_width=True)

# 2. ENTRADA ALMACÉN
elif menu == "📥 Entrada Almacén":
    st.header("Entrada de Material Nuevo")
    col1, col2 = st.columns(2)
    with col1:
        operadora = st.selectbox("Operadora", ["ORANGE", "MASMOVIL"])
        cat = st.selectbox("Categoría", list(MATERIALES[operadora].keys()))
        mod = st.selectbox("Modelo", MATERIALES[operadora][cat])
    with col2:
        sns = st.text_area("Números de Serie (S/N) - Uno por línea")
    
    if st.button("Registrar en Almacén"):
        lista = sns.split('\n')
        for s in lista:
            if s.strip():
                c.execute("INSERT OR REPLACE INTO stock VALUES (?, ?, ?, ?, ?, ?)", 
                         (s.strip(), mod, operadora, "Disponible", "ALMACEN", datetime.now().strftime("%d/%m/%Y")))
        conn.commit()
        st.success("Material guardado correctamente.")

# 3. ASIGNACIÓN Y ALBARÁN
elif menu == "🚚 Asignación y Albarán":
    st.header("Entrega de Material a Técnico")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecnicos = [t[0] for t in c.fetchall()]
    
    tec_selec = st.selectbox("Seleccionar Técnico Destino", tecnicos)
    op_selec = st.selectbox("Marca del Material", ["ORANGE", "MASMOVIL"])
    
    # Buscamos equipos disponibles de esa marca
    df_disp = pd.read_sql_query(f"SELECT sn, modelo FROM stock WHERE marca='{op_selec}' AND estado='Disponible'", conn)
    equipos_selec = st.multiselect("Selecciona los S/N para entregar", df_disp['sn'].tolist())
    
    if st.button("Confirmar Entrega y Generar Albarán"):
        if equipos_selec:
            for s in equipos_selec:
                c.execute("UPDATE stock SET estado='Entregado', poseedor=? WHERE sn=?", (tec_selec, s))
            conn.commit()
            
            # Crear Albarán Visual
            st.markdown("---")
            st.subheader("📄 ALBARÁN DE ENTREGA - ALTRI TELECOM")
            st.write(f"**Técnico:** {tec_selec} | **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            st.table(df_disp[df_disp['sn'].isin(equipos_selec)])
            st.info("Puedes imprimir esta pantalla (Ctrl+P) para entregar al técnico.")
        else:
            st.error("No has seleccionado ningún equipo.")

# 4. TRASPASO ENTRE TÉCNICOS
elif menu == "🔄 Traspaso entre Técnicos":
    st.header("Traspaso de Material (Técnico A -> Técnico B)")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecs = [t[0] for t in c.fetchall()]
    
    origen = st.selectbox("Técnico que entrega", tecs)
    destino = st.selectbox("Técnico que recibe", [t for t in tecs if t != origen])
    
    # Ver qué tiene el técnico de origen
    df_origen = pd.read_sql_query(f"SELECT sn, modelo FROM stock WHERE poseedor='{origen}'", conn)
    items_traspaso = st.multiselect("Equipos a traspasar", df_origen['sn'].tolist())
    
    if st.button("Ejecutar Traspaso"):
        for s in items_traspaso:
            c.execute("UPDATE stock SET poseedor=? WHERE sn=?", (destino, s))
        conn.commit()
        st.success(f"Traspaso completado de {origen} a {destino}")

# 5. GESTIÓN PERSONAL
elif menu == "👥 Gestión Personal":
    st.header("Alta de Técnicos")
    nuevo_u = st.text_input("ID Login")
    nuevo_n = st.text_input("Nombre Completo")
    if st.button("Crear Técnico"):
        c.execute("INSERT INTO usuarios VALUES (?, ?, '1234', 'tecnico')", (nuevo_u, nuevo_n))
        conn.commit()
        st.success(f"Técnico {nuevo_n} añadido.")
