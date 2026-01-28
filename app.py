import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Telecom - Logística Pro", layout="wide")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('altri_v10_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, nombre TEXT, clave TEXT, perfil TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS stock (sn TEXT PRIMARY KEY, familia TEXT, modelo TEXT, marca TEXT, estado TEXT, poseedor TEXT, fecha TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS movimientos (id INTEGER PRIMARY KEY AUTOINCREMENT, sn TEXT, tipo TEXT, origen TEXT, destino TEXT, fecha TEXT, usuario_accion TEXT)')
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'Administrador', '1234', 'admin')")
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ESTRUCTURA DE MATERIALES ---
MATERIALES = {
    "ROUTERS": ["Livebox 6", "Livebox 7", "Livebox Infinity", "ZTE H3640", "Sagemcom 5670", "ZTE F680", "ONT Huawei"],
    "TV": ["STB Android 4K", "Jade", "Agile TV Box"],
    "ACOMETIDA INTERIOR (m)": ["20", "30", "40", "50", "60"],
    "ACOMETIDA EXT. CORNING (m)": ["30", "50", "80", "150", "220"],
    "ACOMETIDA EXT. HUAWEI (m)": ["20", "30", "50", "80", "150", "220"],
    "ROSETAS/CAJAS": ["Roseta Final", "Roseta Transición", "PTR Óptica"],
    "EXTERIOR/INFRA": ["Postes", "Arquetas", "Filtro 4G"]
}

def registrar_movimiento(sn, tipo, origen, destino, usuario):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO movimientos (sn, tipo, origen, destino, fecha, usuario_accion) VALUES (?,?,?,?,?,?)",
              (sn, tipo, origen, destino, fecha, usuario))
    conn.commit()

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🚀 Altri Telecom Login")
    u, p = st.text_input("Usuario"), st.text_input("Clave", type="password")
    if st.button("Entrar"):
        c.execute("SELECT nombre, perfil FROM usuarios WHERE user=? AND clave=?", (u, p))
        res = c.fetchone()
        if res:
            st.session_state.auth, st.session_state.usuario_id, st.session_state.nombre, st.session_state.perfil = True, u, res[0], res[1]
            st.rerun()
        else: st.error("Error")
    st.stop()

# --- INTERFAZ ---
st.sidebar.title(f"👤 {st.session_state.nombre}")
if st.session_state.perfil == 'admin':
    menu = st.sidebar.radio("Panel Admin", ["📊 Inventario Local", "📥 Añadir/Eliminar Stock", "🚚 Asignación a Técnico", "🔄 Traspaso entre Técnicos", "📑 Historial y Excel", "👥 Personal"])
else:
    menu = st.sidebar.radio("Panel Técnico", ["🎒 Mi Mochila", "✅ Instalar", "⚠️ Defectuoso"])

# 1. INVENTARIO LOCAL (COMPACTO)
if menu == "📊 Inventario Local":
    st.header("Estado del Inventario")
    df = pd.read_sql_query("SELECT * FROM stock", conn)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fam = st.selectbox("Familia", ["TODAS"] + list(MATERIALES.keys()))
    with col2:
        mar = st.selectbox("Operadora", ["TODAS", "ORANGE", "MASMOVIL"])
    with col3:
        est = st.selectbox("Estado", ["TODOS", "Almacén", "En Mochila", "INSTALADO", "DEFECTUOSO"])

    query = "SELECT sn, familia, modelo, marca, estado, poseedor FROM stock WHERE 1=1"
    if fam != "TODAS": query += f" AND familia='{fam}'"
    if mar != "TODAS": query += f" AND marca='{mar}'"
    if est != "TODOS": query += f" AND estado='{est}'"
    
    df_filt = pd.read_sql_query(query, conn)
    st.dataframe(df_filt, use_container_width=True)

# 2. AÑADIR / ELIMINAR STOCK
elif menu == "📥 Añadir/Eliminar Stock":
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Añadir Equipos")
        marca = st.selectbox("Operadora", ["ORANGE", "MASMOVIL"])
        fam = st.selectbox("Categoría", list(MATERIALES.keys()))
        mod = st.selectbox("Modelo/Medida", MATERIALES[fam])
        sns = st.text_area("S/N (uno por línea)")
        if st.button("Guardar en Almacén"):
            for s in sns.split('\n'):
                if s.strip():
                    c.execute("INSERT OR REPLACE INTO stock VALUES (?,?,?,?,?,?,?)", 
                             (s.strip(), fam, mod, marca, "Almacén", "ALMACEN", datetime.now().strftime("%d/%m/%Y")))
                    registrar_movimiento(s.strip(), "Entrada", "Proveedor", "ALMACEN", st.session_state.nombre)
            st.success("Cargado")
    with col_b:
        st.subheader("Eliminar por S/N")
        sn_del = st.text_input("S/N a borrar")
        if st.button("Eliminar permanentemente"):
            c.execute("DELETE FROM stock WHERE sn=?", (sn_del,))
            conn.commit()
            st.warning("Equipo eliminado")

# 3. ASIGNACIÓN Y ALBARÁN
elif menu == "🚚 Asignación a Técnico":
    st.header("Entrega de Material")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecs = [t[0] for t in c.fetchall()]
    tec_dest = st.selectbox("Técnico Destino", tecs)
    
    df_disp = pd.read_sql_query("SELECT sn, modelo FROM stock WHERE estado='Almacén'", conn)
    sel = st.multiselect("Equipos a entregar", df_disp['sn'].tolist())
    
    if st.button("Asignar y Generar Albarán"):
        if sel:
            for s in sel:
                c.execute("UPDATE stock SET estado='En Mochila', poseedor=? WHERE sn=?", (tec_dest, s))
                registrar_movimiento(s, "Asignación", "ALMACEN", tec_dest, st.session_state.nombre)
            
            st.markdown("### 📄 ALBARÁN DE ENTREGA")
            st.info(f"Técnico: {tec_dest} | Fecha: {datetime.now().strftime('%d/%m/%Y')}")
            st.table(df_disp[df_disp['sn'].isin(sel)])
            st.write("---")
            st.write("Firma Almacén: _________   Firma Técnico: _________")
            st.caption("Pulsa Ctrl+P para guardar este albarán en PDF")

# 4. TRASPASO ENTRE TÉCNICOS
elif menu == "🔄 Traspaso entre Técnicos":
    st.header("Traspasar material (De Técnico A a Técnico B)")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecs = [t[0] for t in c.fetchall()]
    
    origen = st.selectbox("Técnico Origen", tecs)
    destino = st.selectbox("Técnico Destino", [t for t in tecs if t != origen])
    
    df_mochila = pd.read_sql_query(f"SELECT sn, modelo FROM stock WHERE poseedor='{origen}' AND estado='En Mochila'", conn)
    sn_tras = st.multiselect("Selecciona Números de Serie a traspasar", df_mochila['sn'].tolist())
    
    if st.button("Confirmar Traspaso"):
        for s in sn_tras:
            c.execute("UPDATE stock SET poseedor=? WHERE sn=?", (destino, s))
            registrar_movimiento(s, "Traspaso", origen, destino, st.session_state.nombre)
        st.success(f"Traspaso de {len(sn_tras)} equipos completado.")

# 5. HISTORIAL Y EXCEL
elif menu == "📑 Historial y Excel":
    st.header("Historial de Movimientos")
    df_h = pd.read_sql_query("SELECT * FROM movimientos ORDER BY id DESC", conn)
    st.dataframe(df_h)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_h.to_excel(writer, index=False)
    st.download_button("📥 Descargar Excel Completo", buffer.getvalue(), "logistica_altri.xlsx")

# 6. GESTIÓN PERSONAL
elif menu == "👥 Personal":
    st.header("Gestión de Técnicos")
    with st.expander("Añadir"):
        nu, nn, nc = st.text_input("Usuario"), st.text_input("Nombre"), st.text_input("Clave")
        if st.button("Registrar"):
            c.execute("INSERT INTO usuarios VALUES (?,?,?,'tecnico')", (nu, nn, nc))
            conn.commit()
            st.rerun()
    st.dataframe(pd.read_sql_query("SELECT user, nombre FROM usuarios WHERE perfil='tecnico'", conn))
    elim = st.text_input("Usuario a eliminar")
    if st.button("Eliminar Técnico"):
        c.execute("DELETE FROM usuarios WHERE user=?", (elim,))
        conn.commit()
        st.rerun()

# --- LÓGICA TÉCNICO ---
elif menu == "🎒 Mi Mochila":
    st.header(f"Mi Mochila: {st.session_state.nombre}")
    df_m = pd.read_sql_query(f"SELECT sn, modelo, familia FROM stock WHERE poseedor='{st.session_state.nombre}' AND estado='En Mochila'", conn)
    st.dataframe(df_m)

elif menu == "✅ Instalar":
    st.header("Registrar Instalación")
    c.execute("SELECT sn FROM stock WHERE poseedor=? AND estado='En Mochila'", (st.session_state.nombre,))
    mis_s = [r[0] for r in c.fetchall()]
    if mis_s:
        s_i = st.selectbox("Selecciona S/N", mis_s)
        cli = st.text_input("ID Cliente / Orden de Trabajo")
        if st.button("Finalizar Instalación"):
            if cli:
                c.execute("UPDATE stock SET estado='INSTALADO', poseedor=? WHERE sn=?", (cli, s_i))
                registrar_movimiento(s_i, "Instalación", st.session_state.nombre, cli, st.session_state.nombre)
                st.success("Instalado")
                st.rerun()
    else: st.info("No tienes material.")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.auth = False
    st.rerun()
