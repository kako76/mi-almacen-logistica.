import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Altri Telecom - Sistema Pro", layout="wide")

# --- CONEXIÓN BASE DE DATOS ---
conn = sqlite3.connect('altri_final.db', check_same_thread=False)
c = conn.cursor()

# Tablas: Usuarios, Stock y Movimientos (Historial)
c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
             (user TEXT PRIMARY KEY, nombre TEXT, clave TEXT, perfil TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS stock 
             (sn TEXT PRIMARY KEY, modelo TEXT, marca TEXT, estado TEXT, poseedor TEXT, fecha_actualizacion TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS movimientos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, sn TEXT, tipo TEXT, origen TEXT, destino TEXT, fecha TEXT, usuario_accion TEXT)''')
conn.commit()

# Crear admin por defecto
c.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'Administrador', '1234', 'admin')")
conn.commit()

# --- FUNCIONES AUXILIARES ---
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
    col1, col2 = st.columns(2)
    with col1:
        u = st.text_input
