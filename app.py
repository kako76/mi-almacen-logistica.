import streamlit as st
import pd
import sqlite3
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Telecom - Logística Pro", layout="wide")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('altri_v7_stock.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (user TEXT PRIMARY KEY, nombre TEXT, clave TEXT, perfil TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS stock (sn TEXT PRIMARY KEY, modelo TEXT, familia TEXT, marca TEXT, estado TEXT, poseedor TEXT, fecha TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS movimientos (id INTEGER PRIMARY KEY AUTOINCREMENT, sn TEXT, tipo TEXT, origen TEXT, destino TEXT, fecha TEXT, usuario_accion TEXT)')
    
    c.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios VALUES ('admin', 'Administrador', '1234', 'admin')")
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- CATÁLOGO DE MATERIALES ---
CATALOGO = {
    "ORANGE": {
        "Routers/ONT": ["ZTE LIVEBOX 7", "ARCADYAN LIVEBOX 6", "LIVEBOX INFINITY", "Nokia G-010G-P"],
        "TV": ["STB Android TV 4K", "Jade"],
        "Cableado/Accesorios": ["Acometida Interior 20m", "Acometida Interior 40m", "Acometida Exterior 80m", "PTR Óptica", "Roseta"]
    },
    "MASMOVIL": {
        "Routers/ONT": ["ZTE H3640 Wifi 6", "Sagemcom 5670", "ONT Huawei"],
        "TV": ["Agile TV Box"],
        "Cableado/Accesorios": ["Acometida Prodigy 80m", "Interior MMV 20m", "Filtro 4G", "Latiguillo Fibra"]
    }
}

def registrar_movimiento(sn, tipo, origen, destino, usuario):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO movimientos (sn, tipo, origen, destino, fecha, usuario_accion) VALUES (?,?,?,?,?,?)",
              (sn, tipo, origen, destino, fecha, usuario))
    conn.commit()

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Altri Telecom - Acceso")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        c.execute("SELECT nombre, perfil FROM usuarios WHERE user=? AND clave=?", (u, p))
        res = c.fetchone()
        if res:
            st.session_state.auth, st.session_state.usuario_id, st.session_state.nombre, st.session_state.perfil = True, u, res[0], res[1]
            st.rerun()
        else: st.error("Error de acceso")
    st.stop()

# --- INTERFAZ ---
st.sidebar.title(f"👤 {st.session_state.nombre}")
if st.session_state.perfil == 'admin':
    menu = st.sidebar.radio("Gestión", ["📊 Stock Global", "📥 Carga Inicial (25uds)", "🚚 Asignación/Albarán", "👥 Técnicos", "📑 Historial"])
else:
    menu = st.sidebar.radio("Técnico", ["🎒 Mi Mochila", "✅ Instalar", "⚠️ Defectuoso"])

# --- LÓGICA ADMIN ---
if menu == "📊 Stock Global":
    st.header("Inventario de Materiales")
    marca_f = st.selectbox("Filtrar Marca", ["TODAS", "ORANGE", "MASMOVIL"])
    query = "SELECT * FROM stock" if marca_f == "TODAS" else f"SELECT * FROM stock WHERE marca='{marca_f}'"
    df = pd.read_sql_query(query, conn)
    st.dataframe(df, use_container_width=True)

elif menu == "📥 Carga Inicial (25uds)":
    st.header("Carga Masiva de Materiales")
    st.info("Esta opción añadirá automáticamente 25 unidades de cada producto del catálogo con S/N genéricos.")
    if st.button("🚀 Cargar todo el Stock"):
        for marca, familias in CATALOGO.items():
            for familia, productos in familias.items():
                for producto in productos:
                    for i in range(1, 26):
                        sn_gen = f"{producto[:3]}-{marca[:2]}-{1000+i}"
                        c.execute("INSERT OR IGNORE INTO stock VALUES (?,?,?,?,?,?,?)",
                                 (sn_gen, producto, familia, marca, "Almacén", "ALMACEN", datetime.now().strftime("%d/%m/%Y")))
        conn.commit()
        st.success("✅ Se han añadido 25 unidades de CADA material correctamente.")

elif menu == "🚚 Asignación/Albarán":
    st.header("Entregar Material")
    c.execute("SELECT nombre FROM usuarios WHERE perfil='tecnico'")
    tecs = [t[0] for t in c.fetchall()]
    if tecs:
        t_sel = st.selectbox("Técnico", tecs)
        m_sel = st.selectbox("Marca", ["ORANGE", "MASMOVIL"])
        df_d = pd.read_sql_query(f"SELECT sn, modelo FROM stock WHERE estado='Almacén' AND marca='{m_sel}'", conn)
        items = st.multiselect("Seleccionar S/N", df_d['sn'].tolist())
        if st.button("Firmar Albarán"):
            for s in items:
                c.execute("UPDATE stock SET estado='En Mochila', poseedor=? WHERE sn=?", (t_sel, s))
                registrar_movimiento(s, "Asignación", "ALMACEN", t_sel, st.session_state.nombre)
            st.success("Material asignado. Pulsa Ctrl+P para imprimir el albarán.")
            st.table(df_d[df_d['sn'].isin(items)])
    else: st.warning("Crea técnicos primero.")

elif menu == "👥 Técnicos":
    st.header("Gestión de Usuarios")
    with st.expander("Añadir"):
        u_l, u_n, u_c = st.text_input("Login"), st.text_input("Nombre"), st.text_input("Pass")
        if st.button("Guardar"):
            c.execute("INSERT INTO usuarios VALUES (?,?,?,'tecnico')", (u_l, u_n, u_c))
            conn.commit()
            st.rerun()
    st.dataframe(pd.read_sql_query("SELECT user, nombre FROM usuarios WHERE perfil='tecnico'", conn))

elif menu == "📑 Historial":
    st.header("Movimientos")
    df_h = pd.read_sql_query("SELECT * FROM movimientos ORDER BY id DESC", conn)
    st.dataframe(df_h)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_h.to_excel(writer, index=False)
    st.download_button("📥 Descargar Excel", buffer.getvalue(), "logistica.xlsx")

# --- LÓGICA TÉCNICO ---
elif menu == "🎒 Mi Mochila":
    st.header("Mi Material")
    df_m = pd.read_sql_query(f"SELECT sn, modelo, familia FROM stock WHERE poseedor='{st.session_state.nombre}' AND estado='En Mochila'", conn)
    st.dataframe(df_m)

elif menu == "✅ Instalar":
    st.header("Instalación de Equipo")
    c.execute("SELECT sn FROM stock WHERE poseedor=? AND estado='En Mochila'", (st.session_state.nombre,))
    mis_s = [r[0] for r in c.fetchall()]
    if mis_s:
        s_i = st.selectbox("S/N", mis_s)
        cli = st.text_input("ID Cliente / Orden")
        if st.button("Finalizar Instalación"):
            if cli:
                c.execute("UPDATE stock SET estado='INSTALADO', poseedor=? WHERE sn=?", (cli, s_i))
                registrar_movimiento(s_i, "Instalación", st.session_state.nombre, cli, st.session_state.nombre)
                st.success("Instalado correctamente")
                st.rerun()
    else: st.info("No tienes material.")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.auth = False
    st.rerun()
