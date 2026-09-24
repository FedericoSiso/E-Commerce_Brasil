import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración inicial
st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

# 2. Motor de Base de Datos
@st.cache_data
def load_data(query):
    # Conexión lista para la nube apuntando a la BD optimizada
    db_path = "ecommerce_brasil_lite.db"
    
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 3. Consultas para KPIs Superiores
query_kpis = """
SELECT 
    SUM(payment_value) as Total_Ingresos,
    COUNT(DISTINCT order_id) as Total_Ordenes,
    (SUM(payment_value) / COUNT(DISTINCT order_id)) as Ticket_Promedio
FROM payments
"""
df_kpis = load_data(query_kpis)
ingresos = df_kpis['Total_Ingresos'].iloc[0] / 1000000
ticket_promedio = df_kpis['Ticket_Promedio'].iloc[0]

query_flete = "SELECT AVG(freight_value) as Flete_Prom FROM items"
df_flete = load_data(query_flete)
flete_promedio = df_flete['Flete_Prom'].iloc[0]

query_csat = "SELECT AVG(review_score) as CSAT FROM reviews"
df_csat = load_data(query_csat)
score_promedio = df_csat['CSAT'].iloc[0]

# 4. Construcción de la Interfaz (UI)
st.title("Data Cleansing a Escala: El Caso E-Commerce Brasil")

# Fila superior (Tarjetas)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ingresos Totales", f"${ingresos:.2f} mill.")
with col2:
    st.metric("Ticket Promedio (AOV)", f"${ticket_promedio:.2f}")
with col3:
    st.metric("Costo de Flete Promedio", f"${flete_promedio:.2f}")
with col4:
    st.metric("Satisfacción del Cliente", f"{score_promedio:.2f}")

st.divider()

# DECLARACIÓN DEL GRID (La línea que te faltaba para evitar el NameError)
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

# --- GRÁFICO 1 ---
with row1_col1:
    st.subheader("Evolución Histórica de Ingresos")
    st.caption("Tendencia de facturación mensual (según fecha de envío).")
    
    query_line = """
    SELECT 
        STRFTIME('%Y-%m', i.shipping_limit_date) as Mes,
        SUM(p.payment_value) as Ingresos
    FROM payments p
    JOIN items i ON p.order_id = i.order_id
    WHERE i.shipping_limit_date IS NOT NULL
    GROUP BY Mes
    ORDER BY Mes
    """
    df_line = load_data(query_line)
    
    if not df_line.empty:
        fig_line = px.line(df_line, x='Mes', y='Ingresos', line_shape='spline')
        fig_line.update_traces(line_color='#1E90FF', line_width=3)
        fig_line.update_layout(plot_bgcolor='white', xaxis_title="", yaxis_title="Ingresos Totales")
        st.plotly_chart(fig_line, use_container_width=True)

# --- GRÁFICO 2 ---
with row1_col2:
    st.subheader("Comportamiento de Compra por Método de Pago")
    st.caption("Relación entre costo logístico y el gasto del cliente.")
    
    query_scatter = """
    SELECT 
        p.payment_type,
        AVG(p.payment_value) as Ticket_Promedio,
        AVG(i.freight_value) as Flete_Promedio,
        COUNT(DISTINCT p.order_id) as Volumen_Ventas
    FROM payments p
    JOIN items i ON p.order_id = i.order_id
    GROUP BY p.payment_type
    """
    df_scatter = load_data(query_scatter)
    
    if not df_scatter.empty:
        fig_scatter = px.scatter(
            df_scatter, x='Flete_Promedio', y='Ticket_Promedio', 
            size='Volumen_Ventas', color='payment_type',
            hover_name='payment_type', size_max=40
        )
        fig_scatter.update_layout(plot_bgcolor='white')
        st.plotly_chart(fig_scatter, use_container_width=True)

# --- GRÁFICO 3 ---
with row2_col1:
    st.subheader("Impacto del Costo de Envío en la Satisfacción")
    st.caption("Costo logístico promedio soportado en cada nivel de calificación.")
    
    query_bar = """
    SELECT 
        CAST(r.review_score AS TEXT) as Score,
        AVG(i.freight_value) as Flete_Promedio
    FROM reviews r
    JOIN items i ON r.order_id = i.order_id
    WHERE r.review_score IS NOT NULL
    GROUP BY r.review_score
    ORDER BY r.review_score ASC
    """
    df_bar = load_data(query_bar)
    
    if not df_bar.empty:
        fig_bar = px.bar(df_bar, x='Flete_Promedio', y='Score', orientation='h', text_auto='.2f')
        fig_bar.update_traces(marker_color='#1E90FF', textposition='outside')
        fig_bar.update_layout(plot_bgcolor='white', xaxis_title="Flete Promedio ($)", yaxis_title="Score (1-5)")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- GRÁFICO 4 ---
with row2_col2:
    st.subheader("KPI: Satisfacción Global del Cliente (CSAT)")
    st.caption("Calificación media actual frente al objetivo corporativo de 4.20.")
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score_promedio,
        number = {'valueformat': '.2f'},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [1, 5], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#1E90FF"},
            'bgcolor': "lightgray",
            'borderwidth': 2,
            'bordercolor': "white",
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': 4.20
            }
        }
    ))
    fig_gauge.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)