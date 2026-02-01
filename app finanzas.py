import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Configuración inicial
st.set_page_config(page_title="Personal Finance Pro", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
conn = sqlite3.connect('finanzas_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS movs (user TEXT, pin TEXT, fecha TEXT, cat TEXT, monto REAL, tipo TEXT)')
conn.commit()

# --- LOGIN Y PRIVACIDAD ---
st.sidebar.title("🔐 Acceso Privado")
usuario_activo = st.sidebar.selectbox("¿Quién eres?", ["Seleccionar", "Pablo", "Lucía"])
pin_introducido = st.sidebar.text_input("Introduce tu PIN", type="password")

# PINS de ejemplo (Cámbialos por los que queráis)
pins = {"Pablo": "1234", "Lucía": "5678"}

# --- ESTILOS PERSONALIZADOS (MODO PREMIUM) ---
if usuario_activo == "Lucía":
    primary_color = "#FF69B4"  # Rosa
    secondary_color = "#8A2BE2" # Morado
    bg_style = f"""
    <style>
    .stApp {{ background: linear-gradient(to right, #ff99cc, #cc99ff); }}
    .stMetric {{ background-color: rgba(255, 255, 255, 0.8); border-radius: 20px; border: 2px solid #FF69B4; }}
    </style>
    """
else:
    primary_color = "#00BFFF" # Azul
    secondary_color = "#1E90FF"
    bg_style = """
    <style>
    .stApp { background-color: #f0f4f7; }
    .stMetric { background-color: white; border-radius: 20px; box-shadow: 5px 5px 15px rgba(0,0,0,0.1); }
    </style>
    """
st.markdown(bg_style, unsafe_allow_html=True)

# --- VALIDACIÓN DE PRIVACIDAD ---
if usuario_activo != "Seleccionar" and pin_introducido == pins.get(usuario_activo):
    st.title(f"✨ Panel de {usuario_activo}")
    
    # Lógica de Datos
    df = pd.read_sql_query(f"SELECT * FROM movs WHERE user='{usuario_activo}'", conn)
    
    # Cálculos de Patrimonio
    ingresos = df[df['tipo'] == "Ingreso 💵"]['monto'].sum()
    gastos = df[df['tipo'] == "Gasto 💸"]['monto'].sum()
    inversiones = df[df['tipo'] == "Inversión 📈"]['monto'].sum()
    patrimonio = (ingresos + inversiones) - gastos

    # KPIs Visuales
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Patrimonio Total", f"{patrimonio:,.2f} €")
    m2.metric("📉 Gastos Mes", f"{gastos:,.2f} €")
    m3.metric("🚀 Inversiones", f"{inversiones:,.2f} €")

    st.markdown("---")

    # Formulario de entrada
    with st.expander("📝 Añadir Movimiento Nuevo"):
        c1, c2, c3 = st.columns(3)
        tipo = c1.selectbox("Tipo", ["Gasto 💸", "Ingreso 💵", "Inversión 📈"])
        cat = c2.selectbox("Categoría", ["🍔 Comida", "🏠 Casa", "🛍️ Compras", "🍿 Ocio", "🏦 Inversión", "🚗 Viajes"])
        monto = c3.number_input("Cantidad (€)", min_value=0.0)
        if st.button("Registrar en mi cuenta"):
            c.execute("INSERT INTO movs VALUES (?, ?, date('now'), ?, ?, ?)", 
                      (usuario_activo, pin_introducido, cat, monto, tipo))
            conn.commit()
            st.balloons()
            st.rerun()

    # Gráficos Pro
    if not df.empty:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig = px.pie(df[df['tipo']=="Gasto 💸"], values='monto', names='cat', 
                         hole=0.7, title="Distribución de Gastos",
                         color_discrete_sequence=[primary_color, secondary_color, "#FFD700"])
            st.plotly_chart(fig, use_container_width=True)
        with col_chart2:
            df['fecha'] = pd.to_datetime(df['fecha'])
            fig_line = px.area(df, x='fecha', y='monto', color='tipo', title="Histórico Financiero")
            st.plotly_chart(fig_line, use_container_width=True)

elif usuario_activo != "Seleccionar":
    st.error("❌ PIN incorrecto. Acceso denegado.")
else:
    st.info("👋 Por favor, selecciona tu usuario en la barra lateral para empezar.")
