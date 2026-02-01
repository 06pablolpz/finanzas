import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import calendar
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Family Wealth", page_icon="💰", layout="wide")

# --- CONEXIÓN BASE DE DATOS ---
conn = sqlite3.connect('finanzas_pro_v5.db', check_same_thread=False)
c = conn.cursor()

# Tablas
c.execute('''CREATE TABLE IF NOT EXISTS movs 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, fecha TEXT, cat TEXT, concepto TEXT, monto REAL, tipo TEXT)''')
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
    
    # Encabezado
    color_titulo = "#FF69B4" if user == "Lucía" else "#1E90FF"
    st.markdown(f"<h1 style='color: {color_titulo};'>Hola, {user} 👋</h1>", unsafe_allow_html=True)

    # --- PESTAÑAS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📅 Calendario Visual", "✏️ Gestión & Edición", "💰 Huchas", "➕ Añadir"])

    # Cargar datos
    df = pd.read_sql_query(f"SELECT * FROM movs WHERE user='{user}'", conn)
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Listas Categorías
    cats_pablo = ["🎟️ Entradas", "📈 Trading", "✈️ Viajes", "👔 Ropa", "🍔 Ocio/Cenas", "🏠 Casa", "🚗 Coche", "💸 Varios"]
    cats_lucia = ["🏠 Vivienda", "💅 Belleza", "👗 Ropa", "✈️ Viajes", "🍔 Comida", "🏦 Ahorro General", "🎁 Regalos"]
    lista_categorias = cats_pablo if user == "Pablo" else cats_lucia

    # ---------------------------------------------------------
    # TAB 1: DASHBOARD
    # ---------------------------------------------------------
    with tab1:
        if not df.empty:
            ingresos = df[df['tipo'] == "Ingreso 💵"]['monto'].sum()
            gastos = df[df['tipo'] == "Gasto 💸"]['monto'].sum()
            balance = ingresos - gastos
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Balance Disponible", f"{balance:,.2f} €")
            c2.metric("Ingresos", f"{ingresos:,.2f} €")
            c3.metric("Gastos", f"{gastos:,.2f} €", delta_color="inverse")
            st.divider()
            
            # Gráficas
            g1, g2 = st.columns(2)
            with g1:
                fig_pie = px.pie(df[df['tipo']=="Gasto 💸"], values='monto', names='cat', title="Gastos", hole=0.4, color_discrete_sequence=colors)
                st.plotly_chart(fig_pie, use_container_width=True)
            with g2:
                fig_bar = px.bar(df, x='fecha', y='monto', color='tipo', title="Evolución", color_discrete_map={"Ingreso 💵": "#00CC96", "Gasto 💸": "#EF553B"})
                st.plotly_chart(fig_bar, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: CALENDARIO VISUAL (TIPO APP)
    # ---------------------------------------------------------
    with tab2:
        st.subheader("📅 Tu Agenda Financiera")
        
        # Selectores de Fecha
        col_cal1, col_cal2 = st.columns(2)
        year_sel = col_cal1.selectbox("Año", [2024, 2025, 2026], index=2)
        month_sel = col_cal2.selectbox("Mes", list(calendar.month_name)[1:], index=datetime.now().month-1)
        
        # Lógica del Calendario
        month_idx = list(calendar.month_name).index(month_sel)
        cal = calendar.monthcalendar(year_sel, month_idx)
        
        # Cabecera Días
        dias_sem = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
        cols = st.columns(7)
        for idx, dia in enumerate(dias_sem):
            cols[idx].markdown(f"**{dia}**", unsafe_allow_html=True)
            
        # Dibujar Rejilla
        for week in cal:
            cols = st.columns(7)
            for idx, day in enumerate(week):
                with cols[idx]:
                    if day != 0:
                        # Estilo de caja para el día
                        st.markdown(f"""
                        <div style="
                            background-color: {'#262730' if user=='Pablo' else '#FFF0F5'}; 
                            padding: 10px; border-radius: 10px; 
                            border: 1px solid {'#444' if user=='Pablo' else '#FFB6C1'}; 
                            min-height: 100px;">
                            <strong style='color: {'white' if user=='Pablo' else '#D63384'}'>{day}</strong>
                        """, unsafe_allow_html=True)
                        
                        # Buscar movimientos de este día
                        fecha_actual = f"{year_sel}-{month_idx:02d}-{day:02d}"
                        movs_dia = df[df['fecha'].dt.strftime('%Y-%m-%d') == fecha_actual]
                        
                        if not movs_dia.empty:
                            for _, row in movs_dia.iterrows():
                                # Pill visual (Etiqueta pequeña)
                                color_pill = "#EF553B" if row['tipo'] == "Gasto 💸" else "#00CC96"
                                st.markdown(f"""
                                <div style="background-color: {color_pill}; color: white; padding: 2px 5px; border-radius: 4px; font-size: 10px; margin-bottom: 2px;">
                                {row['monto']:.0f}€
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TAB 3: GESTIÓN Y EDICIÓN (MODIFICABLE)
    # ---------------------------------------------------------
    with tab3:
        st.subheader("✏️ Editar Movimientos")
        st.info("💡 Haz doble clic en cualquier celda para editarla. Al terminar, pulsa el botón 'Guardar Cambios'.")
        
        # Editor de Datos (Data Editor)
        if not df.empty:
            # Ocultamos la columna 'user' para no liarla
            df_editor = df.drop(columns=['user']).copy()
            
            edited_df = st.data_editor(
                df_editor,
                column_config={
                    "id": st.column_config.NumberColumn(disabled=True), # El ID no se toca
                    "fecha": st.column_config.DateColumn("Fecha"),
                    "cat": st.column_config.SelectboxColumn("Categoría", options=lista_categorias),
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=["Gasto 💸", "Ingreso 💵", "Inversión 📈"]),
                    "monto": st.column_config.NumberColumn("Monto (€)", format="%.2f €")
                },
                num_rows="dynamic",
                key="editor_movimientos"
            )
            
            if st.button("💾 Guardar Cambios en Base de Datos"):
                # Proceso de guardado: Borramos y reescribimos los movimientos editados
                # (Esta es la forma más segura para SQLite simple)
                try:
                    # 1. Iterar sobre las filas editadas
                    for index, row in edited_df.iterrows():
                        # Si tiene ID, actualizamos
                        if pd.notna(row['id']):
                            c.execute("""UPDATE movs SET fecha=?, cat=?, concepto=?, monto=?, tipo=? 
                                         WHERE id=? AND user=?""", 
                                      (row['fecha'].strftime('%Y-%m-%d'), row['cat'], row['concepto'], 
                                       row['monto'], row['tipo'], row['id'], user))
                    
                    conn.commit()
                    st.success("✅ ¡Base de datos actualizada correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
        else:
            st.write("No hay movimientos para editar.")

    # ---------------------------------------------------------
    # TAB 4: HUCHAS
    # ---------------------------------------------------------
    with tab4:
        st.subheader("🎯 Metas de Ahorro")
        with st.expander("➕ Crear Nueva Hucha"):
            with st.form("new_hucha"):
                name = st.text_input("Nombre")
                goal = st.number_input("Objetivo (€)", min_value=1.0)
                if st.form_submit_button("Crear"):
                    c.execute("INSERT INTO ahorros (user, nombre, meta, actual) VALUES (?, ?, ?, 0)", (user, name, goal))
                    conn.commit()
                    st.rerun()
        
        huchas = pd.read_sql_query(f"SELECT * FROM ahorros WHERE user='{user}'", conn)
        for _, row in huchas.iterrows():
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.write(f"**{row['nombre']}**")
                progreso = min(1.0, row['actual'] / row['meta'])
                st.progress(progreso)
                st.caption(f"{row['actual']}€ / {row['meta']}€")
            with col_h2:
                add = st.number_input("Insertar €", key=f"add_{row['id']}")
                if st.button("➕", key=f"btn_{row['id']}"):
                    c.execute("UPDATE ahorros SET actual = ? WHERE id = ?", (row['actual'] + add, row['id']))
                    conn.commit()
                    st.rerun()
            st.divider()

    # ---------------------------------------------------------
    # TAB 5: AÑADIR (RÁPIDO)
    # ---------------------------------------------------------
    with tab5:
        st.header("📝 Añadir Rápido")
        with st.form("fast_add", clear_on_submit=True):
            col_in1, col_in2 = st.columns(2)
            fecha = col_in1.date_input("Fecha", datetime.now())
            tipo = col_in2.radio("Tipo", ["Gasto 💸", "Ingreso 💵", "Inversión 📈"], horizontal=True)
            cat = st.selectbox("Categoría", lista_categorias)
            monto = st.number_input("Cantidad (€)", min_value=0.0)
            concepto = st.text_input("Concepto")
            
            if st.form_submit_button("Guardar"):
                # Insertamos con NULL en ID para que sea autoincremental
                c.execute("INSERT INTO movs (user, fecha, cat, concepto, monto, tipo) VALUES (?, ?, ?, ?, ?, ?)", 
                          (user, fecha, cat, concepto, monto, tipo))
                conn.commit()
                st.success("Añadido")

elif user != "Seleccionar":
    st.error("PIN Incorrecto")
