import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Family Wealth", page_icon="💰", layout="wide")

# --- CONEXIÓN BASE DE DATOS ---
conn = sqlite3.connect('finanzas_pro_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS movs 
             (user TEXT, fecha TEXT, cat TEXT, concepto TEXT, monto REAL, tipo TEXT)''')
conn.commit()

# --- FUNCIONES DE ESTILO ---
def get_colors(user):
    if user == "Lucía":
        # Paleta Rosa/Morada para gráficos
        return ["#FF69B4", "#9370DB", "#FF1493", "#8A2BE2", "#FFB6C1"]
    else:
        # Paleta Azul/Profesional para gráficos
        return ["#00BFFF", "#1E90FF", "#4682B4", "#87CEFA", "#2F4F4F"]

# --- BARRA LATERAL (LOGIN) ---
st.sidebar.title("🔐 Acceso")
user = st.sidebar.selectbox("Usuario", ["Seleccionar", "Pablo", "Lucía"])
pin = st.sidebar.text_input("PIN", type="password")

# PINS (Cámbialos si quieres)
AUTH = {"Pablo": "1234", "Lucía": "5678"}

if user != "Seleccionar" and pin == AUTH.get(user):
    # Colores según usuario
    colors = get_colors(user)
    
    # Título personalizado con color
    if user == "Lucía":
        st.markdown(f"<h1 style='color: #FF69B4;'>Hola, {user} 💖</h1>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h1 style='color: #1E90FF;'>Panel de Control: {user} 🦁</h1>", unsafe_allow_html=True)

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Negocios & Dashboard", "📅 Calendario", "📝 Añadir"])

    # Cargar datos del usuario
    df = pd.read_sql_query(f"SELECT * FROM movs WHERE user='{user}'", conn)
    df['fecha'] = pd.to_datetime(df['fecha'])

    # --- LISTAS DE CATEGORÍAS PERSONALIZADAS ---
    # AQUI ESTÁ EL CAMBIO: Tu lista ahora incluye ocio y vida
    cats_pablo = [
        "🎟️ Entradas", "📈 Trading",      # Negocios (Primero)
        "✈️ Viajes", "👔 Ropa",           # Lifestyle
        "🍔 Ocio/Cenas", "🏠 Casa",       # Básicos
        "🚗 Coche/Moto", "📱 Tecnología", # Caprichos
        "💸 Varios"
    ]
    
    cats_lucia = ["🏠 Vivienda", "💅 Belleza", "👗 Ropa", "✈️ Viajes", "🍔 Comida", "🏦 Ahorro", "🎁 Regalos"]
    
    lista_categorias = cats_pablo if user == "Pablo" else cats_lucia

    # ---------------------------------------------------------
    # PESTAÑA 1: DASHBOARD (INTELIGENTE)
    # ---------------------------------------------------------
    with tab1:
        if not df.empty:
            # 1. VISIÓN GENERAL
            ingresos = df[df['tipo'] == "Ingreso 💵"]['monto'].sum()
            gastos = df[df['tipo'] == "Gasto 💸"]['monto'].sum()
            balance = ingresos - gastos
            
            # Métricas Generales
            c1, c2, c3 = st.columns(3)
            c1.metric("Balance Total", f"{balance:,.2f} €", delta_color="normal")
            c2.metric("Ingresos Totales", f"{ingresos:,.2f} €")
            c3.metric("Gastos Totales", f"{gastos:,.2f} €", delta_color="inverse")
            
            st.divider()

            # 2. SECCIÓN EXCLUSIVA PABLO (NEGOCIOS)
            if user == "Pablo":
                st.subheader("💼 Rendimiento de Negocios")
                
                # Calcular Entradas
                df_entradas = df[df['cat'] == "🎟️ Entradas"]
                ing_ent = df_entradas[df_entradas['tipo'] == "Ingreso 💵"]['monto'].sum()
                gas_ent = df_entradas[df_entradas['tipo'] == "Gasto 💸"]['monto'].sum()
                profit_ent = ing_ent - gas_ent

                # Calcular Trading
                df_trading = df[df['cat'] == "📈 Trading"]
                ing_trad = df_trading[df_trading['tipo'] == "Ingreso 💵"]['monto'].sum()
                gas_trad = df_trading[df_trading['tipo'] == "Gasto 💸"]['monto'].sum() 
                profit_trad = ing_trad - gas_trad

                # Tarjetas de Negocio
                b1, b2 = st.columns(2)
                b1.metric("🎟️ Beneficio Entradas", f"{profit_ent:,.2f} €", f"Ingresos: {ing_ent:,.0f}€")
                b2.metric("📈 Beneficio Trading", f"{profit_trad:,.2f} €", f"Ingresos: {ing_trad:,.0f}€")

            # 3. GRÁFICOS GENERALES (PARA AMBOS)
            st.subheader("Visión Global")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                # Tarta de gastos
                fig_pie = px.pie(df[df['tipo']=="Gasto 💸"], values='monto', names='cat', 
                                 title="Distribución de Gastos", hole=0.4, 
                                 color_discrete_sequence=colors)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_g2:
                # Evolución temporal
                fig_line = px.bar(df, x='fecha', y='monto', color='tipo', 
                                  title="Flujo de dinero en el tiempo", 
                                  color_discrete_map={"Ingreso 💵": "#00CC96", "Gasto 💸": "#EF553B", "Inversión 📈": "#636EFA"})
                st.plotly_chart(fig_line, use_container_width=True)

        else:
            st.info("👋 No hay datos aún. Ve a la pestaña 'Añadir' para empezar.")

    # ---------------------------------------------------------
    # PESTAÑA 2: CALENDARIO
    # ---------------------------------------------------------
    with tab2:
        st.subheader("📅 Tu mes día a día")
        if not df.empty:
            # Gráfico de dispersión (Burbujas)
            fig_cal = px.scatter(df, x="fecha", y="monto", size="monto", color="cat",
                                 hover_data=['concepto'], title="Mapa de Movimientos",
                                 color_discrete_sequence=colors)
            st.plotly_chart(fig_cal, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(df[['fecha', 'tipo', 'cat', 'concepto', 'monto']].sort_values('fecha', ascending=False), use_container_width=True)

    # ---------------------------------------------------------
    # PESTAÑA 3: AÑADIR (FORMULARIO)
    # ---------------------------------------------------------
    with tab3:
        st.header("📝 Nuevo Movimiento")
        with st.form("main_form", clear_on_submit=True):
            col_in1, col_in2 = st.columns(2)
            fecha = col_in1.date_input("Fecha", datetime.now())
            tipo = col_in2.radio("Tipo", ["Gasto 💸", "Ingreso 💵", "Inversión 📈"], horizontal=True)
            
            col_in3, col_in4 = st.columns(2)
            # Lista de categorías dinámica según quién sea
            cat = col_in3.selectbox("Categoría", lista_categorias)
            monto = col_in4.number_input("Cantidad (€)", min_value=0.0, step=10.0)
            
            concepto = st.text_input("Concepto / Notas", placeholder="Ej: Venta de entradas VIP, Chaqueta nueva, Vuelo a Roma...")
            
            if st.form_submit_button("💾 Guardar Registro"):
                c.execute("INSERT INTO movs VALUES (?, ?, ?, ?, ?, ?)", 
                          (user, fecha, cat, concepto, monto, tipo))
                conn.commit()
                st.success(f"Añadido a {cat}")
                st.balloons() 

elif user != "Seleccionar":
    st.error("PIN Incorrecto")
