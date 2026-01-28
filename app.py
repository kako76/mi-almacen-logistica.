import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# Configuración de la página
st.set_page_config(page_title="Logística Altri Telecom", layout="wide")

# Conexión a Base de Datos
conn = sqlite3.connect('almacen_altri.db', check_same_thread=False)
c = conn.cursor()

# CREACIÓN DE TABLAS (Usuarios, Stock e Historial)
c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
             (user TEXT PRIMARY KEY, password TEXT, nombre TEXT, perfil TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS stock 
             (id INTEGER PRIMARY KEY, codigo TEXT, material TEXT, familia TEXT, sn TEXT UNIQUE, estado TEXT, asignado_a TEXT)''')

# Insertar admin por defecto si no existe
admin_pass = hashlib.sha256("1234".encode()).hexdigest()
c.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', ?, 'Administrador', 'admin')", (admin_pass,))
conn.commit()

# LISTA ACTUALIZADA DE MATERIALES (Basada en tus fotos)
CATALOGO = {
    "4910034": "FTTH Exterior HUAWEI 100m",
    "4910041": "FTTH Exterior HUAWEI 80m",
    "4910113": "PRODIGY ACOMETIDA EXTERIOR 80M-MO",
    "4910152": "FTTH Exterior HUAWEI 40m",
    "4920210": "ACOMETIDA INTERIOR SC/APC 20M-MMV",
    "R075L6SB2": "Router ZTE LiveBox 6s Wifi6",
    "R085L6SW2": "Arcadyan LiveBox 6s Wifi6",
    "RM14670W4": "Router FTTH Sagemcom Fast 5670 wifi 6",
    "RU14366W2": "Router recuperado Sagecom 5366S",
    "702452": "ARCADYAN LIVEBOX INFINITY (XGSPON)",
    "702478": "ARCADYAN LIVEBOX 7",
    "702479": "ZTE LIVEBOX 7",
    "732426": "P-ARCADYAN LIVEBOX 6 PLUS",
    "G050TVNN2": "Decodificador TV Neutro"
}

# --- FUNCIONES DE SEGURIDAD ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# --- INTERFAZ DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.header("🔑 Acceso Altri Telecom")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type='password')
    if st.button("Entrar"):
        c.execute('SELECT password, perfil FROM usuarios WHERE user = ?', (usuario,))
        data = c.fetchone()
        if data and check_hashes(clave, data[0]):
            st.session_state['logged_in'] = True
            st.session_state['user'] = usuario
            st.session_state['perfil'] = data[1]
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos")
else:
    # --- MENÚ PRINCIPAL ---
    st.sidebar.title(f"Bienvenido, {st.session_state['user']}")
    menu = ["📦 Ver Stock", "📥 Entrada Material", "🚚 Entrega a Técnico", "👥 Gestión Usuarios"]
    
    # Restringir gestión de usuarios solo a admin
    if st.session_state['perfil'] != 'admin':
        menu.remove("👥 Gestión Usuarios")
        
    choice = st.sidebar.selectbox("Menú", menu)

    if choice == "📦 Ver Stock":
        st.header("Inventario Actual")
        df = pd.read_sql_query("SELECT codigo, material, sn, estado, asignado_a FROM stock", conn)
        st.dataframe(df, use_container_width=True)

    elif choice == "📥 Entrada Material":
        st.header("Registro de Material Nuevo")
        col1, col2 = st.columns(2)
        with col1:
            modelo = st.selectbox("Selecciona Material", list(CATALOGO.keys()), format_func=lambda x: f"{x} - {CATALOGO[x]}")
        with col2:
            sns = st.text_area("Pega los Números de Serie (uno por línea)")
        
        if st.button("Guardar en Almacén"):
            lista_sn = [s.strip() for s in sns.split('\n') if s.strip()]
            for s in lista_sn:
                try:
                    c.execute("INSERT INTO stock (codigo, material, sn, estado) VALUES (?,?,?,?)", 
                             (modelo, CATALOGO[modelo], s, "ALMACEN"))
                except:
                    st.warning(f"El S/N {s} ya estaba registrado.")
            conn.commit()
            st.success("Material registrado correctamente")

    elif choice == "🚚 Entrega a Técnico":
        st.header("Asignar Material a Técnico")
        c.execute("SELECT nombre FROM usuarios WHERE perfil = 'tecnico'")
        tecnicos = [t[0] for t in c.fetchall()]
        
        if tecnicos:
            tec = st.selectbox("Selecciona el Técnico", tecnicos)
            sns_entrega = st.text_area("S/N de los equipos entregados")
            if st.button("Confirmar Entrega"):
                lista_sn = [s.strip() for s in sns_entrega.split('\n') if s.strip()]
                for s in lista_sn:
                    c.execute("UPDATE stock SET estado='ENTREGADO', asignado_a=? WHERE sn=?", (tec, s))
                conn.commit()
                st.success(f"Equipos asignados a {tec}")
        else:
            st.info("Primero debes crear técnicos en el menú 'Gestión Usuarios'")

    elif choice == "👥 Gestión Usuarios":
        st.header("Control de Personal")
        with st.expander("Crear Nuevo Usuario"):
            nuevo_u = st.text_input("Nombre de Usuario (para login)")
            nuevo_n = st.text_input("Nombre Real del Técnico")
            nuevo_p = st.text_input("Contraseña", type='password')
            tipo = st.selectbox("Perfil", ["tecnico", "admin"])
            if st.button("Crear"):
                h_p = make_hashes(nuevo_p)
                try:
                    c.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (nuevo_u, h_p, nuevo_n, tipo))
                    conn.commit()
                    st.success(f"Usuario {nuevo_u} creado")
                except:
                    st.error("El usuario ya existe")
        
        st.subheader("Usuarios actuales")
        usuarios_df = pd.read_sql_query("SELECT user, nombre, perfil FROM usuarios", conn)
        st.table(usuarios_df)

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()
