import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Altri Telecom - Logística", layout="wide")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('altri_v6_final.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (user TEXT PRIMARY KEY, nombre TEXT, clave TEXT, perfil TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stock 
                 (sn TEXT PRIMARY KEY, modelo TEXT, marca TEXT, estado TEXT, poseedor TEXT, fecha_actualizacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sn TEXT, tipo TEXT, origen TEXT, destino TEXT, fecha TEXT, usuario_accion TEXT)''')
    c.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios VALUES ('admin', 'Administrador', '1234', 'admin')")
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

def registrar_movimiento(sn, tipo, origen, destino, usuario):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO movimientos (sn, tipo, origen, destino, fecha, usuario_accion) VALUES (?,?,?,?,?,?)",
              (sn, tipo, origen, destino, fecha, usuario))
    conn.commit()

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Acceso Altri Telecom")
    u_input = st.text_input("Usuario")
    p_input = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        c.execute("SELECT nombre, perfil FROM usuarios WHERE user=? AND clave=?", (u_input, p_input))
        res = c.fetchone()
        if res:
            st.session_state.auth = True
            st.session_state.usuario_id = u_input
            st.session_state.nombre = res[0]
            st.session_state.perfil = res[1]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- INTERFAZ ---
st.sidebar.title(f"👤 {st.session_state.nombre}")
if st.session_state.perfil == 'admin':
    menu = st.sidebar.radio("Menú Admin", ["📊 Stock Global", "🔍 Rastreador S/N", "📥 Entrada Almacén", "🚚 Asignación", "👥 Gestión Técnicos", "📑 Historial"])
else:
    menu = st.sidebar.radio("Menú Técnico", ["🎒 Mi Mochila", "✅ Instalar", "⚠️ Defectuoso"])

# --- FUNCIONES ADMIN ---
if menu == "📊 Stock Global":
    st.header("Inventario Completo")
    df = pd.read_sql_query("SELECT * FROM stock", conn)
    st.dataframe(df, use_container_width=True)

elif menu == "🔍 Rastreador S/N":
    st.header("Buscador de Equipos")
    busqueda = st.text_input("Introduce S/N")
    if busqueda:
        c.execute("SELECT * FROM stock WHERE sn=?", (busqueda,))
        item = c.fetchone()
        if item:
            st.write(f"Estado: {item[3]} | Poseedor: {item[4]}")
            hist = pd.read_sql_query(f"SELECT * FROM movimientos WHERE sn='{busqueda}' ORDER BY id DESC", conn)
            st.table(hist)
        else:
            st.error("No encontrado")

elif menu == "📥 Entrada Almacén":
    st.header("Entrada de Material")
    marca = st.selectbox("Operadora", ["ORANGE", "MASMOVIL"])
    mod = st.text_input("Modelo")
    sns = st.text_area("S/N (uno por línea)")
    if st.button("Cargar"):
        if sns.strip() and mod:
            for s in sns.split('\n'):
                if s.strip():
                    c.execute("INSERT OR REPLACE INTO stock VALUES (?,?,?,?,?,?)", 
                             (s.strip(), mod, marca, "Almacén", "ALMACEN", datetime.now().strftime("%d/%m/%Y")))
                    registrar_movimiento(s.strip(), "Entrada", "Proveedor", "ALMACEN", st.session_state.nombre)
            st.success("Carga finalizada correctamente")
        else:
            st.warning("Falta modelo o S/N")

elif menu == "🚚 Asignación":
    st.header("Asignar a Técnico")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecs = [t[0] for t in c.fetchall()]
    if tecs:
        t_dest = st.selectbox("Técnico", tecs)
        df_disp = pd.read_sql_query("SELECT sn FROM stock WHERE estado='Almacén'", conn)
        sel = st.multiselect("Equipos", df_disp['sn'].tolist())
        if st.button("Asignar"):
            if sel:
                for s in sel:
                    c.execute("UPDATE stock SET estado='En Mochila', poseedor=? WHERE sn=?", (t_dest, s))
                    registrar_movimiento(s, "Asignación", "ALMACEN", t_dest, st.session_state.nombre)
                st.success(f"Equipos asignados a {t_dest}")
            else:
                st.warning("Selecciona al menos un equipo")
    else:
        st.warning("Crea técnicos primero en Gestión Técnicos")

elif menu == "👥 Gestión Técnicos":
    st.header("Gestión de Personal")
    with st.expander("Añadir Nuevo"):
        nu = st.text_input("Usuario Login")
        nn = st.text_input("Nombre Real")
        nc = st.text_input("Contraseña")
        if st.button("Crear"):
            if nu and nn and nc:
                c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,'tecnico')", (nu, nn, nc))
                conn.commit()
                st.success("Técnico creado con éxito")
                st.rerun()
            else:
                st.error("Todos los campos son obligatorios")
    df_u = pd.read_sql_query("SELECT user, nombre FROM usuarios WHERE perfil='tecnico'", conn)
    st.dataframe(df_u)
    borrar = st.text_input("Login para eliminar")
    if st.button("Borrar"):
        if borrar:
            c.execute("DELETE FROM usuarios WHERE user=?", (borrar,))
            conn.commit()
            st.success("Usuario eliminado")
            st.rerun()

elif menu == "📑 Historial":
    st.header("Auditoría")
    df_h = pd.read_sql_query("SELECT * FROM movimientos ORDER BY id DESC", conn)
    st.dataframe(df_h)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_h.to_excel(writer, index=False)
    st.download_button("Descargar Excel", buffer.getvalue(), "historial_altri.xlsx")

# --- FUNCIONES TÉCNICO ---
elif menu == "🎒 Mi Mochila":
    st.header("Mi Material")
    df_m = pd.read_sql_query(f"SELECT sn, modelo FROM stock WHERE poseedor='{st.session_state.nombre}' AND estado='En Mochila'", conn)
    st.dataframe(df_m)

elif menu == "✅ Instalar":
    st.header("Instalar")
    c.execute("SELECT sn FROM stock WHERE poseedor=? AND estado='En Mochila'", (st.session_state.nombre,))
    mis_s = [r[0] for r in c.fetchall()]
    if mis_s:
        s_inst = st.selectbox("S/N", mis_s)
        cli = st.text_input("Cliente")
        if st.button("Confirmar Instalación"):
            if cli:
                c.execute("UPDATE stock SET estado='INSTALADO', poseedor=? WHERE sn=?", (cli, s_inst))
                registrar_movimiento(s_inst, "Instalación", st.session_state.nombre, cli, st.session_state.nombre)
                st.success("Equipo instalado")
                st.rerun()
            else:
                st.warning("Introduce el nombre del cliente")
    else:
        st.info("No tienes material asignado")

elif menu == "⚠️ Defectuoso":
    st.header("Reportar Avería")
    c.execute("SELECT sn FROM stock WHERE poseedor=? AND estado='En Mochila'", (st.session_state.nombre,))
    mis_d = [r[0] for r in c.fetchall()]
    if mis_d:
        s_def = st.selectbox("S/N", mis_d)
        if st.button("Enviar a Taller"):
            c.execute("UPDATE stock SET estado='DEFECTUOSO', poseedor='TALLER' WHERE sn=?", (s_def,))
            registrar_movimiento(s_def, "Defectuoso", st.session_state.nombre, "TALLER", st.session_state.nombre)
            st.warning("Reporte enviado")
            st.rerun()

if st.sidebar.button("Salir"):
    st.session_state.auth = False
    st.rerun()
