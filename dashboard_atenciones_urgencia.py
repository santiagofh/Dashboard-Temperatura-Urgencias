# -*- coding: utf-8 -*-
"""
Página de Atenciones de Urgencia y Temperatura en el Sistema Circulatorio

Esta aplicación permite visualizar diversos gráficos que relacionan las atenciones de urgencia 
(con diferentes causas) con la evolución de la temperatura máxima. Cada sección incluye una breve 
explicación, el gráfico interactivo, y una tabla que muestra la información de los últimos 10 días 
utilizados en el gráfico, con la opción de descargar los datos en Excel. Al final se ofrece la opción 
de descargar las bases completas en formato CSV.
"""

# %% 1. Importar librerías y definir funciones auxiliares
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from io import BytesIO
import datetime
import numpy as np
# Función para convertir un DataFrame a Excel (en bytes)
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

# Función para convertir un DataFrame a CSV (en bytes) para las bases completas
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')

# --- Definición de paletas de colores profesionales ---

# Paleta de colores para las series de atenciones (escala de azules)
colors_atenciones = {
    'Total Sistema Circulatorio': '#08306B',       # Azul oscuro
    'Infarto agudo miocardio': '#2171B5',
    'Accidente vascular encefálico': '#4292C6',
    'Crisis hipertensiva': '#6BAED6',
    'Arritmia grave': '#9ECAE1',
    'Otras causas circulatorias': '#C6DBEF'
}

# Color para la serie de Temperatura (variable importante)
color_temperatura = '#B22222'  # Firebrick

# Paleta para los estados de alerta (importantes para resaltar)
colors_alerta = {
    'Sin Alerta': '#6c757d',                # Gris (muted)
    'Alerta temprana preventiva': '#28a745',# Verde (Bootstrap)
    'Alerta Amarilla': '#ffc107',           # Ámbar
    'Alerta Roja': '#dc3545'                # Rojo (Bootstrap)
}

# Paleta para el gráfico de grupos etarios (escala de azules, similar a atenciones)
colors_grupo_etario = {
    'Menores_1': '#08306B',
    'De_1_a_4': '#2171B5',
    'De_5_a_14': '#4292C6',
    'De_15_a_64': '#6BAED6',
    'De_65_y_mas': '#9ECAE1'
}

# %% 2. Configuración del Sidebar y carga de datos

# Definir el rango de fechas permitido y predeterminado
fecha_inicio = datetime.date(2024, 1, 1)  # Mínimo permitido
fecha_fin = datetime.date.today()           # Máximo permitido
fecha_inicio_default = datetime.date(2024, 11, 1)

st.sidebar.write("### Seleccione el rango de fechas")
rango_fechas = st.sidebar.date_input(
    "Rango de Fechas:",
    [fecha_inicio_default, fecha_fin],  # Fechas predeterminadas
    min_value=fecha_inicio,
    max_value=fecha_fin
)

# Cargar la base de datos de atenciones de urgencia
df_au = pd.read_csv("data_atenciones_urgencia/df_rm_circ_2024.csv")
df_au['fecha'] = pd.to_datetime(df_au['fecha'])
if len(rango_fechas) == 2:
    fecha_inicio_sel, fecha_fin_sel = rango_fechas
    df_au = df_au[(df_au['fecha'] >= pd.Timestamp(fecha_inicio_sel)) &
                  (df_au['fecha'] <= pd.Timestamp(fecha_fin_sel))]

# Cargar la base de datos de temperaturas
df_tmm = pd.read_csv("data_temperatura/tmm_historico_2024.csv")
df_tmm['date'] = pd.to_datetime(df_tmm['date'])
if len(rango_fechas) == 2:
    fecha_inicio_sel, fecha_fin_sel = rango_fechas
    df_tmm = df_tmm[(df_tmm['date'] >= pd.Timestamp(fecha_inicio_sel)) &
                    (df_tmm['date'] <= pd.Timestamp(fecha_fin_sel))]

# Diccionario de causas de atenciones (para usar en varios gráficos)
diccionario_causas_au = {
    1: 'Atenciones de urgencia - Total',
    12: 'Atenciones de urgencia - Total Sistema Circulatorio',
    13: 'Atenciones de urgencia - Infarto agudo miocardio',
    14: 'Atenciones de urgencia - Accidente vascular encefálico',
    15: 'Atenciones de urgencia - Crisis hipertensiva',
    16: 'Atenciones de urgencia - Arritmia grave',
    17: 'Atenciones de urgencia - Otras causas circulatorias',
    25: 'Hospitalizaciones - Total',
    22: 'Hospitalizaciones - CAUSAS SISTEMA CIRCUlATORIO',
}

# %% 3. Definición de funciones para crear gráficos y bases de datos combinadas

def grafico_area_atenciones_respiratorias(df_au, df_temp, col, title):
    """
    Gráfico de evolución de atenciones de urgencia en el Sistema Circulatorio
    junto con la evolución de la temperatura máxima.

    Se muestran las líneas temporales de atenciones según:
      - Total Sistema Circulatorio
      - Infarto agudo miocardio
      - Accidente vascular encefálico
      - Crisis hipertensiva
      - Arritmia grave
      - Otras causas circulatorias

    Además, se agrega la serie de la temperatura máxima y se muestran sus alertas.
    """
    # Filtrar y agrupar datos de atenciones por causa
    df_tota_sc = df_au[df_au['Causa'] == diccionario_causas_au[12]].groupby('fecha')[col].sum().reset_index()
    df_infarto = df_au[df_au['Causa'] == diccionario_causas_au[13]].groupby('fecha')[col].sum().reset_index()
    df_accidente = df_au[df_au['Causa'] == diccionario_causas_au[14]].groupby('fecha')[col].sum().reset_index()
    df_crisis = df_au[df_au['Causa'] == diccionario_causas_au[15]].groupby('fecha')[col].sum().reset_index()
    df_arritmia = df_au[df_au['Causa'] == diccionario_causas_au[16]].groupby('fecha')[col].sum().reset_index()
    df_otras = df_au[df_au['Causa'] == diccionario_causas_au[17]].groupby('fecha')[col].sum().reset_index()

    # Configurar las alertas de temperatura
    df_temp = df_temp.copy()
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    # Crear la figura
    fig = go.Figure()
    # Agregar trazas de atenciones (eje Y1) usando la paleta de atenciones
    fig.add_trace(go.Scatter(x=df_tota_sc['fecha'], y=df_tota_sc[col],
                             mode='lines', name='Total Sistema Circulatorio',
                             line=dict(color=colors_atenciones['Total Sistema Circulatorio'])))
    fig.add_trace(go.Scatter(x=df_infarto['fecha'], y=df_infarto[col],
                             mode='lines', name='Infarto agudo miocardio',
                             line=dict(color=colors_atenciones['Infarto agudo miocardio'])))
    fig.add_trace(go.Scatter(x=df_accidente['fecha'], y=df_accidente[col],
                             mode='lines', name='Accidente vascular encefálico',
                             line=dict(color=colors_atenciones['Accidente vascular encefálico'])))
    fig.add_trace(go.Scatter(x=df_crisis['fecha'], y=df_crisis[col],
                             mode='lines', name='Crisis hipertensiva',
                             line=dict(color=colors_atenciones['Crisis hipertensiva'])))
    fig.add_trace(go.Scatter(x=df_arritmia['fecha'], y=df_arritmia[col],
                             mode='lines', name='Arritmia grave',
                             line=dict(color=colors_atenciones['Arritmia grave'])))
    fig.add_trace(go.Scatter(x=df_otras['fecha'], y=df_otras[col],
                             mode='lines', name='Otras causas circulatorias',
                             line=dict(color=colors_atenciones['Otras causas circulatorias'])))
    # Agregar la traza de temperatura (eje Y2) con un color distintivo
    fig.add_trace(go.Scatter(x=df_temp['date'], y=df_temp['t_max'],
                             mode='lines', name='Temperatura Máxima',
                             line=dict(color=color_temperatura), yaxis='y2'))
    # Agregar marcadores de alertas usando la paleta de alerta
    for alerta, color in colors_alerta.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(x=df_alerta['date'], y=df_alerta['t_max'],
                                 mode='markers', name=f'Alerta: {alerta}',
                                 marker=dict(color=color), yaxis='y2'))

    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis=dict(title=col),
        yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right'),
        template='plotly_white',
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )

    # Crear base combinada para descarga (todos los datos usados en el gráfico)
    df_base = pd.DataFrame({
        'Fecha': df_tota_sc['fecha'],
        'Total Sistema Circulatorio': df_tota_sc[col],
        'Infarto Agudo Miocardio': df_infarto[col],
        'Accidente Vascular Encefálico': df_accidente[col],
        'Crisis Hipertensiva': df_crisis[col],
        'Arritmia Grave': df_arritmia[col],
        'Otras Causas Circulatorias': df_otras[col],
        'Temperatura Máxima': df_temp.set_index('date').reindex(df_tota_sc['fecha'], method='nearest')['t_max'].values
    })

    return fig, df_base


def grafico_porcentaje_atenciones(df, df_temp, col, title):
    """
    Gráfico de porcentaje diario de atenciones de urgencia por causa en el Sistema Circulatorio.

    Se calcula el porcentaje que representa cada causa (infarto, accidente, crisis, arritmia y otras)
    respecto al total de atenciones del sistema circulatorio. Además se agrega la serie de temperatura
    máxima (con alertas) en un eje secundario.
    """
    # Agrupar datos por causa
    df_total_sc = df[df['Causa'] == diccionario_causas_au[12]].groupby('fecha')[col].sum().reset_index()
    df_infarto = df[df['Causa'] == diccionario_causas_au[13]].groupby('fecha')[col].sum().reset_index()
    df_accidente = df[df['Causa'] == diccionario_causas_au[14]].groupby('fecha')[col].sum().reset_index()
    df_crisis = df[df['Causa'] == diccionario_causas_au[15]].groupby('fecha')[col].sum().reset_index()
    df_arritmia = df[df['Causa'] == diccionario_causas_au[16]].groupby('fecha')[col].sum().reset_index()
    df_otras = df[df['Causa'] == diccionario_causas_au[17]].groupby('fecha')[col].sum().reset_index()

    # Calcular porcentajes diarios
    porcentajes = pd.DataFrame()
    porcentajes['fecha'] = df_total_sc['fecha']
    porcentajes['Infarto agudo miocardio (%)'] = (df_infarto[col] / df_total_sc[col]) * 100
    porcentajes['Accidente vascular encefálico (%)'] = (df_accidente[col] / df_total_sc[col]) * 100
    porcentajes['Crisis hipertensiva (%)'] = (df_crisis[col] / df_total_sc[col]) * 100
    porcentajes['Arritmia grave (%)'] = (df_arritmia[col] / df_total_sc[col]) * 100
    porcentajes['Otras causas circulatorias (%)'] = (df_otras[col] / df_total_sc[col]) * 100

    # Crear la figura
    fig = go.Figure()
    # Usar tonos de azul de la paleta de atenciones para cada causa
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Infarto agudo miocardio (%)'],
                             mode='lines', name='Infarto agudo miocardio (%)',
                             line=dict(color=colors_atenciones['Infarto agudo miocardio'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Accidente vascular encefálico (%)'],
                             mode='lines', name='Accidente vascular encefálico (%)',
                             line=dict(color=colors_atenciones['Accidente vascular encefálico'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Crisis hipertensiva (%)'],
                             mode='lines', name='Crisis hipertensiva (%)',
                             line=dict(color=colors_atenciones['Crisis hipertensiva'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Arritmia grave (%)'],
                             mode='lines', name='Arritmia grave (%)',
                             line=dict(color=colors_atenciones['Arritmia grave'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Otras causas circulatorias (%)'],
                             mode='lines', name='Otras causas circulatorias (%)',
                             line=dict(color=colors_atenciones['Otras causas circulatorias'])))
    # Agregar la traza de temperatura (eje Y2) con su color distintivo
    df_temp = df_temp.copy()
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'
    fig.add_trace(go.Scatter(x=df_temp['date'], y=df_temp['t_max'],
                             mode='lines', name='Temperatura Máxima',
                             line=dict(color=color_temperatura), yaxis='y2'))
    # Agregar marcadores de alerta (eje Y2)
    for alerta, color in colors_alerta.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(x=df_alerta['date'], y=df_alerta['t_max'],
                                 mode='markers', name=f'Alerta: {alerta}',
                                 marker=dict(color=color), yaxis='y2'))
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis=dict(title='Porcentaje (%)'),
        yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right'),
        template='plotly_white',
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    df_base = pd.DataFrame({
        'Fecha': porcentajes['fecha'],
        'Infarto agudo miocardio (%)': porcentajes['Infarto agudo miocardio (%)'],
        'Accidente vascular encefálico (%)': porcentajes['Accidente vascular encefálico (%)'],
        'Crisis hipertensiva (%)': porcentajes['Crisis hipertensiva (%)'],
        'Arritmia grave (%)': porcentajes['Arritmia grave (%)'],
        'Otras causas circulatorias (%)': porcentajes['Otras causas circulatorias (%)'],
        'Temperatura Máxima': df_temp.set_index('date').reindex(porcentajes['fecha'], method='nearest')['t_max'].values
    })
    return fig, df_base


def grafico_total_grupo_etario(df, df_temp, title):
    """
    Gráfico de consultas de urgencia por grupos etarios en el Sistema Circulatorio.

    Se muestran tanto la tendencia total (línea azul) como la contribución por grupo etario mediante barras.
    También se superpone la temperatura máxima (con alertas) en un eje secundario.
    """
    df_filtrado = df[df['Causa'] == diccionario_causas_au[12]]
    # Agrupar por fecha para cada grupo etario
    df_total = df_filtrado.groupby('fecha')['Total'].sum().reset_index()
    df_menores_1 = df_filtrado.groupby('fecha')['Menores_1'].sum().reset_index()
    df_1_a_4 = df_filtrado.groupby('fecha')['De_1_a_4'].sum().reset_index()
    df_5_a_14 = df_filtrado.groupby('fecha')['De_5_a_14'].sum().reset_index()
    df_15_a_64 = df_filtrado.groupby('fecha')['De_15_a_64'].sum().reset_index()
    df_65_y_mas = df_filtrado.groupby('fecha')['De_65_y_mas'].sum().reset_index()

    fig = go.Figure()
    # Línea del total (usamos un azul oscuro)
    fig.add_trace(go.Scatter(x=df_total['fecha'], y=df_total['Total'],
                             mode='lines', name='Total',
                             line=dict(color='#08306B')))
    # Barras por grupo etario usando la paleta definida
    fig.add_trace(go.Bar(x=df_menores_1['fecha'], y=df_menores_1['Menores_1'],
                         name='Menores_1', marker=dict(color=colors_grupo_etario['Menores_1'])))
    fig.add_trace(go.Bar(x=df_1_a_4['fecha'], y=df_1_a_4['De_1_a_4'],
                         name='De_1_a_4', marker=dict(color=colors_grupo_etario['De_1_a_4'])))
    fig.add_trace(go.Bar(x=df_5_a_14['fecha'], y=df_5_a_14['De_5_a_14'],
                         name='De_5_a_14', marker=dict(color=colors_grupo_etario['De_5_a_14'])))
    fig.add_trace(go.Bar(x=df_15_a_64['fecha'], y=df_15_a_64['De_15_a_64'],
                         name='De_15_a_64', marker=dict(color=colors_grupo_etario['De_15_a_64'])))
    fig.add_trace(go.Bar(x=df_65_y_mas['fecha'], y=df_65_y_mas['De_65_y_mas'],
                         name='De_65_y_mas', marker=dict(color=colors_grupo_etario['De_65_y_mas'])))
    # Configurar alertas de temperatura y agregar la serie en eje Y2
    df_temp = df_temp.copy()
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'
    fig.add_trace(go.Scatter(x=df_temp['date'], y=df_temp['t_max'],
                             mode='lines', name='Temperatura Máxima',
                             line=dict(color=color_temperatura), yaxis='y2'))
    # Agregar marcadores de alerta (eje Y2)
    for alerta, color in colors_alerta.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(x=df_alerta['date'], y=df_alerta['t_max'],
                                 mode='markers', name=f'Alerta: {alerta}',
                                 marker=dict(color=color), yaxis='y2'))
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title='Cantidad de Consultas',
        barmode='stack',
        template='plotly_white',
        yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right'),
        legend=dict(title='Grupos Etarios', orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    df_base = pd.DataFrame({
        'Fecha': df_total['fecha'],
        'Total': df_total['Total'],
        'Menores_1': df_menores_1['Menores_1'],
        'De_1_a_4': df_1_a_4['De_1_a_4'],
        'De_5_a_14': df_5_a_14['De_5_a_14'],
        'De_15_a_64': df_15_a_64['De_15_a_64'],
        'De_65_y_mas': df_65_y_mas['De_65_y_mas'],
        'Temperatura Máxima': df_temp.set_index('date').reindex(df_total['fecha'], method='nearest')['t_max'].values
    })

    return fig, df_base


def grafico_grupos_interes_epidemiologico(df, df_temp, title):
    """
    Gráfico de consultas de urgencia en grupos de interés epidemiológico.

    Se filtra la información para el sistema circulatorio y se muestran las consultas de:
      - Menores de 1 año
      - Adultos mayores (De_65_y_mas)
    También se superpone la serie de temperatura máxima (con alertas) en un eje secundario.
    """
    df_filtrado = df[df['Causa'] == diccionario_causas_au[12]]
    df_menores_1 = df_filtrado.groupby('fecha')['Menores_1'].sum().reset_index()
    df_65_y_mas = df_filtrado.groupby('fecha')['De_65_y_mas'].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_menores_1['fecha'], y=df_menores_1['Menores_1'],
                         name='Menores_1', marker=dict(color=colors_grupo_etario['Menores_1'])))
    fig.add_trace(go.Bar(x=df_65_y_mas['fecha'], y=df_65_y_mas['De_65_y_mas'],
                         name='De_65_y_mas', marker=dict(color=colors_grupo_etario['De_65_y_mas'])))

    df_temp = df_temp.copy()
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'

    fig.add_trace(go.Scatter(x=df_temp['date'], y=df_temp['t_max'],
                             mode='lines', name='Temperatura Máxima',
                             line=dict(color=color_temperatura), yaxis='y2'))
    for alerta, color in colors_alerta.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(x=df_alerta['date'], y=df_alerta['t_max'],
                                 mode='markers', name=f'Alerta: {alerta}',
                                 marker=dict(color=color), yaxis='y2'))
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis_title='Cantidad de Consultas',
        barmode='stack',
        template='plotly_white',
        yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right'),
        legend=dict(title='Grupos de Interés', orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    df_base = pd.DataFrame({
        'Fecha': df_menores_1['fecha'],
        'Menores_1': df_menores_1['Menores_1'],
        'De_65_y_mas': df_65_y_mas['De_65_y_mas'],
        'Temperatura Máxima': df_temp.set_index('date').reindex(df_menores_1['fecha'], method='nearest')['t_max'].values
    })

    return fig, df_base


def grafico_porcentaje_total(df, df_temp, col, title):
    """
    Gráfico del porcentaje de atenciones de urgencia de causas del sistema circulatorio
    respecto al total general de atenciones de urgencia.

    Se calculan los porcentajes diarios y se superpone la serie de temperatura máxima (con alertas) en un eje secundario.
    """
    df_total_urgencias = df[df['Causa'] == 'Atenciones de urgencia - Total'].groupby('fecha')[col].sum().reset_index()
    df_total_sc = df[df['Causa'] == 'Atenciones de urgencia - Total Sistema Circulatorio'].groupby('fecha')[col].sum().reset_index()
    df_infarto = df[df['Causa'] == 'Atenciones de urgencia - Infarto agudo miocardio'].groupby('fecha')[col].sum().reset_index()
    df_accidente = df[df['Causa'] == 'Atenciones de urgencia - Accidente vascular encefálico'].groupby('fecha')[col].sum().reset_index()
    df_crisis = df[df['Causa'] == 'Atenciones de urgencia - Crisis hipertensiva'].groupby('fecha')[col].sum().reset_index()
    df_arritmia = df[df['Causa'] == 'Atenciones de urgencia - Arritmia grave'].groupby('fecha')[col].sum().reset_index()
    df_otras = df[df['Causa'] == 'Atenciones de urgencia - Otras causas circulatorias'].groupby('fecha')[col].sum().reset_index()

    porcentajes = pd.DataFrame()
    porcentajes['fecha'] = df_total_urgencias['fecha']
    porcentajes['Infarto agudo miocardio (%)'] = (df_infarto[col] / df_total_urgencias[col]) * 100
    porcentajes['Accidente vascular encefálico (%)'] = (df_accidente[col] / df_total_urgencias[col]) * 100
    porcentajes['Crisis hipertensiva (%)'] = (df_crisis[col] / df_total_urgencias[col]) * 100
    porcentajes['Arritmia grave (%)'] = (df_arritmia[col] / df_total_urgencias[col]) * 100
    porcentajes['Otras causas circulatorias (%)'] = (df_otras[col] / df_total_urgencias[col]) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Infarto agudo miocardio (%)'],
                             mode='lines', name='Infarto agudo miocardio (%)',
                             line=dict(color=colors_atenciones['Infarto agudo miocardio'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Accidente vascular encefálico (%)'],
                             mode='lines', name='Accidente vascular encefálico (%)',
                             line=dict(color=colors_atenciones['Accidente vascular encefálico'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Crisis hipertensiva (%)'],
                             mode='lines', name='Crisis hipertensiva (%)',
                             line=dict(color=colors_atenciones['Crisis hipertensiva'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Arritmia grave (%)'],
                             mode='lines', name='Arritmia grave (%)',
                             line=dict(color=colors_atenciones['Arritmia grave'])))
    fig.add_trace(go.Scatter(x=porcentajes['fecha'], y=porcentajes['Otras causas circulatorias (%)'],
                             mode='lines', name='Otras causas circulatorias (%)',
                             line=dict(color=colors_atenciones['Otras causas circulatorias'])))
    # Agregar la traza de temperatura (eje Y2)
    df_temp = df_temp.copy()
    df_temp['alerta'] = 'Sin Alerta'
    df_temp['mes'] = df_temp['date'].dt.month
    df_temp.loc[df_temp['mes'].isin([11, 12, 1, 2, 3]), 'alerta'] = 'Alerta temprana preventiva'
    df_temp.loc[df_temp['t_max'] >= 40, 'alerta'] = 'Alerta Roja'
    df_temp['alerta_temporal'] = df_temp['t_max'] >= 34
    df_temp['alerta_consecutiva'] = df_temp['alerta_temporal'].rolling(window=2).sum()
    df_temp.loc[df_temp['alerta_consecutiva'] >= 2, 'alerta'] = 'Alerta Amarilla'
    df_temp['alerta_consecutiva_3'] = df_temp['alerta_temporal'].rolling(window=3).sum()
    df_temp.loc[df_temp['alerta_consecutiva_3'] >= 3, 'alerta'] = 'Alerta Roja'
    fig.add_trace(go.Scatter(x=df_temp['date'], y=df_temp['t_max'],
                             mode='lines', name='Temperatura Máxima',
                             line=dict(color=color_temperatura), yaxis='y2'))
    for alerta, color in colors_alerta.items():
        df_alerta = df_temp[df_temp['alerta'] == alerta]
        fig.add_trace(go.Scatter(x=df_alerta['date'], y=df_alerta['t_max'],
                                 mode='markers', name=f'Alerta: {alerta}',
                                 marker=dict(color=color), yaxis='y2'))
    fig.update_layout(
        title=title,
        xaxis_title='Fecha',
        yaxis=dict(title='Porcentaje (%)'),
        yaxis2=dict(title='Temperatura Máxima', overlaying='y', side='right'),
        template='plotly_white',
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    df_base = pd.DataFrame({
        'Fecha': porcentajes['fecha'],
        'Infarto agudo miocardio (%)': porcentajes['Infarto agudo miocardio (%)'],
        'Accidente vascular encefálico (%)': porcentajes['Accidente vascular encefálico (%)'],
        'Crisis hipertensiva (%)': porcentajes['Crisis hipertensiva (%)'],
        'Arritmia grave (%)': porcentajes['Arritmia grave (%)'],
        'Otras causas circulatorias (%)': porcentajes['Otras causas circulatorias (%)'],
        'Temperatura Máxima': df_temp.set_index('date').reindex(porcentajes['fecha'], method='nearest')['t_max'].values
    })
    return fig, df_base

# %% 4. Construcción de la aplicación principal y renderización de gráficos

st.title("Análisis de Atenciones de Urgencia y Temperatura en el Sistema Circulatorio")
st.write("Esta página permite analizar la evolución de las atenciones de urgencia y su relación con la temperatura máxima. Cada sección incluye una explicación, el gráfico interactivo, y una tabla con los datos de los últimos 10 días, con opción de descargar los datos en Excel.")

### Gráfico 1: Evolución de Atenciones de Urgencia
st.header("Evolución de Atenciones de Urgencia en el Sistema Circulatorio")
st.markdown(
    """
    **Descripción:**  
    Este gráfico muestra la evolución temporal de las atenciones de urgencia (desglosadas por causa) y la serie de temperatura máxima (con alertas) dentro del rango de fechas seleccionado.
    """
)
fig1, base_area = grafico_area_atenciones_respiratorias(df_au, df_tmm, 'Total',
                                                        'Evolución de Atenciones de Urgencia en el Sistema Circulatorio')
st.plotly_chart(fig1, use_container_width=True)
st.markdown("**Tabla: Últimos 10 días (Defunciones Cardiovasculares)**")
table1 = base_area.sort_values(by='Fecha').tail(10)
st.table(table1)
st.download_button(
    label="Descargar Tabla (Excel)",
    data=to_excel_bytes(table1),
    file_name="tabla_area_atenciones_urgencia.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
st.download_button(
    label="Descargar Datos (Excel)",
    data=to_excel_bytes(base_area),
    file_name="datos_area_atenciones_urgencia.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

### Gráfico 2: Porcentaje de Atenciones de Urgencia
st.header("Porcentaje de Atenciones de Urgencia por Causa")
st.markdown(
    """
    **Descripción:**  
    Este gráfico presenta el porcentaje diario de atenciones de urgencia (por causa) respecto al total, 
    junto con la serie de temperatura máxima (y sus alertas) para complementar el análisis.
    """
)
fig2, base_porcentaje = grafico_porcentaje_atenciones(df_au, df_tmm, 'Total',
                                                      'Porcentaje de Atenciones de Urgencia por Causa')
st.plotly_chart(fig2, use_container_width=True)
st.markdown("**Tabla: Últimos 10 días (Porcentaje de Atenciones)**")
table2 = base_porcentaje.sort_values(by='Fecha').tail(10)
st.table(table2)
st.download_button(
    label="Descargar Tabla (Excel)",
    data=to_excel_bytes(table2),
    file_name="tabla_porcentaje_atenciones.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
st.download_button(
    label="Descargar Datos (Excel)",
    data=to_excel_bytes(base_porcentaje),
    file_name="datos_porcentaje_atenciones.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

### Gráfico 3: Atenciones por Grupo de Edad
st.header("Atenciones de Urgencia por Grupo de Edad")
st.markdown(
    """
    **Descripción:**  
    Este gráfico muestra la distribución diaria de atenciones de urgencia por grupo de edad 
    (clasificados como **< 1 año**, **>= 85 años** y **Otros**), superponiendo la serie de temperatura máxima (y alertas) en un eje secundario.
    """
)
fig3, base_grupo = grafico_total_grupo_etario(df_au, df_tmm,
                                              'Consultas de Urgencia por Grupos Etarios del Sistema Circulatorio')
st.plotly_chart(fig3, use_container_width=True)
st.markdown("**Tabla: Últimos 10 días (Atenciones por Grupo de Edad)**")
table3 = base_grupo.sort_values(by='Fecha').tail(10)
st.table(table3)
st.download_button(
    label="Descargar Tabla (Excel)",
    data=to_excel_bytes(table3),
    file_name="tabla_atenciones_por_grupo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
st.download_button(
    label="Descargar Datos (Excel)",
    data=to_excel_bytes(base_grupo),
    file_name="datos_atenciones_por_grupo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

### Gráfico 4: Porcentaje de Atenciones por Grupo de Edad
st.header("Porcentaje de Atenciones por Grupo de Edad")
st.markdown(
    """
    **Descripción:**  
    Este gráfico presenta el porcentaje diario de atenciones de urgencia por grupo de edad 
    (comparando **< 1 año**, **>= 85 años** y **Otros**) respecto al total diario, 
    con la serie de temperatura máxima (y alertas) superpuesta en un eje secundario.
    """
)
fig4, base_porcentaje_grupo = grafico_porcentaje_total(df_au, df_tmm, 'Total',
                                                       'Porcentaje de Atenciones por Causa (Total General)')
st.plotly_chart(fig4, use_container_width=True)
st.markdown("**Tabla: Últimos 10 días (Porcentaje de Atenciones por Grupo de Edad)**")
table4 = base_porcentaje_grupo.sort_values(by='Fecha').tail(10)
st.table(table4)
st.download_button(
    label="Descargar Tabla (Excel)",
    data=to_excel_bytes(table4),
    file_name="tabla_porcentaje_atenciones_por_grupo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.markdown("**Descargar Datos Utilizados en el Gráfico (Excel):**")
st.download_button(
    label="Descargar Datos (Excel)",
    data=to_excel_bytes(base_porcentaje_grupo),
    file_name="datos_porcentaje_atenciones_por_grupo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# %% 5. Sección Final: Descargar Bases de Datos Completas (en CSV)
st.header("Descargar Bases de Datos Completas")
st.markdown(
    """
    **Bases de Datos Completas:**  
    A continuación, puedes descargar los archivos CSV originales que contienen toda la información utilizada en este análisis.
    """
)
with open("data_atenciones_urgencia/df_rm_circ_2024.csv", "rb") as file_au:
    data_au_csv = file_au.read()
st.download_button(
    label="Descargar Base de Atenciones de Urgencia (CSV)",
    data=data_au_csv,
    file_name="df_rm_circ_2024.csv",
    mime="text/csv"
)
with open("data_temperatura/tmm_historico_2024.csv", "rb") as file_tmm:
    data_tmm_csv = file_tmm.read()
st.download_button(
    label="Descargar Base de Temperaturas (CSV)",
    data=data_tmm_csv,
    file_name="tmm_historico_2024.csv",
    mime="text/csv"
)
