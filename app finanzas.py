import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Family Wealth", page_icon="💰", layout="wide")

# --- CONEXIÓN BASE DE DATOS ---
conn = sqlite3.connect('finanzas_pro_v4.db', check_same_thread=False)
c = conn.cursor()

# Tabla de Movimientos (Ingresos/Gastos)
c.execute('''CREATE TABLE IF NOT EXISTS movs 
             (user TEXT, fecha TEXT, cat TEXT, concepto TEXT, monto REAL, tipo TEXT)''')

# NUEVA TABLA: Huchas y Metas de Ahorro
c.execute('''CREATE TABLE IF NOT EXISTS ahorros 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, nombre TEXT, meta REAL, actual REAL)''')
conn.commit()

# --- FUNCIONES DE ESTILO ---
def get_colors(user):
    if user == "Lucía":
        return ["#FF69B4", "#9370DB", "#FF1493", "#8A2BE2", "#FFB6C1"] # Rosas
    else:
        return ["#00BFFF", "#1E90FF", "#4682B4", "#87CEFA", "#2F4F4F"] # Azules

# --- BARRA LATERAL (LOGIN) ---
st.sidebar.title("🔐 Acceso")
user = st.sidebar.selectbox("Usuario", ["Seleccionar", "Pablo", "Lucía"])
pin = st.sidebar.text_input("PIN", type="password")

AUTH = {"Pablo": "1234", "Lucía": "5678"}

if user != "Seleccionar" and pin == AUTH.get(user):
    colors = get_colors(user)
    
    # Encabezado personalizado
    color_titulo = "#FF69B4" if user == "Lucía" else "#1E90FF"
    st.markdown(f"<h1 style='color: {color_titulo};'>Hola, {user} 👋</h1>", unsafe_allow_html=True)

    # --- PESTAÑAS (AHORA SON 4) ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💰 Huchas & Metas", "📅 Calendario", "📝 Añadir"])

    # Cargar datos generales
    df = pd.read_sql_query(f"SELECT * FROM movs WHERE user='{user}'", conn)
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Listas de categorías (Tus negocios + Lifestyle)
    cats_pablo = ["🎟️ Entradas", "📈 Trading", "✈️ Viajes", "👔 Ropa", "🍔 Ocio/Cenas", "🏠 Casa", "🚗 Coche", "💸 Varios"]
    cats_lucia = ["🏠 Vivienda", "💅 Belleza", "👗 Ropa", "✈️ Viajes", "🍔 Comida", "🏦 Ahorro General", "🎁 Regalos"]
    lista_categorias = cats_pablo if user == "Pablo" else cats_lucia

    # ---------------------------------------------------------
    # PESTAÑA 1: DASHBOARD
    # ---------------------------------------------------------
    with tab1:
        if not df.empty:
            ingresos = df[df['tipo'] == "Ingreso 💵"]['monto'].sum()
            gastos = df[df['tipo'] == "Gasto 💸"]['monto'].sum()
            balance = ingresos - gastos
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Balance Disponible", f"{balance:,.2f} €")
            c2.metric("Total Ingresado", f"{ingresos:,.2f} €")
            c3.metric("Total Gastado", f"{gastos:,.2f} €", delta_color="inverse")
            
            st.divider()

            if user == "Pablo":
                st.subheader("💼 Rendimiento de Negocios")
                # Cálculos rápidos negocios Pablo
                ent = df[df['cat'] == "🎟️ Entradas"]
                trad = df[df['cat'] == "📈 Trading"]
                ben_ent = ent[ent['tipo']=="Ingreso 💵"]['monto'].sum() - ent[ent['tipo']=="Gasto 💸"]['monto'].sum()
                ben_trad = trad[trad['tipo']=="Ingreso 💵"]['monto'].sum() - trad[trad['tipo']=="Gasto 💸"]['monto'].sum()
                
                b1, b2 = st.columns(2)
                b1.metric("🎟️ Entradas (Neto)", f"{ben_ent:,.2f} €")
                b2.metric("📈 Trading (Neto)", f"{ben_trad:,.2f} €")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_pie = px.pie(df[df['tipo']=="Gasto 💸"], values='monto', names='cat', title="Gastos", hole=0.4, color_discrete_sequence=colors)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_g2:
                fig_bar = px.bar(df, x='fecha', y='monto', color='tipo', title="Evolución", color_discrete_map={"Ingreso 💵": "#00CC96", "Gasto 💸": "#EF553B"})
                st.plotly_chart(fig_bar, use_container_width=True)

    # ---------------------------------------------------------
    # PESTAÑA 2: HUCHAS Y METAS (¡LO NUEVO DE LUCÍA!)
    # ---------------------------------------------------------
    with tab2:
        st.subheader("🎯 Mis Objetivos de Ahorro")
        
        # 1. Crear Nueva Hucha
        with st.expander("➕ Crear nueva Meta / Hucha"):
            with st.form("nueva_hucha"):
                new_name = st.text_input("Nombre de la meta", placeholder="Ej: Regalo Mamá, Boda, Coche...")
                new_meta = st.number_input("¿Cuánto dinero necesitas?", min_value=1.0)
                if st.form_submit_button("Crear Hucha"):
                    c.execute("INSERT INTO ahorros (user, nombre, meta, actual) VALUES (?, ?, ?, 0)", (user, new_name, new_meta))
                    conn.commit()
                    st.success(f"¡Hucha '{new_name}' creada!")
                    st.rerun()

        # 2. Ver y Gestionar Huchas
        huchas = pd.read_sql_query(f"SELECT * FROM ahorros WHERE user='{user}'", conn)
        
        if not huchas.empty:
            for index, row in huchas.iterrows():
                # Cálculo de progreso
                progreso = min(1.0, row['actual'] / row['meta'])
                porcentaje = int(progreso * 100)
                
                # Tarjeta visual para cada hucha
                st.write(f"### {row['nombre']}")
                col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
                
                with col_h1:
                    # Barra de progreso con color personalizado
                    st.progress(progreso)
                    st.caption(f"Tienes **{row['actual']}€** de **{row['meta']}€** ({porcentaje}%)")
                
                with col_h2:
                    # Formulario pequeño para añadir dinero a esta hucha específica
                    add_money = st.number_input(f"Añadir a {row['nombre']}", min_value=0.0, key=f"in_{row['id']}")
                
                with col_h3:
                    if st.button(f"📥 Ingresar", key=f"btn_{row['id']}"):
                        new_total = row['actual'] + add_money
                        c.execute("UPDATE ahorros SET actual = ? WHERE id = ?", (new_total, row['id']))
                        conn.commit()
                        if new_total >= row['meta']:
                            st.balloons()
                            st.success(f"¡Felicidades! Completaste: {row['nombre']}")
                        st.rerun()
                st.divider()
        else:
            st.info("No tienes metas activas. ¡Crea una arriba!")

    # ---------------------------------------------------------
    # PESTAÑA 3: CALENDARIO
    # ---------------------------------------------------------
    with tab3:
        st.subheader("📅 Histórico")
        if not df.empty:
            st.dataframe(df[['fecha', 'tipo', 'cat', 'concepto', 'monto']].sort_values('fecha', ascending=False), use_container_width=True)

    # ---------------------------------------------------------
    # PESTAÑA 4: AÑADIR GENERAL
    # ---------------------------------------------------------
    with tab4:
        st.header("📝 Registrar Movimiento Diario")
        with st.form("main_form", clear_on_submit=True):
            col_in1, col_in2 = st.columns(2)
            fecha = col_in1.date_input("Fecha", datetime.now())
            tipo = col_in2.radio("Tipo", ["Gasto 💸", "Ingreso 💵", "Inversión 📈"], horizontal=True)
            
            col_in3, col_in4 = st.columns(2)
            cat = col_in3.selectbox("Categoría", lista_categorias)
            monto = col_in4.number_input("Cantidad (€)", min_value=0.0, step=10.0)
            concepto = st.text_input("Concepto", placeholder="Detalle del gasto...")
            
            if st.form_submit_button("💾 Guardar"):
                c.execute("INSERT INTO movs VALUES (?, ?, ?, ?, ?, ?)", (user, fecha, cat, concepto, monto, tipo))
                conn.commit()
                st.success("Guardado")

elif user != "Seleccionar":
    st.error("PIN Incorrecto")
