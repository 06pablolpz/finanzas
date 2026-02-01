import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Configuración con estilo moderno
st.set_page_config(page_title="Love & Money 💖", layout="wide")

# CSS para ponerlo más "mono"
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: white; padding: 15px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

conn = sqlite3.connect('finanzas_v2.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS movs (user TEXT, fecha TEXT, cat TEXT, monto REAL, tipo TEXT)')
conn.commit()

# --- SELECTOR DE USUARIO ---
user = st.sidebar.selectbox("👤 ¿Quién está usando la app?", ["Pablo 🦁", "Novia 🦒"])
st.title(f"Radar de {user}")

# Formulario mejorado
with st.sidebar.expander("➕ Añadir nuevo movimiento", expanded=True):
    tipo = st.radio("Tipo", ["Gasto 💸", "Ingreso 💵", "Inversión 📈"])
    monto = st.number_input("Cantidad (€)", min_value=0.0)
    cat = st.selectbox("Categoría", ["🍔 Comida", "🏠 Casa", "🛍️ Compras", "🍿 Ocio", "📈 Bolsa", "🏦 Ahorro"])
    if st.button("Registrar"):
        c.execute("INSERT INTO movs VALUES (?, date('now'), ?, ?, ?)", (user, cat, monto, tipo))
        conn.commit()
        st.balloons() # ¡Efecto visual de globos!

# Cargar datos
df = pd.read_sql_query(f"SELECT * FROM movs WHERE user='{user}'", conn)

if not df.empty:
    # Gráfico de tarta más "estético"
    fig = px.pie(df, values='monto', names='cat', 
                 hole=0.6, 
                 color_discrete_sequence=px.colors.sequential.Sunsetdark,
                 title="¿A dónde va el dinero?")
    fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("¡Nada por aquí! Empieza a anotar tus gastos.")
