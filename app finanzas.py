import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Family Wealth 💎", page_icon="💰", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
def set_theme(user):
    if user == "Lucía":
        # TEMA LUCÍA: Degradados Rosas/Morados, fuentes suaves
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        }
        div.stButton > button {
            background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 99%);
            color: white; border: none; border-radius: 20px; font-weight: bold;
        }
        [data-testid="stMetricValue"] {
            color: #D63384; font-family: 'Helvetica Neue', sans-serif;
        }
        h1, h2, h3 { color: #8A2BE2; }
        </style>
        """, unsafe_allow_html=True)
        return ["#FF69B4", "#8A2BE2", "#FFB6C1", "#9370DB", "#C71585"]
    else:
        # TEMA PABLO: Minimalista Oscuro/Azul
        st.markdown("""
        <style>
        .stApp { background-color: #f4f6f9; }
        div.stButton > button {
            background-color: #2E86C1; color: white; border-radius: 5px;
        }
        h1, h2, h3 { color: #2C3E50; }
        </style>
        """, unsafe_allow_html=True)
        return px.colors.sequential.Blues[::-1]

# --- BASE DE DATOS ---
conn = sqlite3.connect('finanzas_pro.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS movs 
             (user TEXT, fecha TEXT, cat TEXT, concepto TEXT, monto REAL, tipo TEXT)''')
conn.commit()

# --- SIDEBAR: LOGIN ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2353/2353678.png", width=100)
st.sidebar.title("🔐 Acceso Seguro")

user = st.sidebar.selectbox("Usuario", ["Seleccionar", "Pablo", "Lucía"])
pin = st.sidebar.text_input("PIN de Acceso", type="password")

# PINS (¡Cámbialos aquí!)
AUTH = {"Pablo": "1234", "Lucía": "5678"}

if user != "Seleccionar" and pin == AUTH.get(user):
    colors = set_theme(user)
    st.title(f"Hola, {user} 👋")
    
    # --- PESTAÑAS DE NAVEGACIÓN ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📅 Calendario", "🎯 Objetivos", "➕ Añadir"])

    # Cargar datos
    df = pd.read_sql_query(f"SELECT * FROM movs WHERE user='{user}'", conn)
    df['fecha'] = pd.to_datetime(df['fecha'])

    # --- TAB 1: DASHBOARD GENERAL ---
    with tab1:
        if not df.empty:
            ingresos = df[df['tipo'] == "Ingreso 💵"]['monto'].sum()
            gastos = df[df['tipo'] == "Gasto 💸"]['monto'].sum()
            inversiones = df[df['tipo'] == "Inversión 📈"]['monto'].sum()
            ahorro = ingresos - gastos
            
            # KPI Cards con estilo
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Patrimonio Neto", f"{(ahorro + inversiones):,.0f} €", "💰 Total Acumulado")
            col2.metric("Gastos Totales", f"{gastos:,.0f} €", "- vs mes pasado", delta_color="inverse")
            col3.metric("Inversiones", f"{inversiones:,.0f} €", "🚀 Creciendo")
            
            # Health Score (Puntuación inventada basada en tasa de ahorro)
            tasa_ahorro = (ahorro / ingresos * 100) if ingresos > 0 else 0
            score = min(100, max(0, int(tasa_ahorro * 1.5)))
            col4.metric("❤️ Salud Financiera", f"{score}/100", "Puntos")

            st.divider()

            # Gráficas
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🍩 ¿En qué se va el dinero?")
                fig_pie = px.pie(df[df['tipo']=="Gasto 💸"], values='monto', names='cat', 
                                 hole=0.5, color_discrete_sequence=colors)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader("🌊 Flujo de Caja")
                fig_bar = px.bar(df, x='fecha', y='monto', color='tipo', 
                                 barmode='group', color_discrete_sequence=colors)
                st.plotly_chart(fig_bar, use_container_width=True)

        else:
            st.info("👋 ¡Bienvenido! Empieza añadiendo datos en la pestaña 'Añadir'.")

    # --- TAB 2: CALENDARIO DE GASTOS ---
    with tab2:
        st.header("📅 Tu Diario de Gastos")
        if not df.empty:
            # Heatmap de intensidad de gasto
            gastos_dia = df[df['tipo']=="Gasto 💸"].groupby('fecha')['monto'].sum().reset_index()
            
            fig_cal = px.scatter(gastos_dia, x="fecha", y="monto", size="monto", color="monto",
                                 title="Intensidad de Gastos por Día (Círculos grandes = Más gasto)",
                                 color_continuous_scale="Reds" if user == "Pablo" else "Purples")
            st.plotly_chart(fig_cal, use_container_width=True)
            
            # Lista detallada
            st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True)
        else:
            st.write("Añade movimientos para ver tu calendario.")

    # --- TAB 3: OBJETIVOS Y METAS ---
    with tab3:
        st.header("🎯 Tus Metas Financieras")
        
        # Meta 1: Presupuesto Mensual
        st.subheader("🚦 Semáforo de Presupuesto Mensual")
        presupuesto = 1500 # Ejemplo, podrías hacerlo editable
        gastado_actual = df[df['tipo']=="Gasto 💸"]['monto'].sum() if not df.empty else 0
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = gastado_actual,
            title = {'text': f"Límite: {presupuesto}€"},
            gauge = {'axis': {'range': [None, presupuesto * 1.2]},
                     'bar': {'color': "#FF69B4" if user == "Lucía" else "#2E86C1"},
                     'steps': [
                         {'range': [0, presupuesto * 0.7], 'color': "lightgreen"},
                         {'range': [presupuesto * 0.7, presupuesto], 'color': "yellow"},
                         {'range': [presupuesto, presupuesto * 1.2], 'color': "red"}],
                     'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': presupuesto}}))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Meta 2: Ahorro para algo especial
        st.subheader("✈️ Fondo para Viaje/Capricho")
        meta_viaje = 3000
        ahorrado_viaje = 1250 # Esto podrías calcularlo de una categoría "Ahorro"
        progreso = min(1.0, ahorrado_viaje / meta_viaje)
        st.progress(progreso)
        st.caption(f"Llevas {ahorrado_viaje}€ de {meta_viaje}€ (¡Tú puedes!)")

    # --- TAB 4: AÑADIR MOVIMIENTOS ---
    with tab4:
        st.header("📝 Nuevo Registro")
        with st.form("entry_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            fecha = col_a.date_input("Fecha", datetime.now())
            tipo = col_b.selectbox("Tipo", ["Gasto 💸", "Ingreso 💵", "Inversión 📈"])
            
            concepto = st.text_input("Concepto", placeholder="Ej: Cena sushi, Netflix, Nómina...")
            col_c, col_d = st.columns(2)
            cat = col_c.selectbox("Categoría", ["🏠 Vivienda", "🍔 Comida/Salidas", "🛍️ Compras", 
                                              "🚗 Transporte", "💊 Salud/Belleza", "✈️ Viajes", "💍 Caprichos"])
            monto = col_d.number_input("Importe (€)", min_value=0.0, step=0.50)
            
            submitted = st.form_submit_button("💾 Guardar Movimiento")
            if submitted:
                c.execute("INSERT INTO movs VALUES (?, ?, ?, ?, ?, ?)", 
                          (user, fecha, cat, concepto, monto, tipo))
                conn.commit()
                st.success("¡Registrado con éxito!")
                st.balloons()

elif user != "Seleccionar":
    st.error("🛑 PIN Incorrecto. Inténtalo de nuevo.")
else:
    st.info("👆 Selecciona tu usuario en la barra lateral para comenzar.")
